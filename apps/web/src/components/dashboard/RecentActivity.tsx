import type { RecentEvent } from "@/lib/queries";
import { formatDistanceToNow } from "date-fns";
import { Utensils, Droplets, Eye } from "lucide-react";

// Cat color mapping
const CAT_COLORS: Record<string, string> = {
    "\u5927\u5409": "#f59e0b", // 大吉
    "\u5c0f\u6162": "#3b82f6", // 小慢
    "\u9ebb\u9171": "#d97706", // 麻酱
    "\u677e\u82b1": "#22c55e", // 松花
    "\u5c0f\u9ed1": "#8b5cf6", // 小黑
};

function getActivityIcon(activity: string) {
    switch (activity) {
        case "eating":
            return <Utensils className="h-3 w-3 text-black" />;
        case "drinking":
            return <Droplets className="h-3 w-3 text-black" />;
        default:
            return <Eye className="h-3 w-3 text-black" />;
    }
}

function getActivityLabel(activity: string) {
    switch (activity) {
        case "eating":
            return "ate";
        case "drinking":
            return "drank";
        default:
            return "seen";
    }
}

interface RecentActivityProps {
    events: RecentEvent[];
}

export function RecentActivity({ events }: RecentActivityProps) {
    return (
        <div className="col-span-3 border-4 border-black bg-white shadow-[8px_8px_0_0_rgba(0,0,0,1)]">
            <div className="p-6 border-b-4 border-black bg-[#f4f4f0]">
                <h3 className="font-press-start text-xl font-bold uppercase text-black">
                    Activity Log
                </h3>
            </div>
            <div className="p-6">
                {events.length === 0 ? (
                    <p className="font-space-mono text-sm font-bold uppercase text-black/50 text-center py-8">
                        No events recorded yet
                    </p>
                ) : (
                    <div className="space-y-6">
                        {events.map((event) => {
                            const color = CAT_COLORS[event.cat_name] ?? "#6b7280";
                            const lastChar = event.cat_name.charAt(event.cat_name.length - 1);

                            return (
                                <div key={event.id} className="flex items-center group">
                                    {/* Colored square avatar with first char */}
                                    <div
                                        className="h-12 w-12 border-2 border-black flex items-center justify-center shrink-0"
                                        style={{ backgroundColor: color }}
                                    >
                                        <span className="font-vt323 text-2xl text-white drop-shadow-[1px_1px_0_rgba(0,0,0,0.5)]">
                                            {lastChar}
                                        </span>
                                    </div>
                                    <div className="ml-4 space-y-1 min-w-0">
                                        <p className="text-sm font-space-mono font-bold leading-none flex items-center gap-2 uppercase">
                                            {event.cat_name}
                                            <span className="text-black/70">
                                                {getActivityLabel(event.activity)}
                                            </span>
                                            {getActivityIcon(event.activity)}
                                        </p>
                                        <p className="font-vt323 text-xl leading-none text-black/70 uppercase tracking-wider">
                                            {formatDistanceToNow(new Date(event.started_at), {
                                                addSuffix: true,
                                            })}
                                        </p>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}
