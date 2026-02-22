"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { CatAvgDuration } from "@/lib/queries";
import { CAT_COLORS } from "@/lib/catColors";

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

// Format seconds as "Xm Ys"
function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  if (m === 0) return `${s}s`;
  return `${m}m ${s}s`;
}

interface DurationChartProps {
  data: CatAvgDuration[];
}

export function DurationChart({ data }: DurationChartProps) {
  return (
    <div className="border-4 border-black bg-white shadow-[8px_8px_0_0_rgba(0,0,0,1)] flex flex-col">
      <div className="p-6 border-b-4 border-black bg-[#f4f4f0]">
        <h3 className="font-press-start text-lg font-bold uppercase text-black">
          Avg Duration
        </h3>
        <p className="font-space-mono text-sm font-bold uppercase text-black/70">
          Average feeding duration per cat
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
              style={AXIS_STYLE}
              tickFormatter={formatDuration}
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
            <Tooltip
              contentStyle={TOOLTIP_STYLE}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              formatter={(value: any) => [formatDuration(Number(value ?? 0)), "Avg Duration"]}
            />
            <Bar
              dataKey="avg_seconds"
              name="Avg Duration"
              stroke="#000"
              strokeWidth={1.5}
            >
              {data.map((entry) => (
                <Cell
                  key={entry.name}
                  fill={CAT_COLORS[entry.name] ?? "#888"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
