import { useEffect, useRef } from "react";
import anime from "animejs";
import type { CorrelatedAlert } from "../types";

interface Props {
  alerts: CorrelatedAlert[];
}

const SEVERITY_STYLES: Record<string, { bg: string; border: string; text: string; dot: string }> = {
  critical: {
    bg: "bg-[#ff3131]/8",
    border: "border-[#ff3131]/30",
    text: "text-[#ff3131]",
    dot: "bg-[#ff3131]",
  },
  high: {
    bg: "bg-orange-500/8",
    border: "border-orange-500/30",
    text: "text-orange-400",
    dot: "bg-orange-400",
  },
  medium: {
    bg: "bg-yellow-500/8",
    border: "border-yellow-500/30",
    text: "text-yellow-400",
    dot: "bg-yellow-400",
  },
  low: {
    bg: "bg-blue-500/8",
    border: "border-blue-500/30",
    text: "text-blue-400",
    dot: "bg-blue-400",
  },
};

export default function AlertFeed({ alerts = [] }: Props) {
  const listRef = useRef<HTMLDivElement>(null);
  const prevCount = useRef(0);

  useEffect(() => {
    if (!listRef.current) return;
    const newItems = (alerts ?? []).length - prevCount.current;
    if (newItems > 0) {
      const children = listRef.current.children;
      const targets = Array.from(children).slice(0, newItems);
      if (targets.length > 0) {
        anime({
          targets,
          translateX: [80, 0],
          opacity: [0, 1],
          duration: 500,
          easing: "easeOutExpo",
          delay: anime.stagger(80),
        });
      }
    }
    prevCount.current = alerts.length;
  }, [alerts]);

  if ((alerts ?? []).length === 0) {
    return (
      <div className="border-t border-white/10 bg-[#0d1117]/60 px-6 py-4">
        <div className="text-xs text-white/30 text-center font-mono">
          No correlated alerts — all systems nominal
        </div>
      </div>
    );
  }

  return (
    <div className="border-t border-white/10 bg-[#0d1117]/60 px-6 py-3">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-semibold text-white/60 uppercase tracking-wider">
          Correlated Alerts
        </span>
        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#ff3131]/15 text-[#ff3131]">
          {(alerts ?? []).length}
        </span>
      </div>
      <div
        ref={listRef}
        className="flex gap-3 overflow-x-auto pb-1 scrollbar-thin"
      >
        {(alerts ?? []).map((alert) => {
          const s = SEVERITY_STYLES[alert.severity] ?? SEVERITY_STYLES.low;
          const title = alert.rule_name ?? alert.title ?? "Alert";
          return (
            <div
              key={alert.id}
              className={`shrink-0 w-72 rounded-lg border p-3 ${s.bg} ${s.border} opacity-0`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className={`w-2 h-2 rounded-full ${s.dot}`} />
                <span className={`text-[10px] font-mono uppercase ${s.text}`}>
                  {alert.severity}
                </span>
                {alert.confidence_score !== undefined && (
                  <span className="ml-auto text-[10px] text-white/30 font-mono">
                    {(alert.confidence_score * 100).toFixed(0)}%
                  </span>
                )}
              </div>
              <div className="text-xs text-white/80 font-medium truncate">
                {title}
              </div>
              {alert.description && (
                <div className="text-[11px] text-white/40 mt-1 line-clamp-2">
                  {alert.description}
                </div>
              )}
              <div className="flex gap-1 mt-2">
                {(alert.domains ?? []).map((d) => (
                  <span
                    key={d}
                    className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-white/5 text-white/40"
                  >
                    {d}
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
