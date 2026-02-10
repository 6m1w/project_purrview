"""Offline batch labeling: detect cats in collected frames using Gemini.

Usage:
    cd apps/worker
    python -m src.label --date 2026-02-09               # label all motion frames
    python -m src.label --date 2026-02-09 --limit 50    # label first 50 unlabeled
    python -m src.label --date 2026-02-09 --dry-run     # preview without API calls
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types
from pydantic import BaseModel, Field


# --- Structured output schema ---

class FrameLabel(BaseModel):
    """Gemini response for cat detection in a single frame."""
    cat_detected: bool = Field(description="Whether one or more cats are visible")
    cat_count: int = Field(0, description="Number of cats visible")
    cat_description: Optional[str] = Field(None, description="Brief description of what cats are doing")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Detection confidence")


# --- Constants ---

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_ENV_FILE = _PROJECT_ROOT / ".env"
_PROMPT = (
    "You are analyzing a frame from a fixed camera pointed at cat food bowls. "
    "Determine if there are any cats visible in the image. "
    "Be precise: only mark cat_detected=true if you can clearly see a cat (whole body or partial). "
    "Do not count shadows, reflections, or ambiguous shapes as cats. "
    "If cats are present, briefly describe what they are doing (e.g. 'eating from bowl', 'walking past', 'sitting nearby')."
)


def _load_api_key() -> str:
    """Load GEMINI_API_KEY from environment or .env file."""
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    if _ENV_FILE.exists():
        for line in _ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    print("[label] Error: GEMINI_API_KEY not found in env or .env file")
    sys.exit(1)


def label_frame(client: genai.Client, model: str, image_bytes: bytes) -> FrameLabel:
    """Send a single frame to Gemini for cat detection."""
    response = client.models.generate_content(
        model=model,
        contents=[
            _PROMPT,
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=FrameLabel,
            temperature=0.1,
        ),
    )
    return FrameLabel.model_validate_json(response.text)


def run_labeling(
    date: str,
    output_dir: str = "data",
    limit: int = 0,
    dry_run: bool = False,
    model: str = "gemini-2.5-flash",
    min_score: int = 5000,
) -> None:
    """Label motion frames in a date directory with cat detection."""
    date_dir = Path(output_dir) / date
    meta_path = date_dir / "gallery_meta.jsonl"

    if not meta_path.exists():
        print(f"[label] Error: {meta_path} not found")
        sys.exit(1)

    # Read all entries
    entries: list[dict] = []
    with open(meta_path) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))

    # Find unlabeled frames above the motion score threshold
    # Use motion_score directly rather than has_motion (which may have been written with an old threshold)
    to_label = [
        e for e in entries
        if e.get("motion_score", e.get("motion", 0)) >= min_score
        and "cat_detected" not in e
    ]
    already_labeled = sum(1 for e in entries if "cat_detected" in e)

    if limit > 0:
        to_label = to_label[:limit]

    print(f"[label] {date}: {len(entries)} total frames, {already_labeled} already labeled")
    print(f"[label] {len(to_label)} frames with motion_score >= {min_score:,}" + (" (dry run)" if dry_run else ""))

    if not to_label:
        print("[label] Nothing to label!")
        return

    if dry_run:
        for e in to_label[:10]:
            print(f"  would label: {e['filename']} (motion={e.get('motion_score', 0):,})")
        if len(to_label) > 10:
            print(f"  ... and {len(to_label) - 10} more")
        return

    # Init Gemini client
    api_key = _load_api_key()
    client = genai.Client(api_key=api_key)

    cat_count = 0
    error_count = 0

    for i, entry in enumerate(to_label):
        img_path = date_dir / entry["filename"]
        if not img_path.exists():
            print(f"  [{i+1}/{len(to_label)}] SKIP {entry['filename']} (file missing)")
            continue

        try:
            img_bytes = img_path.read_bytes()
            result = label_frame(client, model, img_bytes)

            # Merge label fields into entry (modifies the dict in `entries` list)
            entry["cat_detected"] = result.cat_detected
            entry["cat_count"] = result.cat_count
            entry["cat_description"] = result.cat_description
            entry["confidence"] = result.confidence

            tag = "CAT" if result.cat_detected else "---"
            if result.cat_detected:
                cat_count += 1

            print(
                f"  [{i+1}/{len(to_label)}] {tag} {entry['filename']} "
                f"conf={result.confidence:.0%}"
                + (f" ({result.cat_description})" if result.cat_description else "")
            )

        except Exception as exc:
            error_count += 1
            print(f"  [{i+1}/{len(to_label)}] ERR {entry['filename']}: {exc}")
            # Continue with next frame instead of crashing
            continue

        # Write back after every frame so progress is saved on crash
        if (i + 1) % 10 == 0 or i == len(to_label) - 1:
            _write_meta(meta_path, entries)

        # Small delay to respect rate limits
        time.sleep(0.15)

    # Final write
    _write_meta(meta_path, entries)

    print(f"\n[label] Done! {cat_count} cats detected in {len(to_label)} frames "
          f"({error_count} errors)")


def _write_meta(path: Path, entries: list[dict]) -> None:
    """Write entries back to JSONL file atomically."""
    tmp = path.with_suffix(".jsonl.tmp")
    with open(tmp, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")
    tmp.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch label frames with Gemini cat detection")
    parser.add_argument("--date", required=True, help="Date directory to label (YYYY-MM-DD)")
    parser.add_argument("--output", default="data", help="Base data directory (default: data)")
    parser.add_argument("--limit", type=int, default=0, help="Max frames to label (0=all)")
    parser.add_argument("--min-score", type=int, default=5000,
                        help="Min motion score to label (default: 5000)")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Gemini model to use")
    parser.add_argument("--dry-run", action="store_true", help="Preview without API calls")
    args = parser.parse_args()
    run_labeling(args.date, args.output, args.limit, args.dry_run, args.model, args.min_score)


if __name__ == "__main__":
    main()
