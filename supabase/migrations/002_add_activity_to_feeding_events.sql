-- Phase 4.3: Add activity classification to feeding events
-- Supports new per-cat session tracking (eating/drinking)

-- Activity type for the feeding session
alter table purrview_feeding_events add column activity text;

-- Denormalized cat name for convenience (avoids join for simple queries)
alter table purrview_feeding_events add column cat_name text;

-- Pre-computed duration in seconds
alter table purrview_feeding_events add column duration_seconds float;

-- Index for activity-based queries
create index idx_purrview_feeding_events_activity on purrview_feeding_events(activity);

-- Note: bowl_id, food_level_before, food_level_after, estimated_portion are kept
-- but no longer populated by the new full-frame pipeline.
-- They can be removed in a future cleanup migration.
