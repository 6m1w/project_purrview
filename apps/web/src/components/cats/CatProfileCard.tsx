import Image from "next/image";
import { formatDistanceToNow } from "date-fns";
import type { CatProfile } from "@/lib/queries";
import { CAT_BIOS } from "@/lib/queries";
import { CAT_COLORS } from "@/lib/catColors";
import { CatMiniChart } from "./CatMiniChart";

interface CatProfileCardProps {
  profile: CatProfile;
}

// Format seconds into "Xm Ys" display string
function formatDuration(seconds: number): string {
  if (seconds === 0) return "N/A";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  if (m === 0) return `${s}s`;
  return `${m}m ${s}s`;
}

export function CatProfileCard({ profile }: CatProfileCardProps) {
  const color = CAT_COLORS[profile.name] ?? "#6b7280";

  const lastSeenText = profile.lastSeen
    ? formatDistanceToNow(new Date(profile.lastSeen), { addSuffix: true })
    : "Never";

  return (
    <div className="border-4 border-black bg-white shadow-[8px_8px_0_0_rgba(0,0,0,1)] flex flex-col transition-transform hover:-translate-y-1 hover:shadow-[12px_12px_0_0_rgba(0,0,0,1)]">
      {/* Color band at top */}
      <div className="h-3 w-full" style={{ backgroundColor: color }} />

      {/* Card content */}
      <div className="p-6 flex flex-col items-center gap-4">
        {/* Cat headshot */}
        <div className="border-4 border-black overflow-hidden">
          <Image
            src={profile.headshot}
            alt={profile.name}
            width={120}
            height={120}
            className="object-cover w-[120px] h-[120px]"
          />
        </div>

        {/* Cat name + bio */}
        <h3 className="font-[family-name:var(--font-noto-sc)] text-2xl font-bold text-black">
          {profile.name}
        </h3>
        {CAT_BIOS[profile.name] && (
          <p className="font-space-mono text-xs text-black/60 text-center leading-relaxed -mt-2">
            {CAT_BIOS[profile.name]}
          </p>
        )}

        {/* Stats 2x2 grid */}
        <div className="grid grid-cols-2 gap-4 w-full">
          <div className="flex flex-col items-center gap-1 p-2 border-2 border-black/20">
            <span className="font-space-mono text-[10px] font-bold uppercase text-black/60">
              Feedings
            </span>
            <span className="font-vt323 text-3xl text-black leading-none">
              {profile.totalEating}
            </span>
          </div>

          <div className="flex flex-col items-center gap-1 p-2 border-2 border-black/20">
            <span className="font-space-mono text-[10px] font-bold uppercase text-black/60">
              Drinkings
            </span>
            <span className="font-vt323 text-3xl text-black leading-none">
              {profile.totalDrinking}
            </span>
          </div>

          <div className="flex flex-col items-center gap-1 p-2 border-2 border-black/20">
            <span className="font-space-mono text-[10px] font-bold uppercase text-black/60">
              Avg Duration
            </span>
            <span className="font-vt323 text-3xl text-black leading-none">
              {formatDuration(profile.avgDuration)}
            </span>
          </div>

          <div className="flex flex-col items-center gap-1 p-2 border-2 border-black/20">
            <span className="font-space-mono text-[10px] font-bold uppercase text-black/60">
              Last Seen
            </span>
            <span className="font-vt323 text-xl text-black leading-none">
              {lastSeenText}
            </span>
          </div>
        </div>

        {/* Mini trend chart */}
        <div className="w-full border-t-2 border-black/20 pt-3">
          <p className="font-space-mono text-[10px] font-bold uppercase text-black/40 mb-1">
            7-day trend
          </p>
          <CatMiniChart data={profile.trend} catColor={color} />
        </div>
      </div>
    </div>
  );
}
