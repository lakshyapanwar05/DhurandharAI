from __future__ import annotations

import asyncio
import json
import os
import random
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ai.assistant import llm_router
from app.store import store
from app.db.supabase_client import log_incident, log_network_snapshot, log_chat, resolve_all_active_incidents, get_recent_incidents, get_incident_stats, resolve_incident, log_real_attack, get_real_attacks
import threading
from engine.correlation import correlation_engine
from simulation.mininet_sim import scenario_manager

load_dotenv()

# ---------------------------------------------------------------------------
# Sync wrapper for Supabase functions
# ---------------------------------------------------------------------------

def log_incident_sync(alert):
    """Sync wrapper for log_incident with error handling"""
    try:
        result = log_incident(alert)
        print("✅ SUPABASE LOG SUCCESS")
        return result
    except Exception as e:
        print(f"❌ Supabase ERROR logging incident: {e}")
        return None

def log_network_snapshot_sync(event):
    """Sync wrapper for log_network_snapshot with error handling"""
    try:
        result = log_network_snapshot(event)
        print("✅ SUPABASE SNAPSHOT SUCCESS")
        return result
    except Exception as e:
        print(f"❌ Supabase ERROR logging snapshot: {e}")
        return None

def log_chat_sync(user_msg, ai_response, provider, context):
    """Sync wrapper for log_chat with error handling"""
    try:
        result = log_chat(user_msg, ai_response, provider, context)
        print("✅ SUPABASE CHAT SUCCESS")
        return result
    except Exception as e:
        print(f"❌ Supabase ERROR logging chat: {e}")
        return None

# ---------------------------------------------------------------------------
# WebSocket connection manager
# ---------------------------------------------------------------------------

class ConnectionManager:
    def __init__(self) -> None:
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self.active.remove(ws)

    async def broadcast(self, data: dict[str, Any]) -> None:
        payload = json.dumps(data)
        stale: list[WebSocket] = []
        for ws in self.active:
            try:
                await ws.send_text(payload)
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.active.remove(ws)


manager = ConnectionManager()

# ---------------------------------------------------------------------------
# Background broadcaster
# ---------------------------------------------------------------------------

_broadcast_task: asyncio.Task[None] | None = None
_broadcast_counter = 0


async def _broadcaster() -> None:
    """Fetch the current simulation state, run correlation, and broadcast every 2 seconds."""
    global _broadcast_counter
    while True:
        event = scenario_manager.get_current_state()
        _broadcast_counter += 1

        # Only generate alerts if a scenario is active
        if scenario_manager.active_scenario:
            # Run correlation engine against the domain snapshot
            engine_alerts = correlation_engine.correlate(event.get("domains", {}))
            if engine_alerts:
                print(f"🔍 Correlation engine found {len(engine_alerts)} alerts")
            else:
                print(f"🔍 Correlation engine: no alerts found")

            # Merge: scenario-generated alerts + engine-generated alerts (deduplicated by rule)
            scenario_alerts = event.get("correlated_alerts", [])
            if scenario_alerts:
                print(f"📋 Scenario alerts: {len(scenario_alerts)}")
            seen_rules = {a.get("title", "") for a in scenario_alerts}
            for ea in engine_alerts:
                if ea["rule_name"] not in seen_rules:
                    scenario_alerts.append(ea)
                    seen_rules.add(ea["rule_name"])
            event["correlated_alerts"] = scenario_alerts

            # Log incidents to Supabase when alerts fire
            for alert in scenario_alerts:
                print(f"🚨 Logging incident: {alert.get('rule_name', 'Unknown')} - {alert.get('severity', 'medium')}")
                # Run in thread to avoid blocking
                threading.Thread(target=lambda: log_incident_sync(alert), daemon=True).start()
        else:
            # No scenario active - clear alerts and only broadcast baseline data
            event["correlated_alerts"] = []
            print(f"🔍 No active scenario - broadcasting baseline only")

        # Log network snapshot to Supabase every 10 ticks (20 seconds)
        if _broadcast_counter % 10 == 0:
            # Run in thread to avoid blocking
            threading.Thread(target=lambda: log_network_snapshot_sync(event), daemon=True).start()

        # Add scenario_active to the event for frontend
        event["scenario_active"] = scenario_manager.active_scenario
        alerts_count = len(event.get("correlated_alerts", []))
        print(f"📡 Broadcasting: scenario_active={scenario_manager.active_scenario}, alerts={alerts_count}")
        
        # Accumulate all correlated alerts into the persistent store
        for alert in event.get("correlated_alerts", []):
            store.push_alert(alert)
        store.push_event(event)
        await manager.broadcast(event)
        await asyncio.sleep(2)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _broadcast_task
    _broadcast_task = asyncio.create_task(_broadcaster())
    yield
    _broadcast_task.cancel()
    try:
        await _broadcast_task
    except asyncio.CancelledError:
        pass


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="Dhurandar AI", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for hackathon demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await manager.connect(ws)
    try:
        while True:
            try:
                # Wait for any message (ping) from client
                data = await asyncio.wait_for(
                    ws.receive_text(), 
                    timeout=30.0
                )
                # Echo back any non-ping messages
                try:
                    parsed = json.loads(data)
                    if parsed.get("type") != "ping":
                        print(f"📨 WebSocket received: {parsed}")
                except:
                    print(f"📨 WebSocket received text: {data}")
            except asyncio.TimeoutError:
                # Send ping to keep alive
                await ws.send_json({"type": "ping"})
                print("🏓 WebSocket ping sent")
    except WebSocketDisconnect:
        manager.disconnect(ws)
        print("🔌 WebSocket disconnected")

# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {"message": "Dhurandar AI backend is running"}


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "gemini_key_set": bool(os.getenv("GEMINI_API_KEY")),
        "influxdb_url_set": bool(os.getenv("INFLUXDB_URL")),
        "llm_provider": llm_router.active_provider,
    }


# -- /api/alerts -------------------------------------------------------

@app.get("/api/alerts")
async def get_alerts():
    return {"alerts": store.get_alerts(50)}


# -- /api/chat ----------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    network_context: dict[str, Any] | None = None


@app.post("/api/chat")
async def chat(req: ChatRequest):
    result = await llm_router.ask(req.message, req.network_context)
    
    # Log chat interaction to Supabase
    # Run in thread to avoid blocking
    threading.Thread(
        target=lambda: log_chat_sync(
            req.message, 
            result["reply"], 
            result["provider"], 
            req.network_context or {}
        ),
        daemon=True
    ).start()
    
    return {
        "reply": result["reply"],
        "provider": result["provider"],
        "cached": result["cached"],
    }


# -- /api/simulate/attack -----------------------------------------------

class AttackRequest(BaseModel):
    scenario: str = "ddos"


@app.post("/api/simulate/attack")
async def simulate_attack(req: AttackRequest):
    print(f"🎯 Starting scenario: {req.scenario}")
    result = await scenario_manager.start_scenario(req.scenario)
    print(f"✅ Scenario result: {result}")
    return result


# -- /api/simulate/stop -------------------------------------------------

@app.post("/api/simulate/stop")
async def simulate_stop():
    result = await scenario_manager.stop_scenario()
    return result


# -- /api/simulate/status -----------------------------------------------

@app.get("/api/simulate/status")
async def simulate_status():
    return {
        "active_scenario": scenario_manager.active_scenario,
        "available": ["ddos", "cryptominer", "bruteforce", "insider"],
    }


# -- /api/simulate/reset -------------------------------------------------

@app.post("/api/simulate/reset")
async def simulate_reset():
    # Stop active scenario and resolve all incidents
    await scenario_manager.stop_scenario()
    resolved_count = resolve_all_active_incidents()
    return {
        "message": "System reset to normal",
        "resolved_incidents": resolved_count
    }


# -- /api/incidents -------------------------------------------------------

@app.get("/api/incidents")
async def get_incidents():
    print("🔍 API: /api/incidents called")
    incidents = get_recent_incidents(50)
    print(f"📊 API: Returning {len(incidents)} incidents")
    return {"incidents": incidents}


@app.get("/api/incidents/stats")
async def get_incident_stats_endpoint():
    stats = get_incident_stats()
    return stats


@app.patch("/api/incidents/resolve-all")
async def resolve_all_incidents_endpoint():
    print("🔍 API: /api/incidents/resolve-all called")
    resolved_count = resolve_all_active_incidents()
    success = resolved_count > 0
    return {"success": success, "resolved_count": resolved_count, "message": f"Resolved {resolved_count} incidents" if success else "No active incidents to resolve"}


@app.patch("/api/incidents/{incident_id}/resolve")
async def resolve_incident_endpoint(incident_id: int):
    success = resolve_incident(incident_id)
    return {"success": success}


# -- /api/report/generate -------------------------------------------------

@app.get("/api/report/generate")
async def generate_threat_report():
    """Generate threat report from last 50 incidents using Gemini"""
    incidents = get_recent_incidents(50)
    
    if not incidents:
        return {"report": "# No incidents to report\n\nSystem is operating normally."}
    
    # Format incidents for AI analysis
    incident_text = "\n\n".join([
        f"- {inc.get('timestamp', '')}: {inc.get('severity', 'medium').upper()} - {inc.get('rule_name', 'Unknown')} affecting {inc.get('affected_domains', [])}"
        for inc in incidents[:20]  # Limit to 20 for context
    ])
    
    prompt = f"""Generate a comprehensive threat analysis report based on these recent incidents:

{incident_text}

Please provide:
1. Executive Summary (2-3 sentences)
2. Threat Landscape Overview
3. Critical Findings
4. Recommendations (numbered list)
5. Risk Assessment (Low/Medium/High/Critical)

Format as markdown with headers."""
    
    try:
        result = await llm_router.ask(prompt, {})
        return {"report": result["reply"]}
    except Exception as e:
        return {"report": f"# Error generating report\n\n{str(e)}"}


# -- /api/chat/proactive --------------------------------------------------

@app.post("/api/chat/proactive")
async def proactive_alert(incident: dict[str, Any]):
    """Generate proactive AI alert for incident"""
    prompt = f"""Generate a 2-sentence urgent proactive alert for this security incident:

Incident: {incident.get('rule_name', 'Unknown')}
Severity: {incident.get('severity', 'medium')}
Affected: {incident.get('affected_domains', [])}

Make it urgent and actionable. Start with "🚨 PROACTIVE ALERT": """
    
    try:
        result = await llm_router.ask(prompt, {})
        return {
            "message": result["reply"],
            "provider": result["provider"]
        }
    except Exception as e:
        return {
            "message": f"🚨 PROACTIVE ALERT: {incident.get('rule_name', 'Unknown')} detected affecting {incident.get('affected_domains', [])}. Immediate investigation recommended.",
            "provider": "stub"
        }


# -- /api/attack/receive -------------------------------------------------

class RealAttackRequest(BaseModel):
    attack_type: str
    source_ip: str
    target_ip: str
    payload: dict[str, Any]
    timestamp: str


# Global state for real attacks
_real_attack_state = {
    "last_attack": None,
    "connected_ips": set(),
    "total_attacks_received": 0
}


@app.post("/api/attack/receive")
async def receive_real_attack(req: RealAttackRequest):
    """Receive real attack events from external attacker devices"""
    print("=" * 60)
    print(f"🚨 REAL ATTACK RECEIVED: {req.attack_type} from {req.source_ip} to {req.target_ip}")
    print("=" * 60)
    print(f"🔍 Request data: {req}")
    print(f"🔍 Active WebSocket clients: {len(manager.active)}")
    print(f"🔍 Raw request received at endpoint!")
    
    # Update attack state
    _real_attack_state["last_attack"] = {
        "attack_type": req.attack_type,
        "source_ip": req.source_ip,
        "target_ip": req.target_ip,
        "timestamp": req.timestamp,
        "payload": req.payload
    }
    _real_attack_state["connected_ips"].add(req.source_ip)
    _real_attack_state["total_attacks_received"] += 1
    
    # Map attack_type to scenario
    scenario_mapping = {
        "ddos": "ddos",
        "bruteforce": "bruteforce", 
        "cryptominer": "cryptominer",
        "insider": "insider"
    }
    
    scenario = scenario_mapping.get(req.attack_type.lower(), "ddos")
    
    # Get current state and inject real source_ip
    event = scenario_manager.get_current_state()
    event["real_attack"] = {
        "source_ip": req.source_ip,
        "target_ip": req.target_ip,
        "payload": req.payload,
        "timestamp": req.timestamp
    }
    event["attack_mode"] = "real"  # Mark as real attack
    event["scenario_active"] = scenario  # Ensure scenario is set
    
    # Apply visual changes based on attack type (same as simulated attacks)
    if scenario == "ddos":
        # DDoS visual effects
        event["domains"]["network"]["packets_per_second"] = random.randint(30000, 55000)
        event["domains"]["network"]["ddos_score"] = round(random.uniform(0.7, 0.98), 2)
        event["domains"]["network"]["anomaly"] = True
        event["domains"]["hardware"]["cpu_percent"] = round(random.uniform(70.0, 95.0), 1)
        event["domains"]["hardware"]["memory_percent"] = round(random.uniform(60.0, 85.0), 1)
        event["domains"]["hardware"]["anomaly"] = True
        event["domains"]["security"]["firewall_hits"] = random.randint(1000, 5000)
        event["domains"]["security"]["ids_alerts"] = random.sample([
            "DDoS attack detected", "Volumetric flood", "Packet storm"
        ], random.randint(1, 3))
        event["domains"]["security"]["anomaly"] = True
        
    elif scenario == "bruteforce":
        # Brute force visual effects
        event["domains"]["user"]["active_users"] = random.randint(80, 120)
        event["domains"]["user"]["flagged_logins"] = [
            f"Failed login from {req.source_ip}" for _ in range(random.randint(5, 15))
        ]
        event["domains"]["user"]["anomaly"] = True
        event["domains"]["security"]["firewall_hits"] = random.randint(500, 2000)
        event["domains"]["security"]["ids_alerts"] = [
            "Brute force attack detected", "SSH login attempts"
        ]
        event["domains"]["security"]["anomaly"] = True
        
    elif scenario == "cryptominer":
        # Cryptomining visual effects
        event["domains"]["hardware"]["cpu_percent"] = round(random.uniform(85.0, 98.0), 1)
        event["domains"]["hardware"]["memory_percent"] = round(random.uniform(70.0, 90.0), 1)
        event["domains"]["hardware"]["anomaly"] = True
        event["domains"]["network"]["packets_per_second"] = random.randint(5000, 15000)
        event["domains"]["network"]["anomaly"] = True
        event["domains"]["security"]["ids_alerts"] = [
            "Cryptocurrency mining detected", "Suspicious process activity"
        ]
        event["domains"]["security"]["anomaly"] = True
        
    elif scenario == "insider":
        # Insider threat visual effects
        event["domains"]["user"]["active_users"] = random.randint(20, 40)
        event["domains"]["user"]["flagged_logins"] = [
            f"Unusual access from {req.source_ip}",
            f"Privilege escalation attempt"
        ]
        event["domains"]["user"]["anomaly"] = True
        event["domains"]["security"]["firewall_hits"] = random.randint(100, 500)
        event["domains"]["security"]["ids_alerts"] = [
            "Insider threat detected", "Data exfiltration pattern"
        ]
        event["domains"]["security"]["anomaly"] = True
    
    # Trigger correlation engine immediately
    engine_alerts = correlation_engine.correlate(event.get("domains", {}))
    print(f"🔍 Real attack correlation: {len(engine_alerts)} alerts found")
    
    # Merge alerts
    scenario_alerts = event.get("correlated_alerts", [])
    seen_rules = {a.get("title", "") for a in scenario_alerts}
    
    for ea in engine_alerts:
        # Inject real source_ip into alert
        ea["root_cause"] = f"Real attack from {req.source_ip}"
        if ea["rule_name"] not in seen_rules:
            scenario_alerts.append(ea)
            seen_rules.add(ea["rule_name"])
    
    # If no alerts generated, create a basic real attack alert
    if not scenario_alerts:
        basic_alert = {
            "rule_name": f"Real {scenario.title()} Attack",
            "severity": "high",
            "affected_domains": ["network"],
            "root_cause": f"Real attack from {req.source_ip}",
            "recommended_actions": "Investigate source IP and block if malicious",
            "confidence_score": 0.9,
            "matched_indicators": [f"External attack from {req.source_ip}"]
        }
        scenario_alerts = [basic_alert]
        print(f"🚨 Created basic real attack alert for {req.source_ip}")
    
    event["correlated_alerts"] = scenario_alerts
    
    # Log real attack to dedicated real_attacks table
    real_attack_data = {
        "attack_type": req.attack_type,
        "source_ip": req.source_ip,
        "target_ip": req.target_ip,
        "payload": req.payload,
        "timestamp": req.timestamp
    }
    threading.Thread(target=lambda: log_real_attack(real_attack_data), daemon=True).start()
    
    # Log incidents to Supabase with real source_ip and enhanced tracking
    for alert in scenario_alerts:
        alert["root_cause"] = f"Real attack from {req.source_ip}"
        alert["is_real_attack"] = True
        alert["source_ip"] = req.source_ip
        alert["target_ip"] = req.target_ip
        alert["attack_payload"] = req.payload
        alert["attack_type"] = req.attack_type
        print(f"🚨 Logging REAL incident: {alert.get('rule_name', 'Unknown')} from {req.source_ip}")
        threading.Thread(target=lambda: log_incident_sync(alert), daemon=True).start()
    
    # Start the scenario system for real attacks (this handles visuals)
    scenario_manager.start_scenario(req.attack_type)
    print(f"🎬 Started scenario: {req.attack_type} for real attack from {req.source_ip}")
    
    # Broadcast immediately to all WebSocket clients
    event["scenario_active"] = scenario
    event["real_attacker_ip"] = req.source_ip  # Add real attacker IP
    event["is_real_attack"] = True  # Mark as real attack
    event["attack_mode"] = "real"  # CRITICAL: Set attack mode to "real"
    alerts_count = len(event.get("correlated_alerts", []))
    print(f"📡 Broadcasting REAL ATTACK: {scenario}, source={req.source_ip}, alerts={alerts_count}")
    
    # Add to store and broadcast
    for alert in event.get("correlated_alerts", []):
        store.push_alert(alert)
    store.push_event(event)
    
    print(f"🌐 Broadcasting to {len(manager.active)} WebSocket clients")
    print(f"🔍 Event data being broadcast:")
    print(f"   - attack_mode: {event.get('attack_mode')}")
    print(f"   - real_attack: {event.get('real_attack')}")
    print(f"   - scenario_active: {event.get('scenario_active')}")
    print(f"   - correlated_alerts: {len(event.get('correlated_alerts', []))}")
    
    await manager.broadcast(event)
    print(f"✅ Broadcast complete")
    
    return {
        "status": "received",
        "attack_type": req.attack_type,
        "source_ip": req.source_ip,
        "alerts_generated": len(scenario_alerts),
        "timestamp": req.timestamp
    }


@app.get("/api/attack/status")
async def get_attack_status():
    """Get current attack status and connected attacker IPs"""
    real_attacks = get_real_attacks(20)  # Get last 20 real attacks
    return {
        "last_attack": _real_attack_state["last_attack"],
        "connected_ips": list(_real_attack_state["connected_ips"]),
        "total_attacks_received": _real_attack_state["total_attacks_received"],
        "active_scenario": scenario_manager.active_scenario,
        "recent_real_attacks": real_attacks,
        "real_attack_count": len(real_attacks)
    }


@app.get("/api/attack/history")
async def get_attack_history():
    """Get real attack history from database"""
    real_attacks = get_real_attacks(100)  # Get last 100 real attacks
    return {
        "real_attacks": real_attacks,
        "total_count": len(real_attacks)
    }
