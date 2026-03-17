import type { SecurityDomain } from "../types";
import React from "react";
import DomainCard from "./DomainCard";

interface Props {
  data: SecurityDomain;
}

const SecurityEvents = function({ data }: Props) {
  const fwColor =
    data.firewall_hits > 1000
      ? "#ff3131"
      : data.firewall_hits > 200
      ? "#f59e0b"
      : "#00ff41";

  return (
    <DomainCard title="Security Events" icon="🛡️" anomaly={data.anomaly}>
      <div className="space-y-3">
        {/* Firewall hits */}
        <div className="flex items-center justify-between">
          <span className="text-xs text-white/50">Firewall Hits</span>
          <span className="text-xl font-mono" style={{ color: fwColor }}>
            {data.firewall_hits.toLocaleString()}
          </span>
        </div>

        {/* IDS Alerts */}
        <div>
          <div className="text-[10px] text-white/40 uppercase mb-2">
            IDS Alerts
            {data.ids_alerts.length > 0 && (
              <span className="ml-1 text-[#ff3131]">
                ({data.ids_alerts.length})
              </span>
            )}
          </div>
          {data.ids_alerts.length === 0 ? (
            <div className="text-xs text-white/30 italic py-2 text-center rounded-lg bg-white/[0.02]">
              No active IDS alerts
            </div>
          ) : (
            <div className="space-y-1.5 max-h-28 overflow-y-auto pr-1 scrollbar-thin">
              {data.ids_alerts.slice(0, 6).map((alert, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 text-xs px-2 py-1.5 rounded-lg bg-[#ff3131]/5 border border-[#ff3131]/10"
                >
                  <span className="text-[#ff3131] shrink-0">⚠</span>
                  <span className="text-white/70 truncate">{alert}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick stat */}
        <div className="rounded-lg bg-white/5 p-2 text-center">
          <div className="text-[10px] text-white/40 uppercase">Threat Level</div>
          <div className="text-sm font-mono" style={{ color: fwColor }}>
            {data.firewall_hits > 1000
              ? "CRITICAL"
              : data.firewall_hits > 200
              ? "ELEVATED"
              : "NORMAL"}
          </div>
        </div>
      </div>
    </DomainCard>
  );
};

export default React.memo(SecurityEvents);
