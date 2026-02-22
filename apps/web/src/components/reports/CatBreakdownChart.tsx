"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { CatEventCount } from "@/lib/queries";

const AXIS_STYLE = {
  fontFamily: "var(--font-space-mono)",
  fontWeight: "bold" as const,
};

const TOOLTIP_STYLE = {
  border: "3px solid #000",
  borderRadius: 0,
  backgroundColor: "#f4f4f0",
  fontFamily: "var(--font-noto-sc), var(--font-space-mono)",
  fontWeight: "bold",
};

interface CatBreakdownChartProps {
  data: CatEventCount[];
}

export function CatBreakdownChart({ data }: CatBreakdownChartProps) {
  return (
    <div className="border-4 border-black bg-white shadow-[8px_8px_0_0_rgba(0,0,0,1)] flex flex-col">
      <div className="p-6 border-b-4 border-black bg-[#f4f4f0]">
        <h3 className="font-press-start text-lg font-bold uppercase text-black">
          Cat Breakdown
        </h3>
        <p className="font-space-mono text-sm font-bold uppercase text-black/70">
          Total events per cat (all time)
        </p>
      </div>
      <div className="p-6 pl-2 flex-1 min-h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical">
            <XAxis
              type="number"
              stroke="#000"
              fontSize={12}
              tickLine={false}
              axisLine={true}
              allowDecimals={false}
              style={AXIS_STYLE}
            />
            <YAxis
              type="category"
              dataKey="name"
              stroke="#000"
              fontSize={14}
              tickLine={false}
              axisLine={true}
              width={60}
              style={{
                fontFamily: "var(--font-noto-sc)",
                fontWeight: "bold",
              }}
            />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Legend
              wrapperStyle={{
                fontFamily: "var(--font-space-mono)",
                fontWeight: "bold",
                fontSize: 14,
              }}
            />
            <Bar
              dataKey="eating"
              name="Eating"
              fill="#f59e0b"
              stroke="#000"
              strokeWidth={1.5}
            />
            <Bar
              dataKey="drinking"
              name="Drinking"
              fill="#3b82f6"
              stroke="#000"
              strokeWidth={1.5}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
