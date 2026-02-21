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

interface FeedingChartProps {
    data: { date: string; eating: number; drinking: number }[];
}

export function FeedingChart({ data }: FeedingChartProps) {
    // Format date labels as MM/DD
    const chartData = data.map((d) => ({
        ...d,
        label: d.date.slice(5), // "YYYY-MM-DD" -> "MM-DD"
    }));

    return (
        <div className="col-span-7 border-4 border-black bg-white shadow-[8px_8px_0_0_rgba(0,0,0,1)] flex flex-col">
            <div className="p-6 border-b-4 border-black bg-[#f4f4f0]">
                <h3 className="font-vt323 text-4xl uppercase tracking-widest text-black">
                    Weekly Activity
                </h3>
                <p className="font-space-mono text-sm font-bold uppercase text-black/70">
                    Eating &amp; drinking events per day (last 7 days).
                </p>
            </div>
            <div className="p-6 pl-2 flex-grow bg-white">
                <ResponsiveContainer width="100%" height={350}>
                    <BarChart data={chartData}>
                        <XAxis
                            dataKey="label"
                            stroke="#000"
                            fontSize={12}
                            tickLine={false}
                            axisLine={true}
                            style={{
                                fontFamily: "var(--font-space-mono)",
                                fontWeight: "bold",
                            }}
                        />
                        <YAxis
                            stroke="#000"
                            fontSize={12}
                            tickLine={false}
                            axisLine={true}
                            allowDecimals={false}
                            style={{
                                fontFamily: "var(--font-space-mono)",
                                fontWeight: "bold",
                            }}
                        />
                        <Tooltip
                            contentStyle={{
                                fontFamily: "var(--font-space-mono)",
                                fontWeight: "bold",
                                border: "3px solid #000",
                                borderRadius: 0,
                                backgroundColor: "#f4f4f0",
                            }}
                        />
                        <Legend
                            wrapperStyle={{
                                fontFamily: "var(--font-space-mono)",
                                fontWeight: "bold",
                                fontSize: 12,
                                textTransform: "uppercase",
                            }}
                        />
                        <Bar
                            dataKey="eating"
                            name="Eating"
                            stackId="a"
                            fill="#FF5722"
                            stroke="#000"
                            strokeWidth={2}
                        />
                        <Bar
                            dataKey="drinking"
                            name="Drinking"
                            stackId="a"
                            fill="#3b82f6"
                            stroke="#000"
                            strokeWidth={2}
                        />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
