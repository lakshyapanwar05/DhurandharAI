import { useEffect, useRef } from "react";
import React from "react";
import * as d3 from "d3";
import type { HardwareDomain } from "../types";
import DomainCard from "./DomainCard";

interface Props {
  data: HardwareDomain;
  history: number[];
}

function Gauge({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  const pct = Math.min(value, 100);
  return (
    <div className="flex-1 text-center">
      <div className="relative w-16 h-16 mx-auto">
        <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
          <circle
            cx="18"
            cy="18"
            r="15.5"
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth="3"
          />
          <circle
            cx="18"
            cy="18"
            r="15.5"
            fill="none"
            stroke={color}
            strokeWidth="3"
            strokeDasharray={`${pct} ${100 - pct}`}
            strokeLinecap="round"
            className="transition-all duration-700"
          />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center text-xs font-mono text-white/80">
          {value.toFixed(0)}%
        </span>
      </div>
      <div className="text-[10px] text-white/40 mt-1 uppercase">{label}</div>
    </div>
  );
}

const HardwareMetrics = function({ data, history }: Props) {
  const chartRef = useRef<SVGSVGElement>(null);

  const cpuColor =
    data.cpu_percent > 85 ? "#ff3131" : data.cpu_percent > 60 ? "#f59e0b" : "#00ff41";
  const memColor =
    data.memory_percent > 80
      ? "#ff3131"
      : data.memory_percent > 55
      ? "#f59e0b"
      : "#00ff41";

  useEffect(() => {
    if (!chartRef.current || history.length < 2) return;
    const svg = d3.select(chartRef.current);
    svg.selectAll("*").remove();

    const w = 220;
    const h = 48;
    svg.attr("width", w).attr("height", h);

    const x = d3
      .scaleLinear()
      .domain([0, history.length - 1])
      .range([0, w]);
    const y = d3.scaleLinear().domain([0, 100]).range([h, 0]);

    const area = d3
      .area<number>()
      .x((_d, i) => x(i))
      .y0(h)
      .y1((d) => y(d))
      .curve(d3.curveBasis);

    const line = d3
      .line<number>()
      .x((_d, i) => x(i))
      .y((d) => y(d))
      .curve(d3.curveBasis);

    svg
      .append("path")
      .datum(history)
      .attr("d", area)
      .attr("fill", "rgba(0,255,65,0.08)");

    svg
      .append("path")
      .datum(history)
      .attr("d", line)
      .attr("fill", "none")
      .attr("stroke", "#00ff41")
      .attr("stroke-width", 1.5);
  }, [history]);

  return (
    <DomainCard title="Hardware Metrics" icon="🖥️" anomaly={data.anomaly}>
      <div className="space-y-4">
        <div className="flex gap-2 justify-center">
          <Gauge label="CPU" value={data.cpu_percent} color={cpuColor} />
          <Gauge label="Memory" value={data.memory_percent} color={memColor} />
        </div>
        <div>
          <div className="text-[10px] text-white/40 uppercase mb-1">CPU History</div>
          <svg ref={chartRef} className="w-full" />
        </div>
      </div>
    </DomainCard>
  );
};

export default React.memo(HardwareMetrics);
