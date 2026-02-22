import type { RecentEvent } from "@/lib/queries";
import { CAT_HEADSHOTS } from "@/lib/queries";
import { formatDistanceToNow } from "date-fns";
import { Utensils, Droplets, Eye } from "lucide-react";
import { CAT_COLORS } from "@/lib/catColors";
import Image from "next/image";

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
        <div className="lg:col-span-3 border-4 border-black bg-white shadow-[8px_8px_0_0_rgba(0,0,0,1)]">
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
                            const headshot = CAT_HEADSHOTS[event.cat_name];
                            const lastChar = event.cat_name.charAt(event.cat_name.length - 1);

                            return (
                                <div key={event.id} className="flex items-center group">
                                    {/* Headshot avatar with colored border */}
                                    <div
                                        className="h-12 w-12 border-[3px] overflow-hidden shrink-0"
                                        style={{ borderColor: color }}
                                    >
                                        {headshot ? (
                                            <Image
                                                src={headshot}
                                                alt={event.cat_name}
                                                width={48}
                                                height={48}
                                                className="h-full w-full object-cover"
                                            />
                                        ) : (
                                            <div
                                                className="h-full w-full flex items-center justify-center"
                                                style={{ backgroundColor: color }}
                                            >
                                                <span className="font-vt323 text-2xl text-white drop-shadow-[1px_1px_0_rgba(0,0,0,0.5)]">
                                                    {lastChar}
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                    <div className="ml-4 space-y-1 min-w-0">
                                        <p className="text-sm font-space-mono font-bold leading-none flex items-center gap-2 uppercase">
                                            <span className="font-[family-name:var(--font-noto-sc)]">{event.cat_name}</span>
                                            <span className="text-black/70">
                                                {getActivityLabel(event.activity)}
                                            </span>
                                            {getActivityIcon(event.activity)}
                                        </p>
                                        <p className="font-press-start text-[10px] leading-none text-black/50 uppercase">
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
