export interface NetworkDomain {
  packets_per_sec: number;
  ddos_score: number;
  anomaly: boolean;
}

export interface HardwareDomain {
  cpu_percent: number;
  memory_percent: number;
  anomaly: boolean;
}

export interface UserDomain {
  active_users: number;
  flagged_logins: string[];
  anomaly: boolean;
}

export interface SecurityDomain {
  firewall_hits: number;
  ids_alerts: string[];
  anomaly: boolean;
}

export interface Domains {
  network: NetworkDomain;
  hardware: HardwareDomain;
  user: UserDomain;
  security: SecurityDomain;
}

export interface CorrelatedAlert {
  id: string;
  timestamp: string;
  severity: "critical" | "high" | "medium" | "low";
  title?: string;
  rule_name?: string;
  domains: string[];
  description?: string;
  root_cause?: string;
  recommended_actions?: string[];
  confidence_score?: number;
  matched_indicators?: string[];
}

export interface TopologyNode {
  id: string;
  label: string;
  type: string;
  status: "normal" | "alert";
}

export interface TopologyEdge {
  source: string;
  target: string;
}

export interface NetworkTopology {
  nodes: TopologyNode[];
  edges: TopologyEdge[];
}

export interface NetworkEvent {
  timestamp: string;
  domains: Domains;
  correlated_alerts: CorrelatedAlert[];
  network_topology: NetworkTopology[];
  scenario_active?: string | null;
  real_attack?: {
    source_ip: string;
    target_ip: string;
    payload: Record<string, any>;
    timestamp: string;
  };
  attack_mode?: "simulated" | "real";
  real_attacker_ip?: string;
}

export interface NodeState {
  nodeId: string;
  status: "healthy" | "warning" | "compromised";
  traffic: number;
  ip?: string;
  alerts?: string[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  provider?: string;
  cached?: boolean;
  timestamp: string;
  isProactive?: boolean;
}
