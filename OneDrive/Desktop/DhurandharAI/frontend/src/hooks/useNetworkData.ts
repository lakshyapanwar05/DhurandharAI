import { useState, useEffect, useRef, useCallback } from "react";
import type { NetworkEvent, CorrelatedAlert, NodeState, Domains } from "../types";
import { MOCK_EVENT, MOCK_ALERTS } from "../mockData";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ConnectionStatus = "CONNECTED" | "RECONNECTING" | "OFFLINE";

export interface UseNetworkDataReturn {
  networkData: NetworkEvent;
  alerts: CorrelatedAlert[];
  topology: NodeState[];
  isConnected: boolean;
  connectionStatus: ConnectionStatus;
  triggerScenario: (scenarioName: string) => Promise<void>;
  activeScenario: string | null;
  // Extracted anomaly states
  networkAnomaly: boolean;
  hardwareAnomaly: boolean;
  userAnomaly: boolean;
  securityAnomaly: boolean;
  realAttackerIp: string | null;
}

// ---------------------------------------------------------------------------
// Helper: derive topology state from domains
// ---------------------------------------------------------------------------

function deriveTopology(domains: Domains): NodeState[] {
  const net = domains.network;
  const hw = domains.hardware;
  const sec = domains.security;
  const usr = domains.user;

  const s = (
    anomaly: boolean,
    score?: number
  ): "healthy" | "warning" | "compromised" => {
    if (anomaly)
      return score !== undefined && score > 0.7 ? "compromised" : "warning";
    return "healthy";
  };

  const fwStatus = s(sec.anomaly, net.ddos_score);
  const routerStatus = s(net.anomaly, net.ddos_score);
  const wsStatus = s(usr.anomaly);
  const dnsStatus =
    sec.anomaly && (sec.ids_alerts ?? []).length > 2
      ? ("compromised" as const)
      : sec.anomaly
      ? ("warning" as const)
      : ("healthy" as const);

  return [
    {
      nodeId: "internet",
      status: "healthy",
      traffic: net.packets_per_sec / 100,
      ip: "0.0.0.0",
    },
    {
      nodeId: "router",
      status: routerStatus,
      traffic: net.packets_per_sec / 80,
      ip: "10.0.0.1",
      alerts: net.anomaly ? ["High packet rate"] : [],
    },
    {
      nodeId: "firewall",
      status: fwStatus,
      traffic: sec.firewall_hits,
      ip: "10.0.0.2",
      alerts: (sec.ids_alerts ?? []).slice(0, 3),
    },
    {
      nodeId: "switch",
      status: s(net.anomaly),
      traffic: net.packets_per_sec / 60,
      ip: "10.0.0.3",
    },
    {
      nodeId: "dns",
      status: dnsStatus,
      traffic: 15 + Math.random() * 10,
      ip: "10.0.0.10",
      alerts: dnsStatus !== "healthy" ? ["DNS amplification risk"] : [],
    },
    {
      nodeId: "ws-01",
      status: wsStatus,
      traffic: 10 + Math.random() * 20,
      ip: "10.0.1.11",
      alerts: (usr.flagged_logins ?? []).slice(0, 1),
    },
    {
      nodeId: "ws-02",
      status:
        hw.cpu_percent > 90
          ? "compromised"
          : hw.cpu_percent > 70
          ? "warning"
          : "healthy",
      traffic: hw.cpu_percent / 3,
      ip: "10.0.1.12",
      alerts: hw.anomaly ? [`CPU ${hw.cpu_percent.toFixed(0)}%`] : [],
    },
    {
      nodeId: "ws-03",
      status: wsStatus,
      traffic: 10 + Math.random() * 20,
      ip: "10.0.1.13",
      alerts: (usr.flagged_logins ?? []).slice(1, 2),
    },
    {
      nodeId: "ws-04",
      status: "healthy",
      traffic: 10 + Math.random() * 15,
      ip: "10.0.1.14",
    },
  ];
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useNetworkData(): UseNetworkDataReturn {
  const [networkData, setNetworkData] = useState<NetworkEvent>(MOCK_EVENT);
  const [alerts, setAlerts] = useState<CorrelatedAlert[]>(MOCK_ALERTS);
  const [topology, setTopology] = useState<NodeState[]>(
    deriveTopology(MOCK_EVENT.domains)
  );
  const [connectionStatus, setConnectionStatus] =
    useState<ConnectionStatus>("OFFLINE");
  const [activeScenario, setActiveScenario] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);
  const scenarioPollerRef = useRef<NodeJS.Timeout | null>(null);

  // -----------------------------------------------------------------------
  // WebSocket connection with auto-reconnect
  // -----------------------------------------------------------------------

  const connect = useCallback(() => {
    // Clear any pending reconnect
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }

    // Connection guard: only create new WebSocket if previous is fully CLOSED
    if (wsRef.current && wsRef.current.readyState !== WebSocket.CLOSED) {
      console.log("[useNetworkData] WebSocket already exists, skipping connection");
      return;
    }

    setConnectionStatus("RECONNECTING");

    const ws = new WebSocket("ws://localhost:8000/ws");
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("[useNetworkData] WebSocket connected - persistent connection established");
      setConnectionStatus("CONNECTED");
      
      // Send a ping to verify connection
      ws.send(JSON.stringify({ type: "ping", timestamp: Date.now() }));
    };

    ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data);
        console.log("🔥 WS RAW DATA:", msg.data);
        console.log("RAW WS MESSAGE KEYS:", Object.keys(data));
        console.log("RAW DOMAINS:", data.domains);
        console.log("🔥 WS PARSED DATA:", data);
        
        // Extract anomaly states correctly
        const networkAnomaly = data.domains?.network?.anomaly ?? false;
        const hardwareAnomaly = data.domains?.hardware?.anomaly ?? false;
        const userAnomaly = data.domains?.user?.anomaly ?? false;
        const securityAnomaly = data.domains?.security?.anomaly ?? false;
        
        // Try multiple locations for real_attacker_ip
        const realAttackerIp = data.real_attacker_ip ?? data.domains?.real_attacker_ip ?? data.metadata?.real_attacker_ip ?? null;
        const scenarioActive = data.scenario_active ?? null;
        
        console.log("🔍 REAL ATTACKER IP DETECTION:", {
          direct: data.real_attacker_ip,
          domains: data.domains?.real_attacker_ip,
          metadata: data.metadata?.real_attacker_ip,
          final: realAttackerIp
        });
        
        console.log("🔍 EXTRACTED ANOMALY STATES:", {
          networkAnomaly,
          hardwareAnomaly,
          userAnomaly,
          securityAnomaly,
          realAttackerIp,
          scenarioActive,
          attackMode: data.attack_mode,
          realAttack: data.real_attack,
          correlatedAlerts: data.correlated_alerts?.length || 0
        });
        
        // Update network data with extracted fields
        setNetworkData(data);

        // Update active scenario from WebSocket
        if (scenarioActive) {
          setActiveScenario(scenarioActive);
        }

        // Derive topology from domains
        setTopology(deriveTopology(data.domains));

        // Merge new correlated alerts
        if ((data.correlated_alerts ?? []).length > 0) {
          setAlerts((prev) => {
            const ids = new Set(prev.map((a) => a.id));
            const fresh = (data.correlated_alerts ?? []).filter((a) => !ids.has(a.id));
            const merged = [...fresh, ...prev];
            return merged.slice(0, 50);
          });
        }
      } catch (e) {
        console.error("[useNetworkData] Parse error", e);
      }
    };

    ws.onclose = () => {
      console.log("[useNetworkData] WebSocket closed — reconnecting in 3s");
      setConnectionStatus("RECONNECTING");
      reconnectTimerRef.current = setTimeout(connect, 3000);
    };

    ws.onerror = () => {
      console.error("[useNetworkData] WebSocket error");
      ws.close();
    };

    wsRef.current = ws;
  }, []);

  // Initial connection and heartbeat
  useEffect(() => {
    connect();
    
    // Add heartbeat: send ping every 10 seconds to keep connection alive
    const heartbeat = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({type: 'ping'}));
        console.log("[useNetworkData] Heartbeat ping sent");
      }
    }, 10000);
    
    return () => {
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) wsRef.current.close();
      if (heartbeat) clearInterval(heartbeat);
    };
  }, [connect]);

  // -----------------------------------------------------------------------
  // Poll simulation status
  // -----------------------------------------------------------------------

  useEffect(() => {
    const pollStatus = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/simulate/status");
        const data = await res.json();
        setActiveScenario(data.active_scenario);
      } catch {
        // ignore
      }
    };

    pollStatus();
    scenarioPollerRef.current = setInterval(pollStatus, 4000);

    return () => {
      if (scenarioPollerRef.current) clearInterval(scenarioPollerRef.current);
    };
  }, []);

  // -----------------------------------------------------------------------
  // Trigger scenario function
  // -----------------------------------------------------------------------

  const triggerScenario = useCallback(async (scenarioName: string) => {
    try {
      const res = await fetch("http://localhost:8000/api/simulate/attack", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario: scenarioName }),
      });
      const data = await res.json();
      console.log("[useNetworkData] Scenario triggered:", data);
      setActiveScenario(scenarioName);
    } catch (e) {
      console.error("[useNetworkData] Failed to trigger scenario:", e);
    }
  }, []);

  // -----------------------------------------------------------------------
  // Return
  // -----------------------------------------------------------------------

  return {
    networkData,
    alerts,
    topology,
    isConnected: connectionStatus === "CONNECTED",
    connectionStatus,
    triggerScenario,
    activeScenario,
    // Extracted anomaly states for components
    networkAnomaly: networkData.domains?.network?.anomaly ?? false,
    hardwareAnomaly: networkData.domains?.hardware?.anomaly ?? false,
    userAnomaly: networkData.domains?.user?.anomaly ?? false,
    securityAnomaly: networkData.domains?.security?.anomaly ?? false,
    realAttackerIp: networkData.real_attacker_ip ?? null,
  };
}
