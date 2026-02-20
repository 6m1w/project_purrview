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
        """Analyze a single frame for cat presence, identity, and activity."""
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
