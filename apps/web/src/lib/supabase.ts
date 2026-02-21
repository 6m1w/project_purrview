import { createClient, SupabaseClient } from "@supabase/supabase-js";
import type { Database } from "./types";

let client: SupabaseClient<Database> | null = null;

export function getSupabase(): SupabaseClient<Database> {
  if (!client) {
    const url = process.env.SUPABASE_URL!;
    const key = process.env.SUPABASE_KEY!;
    client = createClient<Database>(url, key);
  }
  return client;
}
