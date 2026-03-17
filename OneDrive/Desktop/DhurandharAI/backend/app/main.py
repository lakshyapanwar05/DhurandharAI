from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ai.assistant import llm_router
from app.store import store
from engine.correlation import correlation_engine
from simulation.mininet_sim import scenario_manager

load_dotenv()

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


async def _broadcaster() -> None:
    """Fetch the current simulation state, run correlation, and broadcast every 2 seconds."""
    while True:
        event = scenario_manager.get_current_state()

        # Run correlation engine against the domain snapshot
        engine_alerts = correlation_engine.correlate(event.get("domains", {}))

        # Merge: scenario-generated alerts + engine-generated alerts (deduplicated by rule)
        scenario_alerts = event.get("correlated_alerts", [])
        seen_rules = {a.get("title", "") for a in scenario_alerts}
        for ea in engine_alerts:
            if ea["rule_name"] not in seen_rules:
                scenario_alerts.append(ea)
                seen_rules.add(ea["rule_name"])
        event["correlated_alerts"] = scenario_alerts

        # Accumulate all correlated alerts into the persistent store
        for alert in scenario_alerts:
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
    allow_origins=["http://localhost:3000"],
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
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)

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
    networkContext: dict[str, Any] | None = None


@app.post("/api/chat")
async def chat(req: ChatRequest):
    result = await llm_router.ask(req.message, req.networkContext)
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
    result = await scenario_manager.start_scenario(req.scenario)
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
