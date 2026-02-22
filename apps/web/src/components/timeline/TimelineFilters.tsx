"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { CAT_NAMES, CAT_COLORS } from "@/lib/catColors";

const ACTIVITIES = ["all", "eating", "drinking"] as const;

export function TimelineFilters() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const activeCat = searchParams.get("cat") ?? "all";
  const activeActivity = searchParams.get("activity") ?? "all";

  function applyFilter(key: string, value: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (value === "all") {
      params.delete(key);
    } else {
      params.set(key, value);
    }
    // Reset to page 1 when filters change
    params.delete("page");
    router.push(`/timeline?${params.toString()}`);
  }

  return (
    <div className="border-4 border-black bg-white shadow-[8px_8px_0_0_rgba(0,0,0,1)]">
      <div className="p-4 md:p-6 space-y-4">
        {/* Cat filter */}
        <div>
          <p className="font-space-mono text-xs font-bold uppercase text-black/60 mb-2">
            Filter by cat
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => applyFilter("cat", "all")}
              className={`border-2 border-black px-4 py-2 font-space-mono text-sm font-bold uppercase transition-colors ${
                activeCat === "all"
                  ? "bg-[#00FF66]"
                  : "bg-white hover:bg-gray-100"
              }`}
            >
              All
            </button>
            {CAT_NAMES.map((cat) => {
              const isActive = activeCat === cat;
              const color = CAT_COLORS[cat] ?? "#6b7280";
              return (
                <button
                  key={cat}
                  onClick={() => applyFilter("cat", cat)}
                  className={`border-2 border-black px-4 py-2 font-[family-name:var(--font-noto-sc)] text-sm font-bold transition-colors ${
                    isActive
                      ? "bg-[#00FF66]"
                      : "bg-white hover:bg-gray-100"
                  }`}
                  style={{ borderBottomColor: color, borderBottomWidth: 4 }}
                >
                  {cat}
                </button>
              );
            })}
          </div>
        </div>

        {/* Activity filter */}
        <div>
          <p className="font-space-mono text-xs font-bold uppercase text-black/60 mb-2">
            Filter by activity
          </p>
          <div className="flex flex-wrap gap-2">
            {ACTIVITIES.map((activity) => (
              <button
                key={activity}
                onClick={() => applyFilter("activity", activity)}
                className={`border-2 border-black px-4 py-2 font-space-mono text-sm font-bold uppercase transition-colors ${
                  activeActivity === activity
                    ? "bg-[#00FF66]"
                    : "bg-white hover:bg-gray-100"
                }`}
              >
                {activity}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
