import type { Metadata } from "next";
import { Suspense } from "react";

export const metadata: Metadata = {
  title: "Timeline",
  description: "Browse every feeding and drinking event with filters by cat and activity type.",
};
import { getTimelineEvents } from "@/lib/queries";
import { TimelineFilters } from "@/components/timeline/TimelineFilters";
import { TimelineList } from "@/components/timeline/TimelineList";
import { TimelinePagination } from "@/components/timeline/TimelinePagination";

export const dynamic = "force-dynamic";

interface TimelinePageProps {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export default async function TimelinePage({ searchParams }: TimelinePageProps) {
  const params = await searchParams;

  // Parse filter params
  const cat = typeof params.cat === "string" ? params.cat : undefined;
  const activity = typeof params.activity === "string" ? params.activity : undefined;
  const page = typeof params.page === "string" ? Math.max(1, parseInt(params.page, 10) || 1) : 1;

  // Fetch paginated timeline data
  const timeline = await getTimelineEvents({ cat, activity }, page);

  // Build a flat searchParams record for pagination links
  const currentParams: Record<string, string> = {};
  if (cat) currentParams.cat = cat;
  if (activity) currentParams.activity = activity;

  return (
    <div className="flex flex-col space-y-6 p-4 pt-6 pb-20 md:pb-4 max-w-[1600px] mx-auto">
      {/* Page header */}
      <div className="flex items-center justify-between border-b-4 border-black pb-2">
        <h2 className="font-press-start text-2xl md:text-3xl font-bold uppercase">
          Timeline
        </h2>
        <div className="font-press-start text-sm font-bold bg-black text-[#00FF66] px-3 py-1.5 border-2 border-black">
          {timeline.total} EVENTS
        </div>
      </div>

      {/* Filters (client component needs Suspense for useSearchParams) */}
      <Suspense fallback={null}>
        <TimelineFilters />
      </Suspense>

      {/* Event list */}
      <TimelineList events={timeline.events} />

      {/* Pagination */}
      <TimelinePagination
        page={timeline.page}
        totalPages={timeline.totalPages}
        searchParams={currentParams}
      />
    </div>
  );
}
