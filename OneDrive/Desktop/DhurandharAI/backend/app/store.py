from __future__ import annotations

import threading
from collections import deque
from typing import Any


class EventStore:
    """Thread-safe in-memory store for network events and correlated alerts."""

    def __init__(self, max_events: int = 500, max_alerts: int = 200) -> None:
        self._events: deque[dict[str, Any]] = deque(maxlen=max_events)
        self._alerts: deque[dict[str, Any]] = deque(maxlen=max_alerts)
        self._attack_active: bool = False
        self._lock = threading.Lock()

    # -- events --
    def push_event(self, event: dict[str, Any]) -> None:
        with self._lock:
            self._events.append(event)

    def get_events(self, n: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._events)[-n:]

    # -- alerts --
    def push_alert(self, alert: dict[str, Any]) -> None:
        with self._lock:
            self._alerts.append(alert)

    def push_alerts(self, alerts: list[dict[str, Any]]) -> None:
        with self._lock:
            self._alerts.extend(alerts)

    def get_alerts(self, n: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._alerts)[-n:]

    # -- attack flag --
    @property
    def attack_active(self) -> bool:
        return self._attack_active

    @attack_active.setter
    def attack_active(self, value: bool) -> None:
        self._attack_active = value


store = EventStore()
