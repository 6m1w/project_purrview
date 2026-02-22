"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { MonthlyTrend } from "@/lib/queries";

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

interface MonthlyTrendChartProps {
  data: MonthlyTrend[];
}

export function MonthlyTrendChart({ data }: MonthlyTrendChartProps) {
  return (
    <div className="border-4 border-black bg-white shadow-[8px_8px_0_0_rgba(0,0,0,1)] flex flex-col">
      <div className="p-6 border-b-4 border-black bg-[#f4f4f0]">
        <h3 className="font-press-start text-lg font-bold uppercase text-black">
          30-Day Trend
        </h3>
        <p className="font-space-mono text-sm font-bold uppercase text-black/70">
          Daily eating & drinking events
        </p>
      </div>
      <div className="p-6 pl-2 flex-1 min-h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <XAxis
              dataKey="label"
              stroke="#000"
              fontSize={12}
              tickLine={false}
              axisLine={true}
              style={AXIS_STYLE}
              interval={4}
            />
            <YAxis
              stroke="#000"
              fontSize={12}
              tickLine={false}
              axisLine={true}
              allowDecimals={false}
              style={AXIS_STYLE}
            />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Legend
              wrapperStyle={{
                fontFamily: "var(--font-space-mono)",
                fontWeight: "bold",
                fontSize: 14,
              }}
            />
            <Line
              type="monotone"
              dataKey="eating"
              name="Eating"
              stroke="#f59e0b"
              strokeWidth={3}
              dot={{ fill: "#f59e0b", stroke: "#000", strokeWidth: 2, r: 4 }}
              activeDot={{ fill: "#f59e0b", stroke: "#000", strokeWidth: 2, r: 6 }}
            />
            <Line
              type="monotone"
              dataKey="drinking"
              name="Drinking"
              stroke="#3b82f6"
              strokeWidth={3}
              dot={{ fill: "#3b82f6", stroke: "#000", strokeWidth: 2, r: 4 }}
              activeDot={{ fill: "#3b82f6", stroke: "#000", strokeWidth: 2, r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
