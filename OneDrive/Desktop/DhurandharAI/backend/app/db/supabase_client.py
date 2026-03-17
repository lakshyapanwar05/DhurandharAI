"""
Supabase database client for DhurandarAI
Handles incident logging, chat history, and network snapshots
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

# Make sure dotenv is loaded BEFORE reading env variables
load_dotenv()

# ---------------------------------------------------------------------------
# Supabase client initialization
# ---------------------------------------------------------------------------

# Check if Supabase credentials are available
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# Use real Supabase if credentials are available, otherwise fall back to mock
if SUPABASE_URL and SUPABASE_KEY:
    try:
        import httpx
        # Create HTTP client for Supabase REST API
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        supabase_client = httpx.Client(headers=headers, base_url=SUPABASE_URL.rstrip('/'))
        print(f"✅ Real Supabase HTTP client initialized: {SUPABASE_URL}")
        print(f"🔑 Using anon key: {SUPABASE_KEY[:20]}...")
        USE_REAL_SUPABASE = True
        
        # Create a simple wrapper that mimics the supabase-py API
        class SimpleSupabaseClient:
            def __init__(self, client):
                self.client = client
            
            def table(self, table_name: str):
                return TableOperations(self.client, table_name)
        
        class TableOperations:
            def __init__(self, client, table_name: str):
                self.client = client
                self.table_name = table_name
                self.url = f"/rest/v1/{table_name}"
            
            def insert(self, data):
                try:
                    response = self.client.post(self.url, json=data)
                    print(f"📝 Insert response: {response.status_code} - {response.text}")
                    if response.status_code == 201:
                        # Supabase returns 201 with empty body for successful inserts
                        # Create a mock response with the inserted data
                        return MockResponse([data])
                    else:
                        print(f"❌ Insert failed: {response.status_code} - {response.text}")
                        return MockResponse([])
                except Exception as e:
                    print(f"❌ Insert exception: {e}")
                    return MockResponse([])
            
            def select(self, columns="*", filters=None):
                try:
                    params = {"select": columns}
                    if filters:
                        for key, value in filters.items():
                            if key == "order":
                                # Handle order parameter properly
                                if isinstance(value, dict) and "desc" in value:
                                    params["order"] = f"{value['desc']}.desc"
                                elif isinstance(value, str) and "desc=True" in str(value):
                                    # Extract column name from "timestamp desc=True"
                                    col = str(value).split(" ")[0]
                                    params["order"] = f"{col}.desc"
                                else:
                                    params["order"] = value
                            elif key == "limit":
                                params[key] = value
                            else:
                                params[f"{key}=eq.{value}"] = "true"
                    
                    print(f"🔍 Query params: {params}")
                    response = self.client.get(self.url, params=params)
                    print(f"📝 Select response: {response.status_code} - {response.text[:200]}")
                    if response.status_code == 200:
                        data = response.json()
                        print(f"📊 Retrieved {len(data)} incidents")
                        return MockResponse(data)
                    else:
                        print(f"❌ Select failed: {response.status_code}")
                        return MockResponse([])
                except Exception as e:
                    print(f"❌ Select exception: {e}")
                    return MockResponse([])
            
            def update(self, data, filters=None):
                try:
                    # Create a new response object to capture filters
                    response_obj = MockResponse([])
                    
                    if filters:
                        params = {}
                        for key, value in filters.items():
                            params[key] = f"eq.{value}"
                    else:
                        # Use stored filters from eq() calls
                        params = {}
                        # This will be populated by the eq() method
                    
                    print(f"📝 Update params: {params}")
                    print(f"📝 Update data: {data}")
                    response = self.client.patch(self.url, json=data, params=params)
                    print(f"📝 Update response: {response.status_code} - {response.text}")
                    if response.status_code == 204:
                        # Supabase returns 204 with empty body for successful updates
                        return MockResponse([{"status": "updated"}])
                    else:
                        print(f"❌ Update failed: {response.status_code}")
                        return MockResponse([])
                except Exception as e:
                    print(f"❌ Update exception: {e}")
                    return MockResponse([])
        
        class MockResponse:
            def __init__(self, data):
                self.data = data
                self.filters = {}
            
            def execute(self):
                return self
            
            def order(self, column, desc=None):
                # For chaining, return self
                if desc:
                    # Store order info for the actual HTTP request
                    return self
                return self
            
            def limit(self, count):
                # For chaining, return self
                return self
            
            def eq(self, column, value):
                # Store filter for the actual HTTP request
                self.filters[column] = value
                return self
        
        supabase = SimpleSupabaseClient(supabase_client)
        
    except Exception as e:
        print(f"❌ Failed to initialize Supabase HTTP client: {e}")
        print("🔄 Falling back to mock implementation")
        USE_REAL_SUPABASE = False
else:
    print("⚠️  Supabase credentials not found in environment variables")
    print("🔄 Using mock implementation")
    USE_REAL_SUPABASE = False

# ---------------------------------------------------------------------------
# Incident logging functions
# ---------------------------------------------------------------------------

# Mock storage for incidents (until Supabase is properly set up)
MOCK_INCIDENTS = [
    {
        "id": 1,
        "timestamp": datetime.utcnow().isoformat(),
        "severity": "critical",
        "rule_name": "DDoS Attack Detected",
        "affected_domains": ["network", "security"],
        "confidence_score": 0.95,
        "root_cause": "Massive SYN flood from multiple sources",
        "recommended_actions": [
            "Block attacking IP ranges at firewall",
            "Enable rate limiting",
            "Activate DDoS mitigation service"
        ],
        "matched_indicators": ["syn_flood", "high_packet_rate"],
        "status": "active"
    },
    {
        "id": 2,
        "timestamp": datetime.utcnow().isoformat(),
        "severity": "high",
        "rule_name": "Suspicious Login Activity",
        "affected_domains": ["user", "security"],
        "confidence_score": 0.85,
        "root_cause": "Multiple failed login attempts from foreign IPs",
        "recommended_actions": [
            "Enable account lockout",
            "Require MFA",
            "Review login logs"
        ],
        "matched_indicators": ["failed_logins", "foreign_ips"],
        "status": "active"
    }
]
MOCK_CHAT_HISTORY = []

def log_incident(data: Dict[str, Any]) -> Dict[str, Any]:
    """Log a security incident to Supabase"""
    try:
        incident = {
            "timestamp": datetime.utcnow().isoformat(),
            "severity": data.get("severity", "medium").lower(),  # Convert to lowercase
            "rule_name": data.get("rule_name", "Unknown"),
            "affected_domains": data.get("affected_domains", []),
            "confidence_score": data.get("confidence_score", 0.0),
            "root_cause": data.get("root_cause", ""),
            "recommended_actions": data.get("recommended_actions", []),
            "matched_indicators": data.get("matched_indicators", []),
            "status": "active",
            # Add real attack tracking fields
            "is_real_attack": data.get("is_real_attack", False),
            "source_ip": data.get("source_ip", ""),
            "target_ip": data.get("target_ip", ""),
            "attack_payload": data.get("attack_payload", {}),
            "attack_type": data.get("attack_type", "")
        }
        
        if USE_REAL_SUPABASE:
            # Use real Supabase
            result = supabase.table("incidents").insert(incident).execute()
            if result.data and len(result.data) > 0:
                print(f"✅ Supabase incident logged: {incident['rule_name']} ({incident['severity']})")
                return result.data[0]
            else:
                print(f"❌ Supabase error: No data returned")
                return incident
        else:
            # Use mock implementation
            incident["id"] = len(MOCK_INCIDENTS) + 1
            MOCK_INCIDENTS.append(incident)
            print(f"✅ Mock incident logged: {incident['rule_name']} ({incident['severity']})")
            return incident
            
    except Exception as e:
        print(f"❌ Error logging incident: {e}")
        return data

def resolve_incident(incident_id: int) -> bool:
    """Resolve an incident by ID"""
    try:
        print(f"🔧 Resolving incident {incident_id}, USE_REAL_SUPABASE={USE_REAL_SUPABASE}")
        if USE_REAL_SUPABASE:
            # Use real Supabase
            update_data = {
                "status": "resolved",
                "resolved_at": datetime.utcnow().isoformat()
            }
            print(f"📝 Update data: {update_data}")
            result = supabase.table("incidents").update(update_data, {"id": incident_id}).execute()
            print(f"📊 Update result: {result}")
            success = len(result.data) > 0
            if success:
                print(f"✅ Supabase incident {incident_id} resolved")
            else:
                print(f"❌ Failed to resolve incident {incident_id}")
            return success
        else:
            # Use mock implementation
            for incident in MOCK_INCIDENTS:
                if incident["id"] == incident_id:
                    incident["status"] = "resolved"
                    incident["resolved_at"] = datetime.utcnow().isoformat()
                    print(f"✅ Mock incident {incident_id} resolved")
                    return True
            return False
    except Exception as e:
        print(f"❌ Error resolving incident: {e}")
        return False

def get_recent_incidents(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent incidents from Supabase"""
    try:
        print(f"🔍 get_recent_incidents called with limit={limit}, USE_REAL_SUPABASE={USE_REAL_SUPABASE}")
        if USE_REAL_SUPABASE:
            # Use real Supabase
            result = supabase.table("incidents")\
                .select("*")\
                .order("timestamp", desc=True)\
                .limit(limit)\
                .execute()
            incidents = result.data or []
            print(f"✅ Supabase fetched {len(incidents)} incidents")
            return incidents
        else:
            # Use mock implementation
            incidents = sorted(MOCK_INCIDENTS, key=lambda x: x["timestamp"], reverse=True)[:limit]
            print(f"✅ Mock fetched {len(incidents)} incidents")
            return incidents
    except Exception as e:
        print(f"❌ Error fetching incidents: {e}")
        # Fallback to mock if Supabase fails
        incidents = sorted(MOCK_INCIDENTS, key=lambda x: x["timestamp"], reverse=True)[:limit]
        print(f"🔄 Fallback to mock: {len(incidents)} incidents")
        return incidents

def log_real_attack(attack_data: Dict[str, Any]) -> Dict[str, Any]:
    """Log a real attack to the real_attacks table"""
    try:
        real_attack = {
            "timestamp": attack_data.get("timestamp", datetime.utcnow().isoformat()),
            "attack_type": attack_data.get("attack_type", "unknown"),
            "source_ip": attack_data.get("source_ip", ""),
            "target_ip": attack_data.get("target_ip", ""),
            "payload": attack_data.get("payload", {}),
            "status": "detected",
            "severity": "high",
            "processed": True
        }
        
        if USE_REAL_SUPABASE:
            # Use real Supabase
            result = supabase.table("real_attacks").insert(real_attack).execute()
            if result.data and len(result.data) > 0:
                print(f"✅ Real attack logged: {attack_data.get('attack_type')} from {attack_data.get('source_ip')}")
                return result.data[0]
            else:
                print(f"❌ Supabase error: No data returned")
                return real_attack
        else:
            # Use mock implementation
            real_attack["id"] = len(MOCK_INCIDENTS) + 1000  # Different ID range
            print(f"✅ Mock real attack logged: {attack_data.get('attack_type')} from {attack_data.get('source_ip')}")
            return real_attack
            
    except Exception as e:
        print(f"❌ Error logging real attack: {e}")
        return attack_data

def get_real_attacks(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent real attacks from Supabase"""
    try:
        if USE_REAL_SUPABASE:
            # Use real Supabase
            result = supabase.table("real_attacks")\
                .select("*")\
                .order("timestamp", desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
        else:
            # Use mock implementation - return empty list for now
            return []
    except Exception as e:
        print(f"❌ Error getting real attacks: {e}")
        return []

def get_incident_stats() -> Dict[str, Any]:
    """Get incident statistics from Supabase"""
    try:
        if USE_REAL_SUPABASE:
            # Use real Supabase
            result = supabase.table("incidents")\
                .select("severity, status, is_real_attack")\
                .execute()
            
            incidents = result.data if result.data else []
            
            stats = {
                "total": len(incidents),
                "active": len([i for i in incidents if i.get("status") == "active"]),
                "resolved": len([i for i in incidents if i.get("status") == "resolved"]),
                "critical": len([i for i in incidents if i.get("severity") == "critical"]),
                "high": len([i for i in incidents if i.get("severity") == "high"]),
                "medium": len([i for i in incidents if i.get("severity") == "medium"]),
                "low": len([i for i in incidents if i.get("severity") == "low"]),
                "real_attacks": len([i for i in incidents if i.get("is_real_attack") == True]),
                "simulated_attacks": len([i for i in incidents if i.get("is_real_attack") == False])
            }
            return stats
        else:
            # Use mock implementation
            incidents = MOCK_INCIDENTS
            stats = {
                "total": len(incidents),
                "active": len([i for i in incidents if i.get("status") == "active"]),
                "resolved": len([i for i in incidents if i.get("status") == "resolved"]),
                "critical": len([i for i in incidents if i.get("severity") == "critical"]),
                "high": len([i for i in incidents if i.get("severity") == "high"]),
                "medium": len([i for i in incidents if i.get("severity") == "medium"]),
                "low": len([i for i in incidents if i.get("severity") == "low"]),
                "real_attacks": 0,
                "simulated_attacks": len(incidents)
            }
            return stats
    except Exception as e:
        print(f"❌ Error getting incident stats: {e}")
        return {
            "total": 0,
            "active": 0,
            "resolved": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "real_attacks": 0,
            "simulated_attacks": 0
        }

# ---------------------------------------------------------------------------
# Network snapshot logging
# ---------------------------------------------------------------------------

def log_network_snapshot(data: Dict[str, Any]) -> bool:
    """Log network state snapshot"""
    try:
        snapshot = {
            "timestamp": datetime.utcnow().isoformat(),
            "network_data": data
        }
        
        if USE_REAL_SUPABASE:
            # Use real Supabase
            supabase.table("network_snapshots").insert(snapshot).execute()
            print(f"✅ Supabase network snapshot logged")
        else:
            # Mock implementation - just print for now
            print(f"📊 Mock network snapshot logged")
        return True
    except Exception as e:
        print(f"❌ Error logging network snapshot: {e}")
        return False

# ---------------------------------------------------------------------------
# Chat logging
# ---------------------------------------------------------------------------

def log_chat(user_msg: str, ai_response: str, provider: str, context: Dict[str, Any]) -> bool:
    """Log chat interaction"""
    try:
        chat_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_message": user_msg,
            "ai_response": ai_response,
            "provider": provider,
            "context": context
        }
        
        if USE_REAL_SUPABASE:
            # Use real Supabase
            supabase.table("chat_history").insert(chat_entry).execute()
            print(f"✅ Supabase chat logged: {provider}")
        else:
            # Mock implementation
            MOCK_CHAT_HISTORY.append(chat_entry)
            print(f"💬 Mock chat logged: {provider}")
        return True
    except Exception as e:
        print(f"❌ Error logging chat: {e}")
        return False

# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def resolve_all_active_incidents() -> int:
    """Resolve all active incidents"""
    try:
        if USE_REAL_SUPABASE:
            # First, let's see how many active incidents we have
            print("🔍 Checking for active incidents...")
            check_result = supabase.table("incidents").select("id, status").eq("status", "active").execute()
            active_count = len(check_result.data or [])
            print(f"🔍 Found {active_count} active incidents to resolve")
            print(f"🔍 Sample active incidents: {check_result.data[:3] if check_result.data else 'None'}")
            
            if active_count == 0:
                print("🔍 No active incidents found")
                return 0
            
            # Try a simpler approach - get all incidents first, then update them individually
            print("🔍 Getting all incidents to resolve...")
            all_incidents = supabase.table("incidents").select("id, status").execute()
            resolved_count = 0
            
            for incident in all_incidents.data or []:
                if incident.get("status") != "resolved":
                    print(f"🔍 Resolving incident {incident.get('id')}")
                    update_result = supabase.table("incidents").update({
                        "status": "resolved",
                        "resolved_at": datetime.utcnow().isoformat()
                    }).eq("id", incident.get("id")).execute()
                    if update_result.data:
                        resolved_count += 1
            print(f"✅ Supabase resolved {resolved_count} incidents")
            return resolved_count
        else:
            # Mock implementation
            resolved_count = 0
            for incident in MOCK_INCIDENTS:
                if incident["status"] == "active":
                    incident["status"] = "resolved"
                    incident["resolved_at"] = datetime.utcnow().isoformat()
                    resolved_count += 1
            
            print(f"✅ Mock resolved {resolved_count} incidents")
            return resolved_count
    except Exception as e:
        print(f"❌ Error resolving all incidents: {e}")
        return 0

# ---------------------------------------------------------------------------
# Startup test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    result = log_incident({
        "severity": "HIGH",
        "rule_name": "Connection Test",
        "affected_domains": ["network"],
        "root_cause": "Testing Supabase connection",
        "recommended_actions": ["Verify connection"],
        "confidence_score": 0.99,
        "scenario_name": "test",
        "status": "ACTIVE"
    })
    print("Result:", result)
