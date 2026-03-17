import { useState, useEffect, useRef } from "react";
import anime from "animejs";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Scenario {
  id: "ddos" | "cryptominer" | "bruteforce" | "insider";
  label: string;
  icon: string;
  color: string;
}

// ---------------------------------------------------------------------------
// Scenarios
// ---------------------------------------------------------------------------

const SCENARIOS: Scenario[] = [
  { id: "ddos", label: "Trigger DDoS", icon: "🔴", color: "#ff3131" },
  { id: "cryptominer", label: "Deploy Cryptominer", icon: "⚠️", color: "#f59e0b" },
  { id: "bruteforce", label: "Brute Force Attack", icon: "🔑", color: "#f59e0b" },
  { id: "insider", label: "Insider Threat", icon: "🕵️", color: "#f59e0b" },
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function AttackSimulator() {
  const [activeScenario, setActiveScenario] = useState<string | null>(null);
  const [isFlashing, setIsFlashing] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const flashRef = useRef<HTMLDivElement>(null);
  const flashTextRef = useRef<HTMLDivElement>(null);

  // -----------------------------------------------------------------------
  // Panel entrance animation
  // -----------------------------------------------------------------------
  useEffect(() => {
    if (!panelRef.current) return;
    anime({
      targets: panelRef.current,
      translateY: [-12, 0],
      opacity: [0, 1],
      duration: 600,
      easing: "easeOutExpo",
    });
  }, []);

  // -----------------------------------------------------------------------
  // Trigger scenario
  // -----------------------------------------------------------------------
  const triggerScenario = async (scenario: Scenario) => {
    if (activeScenario === scenario.id) return;

    try {
      const res = await fetch("http://localhost:8000/api/simulate/attack", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario: scenario.id }),
      });
      const data = await res.json();
      console.log("[AttackSimulator] Triggered:", data);
      setActiveScenario(scenario.id);
      // Flash effect
      flash(scenario.color);
    } catch (e) {
      console.error("[AttackSimulator] Failed to trigger scenario:", e);
    }
  };

  // -----------------------------------------------------------------------
  // Reset to normal
  // -----------------------------------------------------------------------
  const resetNormal = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/simulate/stop", {
        method: "POST",
      });
      const data = await res.json();
      console.log("[AttackSimulator] Reset:", data);
      setActiveScenario(null);
    } catch (e) {
      console.error("[AttackSimulator] Failed to reset:", e);
    }
  };

  // -----------------------------------------------------------------------
  // Cinematic flash + text overlay
  // -----------------------------------------------------------------------
  const flash = (color: string) => {
    if (!flashRef.current || !flashTextRef.current) return;
    setIsFlashing(true);

    // Ensure overlay is visible during animation
    anime.set(flashRef.current, { 
      backgroundColor: color, 
      opacity: 0,
      display: "flex"
    });

    // Flash overlay - quick fade in/out
    anime({
      targets: flashRef.current,
      opacity: [0, 0.8, 0],
      duration: 300,
      easing: "easeInOutQuad",
      complete: () => {
        // Hide overlay completely after flash
        anime.set(flashRef.current, { display: "none" });
        setIsFlashing(false);
      },
    });

    // Text overlay - longer display
    anime.set(flashTextRef.current, { opacity: 0, scale: 1.2 });
    anime({
      targets: flashTextRef.current,
      opacity: [0, 1, 1, 0],
      scale: [1.2, 1, 1, 0.95],
      duration: 2000,
      easing: "easeInOutQuad",
      delay: anime.stagger(0),
    });
  };

  return (
    <>
      {/* ---- Floating demo control panel ---- */}
      <div
        ref={panelRef}
        className="fixed top-4 right-4 z-40 rounded-xl border border-white/10 bg-[#0d1117]/95 backdrop-blur-md shadow-[-2px_2px_20px_rgba(0,0,0,0.6)] p-4 min-w-[240px]"
      >
        {/* Header */}
        <div className="flex items-center gap-2 mb-3">
          <span className="text-[10px] font-mono text-[#00ff41] font-semibold uppercase tracking-wider">
            DEMO CONTROLS
          </span>
          {activeScenario && (
            <span className="ml-auto text-[9px] font-mono px-2 py-0.5 rounded bg-[#ff3131]/20 text-[#ff3131] border border-[#ff3131]/30">
              ACTIVE
            </span>
          )}
        </div>

        {/* Attack buttons */}
        <div className="space-y-2">
          {SCENARIOS.map((scenario) => (
            <button
              key={scenario.id}
              onClick={() => triggerScenario(scenario)}
              disabled={activeScenario === scenario.id}
              className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-[11px] font-semibold transition-all ${
                activeScenario === scenario.id
                  ? "bg-[#ff3131]/20 text-[#ff3131] border border-[#ff3131]/30 cursor-not-allowed"
                  : "bg-white/5 text-white/70 border border-white/10 hover:bg-white/10 hover:text-white/90 hover:border-white/20"
              }`}
            >
              <span className="text-base">{scenario.icon}</span>
              <span>{scenario.label}</span>
            </button>
          ))}
        </div>

        {/* Reset button */}
        <div className="mt-3 pt-3 border-t border-white/10">
          <button
            onClick={resetNormal}
            disabled={!activeScenario}
            className="w-full px-3 py-2 rounded-lg bg-[#00ff41]/15 text-[#00ff41] border border-[#00ff41]/20 text-[11px] font-semibold hover:bg-[#00ff41]/25 hover:border-[#00ff41]/30 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
          >
            Reset to Normal
          </button>
        </div>
      </div>

      {/* ---- Full-screen cinematic flash overlay ---- */}
      <div
        ref={flashRef}
        className="fixed inset-0 z-[9999] pointer-events-none flex items-center justify-center"
        style={{ display: "none" }} // Controlled by anime.set in flash()
      >
        <div
          ref={flashTextRef}
          className="text-white font-bold text-center"
          style={{
            textShadow: "0 0 30px rgba(255,255,255,0.8), 0 0 60px rgba(255,255,255,0.4)",
          }}
        >
          <div className="text-4xl md:text-6xl tracking-wider uppercase">
            ATTACK SCENARIO
          </div>
          <div className="text-2xl md:text-4xl mt-2 tracking-wider">
            INITIATED
          </div>
        </div>
      </div>
    </>
  );
}
