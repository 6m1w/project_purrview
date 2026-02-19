"""Evaluate cat identification accuracy using few-shot Gemini prompts.

Selects reference photos from labeled data, builds a few-shot prompt with
reference images for each cat, then evaluates identification accuracy against
ground truth labels.

Usage:
    cd apps/worker
    python -m src.eval_identify --date 2026-02-10 --limit 20    # quick test
    python -m src.eval_identify --date 2026-02-10               # full eval
    python -m src.eval_identify --date 2026-02-10 --dry-run     # show refs only
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import defaultdict
from enum import Enum
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from .label import _load_api_key


# --- Structured output schema ---

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

# Appearance descriptions to help disambiguate similar-looking cats
CAT_DESCRIPTIONS: dict[str, str] = {
    "大吉": "Orange/ginger cat with white patches. Light-colored, medium-large build.",
    "小慢": "Calico cat with distinct patches of orange, black and white. Medium build.",
    "小黑": "Solid black cat. Sleek, medium build.",
    "麻酱": "Tortoiseshell cat with a dark mix of black and brown/amber mottled pattern. No stripes.",
    "松花": "Brown tabby cat with visible dark stripes/mackerel pattern. Lighter than 麻酱.",
}

REFS_PER_CAT = 3

# Keywords for parsing activity from cat_description text
_DRINKING_PATTERN = re.compile(
    r"drink|water dispenser|water fountain|water bowl", re.IGNORECASE
)
_EATING_PATTERN = re.compile(
    r"\beat|eating|eats|food bowl", re.IGNORECASE
)


# --- Reference photo selection ---

def select_references(
    labels: dict[str, list[str]],
    meta_by_file: dict[str, dict],
    date_dir: Path,
    per_cat: int = REFS_PER_CAT,
) -> dict[str, list[str]]:
    """Select reference photos for each cat.

    If data/{date}/refs.json exists, use manual overrides from that file.
    Otherwise, auto-select: pick top frames by motion score (proxy for
    cat visibility), then from those pick evenly spaced for temporal spread.

    Returns:
        {cat_name: [filename, ...]} with `per_cat` filenames per cat
    """
    # Check for manual override
    refs_path = date_dir / "refs.json"
    if refs_path.exists():
        manual: dict[str, list[str]] = json.loads(refs_path.read_text())
        print(f"[eval] Using manual refs from {refs_path}")
        return manual

    # Group single-cat frames by cat name
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for fname, cats in labels.items():
        if len(cats) == 1 and fname in meta_by_file:
            by_cat[cats[0]].append(meta_by_file[fname])

    refs: dict[str, list[str]] = {}
    for cat in CAT_NAMES:
        frames = by_cat.get(cat, [])
        if len(frames) <= per_cat:
            refs[cat] = [f["filename"] for f in frames]
        else:
            # First filter to top 60% by motion score (visibility proxy),
            # then pick evenly spaced from those for temporal diversity
            by_motion = sorted(frames, key=lambda e: e.get("motion_score", 0), reverse=True)
            pool_size = max(per_cat, int(len(by_motion) * 0.6))
            pool = sorted(by_motion[:pool_size], key=lambda e: e["timestamp"])
            step = len(pool) / per_cat
            indices = [int(i * step + step / 2) for i in range(per_cat)]
            refs[cat] = [pool[i]["filename"] for i in indices]
    return refs


# --- Activity pseudo-labels ---

def parse_activity_labels(
    labels: dict[str, list[str]],
    meta_by_file: dict[str, dict],
) -> dict[str, dict[str, str]]:
    """Parse activity pseudo-labels from cat_description in gallery_meta.

    For single-cat frames, the whole description maps to that cat's activity.
    For multi-cat frames, try to match per-cat mentions in the description;
    fall back to frame-level activity if per-cat parsing fails.

    Returns:
        {filename: {cat_name: activity_str}} where activity is eating/drinking/present
    """
    result: dict[str, dict[str, str]] = {}

    for fname, cats in labels.items():
        desc = (meta_by_file.get(fname, {}).get("cat_description") or "").lower()
        if not desc:
            # No description — default all cats to "present"
            result[fname] = {c: "present" for c in cats}
            continue

        if len(cats) == 1:
            # Single cat: classify from whole description
            result[fname] = {cats[0]: _classify_text(desc)}
        else:
            # Multi-cat: try per-cat parsing from description sentences
            per_cat = _parse_multi_cat_activity(desc, cats)
            result[fname] = per_cat

    return result


def _classify_text(text: str) -> str:
    """Classify activity from description text."""
    if _DRINKING_PATTERN.search(text):
        return "drinking"
    if _EATING_PATTERN.search(text):
        return "eating"
    return "present"


def _parse_multi_cat_activity(desc: str, cats: list[str]) -> dict[str, str]:
    """Parse per-cat activity from a multi-cat description.

    Looks for cat color/type mentions near activity keywords.
    Falls back to frame-level classification if parsing fails.
    """
    # Color/type hints for matching description text to cat names
    cat_hints: dict[str, list[str]] = {
        "大吉": ["orange", "ginger", "light-colored", "light brown", "light orange"],
        "小慢": ["calico"],
        "小黑": ["black", "dark-colored", "dark cat"],
        "麻酱": ["tortoiseshell", "darker cat"],
        "松花": ["tabby", "striped", "brown tabby"],
    }

    activities: dict[str, str] = {}
    # Split into sentence-like segments
    segments = re.split(r"[.;,]|(?:and )", desc)

    for cat in cats:
        hints = cat_hints.get(cat, [])
        # Find segments mentioning this cat
        cat_segments = [s for s in segments if any(h in s for h in hints)]
        if cat_segments:
            # Classify from cat-specific text
            combined = " ".join(cat_segments)
            activities[cat] = _classify_text(combined)
        else:
            # Fall back to whole description
            activities[cat] = _classify_text(desc)

    return activities


# --- Prompt building ---

def build_identify_prompt(
    ref_images: dict[str, list[bytes]],
    test_image: bytes,
) -> list:
    """Build multimodal few-shot prompt with reference images and test frame.

    Args:
        ref_images: {cat_name: [jpeg_bytes, ...]} reference images per cat
        test_image: JPEG bytes of the frame to identify
    """
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

    # Add reference photos per cat with brief appearance hint
    for cat_name in CAT_NAMES:
        images = ref_images.get(cat_name, [])
        if not images:
            continue
        desc = CAT_DESCRIPTIONS.get(cat_name, "")
        parts.append(f"\n{cat_name} — {desc}\n")
        for img_bytes in images:
            parts.append(types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))

    # Add test frame
    parts.append(
        "\n\nTEST IMAGE — identify the cat(s):\n"
    )
    parts.append(types.Part.from_bytes(data=test_image, mime_type="image/jpeg"))

    return parts


# --- Evaluation ---

def evaluate(
    date: str,
    output_dir: str = "data",
    limit: int = 0,
    dry_run: bool = False,
    model: str = "gemini-2.5-flash",
) -> None:
    """Run cat identification evaluation on labeled data."""
    date_dir = Path(output_dir) / date
    meta_path = date_dir / "gallery_meta.jsonl"
    labels_path = date_dir / "labels.json"

    if not labels_path.exists():
        print(f"[eval] Error: {labels_path} not found")
        sys.exit(1)
    if not meta_path.exists():
        print(f"[eval] Error: {meta_path} not found")
        sys.exit(1)

    # Load data
    labels: dict[str, list[str]] = json.loads(labels_path.read_text())
    meta_by_file: dict[str, dict] = {}
    with open(meta_path) as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                meta_by_file[entry["filename"]] = entry

    # Parse activity pseudo-labels from descriptions
    activity_labels = parse_activity_labels(labels, meta_by_file)

    print(f"[eval] Date: {date}")
    print(f"[eval] Labels: {len(labels)} frames, Meta: {len(meta_by_file)} frames")

    # Show activity distribution
    act_counts: dict[str, int] = defaultdict(int)
    for acts in activity_labels.values():
        for act in acts.values():
            act_counts[act] += 1
    print(f"[eval] Activity labels: {dict(act_counts)}")

    # Step 1: Select reference photos
    refs = select_references(labels, meta_by_file, date_dir)

    print(f"\n[eval] Reference photos selected:")
    ref_filenames: set[str] = set()
    for cat, filenames in refs.items():
        ref_filenames.update(filenames)
        for fn in filenames:
            ts = meta_by_file.get(fn, {}).get("timestamp", "?")[:19]
            print(f"  {cat}: {fn} ({ts})")

    # Step 2: Determine test set (labeled frames minus refs)
    test_frames = [
        (fname, cats)
        for fname, cats in labels.items()
        if fname not in ref_filenames and (date_dir / fname).exists()
    ]
    # Sort by filename for deterministic order
    test_frames.sort(key=lambda x: x[0])

    if limit > 0:
        test_frames = test_frames[:limit]

    print(f"\n[eval] Test set: {len(test_frames)} frames (excluded {len(ref_filenames)} refs)")

    if dry_run:
        print("[eval] Dry run — skipping API calls")
        # Show test set distribution
        cat_dist: dict[str, int] = defaultdict(int)
        test_act_dist: dict[str, int] = defaultdict(int)
        for fname, cats in test_frames:
            for c in cats:
                cat_dist[c] += 1
            for act in activity_labels.get(fname, {}).values():
                test_act_dist[act] += 1
        print(f"[eval] Test set cat distribution: {dict(cat_dist)}")
        print(f"[eval] Test set activity distribution: {dict(test_act_dist)}")
        return

    # Load reference images into memory
    ref_images: dict[str, list[bytes]] = {}
    for cat, filenames in refs.items():
        ref_images[cat] = []
        for fn in filenames:
            img_path = date_dir / fn
            if img_path.exists():
                ref_images[cat].append(img_path.read_bytes())
            else:
                print(f"  WARNING: ref image missing: {fn}")

    # Init Gemini client
    api_key = _load_api_key()
    client = genai.Client(api_key=api_key)

    # Step 3: Run evaluation
    results: list[dict] = []
    errors = 0

    for i, (fname, truth_cats) in enumerate(test_frames):
        img_path = date_dir / fname
        test_bytes = img_path.read_bytes()

        try:
            prompt = build_identify_prompt(ref_images, test_bytes)
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=IdentifyResult,
                    temperature=0.1,
                ),
            )
            result = IdentifyResult.model_validate_json(response.text)

            # Extract cat names and activities from structured response
            pred_names = {ca.name for ca in result.cats}
            pred_activities = {ca.name: ca.activity.value for ca in result.cats}
            truth_set = set(truth_cats)
            truth_activities = activity_labels.get(fname, {})
            match = pred_names == truth_set

            tag = "OK" if match else "XX"
            results.append({
                "filename": fname,
                "truth": sorted(truth_set),
                "pred": sorted(pred_names),
                "match": match,
                "confidence": result.confidence,
                "truth_activities": truth_activities,
                "pred_activities": pred_activities,
            })

            truth_str = ",".join(sorted(truth_set))
            pred_str = ",".join(sorted(pred_names)) or "(none)"
            # Show activity for correctly identified cats
            act_detail = ""
            for cat in sorted(pred_names & truth_set):
                ta = truth_activities.get(cat, "?")
                pa = pred_activities.get(cat, "?")
                act_tag = "=" if ta == pa else "!"
                act_detail += f" {cat}:{pa}({act_tag})"
            print(
                f"  [{i+1}/{len(test_frames)}] {tag} {fname}  "
                f"truth=[{truth_str}] pred=[{pred_str}] "
                f"conf={result.confidence:.0%}{act_detail}"
            )

        except Exception as exc:
            errors += 1
            print(f"  [{i+1}/{len(test_frames)}] ERR {fname}: {exc}")
            continue

        # Rate limit
        time.sleep(0.3)

    # Step 4: Print summary
    _print_id_summary(results, errors)
    _print_activity_summary(results)


def _print_id_summary(results: list[dict], errors: int) -> None:
    """Print cat identification summary with per-cat precision/recall."""
    if not results:
        print("\n[eval] No results to summarize")
        return

    total = len(results)
    correct = sum(1 for r in results if r["match"])

    print(f"\n{'='*60}")
    print(f"[eval] RESULTS: {correct}/{total} exact match ({correct/total:.1%})")
    print(f"[eval] Errors: {errors}")

    # Per-cat precision and recall
    # TP: predicted AND in truth
    # FP: predicted but NOT in truth
    # FN: in truth but NOT predicted
    tp: dict[str, int] = defaultdict(int)
    fp: dict[str, int] = defaultdict(int)
    fn: dict[str, int] = defaultdict(int)

    for r in results:
        truth = set(r["truth"])
        pred = set(r["pred"])
        for cat in truth | pred:
            if cat in truth and cat in pred:
                tp[cat] += 1
            elif cat in pred and cat not in truth:
                fp[cat] += 1
            elif cat in truth and cat not in pred:
                fn[cat] += 1

    print(f"\n{'Cat':<8} {'Prec':>6} {'Recall':>6} {'F1':>6} {'TP':>4} {'FP':>4} {'FN':>4}")
    print("-" * 46)
    for cat in CAT_NAMES:
        p = tp[cat] / (tp[cat] + fp[cat]) if (tp[cat] + fp[cat]) > 0 else 0
        r = tp[cat] / (tp[cat] + fn[cat]) if (tp[cat] + fn[cat]) > 0 else 0
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0
        print(f"{cat:<8} {p:>5.0%} {r:>6.0%} {f1:>6.0%} {tp[cat]:>4} {fp[cat]:>4} {fn[cat]:>4}")

    # Confusion pairs: most common (truth, pred) mismatches
    confusion: dict[tuple[str, str], int] = defaultdict(int)
    for r in results:
        if not r["match"]:
            truth = set(r["truth"])
            pred = set(r["pred"])
            missed = truth - pred
            extra = pred - truth
            for m in missed:
                for e in extra:
                    confusion[(m, e)] += 1
            # Also track missed without replacement
            for m in missed:
                if not extra:
                    confusion[(m, "(missed)")] += 1
            for e in extra:
                if not missed:
                    confusion[("(none)", e)] += 1

    if confusion:
        print(f"\n[eval] Top confusion pairs (truth -> pred):")
        for (t, p), count in sorted(confusion.items(), key=lambda x: -x[1])[:10]:
            print(f"  {t} -> {p}: {count}x")


def _print_activity_summary(results: list[dict]) -> None:
    """Print activity classification summary with confusion matrix.

    Only evaluates activity for cats that were correctly identified
    (both in truth and prediction), so activity accuracy is independent
    of cat ID accuracy.
    """
    if not results:
        return

    activity_types = ["eating", "drinking", "present"]

    # Collect (truth_activity, pred_activity) pairs for correctly ID'd cats
    pairs: list[tuple[str, str]] = []
    for r in results:
        truth_acts: dict[str, str] = r.get("truth_activities", {})
        pred_acts: dict[str, str] = r.get("pred_activities", {})
        # Only compare cats present in both truth and prediction
        for cat in set(r["truth"]) & set(r["pred"]):
            ta = truth_acts.get(cat)
            pa = pred_acts.get(cat)
            if ta and pa:
                pairs.append((ta, pa))

    if not pairs:
        print("\n[eval] No activity pairs to evaluate")
        return

    correct = sum(1 for t, p in pairs if t == p)
    total = len(pairs)

    print(f"\n{'='*60}")
    print(f"[eval] ACTIVITY: {correct}/{total} correct ({correct/total:.1%})")

    # Per-activity precision/recall
    tp: dict[str, int] = defaultdict(int)
    fp: dict[str, int] = defaultdict(int)
    fn: dict[str, int] = defaultdict(int)
    for t, p in pairs:
        if t == p:
            tp[t] += 1
        else:
            fp[p] += 1
            fn[t] += 1

    print(f"\n{'Activity':<10} {'Prec':>6} {'Recall':>6} {'F1':>6} {'TP':>4} {'FP':>4} {'FN':>4}")
    print("-" * 50)
    for act in activity_types:
        p = tp[act] / (tp[act] + fp[act]) if (tp[act] + fp[act]) > 0 else 0
        r = tp[act] / (tp[act] + fn[act]) if (tp[act] + fn[act]) > 0 else 0
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0
        print(f"{act:<10} {p:>5.0%} {r:>6.0%} {f1:>6.0%} {tp[act]:>4} {fp[act]:>4} {fn[act]:>4}")

    # Confusion matrix
    matrix: dict[str, dict[str, int]] = {a: defaultdict(int) for a in activity_types}
    for t, p in pairs:
        if t in matrix:
            matrix[t][p] += 1

    print(f"\n[eval] Activity confusion matrix (rows=truth, cols=pred):")
    header = f"{'':>10}" + "".join(f"{a:>10}" for a in activity_types)
    print(header)
    for t in activity_types:
        row = f"{t:>10}" + "".join(f"{matrix[t][p]:>10}" for p in activity_types)
        print(row)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate cat identification with few-shot Gemini prompts"
    )
    parser.add_argument("--date", required=True, help="Date directory (YYYY-MM-DD)")
    parser.add_argument("--output", default="data", help="Base data directory (default: data)")
    parser.add_argument("--limit", type=int, default=0, help="Max test frames (0=all)")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Gemini model")
    parser.add_argument("--dry-run", action="store_true", help="Show refs, skip API calls")
    args = parser.parse_args()
    evaluate(args.date, args.output, args.limit, args.dry_run, args.model)


if __name__ == "__main__":
    main()
