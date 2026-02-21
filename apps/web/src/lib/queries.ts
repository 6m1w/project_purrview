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
