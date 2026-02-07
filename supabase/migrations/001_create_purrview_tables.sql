-- PurrView: Cat Feeding Monitor tables
-- All tables prefixed with purrview_ to avoid conflicts in shared project

-- Cat profiles
create table purrview_cats (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  description text,
  reference_photos text[],
  created_at timestamptz default now()
);

-- Food bowl ROI configuration
create table purrview_food_bowls (
  id text primary key,
  name text,
  roi_x1 int, roi_y1 int,
  roi_x2 int, roi_y2 int,
  is_active boolean default true
);

-- Feeding events (grouped from multiple frames)
create table purrview_feeding_events (
  id uuid primary key default gen_random_uuid(),
  cat_id uuid references purrview_cats(id),
  bowl_id text references purrview_food_bowls(id),
  started_at timestamptz not null,
  ended_at timestamptz,
  food_level_before text,
  food_level_after text,
  estimated_portion text,
  confidence float,
  notes text,
  created_at timestamptz default now()
);

-- Key frames captured during events
create table purrview_frames (
  id uuid primary key default gen_random_uuid(),
  feeding_event_id uuid references purrview_feeding_events(id),
  captured_at timestamptz not null,
  frame_url text not null,
  analysis jsonb,
  created_at timestamptz default now()
);

-- Indexes for common queries
create index idx_purrview_feeding_events_cat_id on purrview_feeding_events(cat_id);
create index idx_purrview_feeding_events_started_at on purrview_feeding_events(started_at desc);
create index idx_purrview_frames_event_id on purrview_frames(feeding_event_id);

-- Enable RLS
alter table purrview_cats enable row level security;
alter table purrview_food_bowls enable row level security;
alter table purrview_feeding_events enable row level security;
alter table purrview_frames enable row level security;

-- Public read policies (dashboard is read-only for now)
create policy "Allow public read on purrview_cats" on purrview_cats for select using (true);
create policy "Allow public read on purrview_food_bowls" on purrview_food_bowls for select using (true);
create policy "Allow public read on purrview_feeding_events" on purrview_feeding_events for select using (true);
create policy "Allow public read on purrview_frames" on purrview_frames for select using (true);

-- Service role insert/update (worker uses service_role key)
create policy "Allow service insert on purrview_cats" on purrview_cats for insert with check (true);
create policy "Allow service update on purrview_cats" on purrview_cats for update using (true);
create policy "Allow service insert on purrview_food_bowls" on purrview_food_bowls for insert with check (true);
create policy "Allow service update on purrview_food_bowls" on purrview_food_bowls for update using (true);
create policy "Allow service insert on purrview_feeding_events" on purrview_feeding_events for insert with check (true);
create policy "Allow service update on purrview_feeding_events" on purrview_feeding_events for update using (true);
create policy "Allow service insert on purrview_frames" on purrview_frames for insert with check (true);
