import type { NetworkDomain } from "../types";
import React from "react";
import DomainCard from "./DomainCard";

interface Props {
  data: NetworkDomain;
}

function ScoreBar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="w-full h-2 rounded-full bg-white/5 overflow-hidden">
      <div
        className="h-full rounded-full transition-all duration-500"
        style={{ width: `${pct}%`, backgroundColor: color }}
      />
    </div>
  );
};

const NetworkTraffic = function({ data }: Props) {
  const ddosColor =
    data.ddos_score > 0.7 ? "#ff3131" : data.ddos_score > 0.3 ? "#f59e0b" : "#00ff41";

  return (
    <DomainCard title="Network Traffic" icon="🌐" anomaly={data.anomaly}>
      <div className="space-y-4">
        {/* Packets/sec */}
        <div>
          <div className="flex justify-between text-xs text-white/50 mb-1">
            <span>Packets / sec</span>
            <span className="font-mono text-white/80">
              {data.packets_per_sec.toLocaleString()}
            </span>
          </div>
          <ScoreBar value={data.packets_per_sec} max={60000} color="#00ff41" />
        </div>

        {/* DDoS Score */}
        <div>
          <div className="flex justify-between text-xs text-white/50 mb-1">
            <span>DDoS Score</span>
            <span className="font-mono" style={{ color: ddosColor }}>
              {data.ddos_score.toFixed(2)}
            </span>
          </div>
          <ScoreBar value={data.ddos_score} max={1} color={ddosColor} />
        </div>

        {/* Quick stats row */}
        <div className="flex gap-3 pt-1">
          <div className="flex-1 rounded-lg bg-white/5 p-2 text-center">
            <div className="text-[10px] text-white/40 uppercase">Throughput</div>
            <div className="text-sm font-mono text-white/80">
              {(data.packets_per_sec * 0.064).toFixed(1)} Mbps
            </div>
          </div>
          <div className="flex-1 rounded-lg bg-white/5 p-2 text-center">
            <div className="text-[10px] text-white/40 uppercase">Threat</div>
            <div className="text-sm font-mono" style={{ color: ddosColor }}>
              {data.ddos_score > 0.7
                ? "CRITICAL"
                : data.ddos_score > 0.3
                ? "ELEVATED"
                : "LOW"}
            </div>
          </div>
        </div>
      </div>
    </DomainCard>
  );
};

export default React.memo(NetworkTraffic);
