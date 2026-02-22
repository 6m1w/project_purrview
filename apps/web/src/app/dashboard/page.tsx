import type { Metadata } from "next";
import {
    getTodayStats,
    getWeeklyTrendByCat,
    getRecentEvents,
    getCatStatuses,
    getMonthlyTrend,
    getCatEventCounts,
    getHourlyDistribution,
    getCatAvgDurations,
} from "@/lib/queries";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { RecentActivity } from "@/components/dashboard/RecentActivity";
import { FeedingChart } from "@/components/dashboard/FeedingChart";
import { CatStatusGrid } from "@/components/dashboard/CatStatusGrid";
import { MonthlyTrendChart } from "@/components/reports/MonthlyTrendChart";
import { CatBreakdownChart } from "@/components/reports/CatBreakdownChart";
import { HourlyChart } from "@/components/reports/HourlyChart";
import { DurationChart } from "@/components/reports/DurationChart";
import { Utensils, Cat, Droplets, Clock } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

export const metadata: Metadata = {
    title: "Dashboard",
    description: "Real-time feeding stats, weekly trends, and analytics for 5 rescue cats monitored by AI.",
};

export const dynamic = "force-dynamic";

export default async function Dashboard() {
    const [stats, trendByCat, events, catStatuses, monthlyTrend, catCounts, hourly, durations] =
        await Promise.all([
            getTodayStats(),
            getWeeklyTrendByCat(),
            getRecentEvents(),
            getCatStatuses(),
            getMonthlyTrend(),
            getCatEventCounts(),
            getHourlyDistribution(),
            getCatAvgDurations(),
        ]);

    // Format "last signal" as relative time
    const lastSignal = stats.lastEventTime
        ? formatDistanceToNow(new Date(stats.lastEventTime), { addSuffix: true })
        : "No data";

    return (
        <div className="flex flex-col space-y-8 p-4 pt-6 pb-20 md:pb-4 max-w-[1600px] mx-auto">
            {/* Command Center section */}
            <section id="dashboard" className="flex flex-col space-y-4">
                <div className="flex items-center justify-between border-b-4 border-black pb-2">
                    <h2 className="font-press-start text-2xl md:text-3xl font-bold uppercase">Command Center</h2>
                    <div className="font-press-start text-sm font-bold bg-black text-[#00FF66] px-3 py-1.5 border-2 border-black">
                        SYS.ONLINE
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-3 md:gap-6 lg:grid-cols-4">
                    <MetricCard
                        title="FEEDINGS"
                        value={stats.feedingCount}
                        description="Eating events today"
                        icon={<Utensils className="h-6 w-6" />}
                    />
                    <MetricCard
                        title="ACTIVE CATS"
                        value={stats.activeCats}
                        description="Cats detected today"
                        icon={<Cat className="h-6 w-6" />}
                    />
                    <MetricCard
                        title="WATER EVENTS"
                        value={stats.drinkingCount}
                        description="Drinking events today"
                        icon={<Droplets className="h-6 w-6" />}
                    />
                    <MetricCard
                        title="LAST SIGNAL"
                        value={lastSignal}
                        description="Time since last relay"
                        icon={<Clock className="h-6 w-6" />}
                    />
                </div>

                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-10">
                    <FeedingChart eating={trendByCat.eating} drinking={trendByCat.drinking} />
                    <RecentActivity events={events} />
                </div>

                <CatStatusGrid statuses={catStatuses} />
            </section>

            {/* Analytics section (merged from Reports) */}
            <section id="analytics" className="flex flex-col space-y-4">
                <div className="flex items-center justify-between border-b-4 border-black pb-2">
                    <h2 className="font-press-start text-2xl md:text-3xl font-bold uppercase">Analytics</h2>
                    <div className="font-press-start text-sm font-bold bg-black text-[#00FF66] px-3 py-1.5 border-2 border-black">
                        30-DAY
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <MonthlyTrendChart data={monthlyTrend} />
                    <CatBreakdownChart data={catCounts} />
                    <HourlyChart data={hourly} />
                    <DurationChart data={durations} />
                </div>
            </section>
        </div>
    );
}
