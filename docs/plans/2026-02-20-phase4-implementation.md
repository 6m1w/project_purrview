# Phase 4.1 + 4.2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rewrite analyzer.py and tracker.py for full-frame per-cat session tracking, verified with offline replay.

**Architecture:** Full-frame Gemini analysis returns per-cat activities. SessionTracker maintains independent state machines per cat. Schemas shared between eval and production via analyzer.py.

**Tech Stack:** Python 3.12, google-genai, Pydantic v2, pytest

---

### Task 1: Extract shared schema to analyzer.py

Move `Activity`, `CatActivity`, `IdentifyResult`, `CAT_NAMES`, `CAT_DESCRIPTIONS` from `eval_identify.py` to `analyzer.py`. Update `eval_identify.py` to import from `analyzer`. This establishes the single source of truth.

**Files:**
- Rewrite: `apps/worker/src/analyzer.py`
- Modify: `apps/worker/src/eval_identify.py` (lines 33-69, remove schema + constants)
- Test: `apps/worker/tests/test_analyzer.py` (new)

**Step 1: Write test for shared schema imports**

```python
# tests/test_analyzer.py
"""Tests for analyzer module."""

from src.analyzer import (
    Activity,
    CatActivity,
    IdentifyResult,
    CAT_NAMES,
    CAT_DESCRIPTIONS,
)


class TestSchema:
    def test_activity_enum_values(self):
        assert Activity.EATING.value == "eating"
        assert Activity.DRINKING.value == "drinking"
        assert Activity.PRESENT.value == "present"

    def test_cat_activity_model(self):
        ca = CatActivity(name="大吉", activity=Activity.EATING)
        assert ca.name == "大吉"
        assert ca.activity == Activity.EATING

    def test_identify_result_from_json(self):
        data = {
            "cats_present": True,
            "cats": [{"name": "大吉", "activity": "eating"}],
            "description": "test",
            "confidence": 0.95,
        }
        result = IdentifyResult.model_validate(data)
        assert result.cats_present is True
        assert len(result.cats) == 1
        assert result.cats[0].name == "大吉"
        assert result.cats[0].activity == Activity.EATING

    def test_identify_result_empty_cats(self):
        result = IdentifyResult(cats_present=False, confidence=0.0)
        assert result.cats == []

    def test_cat_names_has_five_cats(self):
        assert len(CAT_NAMES) == 5

    def test_cat_descriptions_match_names(self):
        for name in CAT_NAMES:
            assert name in CAT_DESCRIPTIONS
```

**Step 2: Run test — expect FAIL** (old analyzer.py has `FrameAnalysis`, not these classes)

```bash
cd apps/worker && python -m pytest tests/test_analyzer.py -v
```

**Step 3: Rewrite `analyzer.py`** — move schema from eval, add `CatAnalyzer` with ref loading + prompt

```python
# src/analyzer.py
"""Gemini multimodal analyzer: cat identification + activity classification.

Shared schema (Activity, CatActivity, IdentifyResult) used by both
the real-time pipeline and the eval script.
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types
from pydantic import BaseModel, Field


# --- Shared structured output schema ---

class Activity(str, Enum):
    EATING = "eating"
    DRINKING = "drinking"
    PRESENT = "present"


class CatActivity(BaseModel):
    """Per-cat identification with activity classification."""
    name: str = Field(description="Cat name (from known cats only)")
    activity: Activity = Field(description="What this cat is doing")


class IdentifyResult(BaseModel):
    """Gemini response for cat identification in a single frame."""
    cats_present: bool = Field(description="Whether one or more cats are visible")
    cats: list[CatActivity] = Field(
        default_factory=list,
        description="Per-cat identification with activity",
    )
    description: Optional[str] = Field(None, description="Brief description of the scene")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Overall identification confidence")


# --- Constants ---

CAT_NAMES = ["大吉", "小慢", "小黑", "麻酱", "松花"]

CAT_DESCRIPTIONS: dict[str, str] = {
    "大吉": "Orange/ginger cat with white patches. Light-colored, medium-large build.",
    "小慢": "Calico cat with distinct patches of orange, black and white. Medium build.",
    "小黑": "Solid black cat. Sleek, medium build.",
    "麻酱": "Tortoiseshell cat with a dark mix of black and brown/amber mottled pattern. No stripes.",
    "松花": "Brown tabby cat with visible dark stripes/mackerel pattern. Lighter than 麻酱.",
}


# --- Reference photo loading ---

def load_reference_images(refs_dir: Path) -> dict[str, list[bytes]]:
    """Load reference images from a directory with refs.json index.

    Expected layout:
        refs_dir/
        ├── refs.json     # {cat_name: [filename, ...]}
        ├── image1.jpg
        └── ...

    Returns:
        {cat_name: [jpeg_bytes, ...]}
    """
    refs_path = refs_dir / "refs.json"
    if not refs_path.exists():
        raise FileNotFoundError(f"refs.json not found in {refs_dir}")

    index: dict[str, list[str]] = json.loads(refs_path.read_text())
    images: dict[str, list[bytes]] = {}
    for cat_name, filenames in index.items():
        images[cat_name] = []
        for fn in filenames:
            img_path = refs_dir / fn
            if img_path.exists():
                images[cat_name].append(img_path.read_bytes())
            else:
                print(f"[analyzer] WARNING: ref image missing: {img_path}")
    return images


# --- Prompt building ---

def build_identify_prompt(
    ref_images: dict[str, list[bytes]],
    test_image: bytes,
) -> list:
    """Build multimodal few-shot prompt with reference images and test frame."""
    parts: list = []

    parts.append(
        "You are a cat identification system. A fixed camera monitors a feeding area. "
        "The layout from left to right: water dispenser (white round device) → 3 food bowls with kibble. "
        "There are 5 known cats. Identify which cat(s) appear in the test image.\n\n"
        "Rules:\n"
        "- Only return names from the list below\n"
        "- A frame may have 0, 1, or multiple cats\n"
        "- Check edges of the image for partially visible cats\n"
        "- For each cat, classify their activity:\n"
        '  - "eating" if eating from a food bowl (center/right bowls)\n'
        '  - "drinking" if drinking from the water dispenser (white round device on the left)\n'
        '  - "present" if visible but not eating or drinking (sitting, walking, looking)\n\n'
        "Known cats and their reference photos:\n"
    )

    for cat_name in CAT_NAMES:
        images = ref_images.get(cat_name, [])
        if not images:
            continue
        desc = CAT_DESCRIPTIONS.get(cat_name, "")
        parts.append(f"\n{cat_name} — {desc}\n")
        for img_bytes in images:
            parts.append(types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))

    parts.append("\n\nTEST IMAGE — identify the cat(s):\n")
    parts.append(types.Part.from_bytes(data=test_image, mime_type="image/jpeg"))

    return parts


# --- Analyzer ---

class CatAnalyzer:
    """Analyzes camera frames using Gemini to identify cats and classify activity."""

    def __init__(self, api_key: str, refs_dir: Path, model: str = "gemini-2.5-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.ref_images = load_reference_images(refs_dir)
        loaded = sum(len(imgs) for imgs in self.ref_images.values())
        print(f"[analyzer] Loaded {loaded} reference images for {len(self.ref_images)} cats")

    def analyze_frame(self, frame_bytes: bytes) -> IdentifyResult:
        """Analyze a single frame for cat presence, identity, and activity.

        Args:
            frame_bytes: JPEG-encoded full frame

        Returns:
            IdentifyResult with per-cat identification and activity
        """
        prompt = build_identify_prompt(self.ref_images, frame_bytes)
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=IdentifyResult,
                temperature=0.1,
            ),
        )
        return IdentifyResult.model_validate_json(response.text)
```

**Step 4: Update `eval_identify.py`** — remove schema/constants, import from analyzer

Replace the schema section (lines 33-69) with imports:

```python
# At the top of eval_identify.py, replace local schema with:
from .analyzer import (
    Activity,
    CatActivity,
    IdentifyResult,
    CAT_NAMES,
    CAT_DESCRIPTIONS,
    build_identify_prompt,
)
```

Remove the local `Activity`, `CatActivity`, `IdentifyResult`, `CAT_NAMES`, `CAT_DESCRIPTIONS` definitions and the local `build_identify_prompt` function. Keep eval-only code: `_DRINKING_PATTERN`, `_EATING_PATTERN`, `REFS_PER_CAT`, `select_references`, `parse_activity_labels`, etc.

**Step 5: Run tests**

```bash
cd apps/worker && python -m pytest tests/test_analyzer.py -v
```

Expected: all 7 tests PASS.

**Step 6: Verify eval still works**

```bash
cd apps/worker && python -m src.eval_identify --date 2026-02-10 --dry-run
```

Expected: same output as before (activity labels, ref selection, test set distribution).

**Step 7: Commit**

```bash
git add apps/worker/src/analyzer.py apps/worker/src/eval_identify.py apps/worker/tests/test_analyzer.py
git commit -m "refactor: extract shared schema to analyzer.py, rewrite with eval-proven prompt"
```

---

### Task 2: Rewrite tracker.py with per-cat session state machine

Replace the per-bowl `FeedingTracker` with per-cat `SessionTracker`.

**Files:**
- Rewrite: `apps/worker/src/tracker.py`
- Rewrite: `apps/worker/tests/test_tracker.py`

**Step 1: Write tests for SessionTracker**

```python
# tests/test_tracker.py
"""Tests for per-cat session tracker."""

import pytest

from src.analyzer import Activity, CatActivity, IdentifyResult
from src.tracker import FeedingSession, SessionTracker


@pytest.fixture
def tracker():
    return SessionTracker(idle_timeout=10)  # short timeout for tests


def _result(cats: list[tuple[str, str]], confidence: float = 0.95) -> IdentifyResult:
    """Helper to build IdentifyResult from (name, activity) tuples."""
    return IdentifyResult(
        cats_present=len(cats) > 0,
        cats=[CatActivity(name=n, activity=Activity(a)) for n, a in cats],
        confidence=confidence,
    )


class TestSessionStart:
    def test_eating_starts_session(self, tracker):
        completed = tracker.on_analysis(_result([("大吉", "eating")]), timestamp=100.0)
        assert completed == []
        assert "大吉" in tracker.sessions
        assert tracker.sessions["大吉"].activity == "eating"

    def test_drinking_starts_session(self, tracker):
        tracker.on_analysis(_result([("小黑", "drinking")]), timestamp=100.0)
        assert "小黑" in tracker.sessions
        assert tracker.sessions["小黑"].activity == "drinking"

    def test_present_does_not_start_session(self, tracker):
        tracker.on_analysis(_result([("大吉", "present")]), timestamp=100.0)
        assert "大吉" not in tracker.sessions


class TestSessionUpdate:
    def test_same_activity_updates_last_seen(self, tracker):
        tracker.on_analysis(_result([("大吉", "eating")]), timestamp=100.0)
        tracker.on_analysis(_result([("大吉", "eating")]), timestamp=110.0)
        assert tracker.sessions["大吉"].last_seen_at == 110.0

    def test_present_keeps_session_alive(self, tracker):
        tracker.on_analysis(_result([("大吉", "eating")]), timestamp=100.0)
        tracker.on_analysis(_result([("大吉", "present")]), timestamp=105.0)
        assert "大吉" in tracker.sessions
        assert tracker.sessions["大吉"].last_seen_at == 105.0
        assert tracker.sessions["大吉"].activity == "eating"  # unchanged


class TestSessionEnd:
    def test_idle_timeout_ends_session(self, tracker):
        tracker.on_analysis(_result([("大吉", "eating")]), timestamp=100.0)
        completed = tracker.check_idle(now=115.0)  # 15s > 10s timeout
        assert len(completed) == 1
        assert completed[0].cat_name == "大吉"
        assert completed[0].activity == "eating"
        assert "大吉" not in tracker.sessions

    def test_no_timeout_if_recent(self, tracker):
        tracker.on_analysis(_result([("大吉", "eating")]), timestamp=100.0)
        completed = tracker.check_idle(now=105.0)  # 5s < 10s timeout
        assert completed == []
        assert "大吉" in tracker.sessions

    def test_activity_change_ends_old_starts_new(self, tracker):
        tracker.on_analysis(_result([("大吉", "eating")]), timestamp=100.0)
        completed = tracker.on_analysis(_result([("大吉", "drinking")]), timestamp=110.0)
        assert len(completed) == 1
        assert completed[0].activity == "eating"
        assert tracker.sessions["大吉"].activity == "drinking"


class TestMultiCat:
    def test_two_cats_independent_sessions(self, tracker):
        tracker.on_analysis(
            _result([("大吉", "eating"), ("小黑", "drinking")]),
            timestamp=100.0,
        )
        assert "大吉" in tracker.sessions
        assert "小黑" in tracker.sessions
        assert tracker.sessions["大吉"].activity == "eating"
        assert tracker.sessions["小黑"].activity == "drinking"

    def test_one_cat_ends_other_continues(self, tracker):
        tracker.on_analysis(
            _result([("大吉", "eating"), ("小黑", "drinking")]),
            timestamp=100.0,
        )
        # Only 大吉 continues
        tracker.on_analysis(_result([("大吉", "eating")]), timestamp=108.0)
        # 小黑 times out
        completed = tracker.check_idle(now=115.0)
        assert len(completed) == 1
        assert completed[0].cat_name == "小黑"
        assert "大吉" in tracker.sessions


class TestFeedingSession:
    def test_session_tracks_frames(self, tracker):
        tracker.on_analysis(
            _result([("大吉", "eating")]),
            timestamp=100.0,
            frame_info={"filename": "frame1.jpg"},
        )
        tracker.on_analysis(
            _result([("大吉", "eating")]),
            timestamp=105.0,
            frame_info={"filename": "frame2.jpg"},
        )
        session = tracker.sessions["大吉"]
        assert len(session.frames) == 2
        assert session.frames[0]["filename"] == "frame1.jpg"

    def test_session_duration(self, tracker):
        tracker.on_analysis(_result([("大吉", "eating")]), timestamp=100.0)
        tracker.on_analysis(_result([("大吉", "eating")]), timestamp=160.0)
        session = tracker.sessions["大吉"]
        assert session.last_seen_at - session.started_at == 60.0
```

**Step 2: Run tests — expect FAIL**

```bash
cd apps/worker && python -m pytest tests/test_tracker.py -v
```

**Step 3: Implement tracker.py**

```python
# src/tracker.py
"""Per-cat feeding session tracker.

Groups Gemini analysis results into feeding/drinking sessions.
Each cat is tracked independently with a simple state machine:
IDLE → IN_SESSION (on eating/drinking) → IDLE (after timeout).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .analyzer import Activity, IdentifyResult


@dataclass
class FeedingSession:
    """A feeding or drinking session for a single cat."""
    cat_name: str
    activity: str                       # "eating" or "drinking"
    started_at: float                   # unix timestamp
    last_seen_at: float                 # unix timestamp
    frames: list[dict] = field(default_factory=list)


class SessionTracker:
    """Tracks per-cat feeding/drinking sessions.

    Rules:
    - eating/drinking → starts or continues a session
    - present → keeps existing session alive (resets idle timer) but doesn't start one
    - activity change (eating→drinking) → ends old session, starts new one
    - 60s no detection → session ends
    """

    def __init__(self, idle_timeout: int = 60):
        self.idle_timeout = idle_timeout
        self.sessions: dict[str, FeedingSession] = {}  # cat_name → active session

    def on_analysis(
        self,
        result: IdentifyResult,
        timestamp: float,
        frame_info: dict | None = None,
    ) -> list[FeedingSession]:
        """Process a Gemini analysis result. Returns list of completed sessions.

        Args:
            result: Gemini IdentifyResult with per-cat activities
            timestamp: Frame timestamp (unix seconds)
            frame_info: Optional dict with frame metadata (filename, etc.)
        """
        completed: list[FeedingSession] = []

        for cat in result.cats:
            name = cat.name
            activity = cat.activity

            existing = self.sessions.get(name)

            if activity in (Activity.EATING, Activity.DRINKING):
                if existing and existing.activity != activity.value:
                    # Activity changed — end old session, start new one
                    completed.append(existing)
                    del self.sessions[name]
                    existing = None

                if existing:
                    # Continue existing session
                    existing.last_seen_at = timestamp
                    if frame_info:
                        existing.frames.append(frame_info)
                else:
                    # Start new session
                    session = FeedingSession(
                        cat_name=name,
                        activity=activity.value,
                        started_at=timestamp,
                        last_seen_at=timestamp,
                    )
                    if frame_info:
                        session.frames.append(frame_info)
                    self.sessions[name] = session

            elif activity == Activity.PRESENT and existing:
                # Present keeps session alive but doesn't start one
                existing.last_seen_at = timestamp

        return completed

    def check_idle(self, now: float) -> list[FeedingSession]:
        """Check for sessions that have timed out. Returns completed sessions."""
        completed: list[FeedingSession] = []
        for name in list(self.sessions):
            session = self.sessions[name]
            if (now - session.last_seen_at) > self.idle_timeout:
                completed.append(session)
                del self.sessions[name]
        return completed
```

**Step 4: Run tests**

```bash
cd apps/worker && python -m pytest tests/test_tracker.py -v
```

Expected: all 12 tests PASS.

**Step 5: Commit**

```bash
git add apps/worker/src/tracker.py apps/worker/tests/test_tracker.py
git commit -m "feat: rewrite tracker with per-cat session state machine"
```

---

### Task 3: Update config.py and set up refs directory

Add `refs_dir` setting and update `idle_timeout` default. Copy reference photos into a standalone `data/refs/` directory.

**Files:**
- Modify: `apps/worker/src/config.py` (add `refs_dir`, change `idle_timeout` default)
- Create: `apps/worker/data/refs/` (copy refs from 2026-02-10 data + refs.json)

**Step 1: Update config.py**

In `Settings` class, change:
```python
idle_timeout: int = Field(60, description="Seconds of no activity to end feeding session")
refs_dir: str = Field("data/refs", description="Directory with reference photos and refs.json")
```

**Step 2: Set up refs directory**

```bash
cd apps/worker
mkdir -p data/refs
cp data/2026-02-10/refs.json data/refs/
# Copy all referenced images
python3 -c "
import json
refs = json.load(open('data/refs/refs.json'))
for cat, files in refs.items():
    for f in files:
        import shutil
        shutil.copy(f'data/2026-02-10/{f}', f'data/refs/{f}')
print('Done')
"
```

**Step 3: Verify ref loading works**

```bash
cd apps/worker && python3 -c "
from pathlib import Path
from src.analyzer import load_reference_images
imgs = load_reference_images(Path('data/refs'))
for cat, photos in imgs.items():
    print(f'{cat}: {len(photos)} photos, {sum(len(p) for p in photos)} bytes')
"
```

**Step 4: Commit**

```bash
git add apps/worker/src/config.py
git commit -m "chore: add refs_dir config, reduce idle_timeout to 60s"
```

Note: `data/refs/` is in `.gitignore` (binary images), so only config.py is committed.

---

### Task 4: Create replay.py for offline verification

**Files:**
- Create: `apps/worker/src/replay.py`

**Step 1: Implement replay.py**

```python
# src/replay.py
"""Offline replay: run analyzer + tracker on captured data to verify sessions.

Usage:
    cd apps/worker
    python -m src.replay --date 2026-02-10 --limit 20    # quick test
    python -m src.replay --date 2026-02-10                # full day
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from .analyzer import CatAnalyzer, IdentifyResult
from .label import _load_api_key
from .tracker import SessionTracker


def replay(
    date: str,
    output_dir: str = "data",
    refs_dir: str = "data/refs",
    limit: int = 0,
    idle_timeout: int = 60,
    cooldown: int = 30,
    model: str = "gemini-2.5-flash",
) -> None:
    """Replay captured frames through analyzer + tracker."""
    date_dir = Path(output_dir) / date
    meta_path = date_dir / "gallery_meta.jsonl"

    if not meta_path.exists():
        print(f"[replay] Error: {meta_path} not found")
        sys.exit(1)

    # Load metadata, filter to motion frames
    entries: list[dict] = []
    with open(meta_path) as f:
        for line in f:
            if line.strip():
                e = json.loads(line)
                if e.get("motion_score", 0) > 5000:
                    entries.append(e)

    entries.sort(key=lambda e: e["timestamp"])
    print(f"[replay] Date: {date}, motion frames: {len(entries)}")

    if limit > 0:
        entries = entries[:limit]
        print(f"[replay] Limited to {limit} frames")

    # Init analyzer
    api_key = _load_api_key()
    analyzer = CatAnalyzer(api_key=api_key, refs_dir=Path(refs_dir), model=model)
    tracker = SessionTracker(idle_timeout=idle_timeout)

    all_completed: list = []
    last_call = 0.0
    errors = 0

    for i, entry in enumerate(entries):
        fname = entry["filename"]
        img_path = date_dir / fname
        if not img_path.exists():
            continue

        # Parse timestamp to unix seconds
        ts = datetime.fromisoformat(entry["timestamp"]).timestamp()

        # Check idle before each frame (using frame timestamp, not wall clock)
        completed = tracker.check_idle(now=ts)
        all_completed.extend(completed)
        for s in completed:
            _print_session(s, tag="END")

        # Apply cooldown (based on frame timestamps)
        if (ts - last_call) < cooldown:
            continue
        last_call = ts

        # Analyze frame
        frame_bytes = img_path.read_bytes()
        try:
            result = analyzer.analyze_frame(frame_bytes)
            cats_str = ", ".join(f"{c.name}:{c.activity.value}" for c in result.cats) or "(none)"
            print(f"  [{i+1}/{len(entries)}] {fname} → {cats_str}")

            completed = tracker.on_analysis(
                result, timestamp=ts, frame_info={"filename": fname, "timestamp": ts}
            )
            all_completed.extend(completed)
            for s in completed:
                _print_session(s, tag="END")

        except Exception as exc:
            errors += 1
            print(f"  [{i+1}/{len(entries)}] ERR {fname}: {exc}")

        time.sleep(0.3)  # rate limit

    # Flush remaining sessions
    final = tracker.check_idle(now=float("inf"))
    all_completed.extend(final)
    for s in final:
        _print_session(s, tag="END")

    # Summary
    print(f"\n{'='*60}")
    print(f"[replay] Sessions detected: {len(all_completed)}")
    print(f"[replay] Errors: {errors}")
    for s in all_completed:
        duration = s.last_seen_at - s.started_at
        print(f"  {s.cat_name:<6} {s.activity:<10} {duration:>5.0f}s  ({len(s.frames)} frames)")


def _print_session(session, tag: str = "") -> None:
    """Print a session event."""
    duration = session.last_seen_at - session.started_at
    print(f"  [{tag}] {session.cat_name} {session.activity} ({duration:.0f}s, {len(session.frames)} frames)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay captured data through analyzer + tracker")
    parser.add_argument("--date", required=True, help="Date directory (YYYY-MM-DD)")
    parser.add_argument("--output", default="data", help="Base data directory")
    parser.add_argument("--refs", default="data/refs", help="Reference photos directory")
    parser.add_argument("--limit", type=int, default=0, help="Max frames (0=all)")
    parser.add_argument("--idle-timeout", type=int, default=60, help="Session idle timeout (seconds)")
    parser.add_argument("--cooldown", type=int, default=30, help="Seconds between Gemini calls")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Gemini model")
    args = parser.parse_args()
    replay(args.date, args.output, args.refs, args.limit, args.idle_timeout, args.cooldown, args.model)


if __name__ == "__main__":
    main()
```

**Step 2: Smoke test with a small limit**

```bash
cd apps/worker && python -m src.replay --date 2026-02-10 --limit 10
```

Expected: 10 motion frames analyzed, sessions printed.

**Step 3: Commit**

```bash
git add apps/worker/src/replay.py
git commit -m "feat: add offline replay script for analyzer + tracker verification"
```

---

### Task 5: Full replay verification

Run full replay on 2026-02-10 data and sanity-check sessions.

**Step 1: Run full replay**

```bash
cd apps/worker && python -m src.replay --date 2026-02-10
```

**Step 2: Verify eval still works with shared schema**

```bash
cd apps/worker && python -m src.eval_identify --date 2026-02-10 --dry-run
```

Expected: same output as before — activity labels, ref selection, distributions all unchanged.

**Step 3: Run all tests**

```bash
cd apps/worker && python -m pytest tests/ -v
```

Expected: `test_analyzer.py` (7 pass), `test_tracker.py` (12 pass), existing tests may need updating if they import old `FrameAnalysis`.

Note: `test_detector.py` and `test_notifier.py` should be unaffected. If `test_tracker.py` (old) still exists, it was replaced in Task 2.

**Step 4: Final commit if any fixups needed**

```bash
git add -A && git commit -m "fix: post-replay verification fixups"
```
