import type { NetworkEvent, CorrelatedAlert } from "./types";

export const MOCK_EVENT: NetworkEvent = {
  timestamp: new Date().toISOString(),
  domains: {
    network: { packets_per_sec: 2340, ddos_score: 0.08, anomaly: false },
    hardware: { cpu_percent: 34.2, memory_percent: 47.1, anomaly: false },
    user: {
      active_users: 42,
      flagged_logins: [],
      anomaly: false,
    },
    security: { firewall_hits: 12, ids_alerts: [], anomaly: false },
  },
  correlated_alerts: [],
  network_topology: [
    {
      nodes: [
        { id: "fw-1", label: "Firewall", type: "firewall", status: "normal" },
        { id: "sw-core", label: "Core Switch", type: "switch", status: "normal" },
        { id: "srv-web", label: "Web Server", type: "server", status: "normal" },
        { id: "srv-db", label: "Database", type: "server", status: "normal" },
        { id: "srv-ml", label: "ML Pipeline", type: "server", status: "normal" },
        { id: "usr-seg", label: "User Segment", type: "subnet", status: "normal" },
      ],
      edges: [
        { source: "fw-1", target: "sw-core" },
        { source: "sw-core", target: "srv-web" },
        { source: "sw-core", target: "srv-db" },
        { source: "sw-core", target: "srv-ml" },
        { source: "sw-core", target: "usr-seg" },
      ],
    },
  ],
};

export const MOCK_ALERTS: CorrelatedAlert[] = [
  {
    id: "CORR-4821",
    timestamp: new Date(Date.now() - 10000).toISOString(),
    severity: "critical",
    rule_name: "Multi-stage Attack",
    title: "Multi-domain anomaly: network, security",
    domains: ["network", "security"],
    description:
      "DDoS score 0.92 with 4200 firewall hits — coordinated attack pattern.",
    confidence_score: 0.89,
  },
  {
    id: "CORR-3917",
    timestamp: new Date(Date.now() - 25000).toISOString(),
    severity: "high",
    rule_name: "Brute Force",
    title: "Brute-force campaign detected",
    domains: ["user", "security"],
    description: "52 failed logins from 8 unique IPs in the last 60 seconds.",
    confidence_score: 0.76,
  },
  {
    id: "CORR-2055",
    timestamp: new Date(Date.now() - 60000).toISOString(),
    severity: "medium",
    rule_name: "Insider Threat",
    title: "After-hours sensitive file access",
    domains: ["user"],
    description:
      "User jdoe accessed /etc/shadow and /var/db/customers.csv at 03:12 UTC.",
    confidence_score: 0.61,
  },
];
