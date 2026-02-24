import type { TimelineEvent } from "@/lib/queries";
import { CAT_HEADSHOTS } from "@/lib/queries";
// No date-fns needed — we use toLocaleString with Asia/Shanghai timezone
import { Utensils, Droplets, Eye } from "lucide-react";
import { CAT_COLORS } from "@/lib/catColors";
import Image from "next/image";

function getActivityIcon(activity: string) {
  switch (activity) {
    case "eating":
      return <Utensils className="h-3.5 w-3.5 text-black" />;
    case "drinking":
      return <Droplets className="h-3.5 w-3.5 text-black" />;
    default:
      return <Eye className="h-3.5 w-3.5 text-black" />;
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

function formatBeijingTime(date: Date): string {
  return date.toLocaleString("sv-SE", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function formatDuration(seconds: number): string {
  const rounded = Math.round(seconds);
  if (rounded < 60) return `${rounded}s`;
  const mins = Math.floor(rounded / 60);
  const secs = rounded % 60;
  return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`;
}

interface TimelineListProps {
  events: TimelineEvent[];
}

export function TimelineList({ events }: TimelineListProps) {
  if (events.length === 0) {
    return (
      <div className="border-4 border-black bg-white shadow-[8px_8px_0_0_rgba(0,0,0,1)]">
        <div className="p-12 text-center">
          <p className="font-space-mono text-sm font-bold uppercase text-black/50">
            No events found
          </p>
          <p className="font-space-mono text-xs text-black/40 mt-2 uppercase">
            Try adjusting your filters
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="border-4 border-black bg-white shadow-[8px_8px_0_0_rgba(0,0,0,1)]">
      <div className="divide-y-2 divide-black/10">
        {events.map((event) => {
          const color = CAT_COLORS[event.cat_name] ?? "#6b7280";
          const headshot = CAT_HEADSHOTS[event.cat_name];
          const lastChar = event.cat_name.charAt(event.cat_name.length - 1);
          const eventDate = new Date(event.started_at);

          return (
            <div
              key={event.id}
              className="flex items-center p-4 md:p-6 hover:bg-[#f4f4f0] transition-colors"
            >
              {/* Cat avatar with headshot */}
              <div
                className="h-10 w-10 border-[3px] overflow-hidden shrink-0"
                style={{ borderColor: color }}
              >
                {headshot ? (
                  <Image
                    src={headshot}
                    alt={event.cat_name}
                    width={40}
                    height={40}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <div
                    className="h-full w-full flex items-center justify-center"
                    style={{ backgroundColor: color }}
                  >
                    <span className="font-vt323 text-xl text-white drop-shadow-[1px_1px_0_rgba(0,0,0,0.5)]">
                      {lastChar}
                    </span>
                  </div>
                )}
              </div>

              {/* Event info */}
              <div className="ml-4 flex-1 min-w-0 space-y-1">
                <p className="text-sm font-space-mono font-bold leading-none flex items-center gap-2 uppercase">
                  <span className="font-[family-name:var(--font-noto-sc)]">
                    {event.cat_name}
                  </span>
                  <span className="text-black/70">
                    {getActivityLabel(event.activity)}
                  </span>
                  {getActivityIcon(event.activity)}
                </p>
                <p className="font-space-mono text-xs text-black/50 uppercase">
                  {formatBeijingTime(eventDate)}
                  {event.duration_seconds > 0 && (
                    <span className="ml-2 text-black/70">
                      ({formatDuration(event.duration_seconds)})
                    </span>
                  )}
                </p>
              </div>

              {/* Frame link */}
              {event.thumbnail_url && (
                <a
                  href={event.thumbnail_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="ml-4 shrink-0 font-space-mono text-[10px] font-bold uppercase border-2 border-black px-2 py-1 hover:bg-[#00FF66] transition-colors"
                >
                  VIEW
                </a>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
