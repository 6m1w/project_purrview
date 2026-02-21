import { getTodayStats, getWeeklyTrendByCat, getRecentEvents, getCatStatuses } from "@/lib/queries";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { RecentActivity } from "@/components/dashboard/RecentActivity";
import { FeedingChart } from "@/components/dashboard/FeedingChart";
import { CatStatusGrid } from "@/components/dashboard/CatStatusGrid";
import { Utensils, Cat, Droplets, Clock } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

export const dynamic = "force-dynamic";

export default async function Dashboard() {
    const [stats, trendByCat, events, catStatuses] = await Promise.all([
        getTodayStats(),
        getWeeklyTrendByCat(),
        getRecentEvents(),
        getCatStatuses(),
    ]);

    // Format "last signal" as relative time
    const lastSignal = stats.lastEventTime
        ? formatDistanceToNow(new Date(stats.lastEventTime), { addSuffix: true })
        : "No data";

    return (
        <div className="flex flex-col space-y-8 p-4 pt-6 max-w-[1600px] mx-auto">
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
        </div>
    );
}
