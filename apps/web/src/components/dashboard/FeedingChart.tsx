"use client"

import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { MOCK_CATS, MOCK_FEEDING_EVENTS } from "@/lib/mock"

export function FeedingChart() {
    // Aggregate data for the chart (mock logic for now)
    // In a real app, this would process the actual events
    const data = [
        {
            name: "Mon",
            total: Math.floor(Math.random() * 200) + 100,
        },
        {
            name: "Tue",
            total: Math.floor(Math.random() * 200) + 100,
        },
        {
            name: "Wed",
            total: Math.floor(Math.random() * 200) + 100,
        },
        {
            name: "Thu",
            total: Math.floor(Math.random() * 200) + 100,
        },
        {
            name: "Fri",
            total: Math.floor(Math.random() * 200) + 100,
        },
        {
            name: "Sat",
            total: Math.floor(Math.random() * 200) + 100,
        },
        {
            name: "Sun",
            total: Math.floor(Math.random() * 200) + 100,
        },
    ]

    return (
        <Card className="col-span-4">
            <CardHeader>
                <CardTitle>Food Consumption</CardTitle>
                <CardDescription>
                    Total food intake per day (grams).
                </CardDescription>
            </CardHeader>
            <CardContent className="pl-2">
                <ResponsiveContainer width="100%" height={350}>
                    <BarChart data={data}>
                        <XAxis
                            dataKey="name"
                            stroke="#888888"
                            fontSize={12}
                            tickLine={false}
                            axisLine={false}
                        />
                        <YAxis
                            stroke="#888888"
                            fontSize={12}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={(value) => `${value}g`}
                        />
                        <Bar
                            dataKey="total"
                            fill="currentColor"
                            radius={[4, 4, 0, 0]}
                            className="fill-primary"
                        />
                    </BarChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    )
}
