import type { CatStatus } from "@/lib/queries";
import { CAT_HEADSHOTS } from "@/lib/queries";
import { formatDistanceToNow } from "date-fns";
import { Utensils, Droplets, Eye } from "lucide-react";
import { CAT_COLORS } from "@/lib/catColors";
import Image from "next/image";

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
                    const headshot = CAT_HEADSHOTS[cat.name];
                    const lastChar = cat.name.charAt(cat.name.length - 1);
                    const hasActivity = cat.lastTime !== "";

                    return (
                        <div
                            key={cat.name}
                            className="border-4 border-black bg-white shadow-[8px_8px_0_0_rgba(0,0,0,1)] p-4 flex flex-col items-center gap-3 transition-transform hover:-translate-y-1 hover:shadow-[12px_12px_0_0_rgba(0,0,0,1)]"
                        >
                            {/* Headshot with colored border + letter badge */}
                            <div className="relative">
                                <div
                                    className="h-16 w-16 border-[3px] overflow-hidden"
                                    style={{ borderColor: color }}
                                >
                                    {headshot ? (
                                        <Image
                                            src={headshot}
                                            alt={cat.name}
                                            width={64}
                                            height={64}
                                            className="h-full w-full object-cover"
                                        />
                                    ) : (
                                        <div
                                            className="h-full w-full flex items-center justify-center"
                                            style={{ backgroundColor: color }}
                                        >
                                            <span className="font-vt323 text-4xl text-white drop-shadow-[2px_2px_0_rgba(0,0,0,0.5)]">
                                                {lastChar}
                                            </span>
                                        </div>
                                    )}
                                </div>
                                {/* Colored letter badge */}
                                <div
                                    className="absolute -bottom-1 -right-1 h-6 w-6 border-2 border-black flex items-center justify-center"
                                    style={{ backgroundColor: color }}
                                >
                                    <span className="font-vt323 text-sm text-white drop-shadow-[1px_1px_0_rgba(0,0,0,0.5)]">
                                        {lastChar}
                                    </span>
                                </div>
                            </div>

                            {/* Cat name */}
                            <p className="font-[family-name:var(--font-noto-sc)] text-lg font-bold text-black">
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
                            <p className="font-press-start text-[10px] text-black/50 uppercase">
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
