import { useState, useEffect } from "react";
import Navbar from "./Navbar";
import NetworkTraffic from "./NetworkTraffic";
import HardwareMetrics from "./HardwareMetrics";
import UserActivity from "./UserActivity";
import SecurityEvents from "./SecurityEvents";
import AlertFeed from "./AlertFeed";
import ChatAssistant from "./ChatAssistant";
import NetworkTopology from "./NetworkTopology";
import AttackSimulator from "./AttackSimulator";
import ThreatPopup from "./ThreatPopup";
import GeoAttackMap from "./GeoAttackMap";
import ThreatReport from "./ThreatReport";
import AttackTimeline from "./AttackTimeline";
import IncidentPanel from "./IncidentPanel";
import { useIncidents } from "../hooks/useIncidents";
import { useNetworkData, UseNetworkDataReturn } from "../hooks/useNetworkData";

export default function Dashboard() {
  const { 
    networkData, 
    alerts, 
    topology, 
    isConnected, 
    connectionStatus, 
    triggerScenario, 
    activeScenario,
    networkAnomaly,
    hardwareAnomaly,
    userAnomaly,
    securityAnomaly,
    realAttackerIp,
  }: UseNetworkDataReturn = useNetworkData();

  const [cpuHistory, setCpuHistory] = useState<number[]>([34, 32, 36, 33, 35, 34, 37, 33]);
  const [criticalThreat, setCriticalThreat] = useState<any>(null);
  const [showThreatReport, setShowThreatReport] = useState(false);
  const [showGeoMap, setShowGeoMap] = useState(false);
  
  const { stats } = useIncidents();

  // Check if this is a real attack using the extracted realAttackerIp
  const isRealAttack = realAttackerIp != null;
  const realAttackSource = realAttackerIp;
  
  // Debug logging for real attacks
  console.log("🔥 Dashboard Real Attack Check:", {
    attackMode: networkData.attack_mode,
    realAttack: networkData.real_attack,
    isRealAttack,
    realAttackSource,
    fullNetworkData: networkData
  });
  
  // Additional debug for real attack banner
  if (isRealAttack) {
    console.log("🚨 REAL ATTACK MODE DETECTED!");
    console.log("🚨 Real attack data:", networkData.real_attack);
    console.log("🚨 Real attacker IP:", realAttackerIp);
    console.log("🚨 Should show banner for IP:", realAttackSource);
    console.log("🚨 Anomaly states:", {
      networkAnomaly,
      hardwareAnomaly,
      userAnomaly,
      securityAnomaly
    });
  } else {
    console.log("ℹ️ No real attack detected - realAttackerIp:", realAttackerIp);
  }

  // Track CPU history from incoming network data
  useEffect(() => {
    setCpuHistory((prev) => {
      const next = [...prev, networkData.domains.hardware.cpu_percent];
      return next.length > 30 ? next.slice(-30) : next;
    });
  }, [networkData.domains.hardware.cpu_percent]);

  // Listen for critical threat events
  useEffect(() => {
    const handleCriticalThreat = (event: CustomEvent) => {
      setCriticalThreat(event.detail);
    };

    window.addEventListener('criticalThreat', handleCriticalThreat as EventListener);
    return () => {
      window.removeEventListener('criticalThreat', handleCriticalThreat as EventListener);
    };
  }, []);

  // Show geo map when attack is active
  useEffect(() => {
    setShowGeoMap(!!activeScenario);
  }, [activeScenario]);

  const { domains } = networkData;
  const hasAnomaly =
    domains.network.anomaly ||
    domains.hardware.anomaly ||
    domains.user.anomaly ||
    domains.security.anomaly;

  return (
    <div className="min-h-screen bg-[#0a0f0a] flex flex-col">
      <Navbar 
        hasAnomaly={hasAnomaly} 
        activeScenario={activeScenario} 
        onGenerateReport={() => setShowThreatReport(true)} 
        websocketAlerts={alerts}
      />
      
      {/* Real Attack Banner */}
      {isRealAttack && (
        <div className="bg-red-600 border-4 border-red-800 text-white px-6 py-4 rounded-lg mx-6 mt-4 animate-pulse shadow-2xl shadow-red-900/50">
          <div className="flex items-center justify-center">
            <span className="text-3xl font-bold mr-3">⚠️</span>
            <span className="text-2xl font-bold text-center">REAL ATTACK FROM {realAttackSource}</span>
            <span className="text-3xl font-bold ml-3">⚠️</span>
          </div>
        </div>
      )}
      
      {/* Debug Banner - Always show when attack_mode is real */}
      {networkData.attack_mode === "real" && (
        <div className="bg-yellow-600 border-2 border-yellow-800 text-white px-4 py-2 rounded-lg mx-6 mt-2">
          <div className="text-center text-sm">
            DEBUG: attack_mode="real", real_attack={JSON.stringify(networkData.real_attack)}
          </div>
        </div>
      )}
      
      <main className="flex-1 p-6 space-y-6">
        {/* Domain Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <NetworkTraffic data={domains.network} />
          <HardwareMetrics data={domains.hardware} history={cpuHistory} />
          <UserActivity data={domains.user} />
          <SecurityEvents data={domains.security} />
        </div>

        {/* Network Topology Map */}
        <div className="mt-4">
          <NetworkTopology networkState={topology} networkData={networkData} />
        </div>

        {/* Geo Attack Map - shown during attacks */}
        {showGeoMap && (
          <div className="mt-4">
            <GeoAttackMap 
              activeScenario={activeScenario} 
              onReset={() => setShowGeoMap(false)}
            />
          </div>
        )}

        {/* Attack Timeline - shown during attacks */}
        <AttackTimeline 
          networkData={networkData} 
          isActive={!!activeScenario} 
        />
      </main>

      {/* Alert feed */}
      <AlertFeed alerts={alerts} />

      {/* Incident Database Panel */}
      <IncidentPanel />

      {/* AI Chat Assistant */}
      <ChatAssistant networkContext={networkData} />

      {/* Demo Control Panel */}
      <AttackSimulator activeScenario={activeScenario} />

      {/* Critical Threat Popup */}
      <ThreatPopup 
        incident={criticalThreat}
        onClose={() => setCriticalThreat(null)}
        onAskAI={() => {
          // Open chat and focus on AI
          const chatButton = document.querySelector('[data-chat-button]');
          chatButton?.dispatchEvent(new Event('click'));
          setCriticalThreat(null);
        }}
      />

      {/* Threat Report Modal */}
      <ThreatReport 
        isOpen={showThreatReport}
        onClose={() => setShowThreatReport(false)}
      />
    </div>
  );
}
