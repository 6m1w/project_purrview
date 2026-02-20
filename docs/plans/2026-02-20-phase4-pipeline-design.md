# Phase 4: Real-time Pipeline Design

## Overview

Connect the Gemini cat ID + activity classification (validated in Phase 3 eval at 92.8% cat ID, 73.7% activity) into a real-time feeding session tracker.

**Scope**: Steps 4.1 (analyzer) + 4.2 (tracker) + offline replay verification.
**Not in scope**: DB writes, Lark notifications, main.py integration (those are 4.3–4.7).

## Architecture Decision: Full-Frame Mode

**Old design** (Phase 1 skeleton): per-bowl ROI motion detection → per-bowl Gemini calls → per-bowl tracking.

**New design**: full-frame motion detection → single Gemini call per frame → per-cat session tracking.

Rationale:
- Eval proved full-frame identification works (92.8% accuracy)
- No need to calibrate bowl ROI coordinates
- Single Gemini call handles multi-cat frames naturally
- Simpler architecture, fewer API calls

## Schema: Reuse Eval's IdentifyResult

```python
class Activity(str, Enum):
    EATING = "eating"
    DRINKING = "drinking"
    PRESENT = "present"

class CatActivity(BaseModel):
    name: str           # cat name from known cats
    activity: Activity  # what this cat is doing

class IdentifyResult(BaseModel):
    cats_present: bool
    cats: list[CatActivity]
    description: Optional[str]
    confidence: float
```

This schema is shared between eval and production analyzer.

## Component: analyzer.py (Rewrite)

Replace the old `FrameAnalysis`/`CatAnalyzer` with eval-proven prompt and schema.

### Key changes from skeleton:
- Schema: `FrameAnalysis` → `IdentifyResult` (from eval)
- Prompt: Add activity classification rules + camera layout description
- Reference photos: Load from local `data/refs/` directory at startup
- No per-bowl concept — single full-frame analysis per call

### Reference photo loading:
```
data/refs/
├── refs.json          # {cat_name: [filename, ...]}
├── 大吉_01.jpg
├── 大吉_02.jpg
├── 小慢_01.jpg
└── ...
```

Startup: read refs.json, load all images into memory (~15 images × ~100KB = ~1.5MB).

## Component: tracker.py (Rewrite)

Per-cat independent state machine. Each cat tracked separately.

### States

```
IDLE ─── activity=eating/drinking ──→ IN_SESSION
  ↑                                       │
  │     60s no eating/drinking             │
  └────────────────────────────────────────┘
```

- `IDLE`: No active session for this cat
- `IN_SESSION`: Cat has an ongoing feeding/drinking session

### Session lifecycle

| Event | Action |
|-------|--------|
| Cat detected with `eating` or `drinking` | If IDLE → start new session. If IN_SESSION with same activity → update `last_seen`. If IN_SESSION with different activity → end old session, start new one. |
| Cat detected with `present` | If IN_SESSION → update `last_seen` (keeps session alive, cat still nearby). If IDLE → ignore (no session started). |
| Cat not detected for 60s | End session, emit completed event. |

### Data model

```python
@dataclass
class FeedingSession:
    cat_name: str
    activity: str              # "eating" or "drinking"
    started_at: float          # unix timestamp
    last_seen_at: float        # unix timestamp
    frames: list[dict]         # [{timestamp, filename, analysis}, ...]

class SessionTracker:
    sessions: dict[str, FeedingSession]  # cat_name → active session
    idle_timeout: int = 60

    def on_analysis(self, result: IdentifyResult, timestamp: float, frame_info: dict) -> list[FeedingSession]:
        """Process a Gemini result. Returns list of completed sessions."""

    def check_idle(self, now: float) -> list[FeedingSession]:
        """Check for sessions that have timed out. Returns completed sessions."""
```

### Design decisions

1. **`present` keeps session alive** — If a cat is eating, then stands up but stays nearby (`present`), we don't want to end the session immediately. The 60s idle timer resets on any detection of that cat.

2. **Activity change = new session** — If 大吉 switches from `eating` to `drinking`, that's two separate sessions. This matches the PRD's "event_type" distinction.

3. **60s timeout** (down from 120s) — Data shows most frame gaps are 5s. 60s of no detection is a strong signal the cat has left. This reduces phantom long sessions.

## Component: replay.py (New)

Offline replay script to validate analyzer + tracker using existing captured data.

```bash
# Test with captured frames (calls Gemini API)
python -m src.replay --date 2026-02-10 --limit 50

# Output: detected sessions with start/end times, cat names, activities
```

Flow:
1. Load frames from `data/{date}/` sorted by timestamp
2. Filter to motion frames only (motion_score > 5000)
3. Apply cooldown (30s between Gemini calls)
4. Feed each Gemini result into SessionTracker
5. Print detected sessions

## config.py Changes

| Setting | Old default | New default | Notes |
|---------|-------------|-------------|-------|
| `idle_timeout` | 120 | 60 | Shorter based on data analysis |
| `refs_dir` | (new) | `data/refs` | Reference photos directory |

## File Change Summary

| File | Action | Size estimate |
|------|--------|---------------|
| `src/analyzer.py` | Rewrite | ~100 lines |
| `src/tracker.py` | Rewrite | ~120 lines |
| `src/replay.py` | New | ~80 lines |
| `src/config.py` | Minor edit | +2 fields |
| `src/eval_identify.py` | Extract shared schema | Move Activity/CatActivity/IdentifyResult to analyzer.py, import from there |

## Verification Plan

1. `python -m src.replay --date 2026-02-10 --limit 20` — quick smoke test
2. `python -m src.replay --date 2026-02-10` — full day, inspect sessions
3. Compare detected sessions against known feeding patterns in the data
4. Verify eval still works after schema extraction: `python -m src.eval_identify --date 2026-02-10 --dry-run`
