import { useEffect, useRef } from "react";
import React from "react";
import anime from "animejs";

interface DomainCardProps {
  title: string;
  icon: string;
  anomaly: boolean;
  children: React.ReactNode;
}

const DomainCard = function({
  title,
  icon,
  anomaly,
  children,
}: DomainCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const prevAnomaly = useRef(false);

  // Floating entrance animation
  useEffect(() => {
    if (!cardRef.current) return;
    anime({
      targets: cardRef.current,
      translateY: [20, 0],
      opacity: [0, 1],
      duration: 800,
      easing: "easeOutExpo",
      delay: anime.random(0, 300),
    });
  }, []);

  // Anomaly shake + red glow
  useEffect(() => {
    if (!cardRef.current) return;
    if (anomaly && !prevAnomaly.current) {
      anime({
        targets: cardRef.current,
        translateX: [0, -6, 6, -4, 4, -2, 2, 0],
        duration: 500,
        easing: "easeInOutQuad",
      });
    }
    prevAnomaly.current = anomaly;
  }, [anomaly]);

  return (
    <div
      ref={cardRef}
      className={`rounded-xl border p-5 transition-all duration-300 opacity-0 ${
        anomaly
          ? "border-[#ff3131]/60 bg-[#ff3131]/5 shadow-[0_0_20px_rgba(255,49,49,0.15)]"
          : "border-white/10 bg-[#0d1117] shadow-lg"
      }`}
    >
      <div className="flex items-center gap-2 mb-4">
        <span className="text-lg">{icon}</span>
        <h3 className="text-sm font-semibold text-white/90 tracking-wide uppercase">
          {title}
        </h3>
        {anomaly && (
          <span className="ml-auto text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#ff3131]/20 text-[#ff3131] border border-[#ff3131]/30">
            ANOMALY
          </span>
        )}
      </div>
      {children}
    </div>
  );
};

export default React.memo(DomainCard);
