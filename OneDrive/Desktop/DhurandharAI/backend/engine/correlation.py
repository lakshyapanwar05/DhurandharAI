"""
Multi-domain correlation engine for Dhurandar AI.

Receives domain snapshots (network, hardware, user, security) and evaluates
a set of correlation rules.  Each triggered rule produces a structured alert
with severity, affected domains, root cause, recommended actions, and a
confidence score derived from how many individual indicators matched.
"""

from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any, Callable

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

CorrelationAlert = dict[str, Any]
DomainSnapshot = dict[str, Any]
RuleFunc = Callable[[DomainSnapshot], CorrelationAlert | None]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _alert_id() -> str:
    return f"CORR-{random.randint(10000, 99999)}"


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# Individual indicator extractors
# ---------------------------------------------------------------------------

def _get(domains: dict[str, Any], path: str, default: Any = None) -> Any:
    """Dot-path accessor: _get(d, 'network.ddos_score') -> d['network']['ddos_score']."""
    keys = path.split(".")
    cur: Any = domains
    for k in keys:
        if isinstance(cur, dict):
            cur = cur.get(k, default)
        else:
            return default
    return cur


def _has_foreign_login(user: dict[str, Any]) -> bool:
    """True if flagged_logins contains entries from external-looking IPs."""
    for entry in user.get("flagged_logins", []):
        if isinstance(entry, str) and ("@" in entry):
            ip_part = entry.split("@")[-1].split(" ")[0]
            if not ip_part.startswith(("10.", "192.168.", "172.16.")):
                return True
    return bool(user.get("anomaly", False) and user.get("flagged_logins"))


def _has_new_process(user: dict[str, Any]) -> bool:
    """True if flagged_logins or anomaly suggests a new suspicious process."""
    for entry in user.get("flagged_logins", []):
        if isinstance(entry, str) and any(
            kw in entry.lower()
            for kw in ("xmrig", "cryptonight", "minerd", "kworker_crypt", "spawned")
        ):
            return True
    return False


def _has_multiple_ips(user: dict[str, Any]) -> bool:
    """True if flagged logins come from ≥ 2 distinct IPs."""
    ips: set[str] = set()
    for entry in user.get("flagged_logins", []):
        if isinstance(entry, str) and "@" in entry:
            ip = entry.split("@")[-1].split(" ")[0]
            ips.add(ip)
    return len(ips) >= 2


def _is_after_hours(user: dict[str, Any]) -> bool:
    """True if flagged login text mentions an unusual hour (0–6 AM)."""
    for entry in user.get("flagged_logins", []):
        if isinstance(entry, str):
            lower = entry.lower()
            if "login at 0" in lower or "login at 1" in lower or \
               "login at 2" in lower or "login at 3" in lower or \
               "login at 4" in lower or "login at 5" in lower or \
               "login at 6:" in lower or "3am" in lower or "3 am" in lower:
                return True
    return False


def _has_sensitive_file_access(security: dict[str, Any]) -> bool:
    """True if IDS alerts mention exfiltration or escalation."""
    for alert in security.get("ids_alerts", []):
        if isinstance(alert, str):
            lower = alert.lower()
            if "exfiltration" in lower or "privilege escalation" in lower or \
               "lateral movement" in lower:
                return True
    return False


def _has_p2p_traffic(network: dict[str, Any]) -> bool:
    """Heuristic: p2p-like traffic when packets are moderately high but ddos_score is low."""
    pps = network.get("packets_per_sec", 0)
    ddos = network.get("ddos_score", 0.0)
    return pps > 8000 and ddos < 0.3


def _failed_login_count(security: dict[str, Any], user: dict[str, Any]) -> int:
    """Estimate failed login count from available signals."""
    count = len(user.get("flagged_logins", []))
    for alert in security.get("ids_alerts", []):
        if isinstance(alert, str) and "brute" in alert.lower():
            count += 10
    return count


# ===================================================================== #
#                        CORRELATION RULES                              #
# ===================================================================== #

def _rule_multi_stage_attack(domains: DomainSnapshot) -> CorrelationAlert | None:
    """
    RULE 1 — Multi-stage Attack
    network.ddos_score > 0.7 AND hardware.cpu > 85 AND user.foreign_login
    """
    net = domains.get("network", {})
    hw = domains.get("hardware", {})
    usr = domains.get("user", {})

    indicators = [
        ("network.ddos_score > 0.7", net.get("ddos_score", 0) > 0.7),
        ("hardware.cpu_percent > 85", hw.get("cpu_percent", 0) > 85),
        ("user.foreign_login", _has_foreign_login(usr)),
    ]

    matched = [name for name, hit in indicators if hit]
    if len(matched) < 2:
        return None

    confidence = _clamp(len(matched) / len(indicators))

    return {
        "id": _alert_id(),
        "timestamp": _now_iso(),
        "rule_name": "Multi-stage Attack",
        "severity": "critical",
        "affected_domains": ["network", "hardware", "user"],
        "root_cause": (
            f"Coordinated attack pattern: DDoS score "
            f"{net.get('ddos_score', 0):.2f}, CPU at "
            f"{hw.get('cpu_percent', 0):.1f}% with foreign login activity."
        ),
        "recommended_actions": [
            "Activate DDoS mitigation on edge firewall",
            "Isolate compromised user accounts",
            "Scale compute resources to absorb load",
            "Engage incident response team",
        ],
        "confidence_score": round(confidence, 2),
        "matched_indicators": matched,
    }


def _rule_cryptominer(domains: DomainSnapshot) -> CorrelationAlert | None:
    """
    RULE 2 — Cryptominer
    hardware.cpu > 90 AND network.p2p_traffic > threshold AND
    user.new_process_detected
    """
    hw = domains.get("hardware", {})
    net = domains.get("network", {})
    usr = domains.get("user", {})

    indicators = [
        ("hardware.cpu_percent > 90", hw.get("cpu_percent", 0) > 90),
        ("network.p2p_traffic", _has_p2p_traffic(net)),
        ("user.new_process_detected", _has_new_process(usr)),
    ]

    matched = [name for name, hit in indicators if hit]
    if len(matched) < 2:
        return None

    confidence = _clamp(len(matched) / len(indicators))

    return {
        "id": _alert_id(),
        "timestamp": _now_iso(),
        "rule_name": "Cryptominer",
        "severity": "high",
        "affected_domains": ["hardware", "network", "user"],
        "root_cause": (
            f"Suspected cryptomining: CPU at {hw.get('cpu_percent', 0):.1f}% "
            f"with P2P-like traffic ({net.get('packets_per_sec', 0)} pps) and "
            f"suspicious process activity."
        ),
        "recommended_actions": [
            "Kill suspicious mining processes (xmrig, minerd, etc.)",
            "Block outbound P2P connections on firewall",
            "Audit service account credentials",
            "Scan host for rootkits",
        ],
        "confidence_score": round(confidence, 2),
        "matched_indicators": matched,
    }


def _rule_brute_force(domains: DomainSnapshot) -> CorrelationAlert | None:
    """
    RULE 3 — Brute Force
    security.failed_logins > 10 AND user.multiple_ips
    """
    sec = domains.get("security", {})
    usr = domains.get("user", {})

    failed = _failed_login_count(sec, usr)

    indicators = [
        ("security.failed_logins > 10", failed > 10),
        ("user.multiple_ips", _has_multiple_ips(usr)),
        ("security.brute_force_ids_alert", any(
            "brute" in a.lower() for a in sec.get("ids_alerts", []) if isinstance(a, str)
        )),
    ]

    matched = [name for name, hit in indicators if hit]
    if len(matched) < 2:
        return None

    confidence = _clamp(len(matched) / len(indicators))

    return {
        "id": _alert_id(),
        "timestamp": _now_iso(),
        "rule_name": "Brute Force",
        "severity": "high",
        "affected_domains": ["security", "user"],
        "root_cause": (
            f"Credential-stuffing campaign: ~{failed} failed logins from "
            f"multiple source IPs detected."
        ),
        "recommended_actions": [
            "Enable account lockout after 5 failed attempts",
            "Block attacking IPs at WAF / firewall",
            "Force password reset for targeted accounts",
            "Enable MFA for all privileged accounts",
        ],
        "confidence_score": round(confidence, 2),
        "matched_indicators": matched,
    }


def _rule_insider_threat(domains: DomainSnapshot) -> CorrelationAlert | None:
    """
    RULE 4 — Insider Threat
    user.after_hours_login AND user.sensitive_file_access
    """
    usr = domains.get("user", {})
    sec = domains.get("security", {})

    indicators = [
        ("user.after_hours_login", _is_after_hours(usr)),
        ("user.sensitive_file_access", _has_sensitive_file_access(sec)),
        ("user.anomaly_flagged", usr.get("anomaly", False)),
        ("security.escalation_alert", any(
            "escalation" in a.lower() or "lateral" in a.lower()
            for a in sec.get("ids_alerts", []) if isinstance(a, str)
        )),
    ]

    matched = [name for name, hit in indicators if hit]
    if len(matched) < 2:
        return None

    confidence = _clamp(len(matched) / len(indicators))

    return {
        "id": _alert_id(),
        "timestamp": _now_iso(),
        "rule_name": "Insider Threat",
        "severity": "medium",
        "affected_domains": ["user", "security"],
        "root_cause": (
            "After-hours login detected with subsequent access to sensitive "
            "files or privilege escalation attempts — possible insider threat."
        ),
        "recommended_actions": [
            "Review user session recordings for the flagged account",
            "Temporarily revoke elevated privileges",
            "Alert SOC for manual investigation",
            "Check DLP logs for data movement",
        ],
        "confidence_score": round(confidence, 2),
        "matched_indicators": matched,
    }


def _rule_ddos_only(domains: DomainSnapshot) -> CorrelationAlert | None:
    """
    RULE 5 — DDoS Only
    network.ddos_score > 0.9 AND other domains normal
    """
    net = domains.get("network", {})
    hw = domains.get("hardware", {})
    usr = domains.get("user", {})
    sec = domains.get("security", {})

    ddos_high = net.get("ddos_score", 0) > 0.9
    others_normal = (
        hw.get("cpu_percent", 0) < 70
        and not usr.get("anomaly", False)
        and len(usr.get("flagged_logins", [])) == 0
        and sec.get("firewall_hits", 0) < 100
    )

    indicators = [
        ("network.ddos_score > 0.9", ddos_high),
        ("hardware.normal", hw.get("cpu_percent", 0) < 70),
        ("user.normal", not usr.get("anomaly", False)),
        ("security.low_firewall", sec.get("firewall_hits", 0) < 100),
    ]

    if not ddos_high:
        return None

    matched = [name for name, hit in indicators if hit]
    confidence = _clamp(len(matched) / len(indicators))

    if not others_normal:
        return None

    return {
        "id": _alert_id(),
        "timestamp": _now_iso(),
        "rule_name": "DDoS Only",
        "severity": "medium",
        "affected_domains": ["network"],
        "root_cause": (
            f"Pure volumetric DDoS detected (score {net.get('ddos_score', 0):.2f}) "
            f"with no correlated anomalies in hardware, user, or security domains."
        ),
        "recommended_actions": [
            "Engage upstream DDoS scrubbing service",
            "Rate-limit inbound traffic at edge",
            "Monitor for lateral escalation",
        ],
        "confidence_score": round(confidence, 2),
        "matched_indicators": matched,
    }


# ===================================================================== #
#                       CORRELATION ENGINE                              #
# ===================================================================== #

class CorrelationEngine:
    """
    Evaluates a bank of correlation rules against each incoming domain
    snapshot and returns any triggered alerts.

    Usage::

        engine = CorrelationEngine()
        alerts = engine.correlate(event["domains"])
    """

    def __init__(self) -> None:
        self._rules: list[tuple[str, RuleFunc]] = [
            ("Multi-stage Attack", _rule_multi_stage_attack),
            ("Cryptominer", _rule_cryptominer),
            ("Brute Force", _rule_brute_force),
            ("Insider Threat", _rule_insider_threat),
            ("DDoS Only", _rule_ddos_only),
        ]

    @property
    def rule_names(self) -> list[str]:
        return [name for name, _ in self._rules]

    def correlate(self, domain_snapshot: DomainSnapshot) -> list[CorrelationAlert]:
        """
        Run every registered rule against *domain_snapshot* (the ``domains``
        dict from a full event).  Returns a list of triggered alerts (may be
        empty).
        """
        triggered: list[CorrelationAlert] = []
        for _name, rule_fn in self._rules:
            result = rule_fn(domain_snapshot)
            if result is not None:
                triggered.append(result)
        return triggered


# Module-level singleton
correlation_engine = CorrelationEngine()
