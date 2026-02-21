import type { CatStatus } from "@/lib/queries";
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
            return <Utensils className="h-4 w-4" />;
        case "drinking":
            return <Droplets className="h-4 w-4" />;
        default:
            return <Eye className="h-4 w-4" />;
    }
}

function getActivityLabel(activity: string) {
    switch (activity) {
        case "eating":
            return "Eating";
        case "drinking":
            return "Drinking";
        case "none":
            return "No activity";
        default:
            return "Present";
    }
}

interface CatStatusGridProps {
    statuses: CatStatus[];
}

export function CatStatusGrid({ statuses }: CatStatusGridProps) {
    return (
        <div>
            <h3 className="font-press-start text-xl font-bold uppercase text-black mb-4 border-b-4 border-black pb-3">
                Cat Status
            </h3>
            <div className="grid gap-6 grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
                {statuses.map((cat) => {
                    const color = CAT_COLORS[cat.name] ?? "#6b7280";
                    const lastChar = cat.name.charAt(cat.name.length - 1);
                    const hasActivity = cat.lastTime !== "";

                    return (
                        <div
                            key={cat.name}
                            className="border-4 border-black bg-white shadow-[8px_8px_0_0_rgba(0,0,0,1)] p-4 flex flex-col items-center gap-3 transition-transform hover:-translate-y-1 hover:shadow-[12px_12px_0_0_rgba(0,0,0,1)]"
                        >
                            {/* Colored square avatar */}
                            <div
                                className="h-16 w-16 border-2 border-black flex items-center justify-center"
                                style={{ backgroundColor: color }}
                            >
                                <span className="font-vt323 text-4xl text-white drop-shadow-[2px_2px_0_rgba(0,0,0,0.5)]">
                                    {lastChar}
                                </span>
                            </div>

                            {/* Cat name */}
                            <p className="font-vt323 text-3xl uppercase tracking-widest text-black">
                                {cat.name}
                            </p>

                            {/* Last activity */}
                            <div className="flex items-center gap-2 text-black/70">
                                {getActivityIcon(cat.lastActivity)}
                                <span className="font-space-mono text-xs font-bold uppercase">
                                    {getActivityLabel(cat.lastActivity)}
                                </span>
                            </div>

                            {/* Relative time */}
                            <p className="font-space-mono text-xs font-bold text-black/50 uppercase">
                                {hasActivity
                                    ? formatDistanceToNow(new Date(cat.lastTime), {
                                          addSuffix: true,
                                      })
                                    : "Never seen"}
                            </p>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
