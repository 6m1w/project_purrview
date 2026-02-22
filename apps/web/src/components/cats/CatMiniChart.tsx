"use client";

import { Bar, BarChart, ResponsiveContainer, Tooltip } from "recharts";
import type { CatDailyMini } from "@/lib/queries";

interface CatMiniChartProps {
  data: CatDailyMini[];
  catColor: string;
}

export function CatMiniChart({ data, catColor }: CatMiniChartProps) {
  return (
    <div className="h-[80px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} barGap={1}>
          <Tooltip
            contentStyle={{
              fontFamily: "var(--font-space-mono)",
              fontWeight: "bold",
              fontSize: 12,
              border: "3px solid #000",
              borderRadius: 0,
              backgroundColor: "#f4f4f0",
              padding: "4px 8px",
            }}
            labelFormatter={(label) => String(label).slice(5)} // MM-DD
            formatter={(value, name) => [
              value ?? 0,
              name === "eating" ? "Eating" : "Drinking",
            ]}
          />
          <Bar
            dataKey="eating"
            stackId="a"
            fill={catColor}
            stroke="#000"
            strokeWidth={1}
          />
          <Bar
            dataKey="drinking"
            stackId="a"
            fill="#3b82f6"
            stroke="#000"
            strokeWidth={1}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
