import type { UserDomain } from "../types";
import React from "react";
import DomainCard from "./DomainCard";

interface Props {
  data: UserDomain;
}

const UserActivity = function({ data }: Props) {
  return (
    <DomainCard title="User Activity" icon="👤" anomaly={data.anomaly}>
      <div className="space-y-3">
        {/* Active users */}
        <div className="flex items-center justify-between">
          <span className="text-xs text-white/50">Active Users</span>
          <span className="text-xl font-mono text-[#00ff41]">
            {data.active_users}
          </span>
        </div>

        {/* Flagged logins */}
        <div>
          <div className="text-[10px] text-white/40 uppercase mb-2">
            Flagged Logins
            {data.flagged_logins.length > 0 && (
              <span className="ml-1 text-[#ff3131]">
                ({data.flagged_logins.length})
              </span>
            )}
          </div>
          {data.flagged_logins.length === 0 ? (
            <div className="text-xs text-white/30 italic py-2 text-center rounded-lg bg-white/[0.02]">
              No flagged logins
            </div>
          ) : (
            <div className="space-y-1.5 max-h-28 overflow-y-auto pr-1 scrollbar-thin">
              {data.flagged_logins.slice(0, 8).map((login, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 text-xs px-2 py-1.5 rounded-lg bg-[#ff3131]/5 border border-[#ff3131]/10"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-[#ff3131] shrink-0" />
                  <span className="text-white/70 font-mono truncate">
                    {login}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick stat */}
        <div className="rounded-lg bg-white/5 p-2 text-center">
          <div className="text-[10px] text-white/40 uppercase">Status</div>
          <div
            className={`text-sm font-mono ${
              data.anomaly ? "text-[#ff3131]" : "text-[#00ff41]"
            }`}
          >
            {data.anomaly ? "SUSPICIOUS ACTIVITY" : "NORMAL"}
          </div>
        </div>
      </div>
    </DomainCard>
  );
};

export default React.memo(UserActivity);
