"""
Network simulation module for Dhurandar AI.

Operates in two modes:
  - REAL: Uses Mininet for actual network topology simulation (Linux only).
  - MOCK: Generates realistic synthetic telemetry data (works everywhere).

The active mode is auto-detected at import time based on OS and Mininet
availability, but can be overridden via the DHURANDAR_SIM_MODE env var
("real" | "mock").
"""

from __future__ import annotations

import asyncio
import os
import platform
import random
import threading
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Generator

# ---------------------------------------------------------------------------
# Mode detection
# ---------------------------------------------------------------------------

class SimMode(Enum):
    REAL = "real"
    MOCK = "mock"


def _detect_mode() -> SimMode:
    override = os.getenv("DHURANDAR_SIM_MODE", "").lower()
    if override == "real":
        return SimMode.REAL
    if override == "mock":
        return SimMode.MOCK
    if platform.system() == "Linux":
        try:
            import mininet  # noqa: F401
            return SimMode.REAL
        except ImportError:
            pass
    return SimMode.MOCK


ACTIVE_MODE: SimMode = _detect_mode()

# ---------------------------------------------------------------------------
# Constants / pools used by generators
# ---------------------------------------------------------------------------

_ATTACKER_IPS = [
    "203.0.113.10", "198.51.100.44", "192.0.2.77", "185.220.101.3",
    "45.33.32.156", "91.219.236.12", "104.21.45.88", "172.104.210.5",
    "159.89.14.22", "64.225.0.99",
]

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

_USERNAMES = ["admin", "root", "jdoe", "svc_backup", "analyst_1", "devops"]

_SENSITIVE_FILES = [
    "/etc/shadow", "/var/db/customers.csv", "/opt/secrets/api_keys.json",
    "/home/admin/.ssh/id_rsa", "/srv/data/financial_report_2026.xlsx",
    "/var/log/audit/audit.log",
]

_PROCESSES_NORMAL = ["nginx", "postgres", "uvicorn", "redis-server", "node"]
_PROCESSES_SUSPICIOUS = ["xmrig", "cryptonight", "minerd", "kworker_crypt"]

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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation from a to b by factor t ∈ [0, 1]."""
    return a + (b - a) * min(max(t, 0.0), 1.0)


def _jitter(value: float, pct: float = 0.05) -> float:
    """Add ±pct random jitter to value."""
    return value * (1.0 + random.uniform(-pct, pct))


def _build_topology(alert_nodes: list[str] | None = None) -> list[dict[str, Any]]:
    alert_nodes = alert_nodes or []
    nodes = []
    for n in _TOPOLOGY_NODES:
        node = {**n, "status": "alert" if n["id"] in alert_nodes else "normal"}
        nodes.append(node)
    return [{"nodes": nodes, "edges": _TOPOLOGY_EDGES}]


# ---------------------------------------------------------------------------
# Domain snapshot type
# ---------------------------------------------------------------------------

def _baseline_snapshot() -> dict[str, Any]:
    """Return a normal-state domain snapshot with small random variations."""
    return {
        "timestamp": _now_iso(),
        "domains": {
            "network": {
                "packets_per_sec": random.randint(1200, 3500),
                "ddos_score": round(random.uniform(0.01, 0.12), 2),
                "anomaly": False,
            },
            "hardware": {
                "cpu_percent": round(random.uniform(12.0, 40.0), 1),
                "memory_percent": round(random.uniform(25.0, 50.0), 1),
                "anomaly": False,
            },
            "user": {
                "active_users": random.randint(15, 60),
                "flagged_logins": [],
                "anomaly": False,
            },
            "security": {
                "firewall_hits": random.randint(0, 20),
                "ids_alerts": [],
                "anomaly": False,
            },
        },
        "correlated_alerts": [],
        "network_topology": _build_topology(),
    }


# ===================================================================== #
#                         SCENARIO GENERATORS                           #
# ===================================================================== #

def scenario_ddos(
    duration_sec: int = 30,
    tick_interval: float = 2.0,
) -> Generator[dict[str, Any], None, None]:
    """
    DDoS attack: ramps packets/sec from ~3 000 → 55 000, CPU climbs,
    firewall alerts spike over *duration_sec* seconds.
    """
    ticks = int(duration_sec / tick_interval)
    for i in range(ticks):
        t = i / max(ticks - 1, 1)  # 0 → 1
        pps = int(_jitter(_lerp(3000, 55000, t)))
        ddos = round(_jitter(_lerp(0.10, 0.98, t), 0.03), 2)
        cpu = round(_jitter(_lerp(30.0, 92.0, t)), 1)
        mem = round(_jitter(_lerp(35.0, 78.0, t)), 1)
        fw_hits = int(_jitter(_lerp(15, 4800, t)))

        ids = random.sample(_IDS_ALERT_POOL, min(int(1 + t * 4), len(_IDS_ALERT_POOL)))

        net_anomaly = t > 0.25
        hw_anomaly = t > 0.5
        sec_anomaly = t > 0.2

        correlated: list[dict[str, Any]] = []
        if t > 0.3:
            correlated.append({
                "id": f"CORR-{random.randint(1000,9999)}",
                "timestamp": _now_iso(),
                "severity": "critical" if t > 0.6 else "high",
                "title": "DDoS volumetric flood detected",
                "domains": ["network", "security"],
                "description": (
                    f"Packet rate {pps} pps with DDoS score {ddos}. "
                    f"Firewall absorbing {fw_hits} hits/s."
                ),
            })

        yield {
            "timestamp": _now_iso(),
            "domains": {
                "network": {
                    "packets_per_sec": pps,
                    "ddos_score": ddos,
                    "anomaly": net_anomaly,
                },
                "hardware": {
                    "cpu_percent": cpu,
                    "memory_percent": mem,
                    "anomaly": hw_anomaly,
                },
                "user": {
                    "active_users": random.randint(15, 50),
                    "flagged_logins": [],
                    "anomaly": False,
                },
                "security": {
                    "firewall_hits": fw_hits,
                    "ids_alerts": ids,
                    "anomaly": sec_anomaly,
                },
            },
            "correlated_alerts": correlated,
            "network_topology": _build_topology(["fw-1", "srv-web"] if t > 0.3 else []),
        }


def scenario_cryptominer(
    duration_sec: int = 30,
    tick_interval: float = 2.0,
) -> Generator[dict[str, Any], None, None]:
    """
    Cryptominer: CPU spikes to ~95 %, P2P traffic appears, suspicious
    process shows up mid-scenario.
    """
    ticks = int(duration_sec / tick_interval)
    process_appeared = False

    for i in range(ticks):
        t = i / max(ticks - 1, 1)
        cpu = round(_jitter(_lerp(35.0, 95.0, t), 0.02), 1)
        mem = round(_jitter(_lerp(40.0, 72.0, t)), 1)
        pps = int(_jitter(_lerp(2000, 12000, t)))  # P2P traffic growth

        ids: list[str] = []
        if t > 0.3:
            ids.append("Unusual TLS certificate")
        if t > 0.5:
            ids.append("Command-and-control beacon")

        flagged: list[str] = []
        if t > 0.4 and not process_appeared:
            process_appeared = True
            flagged.append("svc_backup@10.0.0.99 (spawned xmrig)")

        hw_anomaly = t > 0.2
        sec_anomaly = t > 0.4

        correlated: list[dict[str, Any]] = []
        if t > 0.5:
            correlated.append({
                "id": f"CORR-{random.randint(1000,9999)}",
                "timestamp": _now_iso(),
                "severity": "high",
                "title": "Cryptomining activity detected",
                "domains": ["hardware", "security"],
                "description": (
                    f"CPU at {cpu}% with suspicious process "
                    f"'{random.choice(_PROCESSES_SUSPICIOUS)}' and "
                    f"outbound P2P traffic at {pps} pps."
                ),
            })

        yield {
            "timestamp": _now_iso(),
            "domains": {
                "network": {
                    "packets_per_sec": pps,
                    "ddos_score": round(random.uniform(0.02, 0.15), 2),
                    "anomaly": t > 0.6,
                },
                "hardware": {
                    "cpu_percent": cpu,
                    "memory_percent": mem,
                    "anomaly": hw_anomaly,
                },
                "user": {
                    "active_users": random.randint(15, 45),
                    "flagged_logins": flagged,
                    "anomaly": bool(flagged),
                },
                "security": {
                    "firewall_hits": random.randint(5, 60),
                    "ids_alerts": ids,
                    "anomaly": sec_anomaly,
                },
            },
            "correlated_alerts": correlated,
            "network_topology": _build_topology(
                ["srv-ml"] if t > 0.3 else []
            ),
        }


def scenario_bruteforce(
    duration_sec: int = 30,
    tick_interval: float = 2.0,
) -> Generator[dict[str, Any], None, None]:
    """
    Brute-force login: 50+ failed login events from multiple IPs in rapid
    succession, with escalation mid-scenario.
    """
    ticks = int(duration_sec / tick_interval)
    total_attempts = 0

    for i in range(ticks):
        t = i / max(ticks - 1, 1)

        attempts_this_tick = int(_jitter(_lerp(2, 15, t)))
        total_attempts += attempts_this_tick

        flagged = [
            f"{random.choice(_USERNAMES)}@{random.choice(_ATTACKER_IPS)}"
            for _ in range(attempts_this_tick)
        ]

        ids: list[str] = ["Brute-force SSH login"]
        if t > 0.4:
            ids.append("Privilege escalation attempt")
        if t > 0.7:
            ids.append("Lateral movement detected")

        user_anomaly = t > 0.15
        sec_anomaly = t > 0.1

        correlated: list[dict[str, Any]] = []
        if total_attempts > 30:
            correlated.append({
                "id": f"CORR-{random.randint(1000,9999)}",
                "timestamp": _now_iso(),
                "severity": "critical" if total_attempts > 60 else "high",
                "title": f"Brute-force campaign: {total_attempts} attempts",
                "domains": ["user", "security"],
                "description": (
                    f"{total_attempts} failed logins from "
                    f"{len(set(flagged))} unique sources this window."
                ),
            })

        yield {
            "timestamp": _now_iso(),
            "domains": {
                "network": {
                    "packets_per_sec": int(_jitter(_lerp(2000, 6000, t))),
                    "ddos_score": round(random.uniform(0.02, 0.18), 2),
                    "anomaly": False,
                },
                "hardware": {
                    "cpu_percent": round(_jitter(_lerp(20.0, 45.0, t)), 1),
                    "memory_percent": round(_jitter(_lerp(30.0, 52.0, t)), 1),
                    "anomaly": False,
                },
                "user": {
                    "active_users": random.randint(20, 70) + attempts_this_tick,
                    "flagged_logins": flagged,
                    "anomaly": user_anomaly,
                },
                "security": {
                    "firewall_hits": int(_jitter(_lerp(10, 300, t))),
                    "ids_alerts": ids,
                    "anomaly": sec_anomaly,
                },
            },
            "correlated_alerts": correlated,
            "network_topology": _build_topology(
                ["usr-seg"] if t > 0.2 else []
            ),
        }


def scenario_insider(
    duration_sec: int = 30,
    tick_interval: float = 2.0,
) -> Generator[dict[str, Any], None, None]:
    """
    Insider threat: 3 AM login from a known user, followed by sensitive
    file access events escalating over time.
    """
    ticks = int(duration_sec / tick_interval)
    insider_user = "jdoe"
    insider_ip = "10.0.0.42"

    fake_3am = datetime.now(timezone.utc).replace(hour=3, minute=random.randint(0, 15))

    for i in range(ticks):
        t = i / max(ticks - 1, 1)

        flagged: list[str] = []
        ids: list[str] = []
        files_accessed: list[str] = []

        if i == 0:
            flagged.append(f"{insider_user}@{insider_ip} (login at {fake_3am.strftime('%H:%M')})")
        if t > 0.15:
            ids.append("Suspicious outbound DNS query")
        if t > 0.3:
            n_files = min(int(1 + t * 5), len(_SENSITIVE_FILES))
            files_accessed = random.sample(_SENSITIVE_FILES, n_files)
            ids.append("Data exfiltration pattern")
        if t > 0.6:
            ids.append("Privilege escalation attempt")
        if t > 0.8:
            ids.append("Lateral movement detected")

        user_anomaly = t > 0.05
        sec_anomaly = t > 0.25

        correlated: list[dict[str, Any]] = []
        if t > 0.35:
            correlated.append({
                "id": f"CORR-{random.randint(1000,9999)}",
                "timestamp": _now_iso(),
                "severity": "critical" if t > 0.65 else "high",
                "title": f"Insider threat: {insider_user}",
                "domains": ["user", "security"],
                "description": (
                    f"User '{insider_user}' logged in at unusual hour from "
                    f"{insider_ip}. Accessed {len(files_accessed)} sensitive "
                    f"files: {', '.join(files_accessed[:3])}."
                ),
            })

        yield {
            "timestamp": _now_iso(),
            "domains": {
                "network": {
                    "packets_per_sec": int(_jitter(2500)),
                    "ddos_score": round(random.uniform(0.01, 0.08), 2),
                    "anomaly": False,
                },
                "hardware": {
                    "cpu_percent": round(_jitter(25.0), 1),
                    "memory_percent": round(_jitter(35.0), 1),
                    "anomaly": False,
                },
                "user": {
                    "active_users": random.randint(2, 8),  # low at 3 AM
                    "flagged_logins": flagged,
                    "anomaly": user_anomaly,
                },
                "security": {
                    "firewall_hits": random.randint(0, 15),
                    "ids_alerts": ids,
                    "anomaly": sec_anomaly,
                },
            },
            "correlated_alerts": correlated,
            "network_topology": _build_topology(
                ["srv-db", "usr-seg"] if t > 0.3 else []
            ),
        }


# ===================================================================== #
#                         SCENARIO MANAGER                              #
# ===================================================================== #

_SCENARIOS: dict[str, Any] = {
    "ddos": scenario_ddos,
    "cryptominer": scenario_cryptominer,
    "bruteforce": scenario_bruteforce,
    "insider": scenario_insider,
}


class ScenarioManager:
    """
    Manages the active simulation scenario.

    * Only one scenario runs at a time.
    * When no scenario is active, ``get_current_state()`` returns baseline data.
    * Calling ``start_scenario(name)`` spins up a background asyncio task that
      iterates through the chosen generator, updating ``_current_state`` every
      tick.  When the generator is exhausted the scenario ends automatically.
    """

    def __init__(self, tick_interval: float = 2.0) -> None:
        self._tick: float = tick_interval
        self._current_state: dict[str, Any] = _baseline_snapshot()
        self._active_scenario: str | None = None
        self._task: asyncio.Task[None] | None = None
        self._lock = threading.Lock()

    # -- public API --------------------------------------------------------

    @property
    def active_scenario(self) -> str | None:
        return self._active_scenario

    def get_current_state(self) -> dict[str, Any]:
        """Return the latest domain snapshot (scenario or baseline)."""
        with self._lock:
            if self._active_scenario is None:
                self._current_state = _baseline_snapshot()
            return self._current_state

    async def start_scenario(self, name: str) -> dict[str, Any]:
        """
        Start a named scenario.  Returns a status dict.
        If a scenario is already running it is stopped first.
        """
        if name not in _SCENARIOS:
            return {
                "status": "error",
                "message": f"Unknown scenario '{name}'",
                "available": list(_SCENARIOS.keys()),
            }

        if self._active_scenario is not None:
            await self.stop_scenario()

        gen = _SCENARIOS[name](tick_interval=self._tick)
        self._active_scenario = name
        self._task = asyncio.create_task(self._run(gen))

        return {
            "status": "started",
            "scenario": name,
            "message": f"Scenario '{name}' is now running.",
        }

    async def stop_scenario(self) -> dict[str, Any]:
        """Stop any running scenario and return to baseline."""
        if self._task is not None and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        prev = self._active_scenario
        self._active_scenario = None
        self._task = None
        with self._lock:
            self._current_state = _baseline_snapshot()

        return {
            "status": "stopped",
            "previous_scenario": prev,
            "message": "Returned to baseline.",
        }

    # -- internal ----------------------------------------------------------

    async def _run(self, gen: Generator[dict[str, Any], None, None]) -> None:
        try:
            for snapshot in gen:
                with self._lock:
                    self._current_state = snapshot
                await asyncio.sleep(self._tick)
        except asyncio.CancelledError:
            raise
        finally:
            self._active_scenario = None
            with self._lock:
                self._current_state = _baseline_snapshot()


# Module-level singleton
scenario_manager = ScenarioManager()


# ===================================================================== #
#                  REAL MODE STUB  (Linux + Mininet)                    #
# ===================================================================== #

if ACTIVE_MODE == SimMode.REAL:
    try:
        from mininet.net import Mininet  # type: ignore[import-untyped]
        from mininet.node import OVSSwitch, Controller  # type: ignore[import-untyped]
        from mininet.topo import Topo  # type: ignore[import-untyped]

        class DhurandarTopo(Topo):
            """Simple Mininet topology mirroring the mock topology graph."""

            def build(self) -> None:
                switch = self.addSwitch("sw-core")
                fw = self.addHost("fw-1")
                web = self.addHost("srv-web")
                db = self.addHost("srv-db")
                ml = self.addHost("srv-ml")
                user = self.addHost("usr-seg")

                for host in (fw, web, db, ml, user):
                    self.addLink(host, switch)

        def start_real_network() -> Mininet:
            topo = DhurandarTopo()
            net = Mininet(topo=topo, switch=OVSSwitch, controller=Controller)
            net.start()
            return net

    except ImportError:
        pass
