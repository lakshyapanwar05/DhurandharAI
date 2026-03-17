from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any

from app.store import store

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_IDS_ALERT_POOL = [
    "SQL injection attempt detected",
    "Port scan from external IP",
    "Brute-force SSH login",
    "Suspicious outbound DNS query",
    "Malware signature match",
    "Privilege escalation attempt",
    "Lateral movement detected",
    "Data exfiltration pattern",
    "Unusual TLS certificate",
    "Command-and-control beacon",
]

_FLAGGED_LOGIN_POOL = [
    "admin@10.0.0.1",
    "root@192.168.1.55",
    "guest@172.16.0.12",
    "svc_account@10.0.0.99",
    "unknown@203.0.113.7",
]


def _rand_ids_alerts(attack: bool) -> list[str]:
    count = random.randint(2, 5) if attack else random.randint(0, 1)
    return random.sample(_IDS_ALERT_POOL, min(count, len(_IDS_ALERT_POOL)))


def _rand_flagged_logins(attack: bool) -> list[str]:
    count = random.randint(2, 4) if attack else random.randint(0, 1)
    return random.sample(_FLAGGED_LOGIN_POOL, min(count, len(_FLAGGED_LOGIN_POOL)))


# ---------------------------------------------------------------------------
# Correlated alert builder
# ---------------------------------------------------------------------------

def _build_correlated_alerts(domains: dict[str, Any], ts: str) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    anomaly_domains = [k for k, v in domains.items() if v.get("anomaly")]

    if len(anomaly_domains) >= 2:
        alerts.append({
            "id": f"CORR-{random.randint(1000,9999)}",
            "timestamp": ts,
            "severity": "critical" if len(anomaly_domains) >= 3 else "high",
            "title": f"Multi-domain anomaly: {', '.join(anomaly_domains)}",
            "domains": anomaly_domains,
            "description": (
                f"Simultaneous anomalies detected across {len(anomaly_domains)} "
                f"domains indicating a potential coordinated attack."
            ),
        })

    if domains["network"].get("anomaly") and domains["security"].get("anomaly"):
        alerts.append({
            "id": f"CORR-{random.randint(1000,9999)}",
            "timestamp": ts,
            "severity": "critical",
            "title": "Network + Security correlated threat",
            "domains": ["network", "security"],
            "description": (
                f"DDoS score {domains['network']['ddos_score']:.2f} with "
                f"{domains['security']['firewall_hits']} firewall hits."
            ),
        })

    return alerts


# ---------------------------------------------------------------------------
# Network topology stub
# ---------------------------------------------------------------------------

_TOPOLOGY_NODES = [
    {"id": "fw-1", "label": "Firewall", "type": "firewall"},
    {"id": "sw-core", "label": "Core Switch", "type": "switch"},
    {"id": "srv-web", "label": "Web Server", "type": "server"},
    {"id": "srv-db", "label": "Database", "type": "server"},
    {"id": "srv-ml", "label": "ML Pipeline", "type": "server"},
    {"id": "usr-seg", "label": "User Segment", "type": "subnet"},
]

_TOPOLOGY_EDGES = [
    {"source": "fw-1", "target": "sw-core"},
    {"source": "sw-core", "target": "srv-web"},
    {"source": "sw-core", "target": "srv-db"},
    {"source": "sw-core", "target": "srv-ml"},
    {"source": "sw-core", "target": "usr-seg"},
]


def _build_topology(attack: bool) -> list[dict[str, Any]]:
    nodes = []
    for n in _TOPOLOGY_NODES:
        node = {**n, "status": "normal"}
        if attack and n["id"] in ("fw-1", "srv-web"):
            node["status"] = "alert"
        nodes.append(node)
    return [{"nodes": nodes, "edges": _TOPOLOGY_EDGES}]


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate_event() -> dict[str, Any]:
    """Generate a single network telemetry snapshot."""
    attack = store.attack_active
    ts = datetime.now(timezone.utc).isoformat()

    network_anomaly = random.random() < (0.8 if attack else 0.08)
    hardware_anomaly = random.random() < (0.5 if attack else 0.05)
    user_anomaly = random.random() < (0.6 if attack else 0.04)
    security_anomaly = random.random() < (0.85 if attack else 0.06)

    domains: dict[str, Any] = {
        "network": {
            "packets_per_sec": random.randint(8000, 50000) if attack else random.randint(1000, 5000),
            "ddos_score": round(random.uniform(0.7, 1.0), 2) if attack else round(random.uniform(0.0, 0.3), 2),
            "anomaly": network_anomaly,
        },
        "hardware": {
            "cpu_percent": round(random.uniform(70, 99), 1) if attack else round(random.uniform(10, 60), 1),
            "memory_percent": round(random.uniform(65, 95), 1) if attack else round(random.uniform(20, 55), 1),
            "anomaly": hardware_anomaly,
        },
        "user": {
            "active_users": random.randint(50, 300) if attack else random.randint(10, 80),
            "flagged_logins": _rand_flagged_logins(attack),
            "anomaly": user_anomaly,
        },
        "security": {
            "firewall_hits": random.randint(500, 5000) if attack else random.randint(0, 50),
            "ids_alerts": _rand_ids_alerts(attack),
            "anomaly": security_anomaly,
        },
    }

    correlated = _build_correlated_alerts(domains, ts)
    if correlated:
        store.push_alerts(correlated)

    event: dict[str, Any] = {
        "timestamp": ts,
        "domains": domains,
        "correlated_alerts": correlated,
        "network_topology": _build_topology(attack),
    }

    store.push_event(event)
    return event
