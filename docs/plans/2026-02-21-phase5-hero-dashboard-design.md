# Phase 5 Design: Hero Page + Dashboard

## Overview

Two pages with a unified pixel/scanline aesthetic:
- `/` — Hero landing page with Canvas scanline cat animation
- `/dashboard` — Real-time feeding data from Supabase

## Hero Page

### Layout
Split layout, full viewport height:
- **Left**: Title "PURRVIEW" (VT323 pixel font, large), subtitle (Space Mono), CTA button → /dashboard
- **Right**: `<ScanlineCanvas>` component rendering transparent-bg cat video with horizontal scan-line effect + mouse glitch interaction

### Visual Style
- Background: `#f4f4f0` (off-white)
- Scanlines: `#111` (black), thickness varies by pixel brightness
- Font: VT323 for headings, Space Mono for body
- Mouse hover: sine-wave jitter distortion within 120px radius
- Minimal nav bar: logo + links

### Video Pipeline
```
Cat photo → Seedance/Veo3 (pixel-glitch style, white bg)
→ remove_bg.py (brightness threshold → transparent WebM)
→ ScanlineCanvas (real-time Canvas rendering)
```

### ScanlineCanvas Component (Client)
Port from `index.html` into React:
- Props: `videoSrc`, `className`
- Uses `useRef` (canvas + video) + `useEffect` + `requestAnimationFrame`
- Config: stepY=7, stepX=3, maxThick=6.5, minThick=0.5, threshold=240
- Reads video alpha channel to skip transparent pixels
- Mouse interaction for glitch effect

## Dashboard Page

### Data Source
Supabase `purrview_feeding_events` table via server component queries.
Fields: `cat_name`, `activity` (eating/drinking), `started_at`, `duration_seconds`.

### Layout (4 sections)

#### 1. Metric Cards (grid, 4 columns)
| Card | Query |
|------|-------|
| Today's Feedings | `count(*) WHERE activity='eating' AND started_at >= today` |
| Active Cats | `count(DISTINCT cat_name) WHERE started_at >= today` |
| Water Events | `count(*) WHERE activity='drinking' AND started_at >= today` |
| Last Event | `MAX(started_at)` formatted as relative time |

#### 2. Weekly Trend Chart
Bar chart (recharts) showing daily feeding event counts for past 7 days.
Query: `GROUP BY date(started_at) WHERE started_at >= 7 days ago`

#### 3. Activity Log
Most recent 10 events with cat name, activity type icon, relative timestamp.
Query: `ORDER BY started_at DESC LIMIT 10`

#### 4. Cat Status Grid
Each of 5 cats with their last activity time and current status indicator.
Query: `DISTINCT ON (cat_name) ORDER BY started_at DESC`

### Visual Style
Same neo-brutalist aesthetic as current:
- Thick black borders (`border-4 border-black`)
- Blocky shadows (`shadow-[8px_8px_0_0_rgba(0,0,0,1)]`)
- VT323 headings, Space Mono body
- Accent colors: `#00FF66` (positive), `#FF5722` (alert)

## Technical Changes

### New Files
- `src/components/ScanlineCanvas.tsx` — Canvas scanline renderer (client component)
- `src/app/dashboard/page.tsx` — Dashboard with real Supabase data
- `src/lib/queries.ts` — Supabase query functions

### Modified Files
- `src/app/page.tsx` — Replace current content with Hero-only page
- `src/app/layout.tsx` — Simplify nav for hero, full nav for dashboard
- `src/lib/supabase.ts` — Lazy init pattern (avoid module-level side effects)
- `src/lib/types.ts` — Add `activity`, `cat_name`, `duration_seconds` fields

### Removed
- `src/lib/mock.ts` — No longer needed (real data)
- `src/components/dashboard/Hero.tsx` — Replaced by new hero in page.tsx
