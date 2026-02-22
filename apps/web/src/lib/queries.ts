import { getSupabase } from "./supabase";
import { CAT_NAMES } from "./catColors";

// --- Types ---

export type TodayStats = {
  feedingCount: number;
  drinkingCount: number;
  activeCats: number;
  lastEventTime: string | null;
};

export type DailyCount = {
  date: string; // YYYY-MM-DD
  eating: number;
  drinking: number;
};

// Per-cat daily breakdown for stacked bar charts
// Each entry: { date, label, "大吉": 3, "小慢": 1, ... }
export type DailyCatCount = Record<string, number | string>;

export type WeeklyTrendByCat = {
  eating: DailyCatCount[];
  drinking: DailyCatCount[];
};

export type RecentEvent = {
  id: string;
  cat_name: string;
  activity: string;
  started_at: string;
  duration_seconds: number;
};

export type CatStatus = {
  name: string;
  lastActivity: string;
  lastTime: string;
};

// All 5 known cats
const ALL_CATS = ["大吉", "小慢", "麻酱", "松花", "小黑"];

// Cat headshot mapping (pinyin filename -> Chinese name)
export const CAT_HEADSHOTS: Record<string, string> = {
  大吉: "/daji_headshot.jpeg",
  小慢: "/xiaoman_headshot.jpeg",
  麻酱: "/majiang_headshot.jpeg",
  松花: "/songhua_headshot.jpeg",
  小黑: "/xiaohei_headshot.jpeg",
};

// One-line cat bios
export const CAT_BIOS: Record<string, string> = {
  麻酱: "The OG rescue — a stray-turned-hero-mom who raised a dozen kittens.",
  松花: "Majiang's son. A big cuddly boy who's also the biggest scaredy-cat.",
  小黑: "Once hired by a restaurant to hunt mice. Now a retired sun-worshipper.",
  大吉: "Thinks he's a dog. Best personality in the house, and the biggest appetite.",
  小慢: "Lost one eye to surgery — only then did her gentle side come through.",
};

// --- Timeline types ---

export type TimelineEvent = {
  id: string;
  cat_name: string;
  activity: string;
  started_at: string;
  duration_seconds: number;
  thumbnail_url: string | null;
};

export type PaginatedTimeline = {
  events: TimelineEvent[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
};

export type TimelineFilters = {
  cat?: string;
  activity?: string;
};

// --- Reports types ---

export type MonthlyTrend = {
  date: string;
  label: string;
  eating: number;
  drinking: number;
};

export type CatEventCount = {
  name: string;
  eating: number;
  drinking: number;
};

export type HourlyDistribution = {
  hour: number;
  label: string;
  eating: number;
  drinking: number;
};

export type CatAvgDuration = {
  name: string;
  avg_seconds: number;
};

// --- Cat profile types ---

export type CatDailyMini = {
  date: string;
  eating: number;
  drinking: number;
};

export type CatProfile = {
  name: string;
  headshot: string;
  totalEating: number;
  totalDrinking: number;
  avgDuration: number;
  lastSeen: string | null;
  trend: CatDailyMini[];
};

// Row subset types for Supabase .returns<T>() type hints
type StatsRow = { cat_name: string | null; activity: string | null; started_at: string };
type TrendRow = { cat_name: string | null; activity: string | null; started_at: string };
type EventRow = {
  id: string;
  cat_name: string | null;
  activity: string | null;
  started_at: string;
  duration_seconds: number | null;
};
type FrameRow = {
  feeding_event_id: string;
  frame_url: string | null;
};
type FullEventRow = EventRow & { ended_at: string | null };

// --- Query Functions ---

/**
 * Get today's aggregated stats: feeding/drinking counts, active cats, last event time.
 * "Today" is defined as UTC midnight of the current day.
 */
export async function getTodayStats(): Promise<TodayStats> {
  const supabase = getSupabase();

  // UTC midnight today
  const now = new Date();
  const todayStart = new Date(
    Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate())
  ).toISOString();

  const { data, error } = await supabase
    .from("purrview_feeding_events")
    .select("cat_name, activity, started_at")
    .gte("started_at", todayStart)
    .returns<StatsRow[]>();

  if (error) {
    console.error("getTodayStats error:", error.message);
    return { feedingCount: 0, drinkingCount: 0, activeCats: 0, lastEventTime: null };
  }

  if (!data || data.length === 0) {
    return { feedingCount: 0, drinkingCount: 0, activeCats: 0, lastEventTime: null };
  }

  let feedingCount = 0;
  let drinkingCount = 0;
  const catSet = new Set<string>();
  let lastEventTime: string | null = null;

  for (const row of data) {
    if (row.activity === "eating") feedingCount++;
    else if (row.activity === "drinking") drinkingCount++;

    if (row.cat_name) catSet.add(row.cat_name);

    if (!lastEventTime || row.started_at > lastEventTime) {
      lastEventTime = row.started_at;
    }
  }

  return {
    feedingCount,
    drinkingCount,
    activeCats: catSet.size,
    lastEventTime,
  };
}

/**
 * Get weekly trend: eating/drinking counts per day for the last 7 days.
 * Missing days are filled with 0.
 */
export async function getWeeklyTrend(): Promise<DailyCount[]> {
  const supabase = getSupabase();

  // Build date range: 6 days ago through today (7 days total)
  const now = new Date();
  const startDate = new Date(
    Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() - 6)
  );
  const startISO = startDate.toISOString();

  const { data, error } = await supabase
    .from("purrview_feeding_events")
    .select("cat_name, activity, started_at")
    .gte("started_at", startISO)
    .order("started_at", { ascending: true })
    .returns<TrendRow[]>();

  // Build a map for all 7 days initialized to 0
  const dayMap: Record<string, { eating: number; drinking: number }> = {};
  const orderedDates: string[] = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(
      Date.UTC(startDate.getUTCFullYear(), startDate.getUTCMonth(), startDate.getUTCDate() + i)
    );
    const key = d.toISOString().slice(0, 10); // YYYY-MM-DD
    dayMap[key] = { eating: 0, drinking: 0 };
    orderedDates.push(key);
  }

  if (error) {
    console.error("getWeeklyTrend error:", error.message);
  } else if (data) {
    for (const row of data) {
      const dateKey = row.started_at.slice(0, 10);
      const entry = dayMap[dateKey];
      if (!entry) continue;

      if (row.activity === "eating") entry.eating++;
      else if (row.activity === "drinking") entry.drinking++;
    }
  }

  // Convert to sorted array
  return orderedDates.map((date) => ({
    date,
    eating: dayMap[date].eating,
    drinking: dayMap[date].drinking,
  }));
}

/**
 * Get weekly trend broken down by cat: separate eating/drinking datasets.
 * Each entry: { date, label, "大吉": 3, "小慢": 1, ... }
 * Reuses the same Supabase query as getWeeklyTrend but groups by cat_name.
 */
export async function getWeeklyTrendByCat(): Promise<WeeklyTrendByCat> {
  const supabase = getSupabase();

  const now = new Date();
  const startDate = new Date(
    Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() - 6)
  );
  const startISO = startDate.toISOString();

  const { data, error } = await supabase
    .from("purrview_feeding_events")
    .select("cat_name, activity, started_at")
    .gte("started_at", startISO)
    .order("started_at", { ascending: true })
    .returns<TrendRow[]>();

  // Initialize per-day per-cat counters for both activities
  const orderedDates: string[] = [];
  const eatingMap: Record<string, Record<string, number>> = {};
  const drinkingMap: Record<string, Record<string, number>> = {};

  for (let i = 0; i < 7; i++) {
    const d = new Date(
      Date.UTC(startDate.getUTCFullYear(), startDate.getUTCMonth(), startDate.getUTCDate() + i)
    );
    const key = d.toISOString().slice(0, 10);
    orderedDates.push(key);
    eatingMap[key] = {};
    drinkingMap[key] = {};
    for (const cat of CAT_NAMES) {
      eatingMap[key][cat] = 0;
      drinkingMap[key][cat] = 0;
    }
  }

  if (error) {
    console.error("getWeeklyTrendByCat error:", error.message);
  } else if (data) {
    for (const row of data) {
      const dateKey = row.started_at.slice(0, 10);
      const catName = row.cat_name;
      if (!catName || !eatingMap[dateKey]) continue;

      if (row.activity === "eating") {
        eatingMap[dateKey][catName] = (eatingMap[dateKey][catName] ?? 0) + 1;
      } else if (row.activity === "drinking") {
        drinkingMap[dateKey][catName] = (drinkingMap[dateKey][catName] ?? 0) + 1;
      }
    }
  }

  const toChartData = (map: Record<string, Record<string, number>>) =>
    orderedDates.map((date) => ({
      date,
      label: date.slice(5),
      ...map[date],
    }));

  return {
    eating: toChartData(eatingMap),
    drinking: toChartData(drinkingMap),
  };
}

/**
 * Get recent feeding/drinking events, ordered by most recent first.
 */
export async function getRecentEvents(limit: number = 10): Promise<RecentEvent[]> {
  const supabase = getSupabase();

  const { data, error } = await supabase
    .from("purrview_feeding_events")
    .select("id, cat_name, activity, started_at, duration_seconds")
    .order("started_at", { ascending: false })
    .limit(limit)
    .returns<EventRow[]>();

  if (error) {
    console.error("getRecentEvents error:", error.message);
    return [];
  }

  if (!data || data.length === 0) {
    return [];
  }

  return data.map((row) => ({
    id: row.id,
    cat_name: row.cat_name ?? "unknown",
    activity: row.activity ?? "unknown",
    started_at: row.started_at,
    duration_seconds: row.duration_seconds ?? 0,
  }));
}

/**
 * Get the most recent activity status for each of the 5 known cats.
 * Cats with no events return lastActivity="none" and lastTime="".
 */
export async function getCatStatuses(): Promise<CatStatus[]> {
  const supabase = getSupabase();

  // Fetch the most recent event per cat using one query ordered by started_at DESC.
  // We fetch a reasonable number of recent events and pick the latest per cat.
  const { data, error } = await supabase
    .from("purrview_feeding_events")
    .select("cat_name, activity, started_at")
    .order("started_at", { ascending: false })
    .limit(100)
    .returns<StatsRow[]>();

  // Build a map: cat_name -> latest event
  const latestMap: Record<string, { activity: string; started_at: string }> = {};

  if (error) {
    console.error("getCatStatuses error:", error.message);
  } else if (data) {
    for (const row of data) {
      const name = row.cat_name;
      if (!name) continue;
      // Since results are ordered DESC, the first occurrence per cat is the most recent
      if (!latestMap[name]) {
        latestMap[name] = {
          activity: row.activity ?? "unknown",
          started_at: row.started_at,
        };
      }
    }
  }

  // Map all 5 cats, filling in defaults for cats with no events
  return ALL_CATS.map((name) => {
    const latest = latestMap[name];
    if (latest) {
      return {
        name,
        lastActivity: latest.activity,
        lastTime: latest.started_at,
      };
    }
    return {
      name,
      lastActivity: "none",
      lastTime: "",
    };
  });
}

// --- Timeline queries ---

/**
 * Get paginated timeline events with optional cat/activity filters.
 * Joins first frame thumbnail when available.
 */
export async function getTimelineEvents(
  filters: TimelineFilters = {},
  page: number = 1,
  pageSize: number = 20
): Promise<PaginatedTimeline> {
  const supabase = getSupabase();
  const offset = (page - 1) * pageSize;

  // Build filtered query for count
  let countQuery = supabase
    .from("purrview_feeding_events")
    .select("id", { count: "exact", head: true });

  if (filters.cat) countQuery = countQuery.eq("cat_name", filters.cat);
  if (filters.activity) countQuery = countQuery.eq("activity", filters.activity);

  const { count } = await countQuery;
  const total = count ?? 0;

  // Build filtered query for data
  let dataQuery = supabase
    .from("purrview_feeding_events")
    .select("id, cat_name, activity, started_at, duration_seconds")
    .order("started_at", { ascending: false })
    .range(offset, offset + pageSize - 1);

  if (filters.cat) dataQuery = dataQuery.eq("cat_name", filters.cat);
  if (filters.activity) dataQuery = dataQuery.eq("activity", filters.activity);

  const { data, error } = await dataQuery.returns<EventRow[]>();

  if (error) {
    console.error("getTimelineEvents error:", error.message);
    return { events: [], total: 0, page, pageSize, totalPages: 0 };
  }

  // Look up frame URLs from Storage bucket (each event_id is a folder with 1 JPEG)
  const eventIds = (data ?? []).map((e) => e.id);
  let frameMap: Record<string, string> = {};

  if (eventIds.length > 0) {
    const results = await Promise.all(
      eventIds.map(async (eid) => {
        const { data: files } = await supabase.storage
          .from("purrview-frames")
          .list(eid, { limit: 1 });
        if (files && files.length > 0) {
          const { data: urlData } = supabase.storage
            .from("purrview-frames")
            .getPublicUrl(`${eid}/${files[0].name}`);
          return { eid, url: urlData.publicUrl };
        }
        return null;
      })
    );
    for (const r of results) {
      if (r) frameMap[r.eid] = r.url;
    }
  }

  const events: TimelineEvent[] = (data ?? []).map((row) => ({
    id: row.id,
    cat_name: row.cat_name ?? "unknown",
    activity: row.activity ?? "unknown",
    started_at: row.started_at,
    duration_seconds: row.duration_seconds ?? 0,
    thumbnail_url: frameMap[row.id] ?? null,
  }));

  return {
    events,
    total,
    page,
    pageSize,
    totalPages: Math.ceil(total / pageSize),
  };
}

// --- Reports queries ---

/**
 * Get 30-day daily eating/drinking counts for line chart.
 */
export async function getMonthlyTrend(): Promise<MonthlyTrend[]> {
  const supabase = getSupabase();

  const now = new Date();
  const startDate = new Date(
    Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() - 29)
  );
  const startISO = startDate.toISOString();

  const { data, error } = await supabase
    .from("purrview_feeding_events")
    .select("activity, started_at")
    .gte("started_at", startISO)
    .order("started_at", { ascending: true })
    .returns<{ activity: string | null; started_at: string }[]>();

  // Build 30-day map
  const dayMap: Record<string, { eating: number; drinking: number }> = {};
  const orderedDates: string[] = [];

  for (let i = 0; i < 30; i++) {
    const d = new Date(
      Date.UTC(startDate.getUTCFullYear(), startDate.getUTCMonth(), startDate.getUTCDate() + i)
    );
    const key = d.toISOString().slice(0, 10);
    dayMap[key] = { eating: 0, drinking: 0 };
    orderedDates.push(key);
  }

  if (error) {
    console.error("getMonthlyTrend error:", error.message);
  } else if (data) {
    for (const row of data) {
      const dateKey = row.started_at.slice(0, 10);
      const entry = dayMap[dateKey];
      if (!entry) continue;
      if (row.activity === "eating") entry.eating++;
      else if (row.activity === "drinking") entry.drinking++;
    }
  }

  return orderedDates.map((date) => ({
    date,
    label: date.slice(5), // MM-DD
    eating: dayMap[date].eating,
    drinking: dayMap[date].drinking,
  }));
}

/**
 * Get total event counts per cat (all time), for horizontal stacked bar.
 */
export async function getCatEventCounts(): Promise<CatEventCount[]> {
  const supabase = getSupabase();

  const { data, error } = await supabase
    .from("purrview_feeding_events")
    .select("cat_name, activity")
    .returns<{ cat_name: string | null; activity: string | null }[]>();

  const countMap: Record<string, { eating: number; drinking: number }> = {};
  for (const cat of ALL_CATS) {
    countMap[cat] = { eating: 0, drinking: 0 };
  }

  if (error) {
    console.error("getCatEventCounts error:", error.message);
  } else if (data) {
    for (const row of data) {
      const name = row.cat_name;
      if (!name || !countMap[name]) continue;
      if (row.activity === "eating") countMap[name].eating++;
      else if (row.activity === "drinking") countMap[name].drinking++;
    }
  }

  return ALL_CATS.map((name) => ({
    name,
    eating: countMap[name].eating,
    drinking: countMap[name].drinking,
  }));
}

/**
 * Get events bucketed by hour (0-23) for bar chart.
 */
export async function getHourlyDistribution(): Promise<HourlyDistribution[]> {
  const supabase = getSupabase();

  const { data, error } = await supabase
    .from("purrview_feeding_events")
    .select("activity, started_at")
    .returns<{ activity: string | null; started_at: string }[]>();

  // Initialize 24 hours
  const hourMap: Record<number, { eating: number; drinking: number }> = {};
  for (let h = 0; h < 24; h++) {
    hourMap[h] = { eating: 0, drinking: 0 };
  }

  if (error) {
    console.error("getHourlyDistribution error:", error.message);
  } else if (data) {
    for (const row of data) {
      const hour = new Date(row.started_at).getUTCHours();
      if (row.activity === "eating") hourMap[hour].eating++;
      else if (row.activity === "drinking") hourMap[hour].drinking++;
    }
  }

  return Array.from({ length: 24 }, (_, h) => ({
    hour: h,
    label: `${h.toString().padStart(2, "0")}:00`,
    eating: hourMap[h].eating,
    drinking: hourMap[h].drinking,
  }));
}

/**
 * Get average eating/drinking duration per cat.
 */
export async function getCatAvgDurations(): Promise<CatAvgDuration[]> {
  const supabase = getSupabase();

  const { data, error } = await supabase
    .from("purrview_feeding_events")
    .select("cat_name, duration_seconds")
    .not("duration_seconds", "is", null)
    .returns<{ cat_name: string | null; duration_seconds: number }[]>();

  const durMap: Record<string, { total: number; count: number }> = {};
  for (const cat of ALL_CATS) {
    durMap[cat] = { total: 0, count: 0 };
  }

  if (error) {
    console.error("getCatAvgDurations error:", error.message);
  } else if (data) {
    for (const row of data) {
      const name = row.cat_name;
      if (!name || !durMap[name]) continue;
      durMap[name].total += row.duration_seconds;
      durMap[name].count++;
    }
  }

  return ALL_CATS.map((name) => ({
    name,
    avg_seconds: durMap[name].count > 0
      ? Math.round(durMap[name].total / durMap[name].count)
      : 0,
  }));
}

/**
 * Get full cat profiles with stats and 7-day mini trend.
 */
export async function getCatProfiles(): Promise<CatProfile[]> {
  const supabase = getSupabase();

  const now = new Date();
  const weekAgo = new Date(
    Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() - 6)
  );

  // Fetch all events (we need all-time stats + 7-day trend)
  const { data, error } = await supabase
    .from("purrview_feeding_events")
    .select("cat_name, activity, started_at, duration_seconds")
    .order("started_at", { ascending: false })
    .returns<EventRow[]>();

  // Initialize per-cat accumulators
  const profileMap: Record<
    string,
    {
      totalEating: number;
      totalDrinking: number;
      totalDuration: number;
      durationCount: number;
      lastSeen: string | null;
      trendMap: Record<string, { eating: number; drinking: number }>;
    }
  > = {};

  // Build 7-day date keys
  const trendDates: string[] = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(
      Date.UTC(weekAgo.getUTCFullYear(), weekAgo.getUTCMonth(), weekAgo.getUTCDate() + i)
    );
    trendDates.push(d.toISOString().slice(0, 10));
  }

  for (const cat of ALL_CATS) {
    const trendMap: Record<string, { eating: number; drinking: number }> = {};
    for (const date of trendDates) {
      trendMap[date] = { eating: 0, drinking: 0 };
    }
    profileMap[cat] = {
      totalEating: 0,
      totalDrinking: 0,
      totalDuration: 0,
      durationCount: 0,
      lastSeen: null,
      trendMap,
    };
  }

  if (error) {
    console.error("getCatProfiles error:", error.message);
  } else if (data) {
    for (const row of data) {
      const name = row.cat_name;
      if (!name || !profileMap[name]) continue;

      const p = profileMap[name];

      if (row.activity === "eating") p.totalEating++;
      else if (row.activity === "drinking") p.totalDrinking++;

      if (row.duration_seconds != null) {
        p.totalDuration += row.duration_seconds;
        p.durationCount++;
      }

      // Since ordered DESC, first occurrence is most recent
      if (!p.lastSeen) p.lastSeen = row.started_at;

      // 7-day trend
      const dateKey = row.started_at.slice(0, 10);
      const trendEntry = p.trendMap[dateKey];
      if (trendEntry) {
        if (row.activity === "eating") trendEntry.eating++;
        else if (row.activity === "drinking") trendEntry.drinking++;
      }
    }
  }

  return ALL_CATS.map((name) => {
    const p = profileMap[name];
    return {
      name,
      headshot: CAT_HEADSHOTS[name] ?? "",
      totalEating: p.totalEating,
      totalDrinking: p.totalDrinking,
      avgDuration:
        p.durationCount > 0
          ? Math.round(p.totalDuration / p.durationCount)
          : 0,
      lastSeen: p.lastSeen,
      trend: trendDates.map((date) => ({
        date,
        eating: p.trendMap[date].eating,
        drinking: p.trendMap[date].drinking,
      })),
    };
  });
}
