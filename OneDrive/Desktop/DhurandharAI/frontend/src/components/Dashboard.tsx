import { useState, useEffect } from "react";
import type { UseNetworkDataReturn } from "../hooks/useNetworkData";
import Navbar from "./Navbar";
import NetworkTraffic from "./NetworkTraffic";
import HardwareMetrics from "./HardwareMetrics";
import UserActivity from "./UserActivity";
import SecurityEvents from "./SecurityEvents";
import AlertFeed from "./AlertFeed";
import ChatAssistant from "./ChatAssistant";
import NetworkTopology from "./NetworkTopology";
import AttackSimulator from "./AttackSimulator";

export default function Dashboard({
  networkData,
  alerts,
  topology,
  isConnected,
  connectionStatus,
  activeScenario,
}: UseNetworkDataReturn) {
  const [cpuHistory, setCpuHistory] = useState<number[]>([34, 32, 36, 33, 35, 34, 37, 33]);

  // Track CPU history from incoming network data
  useEffect(() => {
    setCpuHistory((prev) => {
      const next = [...prev, networkData.domains.hardware.cpu_percent];
      return next.length > 30 ? next.slice(-30) : next;
    });
  }, [networkData.domains.hardware.cpu_percent]);

  const { domains } = networkData;
  const hasAnomaly =
    domains.network.anomaly ||
    domains.hardware.anomaly ||
    domains.user.anomaly ||
    domains.security.anomaly;

  return (
    <div className="min-h-screen bg-[#0a0f0a] flex flex-col">
      <Navbar hasAnomaly={hasAnomaly} activeScenario={activeScenario} />

      {/* Domain cards grid */}
      <main className="flex-1 p-4 md:p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          <NetworkTraffic data={domains.network} />
          <HardwareMetrics data={domains.hardware} history={cpuHistory} />
          <UserActivity data={domains.user} />
          <SecurityEvents data={domains.security} />
        </div>

        {/* Network Topology Map */}
        <div className="mt-4">
          <NetworkTopology networkState={topology} />
        </div>
      </main>

      {/* Alert feed */}
      <AlertFeed alerts={alerts} />

      {/* AI Chat Assistant */}
      <ChatAssistant networkContext={networkData} />

      {/* Demo Control Panel */}
      <AttackSimulator />
    </div>
  );
}
