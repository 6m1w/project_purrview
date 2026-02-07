# PurrView - Cat Feeding Monitor

## Project Overview
PurrView is a cat feeding monitoring system for 5 cats using an RTMP camera with OpenCV motion detection and Gemini multimodal AI for cat identification and food level estimation.

## Tech Stack
- **Stream Worker**: Python 3.12, ffmpeg, OpenCV, google-genai (Gemini 2.5 Flash)
- **Web Dashboard**: Next.js 15 (App Router), Tailwind CSS, shadcn/ui
- **Database**: Supabase (PostgreSQL + Storage) — shared project `project-kalshi` (ID: `odyholdlespkvyxvswrx`)
- **Deploy**: Worker on Cloud VPS (Docker), Web on Vercel

## Project Structure
```
project_purrview/
├── apps/
│   ├── worker/          # Python stream processing
│   │   ├── src/         # capture, detector, analyzer, tracker, storage, config, main
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   └── web/             # Next.js dashboard
│       ├── src/app/     # pages: landing, cats/, timeline/, reports/
│       └── package.json
├── supabase/migrations/ # SQL migration files
├── docs/PRD.md          # Product requirements (Chinese)
└── .env.example
```

## Project Rules
- All database tables use `purrview_` prefix (shared Supabase project)
- Supabase project ID: `odyholdlespkvyxvswrx`
- Supabase URL: `https://odyholdlespkvyxvswrx.supabase.co`
- Python code: type hints required, use Pydantic for data models
- Web code: TypeScript strict mode, use server components by default
- Tests: Python uses pytest, Web uses vitest

## Key Commands
```bash
# Worker
cd apps/worker && pip install -e ".[dev]"
cd apps/worker && pytest

# Web
cd apps/web && npm install
cd apps/web && npm run dev
cd apps/web && npm run build
```

## Database Tables
All tables prefixed with `purrview_`:
- `purrview_cats` — Cat profiles with reference photos
- `purrview_feeding_events` — Grouped feeding events
- `purrview_frames` — Key frames captured during events
- `purrview_food_bowls` — Food bowl ROI configuration
