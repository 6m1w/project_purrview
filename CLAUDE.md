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
│   │   │   ├── collect.py   # Data collection tool (RTMP → local frames)
│   │   │   ├── notifier.py  # Lark webhook notifications
│   │   │   └── digest.py    # Daily digest cron script
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   └── web/             # Next.js dashboard
│       ├── src/app/     # pages: landing, cats/, timeline/, reports/
│       └── package.json
├── scripts/
│   └── ec2-collect.sh   # EC2 data collection (setup/start/stop/status)
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

# Data collection (local)
cd apps/worker && .venv/bin/python -m src.collect --duration 3600 --interval 5

# Data collection (EC2)
./scripts/ec2-collect.sh setup   # first time
./scripts/ec2-collect.sh start   # 24h, 5s/frame
./scripts/ec2-collect.sh status  # check progress

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