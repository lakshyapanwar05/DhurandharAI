import { useEffect, useRef } from "react";
import anime from "animejs";

interface NavbarProps {
  hasAnomaly: boolean;
  activeScenario: string | null;
}

export default function Navbar({ hasAnomaly, activeScenario }: NavbarProps) {
  const dotRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (!dotRef.current) return;
    anime.remove(dotRef.current);
    anime({
      targets: dotRef.current,
      scale: [1, 1.5, 1],
      opacity: [1, 0.4, 1],
      duration: hasAnomaly ? 600 : 1800,
      easing: "easeInOutSine",
      loop: true,
    });
  }, [hasAnomaly]);

  return (
    <nav className="flex items-center justify-between px-6 py-3 border-b border-white/10 bg-[#0d1117]/80 backdrop-blur-md sticky top-0 z-50">
      {/* Logo */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-[#00ff41]/20 flex items-center justify-center">
          <span className="text-[#00ff41] font-bold text-lg">D</span>
        </div>
        <span className="text-white font-semibold text-lg tracking-wide">
          Dhurandar<span className="text-[#00ff41]">AI</span>
        </span>
      </div>

      {/* Status */}
      <div className="flex items-center gap-4">
        {activeScenario && (
          <span className="text-xs font-mono px-2 py-1 rounded bg-red-500/20 text-red-400 border border-red-500/30">
            SIM: {activeScenario.toUpperCase()}
          </span>
        )}
        <div className="flex items-center gap-2">
          <span
            ref={dotRef}
            className={`inline-block w-2.5 h-2.5 rounded-full ${
              hasAnomaly ? "bg-[#ff3131]" : "bg-[#00ff41]"
            }`}
          />
          <span
            className={`text-xs font-mono tracking-wider ${
              hasAnomaly ? "text-[#ff3131]" : "text-[#00ff41]"
            }`}
          >
            SYSTEM {hasAnomaly ? "ALERT" : "NOMINAL"}
          </span>
        </div>
      </div>
    </nav>
  );
}
