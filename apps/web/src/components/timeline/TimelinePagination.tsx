import Link from "next/link";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface TimelinePaginationProps {
  page: number;
  totalPages: number;
  searchParams: Record<string, string>;
}

function buildPageUrl(page: number, searchParams: Record<string, string>): string {
  const params = new URLSearchParams(searchParams);
  if (page <= 1) {
    params.delete("page");
  } else {
    params.set("page", String(page));
  }
  const qs = params.toString();
  return `/timeline${qs ? `?${qs}` : ""}`;
}

export function TimelinePagination({
  page,
  totalPages,
  searchParams,
}: TimelinePaginationProps) {
  if (totalPages <= 1) return null;

  const hasPrev = page > 1;
  const hasNext = page < totalPages;

  // Build searchParams without the "page" key for building URLs
  const filterParams: Record<string, string> = {};
  for (const [key, value] of Object.entries(searchParams)) {
    if (key !== "page") {
      filterParams[key] = value;
    }
  }

  return (
    <div className="flex items-center justify-center gap-4">
      {hasPrev ? (
        <Link
          href={buildPageUrl(page - 1, filterParams)}
          className="border-2 border-black px-4 py-2 font-space-mono text-sm font-bold uppercase bg-white hover:bg-gray-100 transition-colors flex items-center gap-1"
        >
          <ChevronLeft className="h-4 w-4" />
          Prev
        </Link>
      ) : (
        <span className="border-2 border-black/30 px-4 py-2 font-space-mono text-sm font-bold uppercase text-black/30 cursor-not-allowed flex items-center gap-1">
          <ChevronLeft className="h-4 w-4" />
          Prev
        </span>
      )}

      <span className="font-space-mono text-sm font-bold uppercase">
        Page {page} of {totalPages}
      </span>

      {hasNext ? (
        <Link
          href={buildPageUrl(page + 1, filterParams)}
          className="border-2 border-black px-4 py-2 font-space-mono text-sm font-bold uppercase bg-white hover:bg-gray-100 transition-colors flex items-center gap-1"
        >
          Next
          <ChevronRight className="h-4 w-4" />
        </Link>
      ) : (
        <span className="border-2 border-black/30 px-4 py-2 font-space-mono text-sm font-bold uppercase text-black/30 cursor-not-allowed flex items-center gap-1">
          Next
          <ChevronRight className="h-4 w-4" />
        </span>
      )}
    </div>
  );
}
