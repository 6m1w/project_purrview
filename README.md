# PurrView

Cat feeding monitoring system using RTMP camera + OpenCV motion detection + Gemini AI analysis.

## Architecture

```
RTMP Camera → Stream Worker (Python) → Supabase → Web Dashboard (Next.js)
```

- **Stream Worker**: Extracts frames from RTMP, detects motion via OpenCV MOG2, analyzes with Gemini 2.5 Flash
- **Web Dashboard**: Cat profiles, feeding timeline, daily reports

## Quick Start

### Worker
```bash
cd apps/worker
pip install -e ".[dev]"
cp ../../.env.example .env  # fill in your values
python -m src.main
```

### Web
```bash
cd apps/web
npm install
cp ../../.env.example .env.local  # fill in your values
npm run dev
```

## Domain
[purrview.dev](https://purrview.dev)
