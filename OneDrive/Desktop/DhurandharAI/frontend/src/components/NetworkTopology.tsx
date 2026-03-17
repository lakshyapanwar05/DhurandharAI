import { useEffect, useRef, useState, useCallback } from "react";
import * as d3 from "d3";
import anime from "animejs";
import type { NodeState } from "../types";

// ---------------------------------------------------------------------------
// Topology definition — fixed positions for a clean NOC layout
// ---------------------------------------------------------------------------

interface TopoNode {
  id: string;
  label: string;
  icon: string;
  x: number;
  y: number;
  ip: string;
}

interface TopoEdge {
  source: string;
  target: string;
}

const NODES: TopoNode[] = [
  { id: "internet", label: "Internet",    icon: "🌐", x: 400, y: 30,  ip: "0.0.0.0" },
  { id: "router",   label: "Router",      icon: "📡", x: 400, y: 110, ip: "10.0.0.1" },
  { id: "firewall", label: "Firewall",    icon: "🛡️", x: 400, y: 195, ip: "10.0.0.2" },
  { id: "switch",   label: "Switch",      icon: "🔀", x: 400, y: 280, ip: "10.0.0.3" },
  { id: "dns",      label: "DNS Server",  icon: "📋", x: 160, y: 280, ip: "10.0.0.10" },
  { id: "ws-01",    label: "WS-01",       icon: "💻", x: 160, y: 380, ip: "10.0.1.11" },
  { id: "ws-02",    label: "WS-02",       icon: "💻", x: 310, y: 380, ip: "10.0.1.12" },
  { id: "ws-03",    label: "WS-03",       icon: "💻", x: 490, y: 380, ip: "10.0.1.13" },
  { id: "ws-04",    label: "WS-04",       icon: "💻", x: 640, y: 380, ip: "10.0.1.14" },
];

const EDGES: TopoEdge[] = [
  { source: "internet", target: "router" },
  { source: "router",   target: "firewall" },
  { source: "firewall", target: "switch" },
  { source: "switch",   target: "dns" },
  { source: "switch",   target: "ws-01" },
  { source: "switch",   target: "ws-02" },
  { source: "switch",   target: "ws-03" },
  { source: "switch",   target: "ws-04" },
];

// ---------------------------------------------------------------------------
// Default / mock network state
// ---------------------------------------------------------------------------

const DEFAULT_STATE: NodeState[] = NODES.map((n) => ({
  nodeId: n.id,
  status: "healthy" as const,
  traffic: Math.random() * 40 + 10,
  ip: n.ip,
  alerts: [],
}));

// ---------------------------------------------------------------------------
// Color helpers
// ---------------------------------------------------------------------------

const STATUS_COLORS: Record<string, string> = {
  healthy: "#00ff41",
  warning: "#f59e0b",
  compromised: "#ff3131",
};

const STATUS_GLOW: Record<string, string> = {
  healthy: "rgba(0,255,65,0.25)",
  warning: "rgba(245,158,11,0.3)",
  compromised: "rgba(255,49,49,0.45)",
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface Props {
  networkState?: NodeState[];
}

export default function NetworkTopology({ networkState }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [tooltip, setTooltip] = useState<{
    x: number;
    y: number;
    node: TopoNode;
    state: NodeState;
  } | null>(null);
  const prevStates = useRef<Map<string, string>>(new Map());
  const trafficDotsRef = useRef<SVGGElement | null>(null);

  const states = networkState ?? DEFAULT_STATE;
  const stateMap = new Map(states.map((s) => [s.nodeId, s]));

  // Get state for a node id
  const getState = useCallback(
    (id: string): NodeState =>
      stateMap.get(id) ?? { nodeId: id, status: "healthy", traffic: 20 },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [states]
  );

  // -----------------------------------------------------------------------
  // Initial D3 render (runs once)
  // -----------------------------------------------------------------------
  useEffect(() => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const W = 800;
    const H = 430;
    svg.attr("viewBox", `0 0 ${W} ${H}`);

    // -- Defs: glow filters & gradients -----------------------------------
    const defs = svg.append("defs");

    // Glow filter for edges
    const edgeGlow = defs.append("filter").attr("id", "edge-glow");
    edgeGlow
      .append("feGaussianBlur")
      .attr("in", "SourceGraphic")
      .attr("stdDeviation", "2")
      .attr("result", "blur");
    edgeGlow
      .append("feMerge")
      .selectAll("feMergeNode")
      .data(["blur", "SourceGraphic"])
      .enter()
      .append("feMergeNode")
      .attr("in", (d) => d);

    // Glow filters per status
    for (const [status, color] of Object.entries(STATUS_GLOW)) {
      const f = defs
        .append("filter")
        .attr("id", `glow-${status}`)
        .attr("x", "-50%")
        .attr("y", "-50%")
        .attr("width", "200%")
        .attr("height", "200%");
      f.append("feDropShadow")
        .attr("dx", 0)
        .attr("dy", 0)
        .attr("stdDeviation", status === "compromised" ? 6 : 4)
        .attr("flood-color", color);
    }

    // Grid pattern for NOC background
    const grid = defs
      .append("pattern")
      .attr("id", "noc-grid")
      .attr("width", 40)
      .attr("height", 40)
      .attr("patternUnits", "userSpaceOnUse");
    grid
      .append("path")
      .attr("d", "M 40 0 L 0 0 0 40")
      .attr("fill", "none")
      .attr("stroke", "rgba(0,255,65,0.04)")
      .attr("stroke-width", 0.5);

    // Background
    svg
      .append("rect")
      .attr("width", W)
      .attr("height", H)
      .attr("fill", "url(#noc-grid)");

    // Scanline overlay
    svg
      .append("rect")
      .attr("width", W)
      .attr("height", H)
      .attr("fill", "none")
      .attr("stroke", "none")
      .style("pointer-events", "none");

    // -- Edges ------------------------------------------------------------
    const nodeMap = new Map(NODES.map((n) => [n.id, n]));

    const edgeGroup = svg.append("g").attr("class", "edges");
    EDGES.forEach((e) => {
      const s = nodeMap.get(e.source)!;
      const t = nodeMap.get(e.target)!;
      // Shadow edge
      edgeGroup
        .append("line")
        .attr("x1", s.x)
        .attr("y1", s.y)
        .attr("x2", t.x)
        .attr("y2", t.y)
        .attr("stroke", "rgba(0,255,65,0.06)")
        .attr("stroke-width", 4)
        .attr("filter", "url(#edge-glow)");
      // Main edge
      edgeGroup
        .append("line")
        .attr("class", `edge-${e.source}-${e.target}`)
        .attr("x1", s.x)
        .attr("y1", s.y)
        .attr("x2", t.x)
        .attr("y2", t.y)
        .attr("stroke", "rgba(0,255,65,0.18)")
        .attr("stroke-width", 1.5)
        .attr("stroke-dasharray", "6,4");
    });

    // -- Traffic dots layer ------------------------------------------------
    trafficDotsRef.current = svg
      .append("g")
      .attr("class", "traffic-dots")
      .node();

    // -- Nodes ------------------------------------------------------------
    const nodeGroup = svg.append("g").attr("class", "nodes");

    NODES.forEach((n) => {
      const g = nodeGroup
        .append("g")
        .attr("class", `node-group`)
        .attr("data-node-id", n.id)
        .attr("transform", `translate(${n.x}, ${n.y})`)
        .style("cursor", "pointer");

      // Outer glow ring
      g.append("circle")
        .attr("class", "node-glow")
        .attr("r", 28)
        .attr("fill", "none")
        .attr("stroke", STATUS_COLORS.healthy)
        .attr("stroke-width", 1)
        .attr("opacity", 0.3);

      // Main circle
      g.append("circle")
        .attr("class", "node-bg")
        .attr("r", 22)
        .attr("fill", "rgba(0,255,65,0.06)")
        .attr("stroke", STATUS_COLORS.healthy)
        .attr("stroke-width", 1.5);

      // Icon
      g.append("text")
        .attr("class", "node-icon")
        .attr("text-anchor", "middle")
        .attr("dy", "0.35em")
        .attr("font-size", "16px")
        .text(n.icon);

      // Label
      g.append("text")
        .attr("class", "node-label")
        .attr("text-anchor", "middle")
        .attr("dy", 40)
        .attr("fill", "rgba(255,255,255,0.5)")
        .attr("font-size", "10px")
        .attr("font-family", "monospace")
        .text(n.label);

      // Warning icon (hidden by default)
      g.append("text")
        .attr("class", "node-warning")
        .attr("text-anchor", "middle")
        .attr("dy", -32)
        .attr("font-size", "14px")
        .attr("opacity", 0)
        .text("⚡");
    });

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // -----------------------------------------------------------------------
  // Update node visuals when states change
  // -----------------------------------------------------------------------
  useEffect(() => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);

    NODES.forEach((n) => {
      const s = getState(n.id);
      const color = STATUS_COLORS[s.status] ?? STATUS_COLORS.healthy;
      const prev = prevStates.current.get(n.id);
      const g = svg.select(`[data-node-id="${n.id}"]`);

      // Update colors
      g.select(".node-bg")
        .transition()
        .duration(400)
        .attr("stroke", color)
        .attr("fill", `${color}11`);

      g.select(".node-glow")
        .transition()
        .duration(400)
        .attr("stroke", color)
        .attr("opacity", s.status === "compromised" ? 0.7 : 0.3)
        .attr("filter", `url(#glow-${s.status})`);

      g.select(".node-label")
        .transition()
        .duration(400)
        .attr("fill", s.status === "compromised" ? color : "rgba(255,255,255,0.5)");

      // Warning icon
      g.select(".node-warning")
        .transition()
        .duration(300)
        .attr("opacity", s.status === "compromised" ? 1 : 0);

      // Trigger animations on transition to compromised
      if (s.status === "compromised" && prev !== "compromised") {
        const el = g.node() as SVGGElement | null;
        if (el) {
          // Shake
          anime({
            targets: el,
            translateX: [0, -5, 6, -4, 4, -2, 2, 0],
            duration: 500,
            easing: "easeInOutQuad",
          });
          // Pulse glow ring
          anime({
            targets: el.querySelector(".node-glow"),
            r: [28, 36, 28],
            opacity: [0.7, 1, 0.7],
            duration: 800,
            easing: "easeInOutSine",
            loop: 3,
          });
        }
      }

      prevStates.current.set(n.id, s.status);
    });
  }, [states, getState]);

  // -----------------------------------------------------------------------
  // Animated traffic dots along edges (Anime.js)
  // -----------------------------------------------------------------------
  useEffect(() => {
    if (!trafficDotsRef.current) return;
    const g = d3.select(trafficDotsRef.current);
    g.selectAll("*").remove();

    const nodeMap = new Map(NODES.map((n) => [n.id, n]));

    EDGES.forEach((e) => {
      const src = nodeMap.get(e.source)!;
      const tgt = nodeMap.get(e.target)!;
      const srcState = getState(e.source);
      const tgtState = getState(e.target);
      const traffic = Math.max(srcState.traffic, tgtState.traffic);

      // Number of dots proportional to traffic (1–4)
      const dotCount = Math.min(Math.max(Math.round(traffic / 25), 1), 4);
      const edgeColor =
        srcState.status === "compromised" || tgtState.status === "compromised"
          ? "#ff3131"
          : srcState.status === "warning" || tgtState.status === "warning"
          ? "#f59e0b"
          : "#00ff41";

      for (let i = 0; i < dotCount; i++) {
        const dot = g
          .append("circle")
          .attr("r", 2)
          .attr("fill", edgeColor)
          .attr("opacity", 0.8)
          .attr("cx", src.x)
          .attr("cy", src.y)
          .node();

        if (dot) {
          anime({
            targets: dot,
            cx: [src.x, tgt.x],
            cy: [src.y, tgt.y],
            duration: 1500 + Math.random() * 1000,
            easing: "linear",
            loop: true,
            delay: i * (1500 / dotCount) + Math.random() * 300,
          });
        }
      }
    });

    return () => {
      g.selectAll("*").each(function () {
        anime.remove(this);
      });
      g.selectAll("*").remove();
    };
  }, [states, getState]);

  // -----------------------------------------------------------------------
  // Hover handler
  // -----------------------------------------------------------------------
  const handleMouseMove = useCallback(
    (e: React.MouseEvent<SVGSVGElement>) => {
      const target = (e.target as SVGElement).closest("[data-node-id]");
      if (!target) {
        setTooltip(null);
        return;
      }
      const nodeId = target.getAttribute("data-node-id")!;
      const node = NODES.find((n) => n.id === nodeId);
      const state = getState(nodeId);
      if (node) {
        const rect = svgRef.current!.getBoundingClientRect();
        setTooltip({
          x: e.clientX - rect.left,
          y: e.clientY - rect.top - 12,
          node,
          state,
        });
      }
    },
    [getState]
  );

  const handleMouseLeave = useCallback(() => setTooltip(null), []);

  return (
    <div
      ref={containerRef}
      className="relative rounded-xl border border-white/10 bg-[#0d1117] overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/10">
        <div className="flex items-center gap-2">
          <span className="text-sm">🗺️</span>
          <span className="text-xs font-semibold text-white/80 uppercase tracking-wider">
            Network Topology
          </span>
        </div>
        <div className="flex items-center gap-3">
          {(["healthy", "warning", "compromised"] as const).map((s) => (
            <div key={s} className="flex items-center gap-1">
              <span
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: STATUS_COLORS[s] }}
              />
              <span className="text-[9px] text-white/40 font-mono capitalize">
                {s}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* SVG Canvas */}
      <svg
        ref={svgRef}
        className="w-full"
        style={{ maxHeight: 430 }}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      />

      {/* Tooltip */}
      {tooltip && (
        <div
          className="absolute z-40 pointer-events-none px-3 py-2 rounded-lg border bg-[#0a0f0a]/95 backdrop-blur-sm text-xs max-w-[220px]"
          style={{
            left: tooltip.x,
            top: tooltip.y,
            transform: "translate(-50%, -100%)",
            borderColor: STATUS_COLORS[tooltip.state.status] + "40",
            boxShadow: `0 0 12px ${STATUS_GLOW[tooltip.state.status]}`,
          }}
        >
          <div className="flex items-center gap-2 mb-1">
            <span>{tooltip.node.icon}</span>
            <span className="font-semibold text-white/90">
              {tooltip.node.label}
            </span>
          </div>
          <div className="space-y-0.5 text-white/50 font-mono">
            <div>
              IP:{" "}
              <span className="text-white/70">
                {tooltip.state.ip ?? tooltip.node.ip}
              </span>
            </div>
            <div>
              Status:{" "}
              <span
                className="font-semibold uppercase"
                style={{ color: STATUS_COLORS[tooltip.state.status] }}
              >
                {tooltip.state.status}
              </span>
            </div>
            <div>
              Traffic:{" "}
              <span className="text-white/70">
                {tooltip.state.traffic.toFixed(0)} pps
              </span>
            </div>
          </div>
          {tooltip.state.alerts && tooltip.state.alerts.length > 0 && (
            <div className="mt-1.5 pt-1.5 border-t border-white/10">
              <div className="text-[9px] text-[#ff3131] uppercase mb-0.5">
                Active Alerts
              </div>
              {tooltip.state.alerts.slice(0, 3).map((a, i) => (
                <div key={i} className="text-white/60 truncate">
                  • {a}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Scanline overlay for cinematic effect */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.03]"
        style={{
          backgroundImage:
            "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,255,65,0.15) 2px, rgba(0,255,65,0.15) 4px)",
        }}
      />
    </div>
  );
}
