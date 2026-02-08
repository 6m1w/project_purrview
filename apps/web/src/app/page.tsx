import { MOCK_STATS, MOCK_FEEDING_EVENTS } from "@/lib/mock";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { RecentActivity } from "@/components/dashboard/RecentActivity";
import { FeedingChart } from "@/components/dashboard/FeedingChart";
import { Activity, Utensils, Cat, Droplets, Clock } from "lucide-react";

export default function Home() {
  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Today's Feedings"
          value={MOCK_STATS.todayCount}
          description="Total feeding events"
          icon={<Utensils className="h-4 w-4 text-muted-foreground" />}
          trend="up"
          trendValue="+12%"
        />
        <MetricCard
          title="Active Cats"
          value={MOCK_STATS.activeCats}
          description="Cats fed today"
          icon={<Cat className="h-4 w-4 text-muted-foreground" />}
        />
        <MetricCard
          title="Water Intake"
          value="450ml"
          description="Total water consumed today"
          icon={<Droplets className="h-4 w-4 text-muted-foreground" />}
          trend="up"
          trendValue="+5%"
        />
        <MetricCard
          title="Last Fed"
          value={MOCK_STATS.lastFed}
          description="Time since last activity"
          icon={<Clock className="h-4 w-4 text-muted-foreground" />}
        />
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <FeedingChart />
        <RecentActivity events={MOCK_FEEDING_EVENTS} />
      </div>
    </div>
  );
}
