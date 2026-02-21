# Phase 5: Hero + Dashboard Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a pixel-aesthetic hero landing page with Canvas scanline cat animation, and a real-data dashboard pulling from Supabase.

**Architecture:** Hero page (`/`) is a full-screen landing with a `ScanlineCanvas` client component rendering a transparent-bg cat video as animated horizontal lines. Dashboard (`/dashboard`) is a server component querying `purrview_feeding_events` from Supabase. Both share VT323 + Space Mono fonts, neo-brutalist styling.

**Tech Stack:** Next.js 15 (App Router), Tailwind CSS, Supabase JS client, recharts, Canvas API

---

### Task 1: Update types and Supabase client

**Files:**
- Modify: `apps/web/src/lib/types.ts`
- Modify: `apps/web/src/lib/supabase.ts`

**Step 1: Update types.ts — add new fields from DB migration 002**

Add `activity`, `cat_name`, `duration_seconds` to `purrview_feeding_events` type:

```typescript
// In the Row type for purrview_feeding_events, add after existing fields:
activity: string | null;
cat_name: string | null;
duration_seconds: number | null;
```

Add same fields to Insert and Update types (all optional).

**Step 2: Fix supabase.ts — lazy init pattern**

Replace module-level `createClient` with a `getSupabase()` function to avoid import-time crashes when env vars are missing:

```typescript
import { createClient, SupabaseClient } from "@supabase/supabase-js";
import type { Database } from "./types";

let client: SupabaseClient<Database> | null = null;

export function getSupabase(): SupabaseClient<Database> {
  if (!client) {
    const url = process.env.NEXT_PUBLIC_SUPABASE_URL!;
    const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;
    client = createClient<Database>(url, key);
  }
  return client;
}
```

**Step 3: Verify build**

Run: `cd apps/web && npm run build`
Expected: Build succeeds (pages still use mock data, that's fine)

**Step 4: Commit**

```
feat: update types for migration 002 and lazy supabase init
```

---

### Task 2: Create Supabase query functions

**Files:**
- Create: `apps/web/src/lib/queries.ts`

**Step 1: Write query module**

All queries use server-side Supabase. Each function returns typed data. The table is `purrview_feeding_events`.

```typescript
import { getSupabase } from "./supabase";

const TABLE = "purrview_feeding_events";

// Get start of today in UTC
function todayUTC(): string {
  const d = new Date();
  d.setUTCHours(0, 0, 0, 0);
  return d.toISOString();
}

// Get date N days ago in UTC
function daysAgoUTC(n: number): string {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() - n);
  d.setUTCHours(0, 0, 0, 0);
  return d.toISOString();
}

export type TodayStats = {
  feedingCount: number;
  drinkingCount: number;
  activeCats: number;
  lastEventTime: string | null;
};

export async function getTodayStats(): Promise<TodayStats> {
  const sb = getSupabase();
  const today = todayUTC();

  const { data } = await sb
    .from(TABLE)
    .select("cat_name, activity, started_at")
    .gte("started_at", today);

  const rows = data ?? [];
  const cats = new Set(rows.map((r) => r.cat_name).filter(Boolean));
  const feedingCount = rows.filter((r) => r.activity === "eating").length;
  const drinkingCount = rows.filter((r) => r.activity === "drinking").length;

  let lastEventTime: string | null = null;
  if (rows.length > 0) {
    lastEventTime = rows.reduce((latest, r) =>
      r.started_at > latest ? r.started_at : latest,
      rows[0].started_at
    );
  }

  return { feedingCount, drinkingCount, activeCats: cats.size, lastEventTime };
}

export type DailyCount = { date: string; eating: number; drinking: number };

export async function getWeeklyTrend(): Promise<DailyCount[]> {
  const sb = getSupabase();
  const weekAgo = daysAgoUTC(7);

  const { data } = await sb
    .from(TABLE)
    .select("started_at, activity")
    .gte("started_at", weekAgo);

  // Group by date
  const byDate: Record<string, { eating: number; drinking: number }> = {};
  for (const row of data ?? []) {
    const date = row.started_at.slice(0, 10); // YYYY-MM-DD
    if (!byDate[date]) byDate[date] = { eating: 0, drinking: 0 };
    if (row.activity === "eating") byDate[date].eating++;
    else if (row.activity === "drinking") byDate[date].drinking++;
  }

  // Fill in missing days
  const result: DailyCount[] = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setUTCDate(d.getUTCDate() - i);
    const date = d.toISOString().slice(0, 10);
    result.push({ date, eating: byDate[date]?.eating ?? 0, drinking: byDate[date]?.drinking ?? 0 });
  }
  return result;
}

export type RecentEvent = {
  id: string;
  cat_name: string;
  activity: string;
  started_at: string;
  duration_seconds: number | null;
};

export async function getRecentEvents(limit = 10): Promise<RecentEvent[]> {
  const sb = getSupabase();
  const { data } = await sb
    .from(TABLE)
    .select("id, cat_name, activity, started_at, duration_seconds")
    .order("started_at", { ascending: false })
    .limit(limit);

  return (data ?? []).map((r) => ({
    id: r.id,
    cat_name: r.cat_name ?? "Unknown",
    activity: r.activity ?? "eating",
    started_at: r.started_at,
    duration_seconds: r.duration_seconds,
  }));
}

export type CatStatus = {
  name: string;
  lastActivity: string;
  lastTime: string;
};

export async function getCatStatuses(): Promise<CatStatus[]> {
  const sb = getSupabase();
  const CAT_NAMES = ["大吉", "小慢", "麻酱", "松花", "小黑"];

  const { data } = await sb
    .from(TABLE)
    .select("cat_name, activity, started_at")
    .in("cat_name", CAT_NAMES)
    .order("started_at", { ascending: false });

  // Get most recent event per cat
  const seen = new Set<string>();
  const statuses: CatStatus[] = [];
  for (const row of data ?? []) {
    const name = row.cat_name ?? "";
    if (seen.has(name)) continue;
    seen.add(name);
    statuses.push({
      name,
      lastActivity: row.activity ?? "eating",
      lastTime: row.started_at,
    });
  }

  // Add cats with no events
  for (const name of CAT_NAMES) {
    if (!seen.has(name)) {
      statuses.push({ name, lastActivity: "none", lastTime: "" });
    }
  }

  return statuses;
}
```

**Step 2: Verify build**

Run: `cd apps/web && npm run build`
Expected: Succeeds (queries not called yet)

**Step 3: Commit**

```
feat: add Supabase query functions for dashboard
```

---

### Task 3: Create ScanlineCanvas component

**Files:**
- Create: `apps/web/src/components/ScanlineCanvas.tsx`

**Step 1: Write the client component**

Port the Canvas logic from `index.html` into a React component. Key behaviors:
- Loads a `<video>` element (hidden), plays it looped + muted
- On each `requestAnimationFrame`, reads video frame pixels via offscreen canvas
- Draws horizontal lines where thickness = pixel darkness
- Skips transparent pixels (alpha < 50)
- Mouse proximity causes sine-wave jitter distortion

```typescript
"use client";

import { useRef, useEffect, useCallback } from "react";

interface ScanlineCanvasProps {
  videoSrc: string;
  className?: string;
}

const CONFIG = {
  stepY: 7,
  stepX: 3,
  maxThick: 6.5,
  minThick: 0.5,
  threshold: 240,
  mouseRadius: 120,
};

export function ScanlineCanvas({ videoSrc, className }: ScanlineCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const offCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const mouseRef = useRef({ x: -1000, y: -1000 });
  const timeRef = useRef(0);
  const sizeRef = useRef({ w: 0, h: 0 });

  const animate = useCallback(() => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    const offCanvas = offCanvasRef.current;
    if (!canvas || !video || !offCanvas) return;
    if (video.readyState < 2 || video.paused || video.ended) return;

    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    const offCtx = offCanvas.getContext("2d", { willReadFrequently: true });
    if (!ctx || !offCtx) return;

    const { w, h } = sizeRef.current;
    offCtx.clearRect(0, 0, w, h);
    offCtx.drawImage(video, 0, 0, w, h);
    const imgData = offCtx.getImageData(0, 0, w, h);
    const data = imgData.data;

    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "#111";

    const { stepY, stepX, maxThick, minThick, threshold, mouseRadius } = CONFIG;
    const { x: mx, y: my } = mouseRef.current;
    const t = timeRef.current;

    for (let y = 0; y < h; y += stepY) {
      for (let x = 0; x < w; x += stepX) {
        const idx = (Math.floor(y) * w + Math.floor(x)) * 4;
        const a = data[idx + 3];
        if (a < 50) continue;

        const r = data[idx], g = data[idx + 1], b = data[idx + 2];
        const brightness = 0.299 * r + 0.587 * g + 0.114 * b;
        if (brightness > threshold) continue;

        const darkFactor = 1 - brightness / 255;
        let thick = Math.max(darkFactor * maxThick, minThick);
        let offsetX = 0;

        const dx = x - mx, dy = y - my;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < mouseRadius) {
          const force = (mouseRadius - dist) / mouseRadius;
          offsetX = Math.sin(t * 0.1 + y) * 15 * force;
          thick *= 1 - force * 0.2;
        }

        ctx.fillRect(x + offsetX, y - thick / 2, stepX, thick);
      }
    }
    timeRef.current++;
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const video = document.createElement("video");
    video.src = videoSrc;
    video.autoplay = true;
    video.loop = true;
    video.muted = true;
    video.playsInline = true;
    video.crossOrigin = "anonymous";
    video.style.display = "none";
    document.body.appendChild(video);
    videoRef.current = video;

    const offCanvas = document.createElement("canvas");
    offCanvasRef.current = offCanvas;

    const onMeta = () => {
      const scale = (window.innerHeight * 0.8) / video.videoHeight;
      const w = Math.round(video.videoWidth * scale);
      const h = Math.round(window.innerHeight * 0.8);
      canvas.width = w;
      canvas.height = h;
      offCanvas.width = w;
      offCanvas.height = h;
      sizeRef.current = { w, h };
      video.play().catch(() => {});
    };
    video.addEventListener("loadedmetadata", onMeta);

    // Click to play (autoplay policy)
    const onClick = () => { if (video.paused) video.play(); };
    document.body.addEventListener("click", onClick);

    // Mouse tracking
    const onMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const scaleX = canvas.width / rect.width;
      const scaleY = canvas.height / rect.height;
      mouseRef.current = {
        x: (e.clientX - rect.left) * scaleX,
        y: (e.clientY - rect.top) * scaleY,
      };
      // Parallax
      const xAxis = (window.innerWidth / 2 - e.pageX) / 40;
      const yAxis = (window.innerHeight / 2 - e.pageY) / 40;
      canvas.style.transform = `translate(${xAxis}px, ${yAxis}px)`;
    };
    const onLeave = () => {
      mouseRef.current = { x: -1000, y: -1000 };
      canvas.style.transform = "translate(0,0)";
    };
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseleave", onLeave);

    // Animation loop
    let rafId: number;
    const loop = () => { animate(); rafId = requestAnimationFrame(loop); };
    rafId = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(rafId);
      video.removeEventListener("loadedmetadata", onMeta);
      document.body.removeEventListener("click", onClick);
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseleave", onLeave);
      video.pause();
      video.remove();
    };
  }, [videoSrc, animate]);

  return <canvas ref={canvasRef} className={className} />;
}
```

**Step 2: Verify build**

Run: `cd apps/web && npm run build`
Expected: Succeeds (component not rendered yet)

**Step 3: Commit**

```
feat: add ScanlineCanvas component for hero animation
```

---

### Task 4: Rewrite Hero page (`/`)

**Files:**
- Modify: `apps/web/src/app/page.tsx` — replace entirely
- Modify: `apps/web/src/app/layout.tsx` — conditional nav

**Step 1: Rewrite page.tsx as Hero-only landing**

Layout: left text + right ScanlineCanvas, full viewport height.
No imports from mock.ts. No dashboard content.

```typescript
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { ScanlineCanvas } from "@/components/ScanlineCanvas";

export default function Home() {
  return (
    <div className="flex min-h-[calc(100vh-64px)] w-full items-center px-[5%]">
      {/* Left: text content */}
      <div className="flex-1 max-w-xl z-10">
        <h1 className="font-vt323 text-[8rem] lg:text-[10rem] leading-[0.9] uppercase tracking-tight">
          PURR<br />VIEW
        </h1>
        <p className="font-space-mono text-lg leading-relaxed mt-6 max-w-md">
          AI-powered cat feeding monitor. Tracking meals, water intake, and
          habits for your feline family.
        </p>
        <div className="flex items-center gap-6 mt-10">
          <Link
            href="/dashboard"
            className="group flex items-center bg-black text-[#f4f4f0] px-8 py-4 font-space-mono text-base font-bold transition-all hover:shadow-[6px_6px_0_0_rgba(0,0,0,1)] hover:bg-[#111]"
          >
            Enter Dashboard
            <ArrowRight className="ml-3 h-5 w-5 transition-transform group-hover:translate-x-1" />
          </Link>
          <Link
            href="#about"
            className="font-space-mono text-base font-bold hover:opacity-60 transition-opacity"
          >
            How It Works &gt;
          </Link>
        </div>
      </div>

      {/* Right: scanline cat animation */}
      <div className="flex-[1.2] flex justify-center items-center">
        <ScanlineCanvas videoSrc="/majiang_nobg.webm" />
      </div>
    </div>
  );
}
```

**Step 2: Update layout.tsx — hide full nav on hero, show on dashboard**

Use `usePathname` via a client NavBar component, or simply keep nav visible on all pages with the existing brutalist style. The simpler approach: keep the current nav bar as-is (it already links to dashboard, cats, timeline). No changes needed to layout.tsx for now.

**Step 3: Run dev server and visually verify**

Run: `cd apps/web && npm run dev`
Open: `http://localhost:3000`
Expected: Full-screen hero with scanline cat on right, text on left

**Step 4: Commit**

```
feat: rewrite hero page with scanline cat animation
```

---

### Task 5: Rewrite Dashboard page with real Supabase data

**Files:**
- Modify: `apps/web/src/app/dashboard/page.tsx` — replace entirely
- Modify: `apps/web/src/components/dashboard/MetricCard.tsx` — keep as-is (already good)
- Modify: `apps/web/src/components/dashboard/FeedingChart.tsx` — real data
- Modify: `apps/web/src/components/dashboard/RecentActivity.tsx` — real data

**Step 1: Rewrite dashboard/page.tsx as server component with real queries**

```typescript
import { getTodayStats, getWeeklyTrend, getRecentEvents, getCatStatuses } from "@/lib/queries";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { RecentActivity } from "@/components/dashboard/RecentActivity";
import { FeedingChart } from "@/components/dashboard/FeedingChart";
import { CatStatusGrid } from "@/components/dashboard/CatStatusGrid";
import { Utensils, Cat, Droplets, Clock } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

export const dynamic = "force-dynamic";

export default async function Dashboard() {
  const [stats, trend, events, catStatuses] = await Promise.all([
    getTodayStats(),
    getWeeklyTrend(),
    getRecentEvents(),
    getCatStatuses(),
  ]);

  const lastEventLabel = stats.lastEventTime
    ? formatDistanceToNow(new Date(stats.lastEventTime), { addSuffix: true })
    : "No events";

  return (
    <div className="flex flex-col space-y-8 p-4 pt-6 max-w-[1600px] mx-auto">
      <section className="flex flex-col space-y-4">
        <div className="flex items-center justify-between border-b-4 border-black pb-2">
          <h2 className="font-vt323 text-5xl font-bold uppercase tracking-widest">
            Command Center
          </h2>
          <div className="font-space-mono text-sm font-bold bg-black text-[#00FF66] px-4 py-1 border-2 border-black">
            SYSTEM.ONLINE
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="FEEDINGS"
            value={stats.feedingCount}
            description="Eating events today"
            icon={<Utensils className="h-6 w-6" />}
          />
          <MetricCard
            title="ACTIVE CATS"
            value={stats.activeCats}
            description="Cats detected today"
            icon={<Cat className="h-6 w-6" />}
          />
          <MetricCard
            title="WATER EVENTS"
            value={stats.drinkingCount}
            description="Drinking events today"
            icon={<Droplets className="h-6 w-6" />}
          />
          <MetricCard
            title="LAST SIGNAL"
            value={lastEventLabel}
            description="Most recent event"
            icon={<Clock className="h-6 w-6" />}
          />
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-7">
          <FeedingChart data={trend} />
          <RecentActivity events={events} />
        </div>

        <CatStatusGrid statuses={catStatuses} />
      </section>
    </div>
  );
}
```

**Step 2: Update FeedingChart to accept real data as props**

Change from generating random data to receiving `data` prop:

```typescript
"use client";

import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip } from "recharts";

interface FeedingChartProps {
  data: { date: string; eating: number; drinking: number }[];
}

export function FeedingChart({ data }: FeedingChartProps) {
  // Format date labels (MM/DD)
  const chartData = data.map((d) => ({
    name: d.date.slice(5), // "02-21" from "2026-02-21"
    eating: d.eating,
    drinking: d.drinking,
  }));

  return (
    <div className="col-span-4 border-4 border-black bg-white shadow-[8px_8px_0_0_rgba(0,0,0,1)] flex flex-col">
      <div className="p-6 border-b-4 border-black bg-[#f4f4f0]">
        <h3 className="font-vt323 text-4xl uppercase tracking-widest text-black">
          Weekly Activity
        </h3>
        <p className="font-space-mono text-sm font-bold uppercase text-black/70">
          Feeding &amp; drinking events per day
        </p>
      </div>
      <div className="p-6 pl-2 flex-grow bg-white">
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={chartData}>
            <XAxis dataKey="name" stroke="#000" fontSize={12} tickLine={false}
              style={{ fontFamily: "var(--font-space-mono)", fontWeight: "bold" }} />
            <YAxis stroke="#000" fontSize={12} tickLine={false}
              style={{ fontFamily: "var(--font-space-mono)", fontWeight: "bold" }} />
            <Bar dataKey="eating" fill="#FF5722" stroke="#000" strokeWidth={2} stackId="a" />
            <Bar dataKey="drinking" fill="#3b82f6" stroke="#000" strokeWidth={2} stackId="a" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
```

**Step 3: Update RecentActivity to use real event data**

```typescript
import { Utensils, Droplets, Eye } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import type { RecentEvent } from "@/lib/queries";

const CAT_COLORS: Record<string, string> = {
  "大吉": "#f59e0b",
  "小慢": "#3b82f6",
  "麻酱": "#d97706",
  "松花": "#22c55e",
  "小黑": "#8b5cf6",
};

const ACTIVITY_ICON = {
  eating: Utensils,
  drinking: Droplets,
  present: Eye,
};

interface RecentActivityProps {
  events: RecentEvent[];
}

export function RecentActivity({ events }: RecentActivityProps) {
  return (
    <div className="col-span-3 border-4 border-black bg-white shadow-[8px_8px_0_0_rgba(0,0,0,1)]">
      <div className="p-6 border-b-4 border-black bg-[#f4f4f0]">
        <h3 className="font-vt323 text-4xl uppercase tracking-widest text-black">
          Activity Log
        </h3>
      </div>
      <div className="p-6">
        <div className="space-y-5">
          {events.map((event) => {
            const Icon = ACTIVITY_ICON[event.activity as keyof typeof ACTIVITY_ICON] ?? Eye;
            const color = CAT_COLORS[event.cat_name] ?? "#666";
            return (
              <div key={event.id} className="flex items-center">
                <div
                  className="h-10 w-10 border-2 border-black flex items-center justify-center font-vt323 text-xl text-white font-bold"
                  style={{ backgroundColor: color }}
                >
                  {event.cat_name.slice(0, 1)}
                </div>
                <div className="ml-4 space-y-1">
                  <p className="text-sm font-space-mono font-bold leading-none flex items-center gap-2 uppercase">
                    {event.cat_name}
                    <Icon className="h-3 w-3 text-black" />
                  </p>
                  <p className="font-vt323 text-lg leading-none text-black/70 uppercase tracking-wider">
                    {formatDistanceToNow(new Date(event.started_at), { addSuffix: true })}
                  </p>
                </div>
                <div className="ml-auto font-vt323 text-xl bg-[#f4f4f0] border-2 border-black px-2 py-1">
                  {event.activity}
                </div>
              </div>
            );
          })}
          {events.length === 0 && (
            <p className="font-space-mono text-sm text-black/50 uppercase">No events recorded yet</p>
          )}
        </div>
      </div>
    </div>
  );
}
```

**Step 4: Create CatStatusGrid component**

Create: `apps/web/src/components/dashboard/CatStatusGrid.tsx`

```typescript
import { formatDistanceToNow } from "date-fns";
import type { CatStatus } from "@/lib/queries";

const CAT_COLORS: Record<string, string> = {
  "大吉": "#f59e0b",
  "小慢": "#3b82f6",
  "麻酱": "#d97706",
  "松花": "#22c55e",
  "小黑": "#8b5cf6",
};

interface CatStatusGridProps {
  statuses: CatStatus[];
}

export function CatStatusGrid({ statuses }: CatStatusGridProps) {
  return (
    <div className="border-4 border-black bg-white shadow-[8px_8px_0_0_rgba(0,0,0,1)]">
      <div className="p-6 border-b-4 border-black bg-[#f4f4f0]">
        <h3 className="font-vt323 text-4xl uppercase tracking-widest text-black">
          Cat Status
        </h3>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-0">
        {statuses.map((cat) => {
          const color = CAT_COLORS[cat.name] ?? "#666";
          const timeLabel = cat.lastTime
            ? formatDistanceToNow(new Date(cat.lastTime), { addSuffix: true })
            : "No data";
          return (
            <div key={cat.name} className="p-6 border-2 border-black/10 flex flex-col items-center text-center">
              <div
                className="h-14 w-14 border-3 border-black flex items-center justify-center font-vt323 text-3xl text-white font-bold mb-3"
                style={{ backgroundColor: color }}
              >
                {cat.name.slice(0, 1)}
              </div>
              <p className="font-space-mono text-sm font-bold uppercase">{cat.name}</p>
              <p className="font-vt323 text-lg text-black/60 uppercase mt-1">{cat.lastActivity}</p>
              <p className="font-space-mono text-xs text-black/40 mt-1">{timeLabel}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

**Step 5: Verify build and dev server**

Run: `cd apps/web && npm run build`
Expected: Build succeeds. Dashboard page renders (may show empty data if no env vars).

Run: `cd apps/web && npm run dev`
Open: `http://localhost:3000/dashboard`
Expected: Dashboard with real Supabase data (or empty state with "No events")

**Step 6: Commit**

```
feat: dashboard with real Supabase data
```

---

### Task 6: Cleanup — remove mock data, delete old Hero

**Files:**
- Delete: `apps/web/src/lib/mock.ts`
- Delete: `apps/web/src/components/dashboard/Hero.tsx`
- Verify: no remaining imports from mock.ts

**Step 1: Remove mock.ts and Hero.tsx**

Delete both files. Search for any remaining imports:

Run: `grep -r "mock" apps/web/src/ --include="*.ts" --include="*.tsx"`
Run: `grep -r "Hero" apps/web/src/ --include="*.ts" --include="*.tsx"`

Fix any remaining references.

**Step 2: Verify build**

Run: `cd apps/web && npm run build`
Expected: Clean build, no errors

**Step 3: Commit**

```
chore: remove mock data and old Hero component
```

---

### Task 7: Visual polish and verify

**Step 1: Run dev server, check both pages end-to-end**

- `http://localhost:3000` — Hero page with scanline cat
- `http://localhost:3000/dashboard` — Dashboard with real data

**Step 2: Check for visual issues**

- Hero: Canvas renders correctly, mouse glitch works, responsive on smaller screens
- Dashboard: Cards show real numbers, chart renders, activity log populates, cat status grid shows all 5 cats

**Step 3: Final build check**

Run: `cd apps/web && npm run build`
Expected: Clean build, no warnings

**Step 4: Commit everything**

```
feat: Phase 5 — hero landing page + real-data dashboard
```
