"""Configuration and settings for PurrView worker."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # Supabase
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_service_role_key: str = Field(..., description="Supabase service role key")

    # Gemini
    gemini_api_key: str = Field(..., description="Google Gemini API key")
    gemini_model: str = Field("gemini-2.5-flash", description="Gemini model to use")

    # RTMP Stream
    rtmp_url: str = Field(..., description="RTMP stream URL")

    # Worker tuning
    frame_interval: int = Field(2, description="Seconds between frame extraction")
    motion_threshold: int = Field(500, description="Min non-zero pixels to trigger detection")
    motion_cooldown: int = Field(30, description="Seconds between Gemini API calls")
    idle_timeout: int = Field(120, description="Seconds of no motion to end feeding event")

    # Lark (Feishu) notifications
    lark_webhook_url: str = Field("", description="Lark webhook URL (empty = disabled)")


class ROI:
    """Region of Interest for a food bowl."""

    def __init__(self, x1: int, y1: int, x2: int, y2: int):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def crop(self, frame):
        """Crop a frame to this ROI region."""
        return frame[self.y1 : self.y2, self.x1 : self.x2]


_settings: Settings | None = None


def get_settings() -> Settings:
    """Lazy-load settings to avoid import-time validation errors in tests."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
