"""Gemini multimodal API for cat identification and food level analysis."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from .config import get_settings


# --- Structured output schemas ---

class FoodLevel(str, Enum):
    FULL = "full"
    THREE_QUARTERS = "3/4"
    HALF = "1/2"
    QUARTER = "1/4"
    EMPTY = "empty"


class PortionSize(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class FrameAnalysis(BaseModel):
    """Structured response from Gemini for a single frame."""
    cat_detected: bool = Field(description="Whether a cat is detected near the food bowl")
    cat_name: Optional[str] = Field(None, description="Identified cat name, if recognized")
    is_eating: bool = Field(False, description="Whether the cat is actively eating")
    food_level: Optional[FoodLevel] = Field(None, description="Current food level in the bowl")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Overall confidence score")
    notes: Optional[str] = Field(None, description="Additional observations")


# --- Analyzer ---

class CatAnalyzer:
    """Analyzes camera frames using Gemini to identify cats and food levels."""

    def __init__(self):
        s = get_settings()
        self.client = genai.Client(api_key=s.gemini_api_key)
        self.model = s.gemini_model

    def analyze_frame(
        self,
        frame_bytes: bytes,
        cat_profiles: list[dict],
        bowl_name: str = "food bowl",
    ) -> FrameAnalysis:
        """Analyze a single frame for cat presence and food level.

        Args:
            frame_bytes: JPEG-encoded frame bytes
            cat_profiles: List of dicts with 'name', 'description', 'reference_photos' (bytes)
            bowl_name: Name of the food bowl being monitored

        Returns:
            FrameAnalysis with structured detection results
        """
        # Build few-shot context with cat reference photos
        contents = self._build_prompt(frame_bytes, cat_profiles, bowl_name)

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=FrameAnalysis,
                temperature=0.1,
            ),
        )

        return FrameAnalysis.model_validate_json(response.text)

    def _build_prompt(
        self,
        frame_bytes: bytes,
        cat_profiles: list[dict],
        bowl_name: str,
    ) -> list:
        """Build the multimodal prompt with reference photos and current frame."""
        parts = []

        # System context
        parts.append(
            "You are a cat feeding monitor. Analyze the camera frame to detect "
            "if a cat is near the food bowl and identify which cat it is.\n\n"
            "Here are the cats you should recognize:\n"
        )

        # Add cat reference photos
        for profile in cat_profiles:
            parts.append(f"\n**{profile['name']}**: {profile.get('description', 'No description')}\n")
            for photo_bytes in profile.get("reference_photos", []):
                parts.append(types.Part.from_bytes(data=photo_bytes, mime_type="image/jpeg"))

        # Add current frame
        parts.append(
            f"\n\nNow analyze this frame from the '{bowl_name}' camera. "
            "Identify if a cat is present, which cat it is, whether it's eating, "
            "and estimate the food level in the bowl."
        )
        parts.append(types.Part.from_bytes(data=frame_bytes, mime_type="image/jpeg"))

        return parts
