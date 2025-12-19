"""
Test suite for settings and environment variable handling.
Following TDD - tests written first.
"""
import os
import pytest
from modules.settings import Settings, get_settings


class TestSettingsDefaults:
    """Test Settings with default values (no env vars)."""

    def test_default_database_path(self):
        """Test default database path."""
        settings = Settings()
        assert settings.DATABASE_PATH == "training/training_data.db"

    def test_default_uploads_path(self):
        """Test default uploads path."""
        settings = Settings()
        assert settings.UPLOADS_PATH == "uploads"

    def test_default_temp_path(self):
        """Test default temp path."""
        settings = Settings()
        assert settings.TEMP_PATH == "temp"

    def test_default_max_upload_size(self):
        """Test default max upload size (50MB in bytes)."""
        settings = Settings()
        assert settings.MAX_UPLOAD_SIZE == 52428800  # 50 * 1024 * 1024

    def test_bounding_box_max_dimensions(self):
        """Test bounding box max dimensions from spec."""
        settings = Settings()
        assert settings.BOUNDING_BOX_MAX_X == 600.0
        assert settings.BOUNDING_BOX_MAX_Y == 400.0
        assert settings.BOUNDING_BOX_MAX_Z == 500.0

    def test_quantity_limits(self):
        """Test quantity limits from spec."""
        settings = Settings()
        assert settings.MIN_QUANTITY == 1
        assert settings.MAX_QUANTITY == 50

    def test_minimum_order_price(self):
        """Test minimum order price."""
        settings = Settings()
        assert settings.MINIMUM_ORDER_PRICE == 30.0


class TestSettingsEnvVarOverrides:
    """Test Settings with environment variable overrides."""

    def test_database_path_from_env(self, monkeypatch):
        """Test DATABASE_PATH can be overridden by env var."""
        monkeypatch.setenv("DATABASE_PATH", "/custom/path/data.db")
        settings = Settings()
        assert settings.DATABASE_PATH == "/custom/path/data.db"

    def test_uploads_path_from_env(self, monkeypatch):
        """Test UPLOADS_PATH can be overridden by env var."""
        monkeypatch.setenv("UPLOADS_PATH", "/custom/uploads")
        settings = Settings()
        assert settings.UPLOADS_PATH == "/custom/uploads"

    def test_temp_path_from_env(self, monkeypatch):
        """Test TEMP_PATH can be overridden by env var."""
        monkeypatch.setenv("TEMP_PATH", "/custom/temp")
        settings = Settings()
        assert settings.TEMP_PATH == "/custom/temp"

    def test_max_upload_size_from_env(self, monkeypatch):
        """Test MAX_UPLOAD_SIZE can be overridden by env var."""
        monkeypatch.setenv("MAX_UPLOAD_SIZE", "104857600")  # 100MB
        settings = Settings()
        assert settings.MAX_UPLOAD_SIZE == 104857600

    def test_multiple_env_vars(self, monkeypatch):
        """Test multiple env vars can be set at once."""
        monkeypatch.setenv("DATABASE_PATH", "/custom/db.db")
        monkeypatch.setenv("UPLOADS_PATH", "/custom/uploads")
        monkeypatch.setenv("TEMP_PATH", "/custom/temp")
        monkeypatch.setenv("MAX_UPLOAD_SIZE", "10485760")  # 10MB

        settings = Settings()

        assert settings.DATABASE_PATH == "/custom/db.db"
        assert settings.UPLOADS_PATH == "/custom/uploads"
        assert settings.TEMP_PATH == "/custom/temp"
        assert settings.MAX_UPLOAD_SIZE == 10485760

    def test_partial_env_vars(self, monkeypatch):
        """Test that only some env vars can be overridden."""
        monkeypatch.setenv("DATABASE_PATH", "/override/db.db")
        # Don't set UPLOADS_PATH, TEMP_PATH, MAX_UPLOAD_SIZE

        settings = Settings()

        assert settings.DATABASE_PATH == "/override/db.db"
        assert settings.UPLOADS_PATH == "uploads"  # Default
        assert settings.TEMP_PATH == "temp"  # Default
        assert settings.MAX_UPLOAD_SIZE == 52428800  # Default


class TestGetSettings:
    """Test get_settings() function."""

    def test_get_settings_returns_settings_instance(self):
        """Test that get_settings() returns a Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_is_cached(self):
        """Test that get_settings() returns the same instance (cached)."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_get_settings_with_env_vars(self, monkeypatch):
        """Test get_settings() with environment variables."""
        # Clear any existing cache
        from modules import settings as settings_module
        if hasattr(settings_module, '_settings_cache'):
            settings_module._settings_cache = None

        monkeypatch.setenv("DATABASE_PATH", "/env/test.db")
        monkeypatch.setenv("UPLOADS_PATH", "/env/uploads")

        settings = get_settings()

        assert settings.DATABASE_PATH == "/env/test.db"
        assert settings.UPLOADS_PATH == "/env/uploads"

    def test_get_settings_no_side_effects(self):
        """Test that calling get_settings() has no side effects."""
        # Should be able to import and call multiple times
        settings1 = get_settings()
        settings2 = get_settings()
        settings3 = get_settings()

        assert settings1 is settings2
        assert settings2 is settings3

    def test_hardcoded_values_not_overridable(self):
        """Test that hardcoded values (bounding box, quantity limits) cannot be overridden."""
        settings = get_settings()

        # These are hardcoded from spec and shouldn't change
        assert settings.BOUNDING_BOX_MAX_X == 600.0
        assert settings.BOUNDING_BOX_MAX_Y == 400.0
        assert settings.BOUNDING_BOX_MAX_Z == 500.0
        assert settings.MIN_QUANTITY == 1
        assert settings.MAX_QUANTITY == 50
        assert settings.MINIMUM_ORDER_PRICE == 30.0


class TestSettingsValidation:
    """Test Settings validation."""

    def test_max_upload_size_is_positive(self):
        """Test that MAX_UPLOAD_SIZE is positive."""
        settings = Settings()
        assert settings.MAX_UPLOAD_SIZE > 0

    def test_bounding_box_dimensions_are_positive(self):
        """Test that bounding box dimensions are positive."""
        settings = Settings()
        assert settings.BOUNDING_BOX_MAX_X > 0
        assert settings.BOUNDING_BOX_MAX_Y > 0
        assert settings.BOUNDING_BOX_MAX_Z > 0

    def test_quantity_limits_are_valid(self):
        """Test that quantity limits are valid."""
        settings = Settings()
        assert settings.MIN_QUANTITY >= 1
        assert settings.MAX_QUANTITY >= settings.MIN_QUANTITY
        assert settings.MAX_QUANTITY == 50

    def test_minimum_order_price_is_positive(self):
        """Test that minimum order price is positive."""
        settings = Settings()
        assert settings.MINIMUM_ORDER_PRICE > 0
        assert settings.MINIMUM_ORDER_PRICE == 30.0
