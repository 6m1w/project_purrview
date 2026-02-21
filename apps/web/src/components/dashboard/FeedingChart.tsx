"use client";

import {
    Bar,
    BarChart,
    ResponsiveContainer,
    XAxis,
    YAxis,
    Tooltip,
    Legend,
} from "recharts";
import type { DailyCatCount } from "@/lib/queries";
import { CAT_NAMES, CAT_COLORS } from "@/lib/catColors";

interface FeedingChartProps {
    eating: DailyCatCount[];
    drinking: DailyCatCount[];
}

const AXIS_STYLE = {
    fontFamily: "var(--font-space-mono)",
    fontWeight: "bold" as const,
};

function CatBarChart({
    data,
    title,
}: {
    data: DailyCatCount[];
    title: string;
}) {
    return (
        <div className="flex-1 min-h-[200px] flex flex-col">
            <p className="font-space-mono text-xs font-bold uppercase text-black/60 mb-2 pl-2">
                {title}
            </p>
            <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data}>
                    <XAxis
                        dataKey="label"
                        stroke="#000"
                        fontSize={12}
                        tickLine={false}
                        axisLine={true}
                        style={AXIS_STYLE}
                    />
                    <YAxis
                        stroke="#000"
                        fontSize={12}
                        tickLine={false}
                        axisLine={true}
                        allowDecimals={false}
                        style={AXIS_STYLE}
                    />
                    <Tooltip
                        contentStyle={{
                            fontFamily: "var(--font-noto-sc), var(--font-space-mono)",
                            fontWeight: "bold",
                            border: "3px solid #000",
                            borderRadius: 0,
                            backgroundColor: "#f4f4f0",
                        }}
                    />
                    <Legend
                        wrapperStyle={{
                            fontFamily: "var(--font-noto-sc), var(--font-space-mono)",
                            fontWeight: "bold",
                            fontSize: 14,
                        }}
                    />
                    {CAT_NAMES.map((cat) => (
                        <Bar
                            key={cat}
                            dataKey={cat}
                            stackId="a"
                            fill={CAT_COLORS[cat]}
                            stroke="#000"
                            strokeWidth={1.5}
                        />
                    ))}
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}

export function FeedingChart({ eating, drinking }: FeedingChartProps) {
    return (
        <div className="lg:col-span-7 border-4 border-black bg-white shadow-[8px_8px_0_0_rgba(0,0,0,1)] flex flex-col">
            <div className="p-6 border-b-4 border-black bg-[#f4f4f0]">
                <h3 className="font-press-start text-xl font-bold uppercase text-black">
                    Weekly Activity
                </h3>
                <p className="font-space-mono text-sm font-bold uppercase text-black/70">
                    Events per day by cat (last 7 days).
                </p>
            </div>
            <div className="p-6 pl-2 flex-1 min-h-0 bg-white flex flex-col gap-4">
                <CatBarChart data={eating} title="Eating" />
                <CatBarChart data={drinking} title="Drinking" />
            </div>
        </div>
    );
}
