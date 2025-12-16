"""
Settings and configuration for Tiento Quote v0.1.
Handles environment variables with sensible defaults.
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Settings:
    """
    Application settings with environment variable support.

    Environment variables (with defaults):
    - DATABASE_PATH: Path to SQLite training database
    - UPLOADS_PATH: Directory for uploaded STEP files
    - TEMP_PATH: Directory for temporary STL files
    - MAX_UPLOAD_SIZE: Maximum file upload size in bytes

    Hardcoded values from spec (not overridable):
    - BOUNDING_BOX_MAX_X/Y/Z: Maximum part dimensions (600×400×500mm)
    - MIN_QUANTITY/MAX_QUANTITY: Quantity limits (1-50)
    - MINIMUM_ORDER_PRICE: Minimum order price in EUR (30.0)
    """

    # Paths (overridable via env vars)
    DATABASE_PATH: str = "training/training_data.db"
    UPLOADS_PATH: str = "uploads"
    TEMP_PATH: str = "temp"
    MAX_UPLOAD_SIZE: int = 52428800  # 50MB in bytes

    # Bounding box limits (hardcoded from spec)
    BOUNDING_BOX_MAX_X: float = 600.0  # mm
    BOUNDING_BOX_MAX_Y: float = 400.0  # mm
    BOUNDING_BOX_MAX_Z: float = 500.0  # mm

    # Quantity limits (hardcoded from spec)
    MIN_QUANTITY: int = 1
    MAX_QUANTITY: int = 50

    # Pricing (hardcoded from spec)
    MINIMUM_ORDER_PRICE: float = 30.0  # EUR

    def __post_init__(self):
        """Override defaults with environment variables if present."""
        # Read environment variables and override defaults
        if "DATABASE_PATH" in os.environ:
            self.DATABASE_PATH = os.environ["DATABASE_PATH"]

        if "UPLOADS_PATH" in os.environ:
            self.UPLOADS_PATH = os.environ["UPLOADS_PATH"]

        if "TEMP_PATH" in os.environ:
            self.TEMP_PATH = os.environ["TEMP_PATH"]

        if "MAX_UPLOAD_SIZE" in os.environ:
            self.MAX_UPLOAD_SIZE = int(os.environ["MAX_UPLOAD_SIZE"])


# Global cache for settings instance
_settings_cache: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get application settings (cached).

    Returns the same Settings instance on subsequent calls.
    Safe to import and call multiple times without side effects.

    Returns:
        Settings instance with current configuration
    """
    global _settings_cache

    if _settings_cache is None:
        _settings_cache = Settings()

    return _settings_cache
