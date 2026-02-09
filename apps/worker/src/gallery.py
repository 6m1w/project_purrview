"""Generate an HTML thumbnail gallery for collected frames.

Usage:
    cd apps/worker
    python -m src.gallery data/2026-02-08
    # Then open data/2026-02-08/gallery.html via HTTP server
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np


THUMB_WIDTH = 220
THUMB_HEIGHT = 124
MOTION_THRESHOLD = 1000


def compute_motion(current: np.ndarray, previous: np.ndarray | None) -> int:
    """Simple frame-diff motion score."""
    if previous is None:
        return 0
    diff = cv2.absdiff(current, previous)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 25, 255, cv2.THRESH_BINARY)
    return int(cv2.countNonZero(thresh))


def generate_gallery(data_dir: str) -> None:
    """Scan a date folder, compute motion, generate gallery.html + thumbnails."""
    src = Path(data_dir)
    if not src.is_dir():
        print(f"[gallery] Error: {src} is not a directory")
        sys.exit(1)

    jpgs = sorted(src.glob("*.jpg"))
    if not jpgs:
        print(f"[gallery] No JPG files found in {src}")
        sys.exit(1)

    # Create thumbnail directory
    thumb_dir = src / "thumbs"
    thumb_dir.mkdir(exist_ok=True)

    print(f"[gallery] Processing {len(jpgs)} frames from {src}")

    # Compute motion scores and generate thumbnails
    entries: list[dict] = []
    prev_frame: np.ndarray | None = None
    motion_count = 0

    for i, jpg in enumerate(jpgs):
        frame = cv2.imread(str(jpg))
        if frame is None:
            continue

        motion = compute_motion(frame, prev_frame)
        prev_frame = frame.copy()
        has_motion = motion > MOTION_THRESHOLD

        if has_motion:
            motion_count += 1

        # Generate thumbnail
        thumb = cv2.resize(frame, (THUMB_WIDTH, THUMB_HEIGHT))
        thumb_path = thumb_dir / jpg.name
        cv2.imwrite(str(thumb_path), thumb, [cv2.IMWRITE_JPEG_QUALITY, 70])

        entries.append({
            "filename": jpg.name,
            "motion": motion,
            "has_motion": has_motion,
        })

        if (i + 1) % 100 == 0:
            print(f"[gallery] {i + 1}/{len(jpgs)} processed")

    # Write metadata
    meta_path = src / "gallery_meta.json"
    with open(meta_path, "w") as f:
        json.dump(entries, f)

    # Generate HTML
    html_path = src / "gallery.html"
    html_path.write_text(_build_html(entries))

    print(f"\n[gallery] Done!")
    print(f"  Total frames:    {len(entries)}")
    print(f"  With motion:     {motion_count}")
    print(f"  Gallery:         {html_path}")
    print(f"  Thumbnails:      {thumb_dir}/")


def _build_html(entries: list[dict]) -> str:
    """Build a self-contained HTML gallery page."""
    # Pre-compute stats for display
    motion_scores = [e["motion"] for e in entries]
    max_motion = max(motion_scores) if motion_scores else 1
    motion_count = sum(1 for e in entries if e["has_motion"])

    # Build thumbnail grid items
    items_html = []
    for e in entries:
        cls = "thumb motion" if e["has_motion"] else "thumb"
        score = e["motion"]
        # Color intensity based on motion score (0=gray, high=red)
        intensity = min(score / max(max_motion * 0.3, 1), 1.0)
        border_color = f"rgba(239,68,68,{intensity:.2f})" if score > 0 else "#333"
        items_html.append(
            f'<div class="{cls}" data-motion="{score}" '
            f'style="border-color:{border_color}">'
            f'<a href="{e["filename"]}" target="_blank">'
            f'<img src="thumbs/{e["filename"]}" loading="lazy" '
            f'alt="{e["filename"]}">'
            f'</a>'
            f'<span class="label">{e["filename"][:6]}</span>'
            f'<span class="score">{score:,}</span>'
            f'</div>'
        )
    grid = "\n".join(items_html)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>PurrView Gallery</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#111; color:#eee; font-family:system-ui,sans-serif; padding:16px; }}
  h1 {{ font-size:1.4rem; margin-bottom:4px; }}
  .stats {{ color:#999; font-size:0.85rem; margin-bottom:12px; }}
  .controls {{ display:flex; gap:8px; margin-bottom:16px; flex-wrap:wrap; align-items:center; }}
  .controls button {{
    padding:6px 14px; border:1px solid #444; border-radius:6px;
    background:#222; color:#ddd; cursor:pointer; font-size:0.85rem;
  }}
  .controls button.active {{ background:#3b82f6; border-color:#3b82f6; color:#fff; }}
  .controls button:hover {{ background:#333; }}
  .controls button.active:hover {{ background:#2563eb; }}
  .size-controls {{ margin-left:auto; display:flex; gap:4px; }}
  .size-controls button {{ padding:4px 10px; font-size:0.8rem; }}
  .grid {{
    display:grid;
    grid-template-columns:repeat(auto-fill, minmax(var(--thumb-w, 220px), 1fr));
    gap:6px;
  }}
  .thumb {{
    border:2px solid #333; border-radius:4px; overflow:hidden;
    position:relative; background:#000;
  }}
  .thumb img {{ width:100%; display:block; }}
  .thumb .label {{
    position:absolute; bottom:0; left:0; font-size:0.65rem;
    background:rgba(0,0,0,0.7); padding:1px 4px; color:#aaa;
  }}
  .thumb .score {{
    position:absolute; top:0; right:0; font-size:0.65rem;
    background:rgba(0,0,0,0.7); padding:1px 4px; color:#f87171;
  }}
  .thumb.hidden {{ display:none; }}
</style>
</head>
<body>
<h1>PurrView Gallery</h1>
<div class="stats">{len(entries)} frames | {motion_count} with motion (threshold: {MOTION_THRESHOLD:,} px)</div>
<div class="controls">
  <button class="active" onclick="filter('all')">All ({len(entries)})</button>
  <button onclick="filter('motion')">Motion only ({motion_count})</button>
  <button onclick="filter('no-motion')">No motion ({len(entries) - motion_count})</button>
  <div class="size-controls">
    <button onclick="setSize(150)">S</button>
    <button class="active" onclick="setSize(220)">M</button>
    <button onclick="setSize(320)">L</button>
  </div>
</div>
<div class="grid" id="grid">
{grid}
</div>
<script>
function filter(mode) {{
  document.querySelectorAll('.controls > button:not(.size-controls button)').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  document.querySelectorAll('.thumb').forEach(el => {{
    const m = parseInt(el.dataset.motion);
    if (mode === 'all') el.classList.remove('hidden');
    else if (mode === 'motion') el.classList.toggle('hidden', m <= {MOTION_THRESHOLD});
    else el.classList.toggle('hidden', m > {MOTION_THRESHOLD});
  }});
}}
function setSize(w) {{
  document.querySelector('.grid').style.setProperty('--thumb-w', w + 'px');
  document.querySelectorAll('.size-controls button').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
}}
</script>
</body>
</html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate thumbnail gallery for collected frames")
    parser.add_argument("data_dir", help="Path to date folder (e.g. data/2026-02-08)")
    args = parser.parse_args()
    generate_gallery(args.data_dir)


if __name__ == "__main__":
    main()
