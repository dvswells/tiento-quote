"""
Test suite for pricing configuration loader and validation.
Following TDD - tests written first.
"""
import json
import os
import tempfile
import pytest
from modules.pricing_config import (
    load_pricing_config,
    PricingConfigError,
    REQUIRED_COEFFICIENT_FEATURES,
)


class TestLoadPricingConfig:
    """Test loading and validation of pricing configuration."""

    def test_valid_config_loads(self, tmp_path):
        """Test that a valid config file loads successfully."""
        config_data = {
            "base_price": 30.0,
            "minimum_order_price": 30.0,
            "coefficients": {
                "volume": 0.001,
                "through_hole_count": 2.5,
                "blind_hole_count": 6.0,
                "blind_hole_avg_depth_to_diameter": 1.5,
                "blind_hole_max_depth_to_diameter": 2.0,
                "pocket_count": 5.0,
                "pocket_total_volume": 0.002,
                "pocket_avg_depth": 0.8,
                "pocket_max_depth": 1.2,
                "non_standard_hole_count": 5.0,
            },
            "r_squared": 0.85,
            "scaler_mean": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            "scaler_std": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        }

        config_file = tmp_path / "pricing_config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        result = load_pricing_config(str(config_file))

        assert result["base_price"] == 30.0
        assert result["minimum_order_price"] == 30.0
        assert result["r_squared"] == 0.85
        assert "coefficients" in result
        assert len(result["coefficients"]) == 10
        assert result["coefficients"]["volume"] == 0.001

    def test_valid_config_with_zero_r_squared(self, tmp_path):
        """Test that config with R² = 0.0 is valid (untrained model)."""
        config_data = {
            "base_price": 30.0,
            "minimum_order_price": 30.0,
            "coefficients": {
                "volume": 0.0,
                "through_hole_count": 0.0,
                "blind_hole_count": 0.0,
                "blind_hole_avg_depth_to_diameter": 0.0,
                "blind_hole_max_depth_to_diameter": 0.0,
                "pocket_count": 0.0,
                "pocket_total_volume": 0.0,
                "pocket_avg_depth": 0.0,
                "pocket_max_depth": 0.0,
                "non_standard_hole_count": 0.0,
            },
            "r_squared": 0.0,
            "scaler_mean": [],
            "scaler_std": [],
        }

        config_file = tmp_path / "pricing_config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        result = load_pricing_config(str(config_file))

        assert result["r_squared"] == 0.0
        assert result["coefficients"]["volume"] == 0.0

    def test_missing_base_price_raises(self, tmp_path):
        """Test that missing base_price raises PricingConfigError."""
        config_data = {
            "minimum_order_price": 30.0,
            "coefficients": {},
            "r_squared": 0.85,
            "scaler_mean": [],
            "scaler_std": [],
        }

        config_file = tmp_path / "pricing_config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        with pytest.raises(PricingConfigError) as exc_info:
            load_pricing_config(str(config_file))

        assert "base_price" in str(exc_info.value).lower()

    def test_missing_minimum_order_price_raises(self, tmp_path):
        """Test that missing minimum_order_price raises PricingConfigError."""
        config_data = {
            "base_price": 30.0,
            "coefficients": {},
            "r_squared": 0.85,
            "scaler_mean": [],
            "scaler_std": [],
        }

        config_file = tmp_path / "pricing_config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        with pytest.raises(PricingConfigError) as exc_info:
            load_pricing_config(str(config_file))

        assert "minimum_order_price" in str(exc_info.value).lower()

    def test_missing_coefficients_raises(self, tmp_path):
        """Test that missing coefficients key raises PricingConfigError."""
        config_data = {
            "base_price": 30.0,
            "minimum_order_price": 30.0,
            "r_squared": 0.85,
            "scaler_mean": [],
            "scaler_std": [],
        }

        config_file = tmp_path / "pricing_config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        with pytest.raises(PricingConfigError) as exc_info:
            load_pricing_config(str(config_file))

        assert "coefficients" in str(exc_info.value).lower()

    def test_missing_r_squared_raises(self, tmp_path):
        """Test that missing r_squared raises PricingConfigError."""
        config_data = {
            "base_price": 30.0,
            "minimum_order_price": 30.0,
            "coefficients": {},
            "scaler_mean": [],
            "scaler_std": [],
        }

        config_file = tmp_path / "pricing_config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        with pytest.raises(PricingConfigError) as exc_info:
            load_pricing_config(str(config_file))

        assert "r_squared" in str(exc_info.value).lower()

    def test_missing_scaler_mean_raises(self, tmp_path):
        """Test that missing scaler_mean raises PricingConfigError."""
        config_data = {
            "base_price": 30.0,
            "minimum_order_price": 30.0,
            "coefficients": {},
            "r_squared": 0.85,
            "scaler_std": [],
        }

        config_file = tmp_path / "pricing_config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        with pytest.raises(PricingConfigError) as exc_info:
            load_pricing_config(str(config_file))

        assert "scaler_mean" in str(exc_info.value).lower()

    def test_missing_scaler_std_raises(self, tmp_path):
        """Test that missing scaler_std raises PricingConfigError."""
        config_data = {
            "base_price": 30.0,
            "minimum_order_price": 30.0,
            "coefficients": {},
            "r_squared": 0.85,
            "scaler_mean": [],
        }

        config_file = tmp_path / "pricing_config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        with pytest.raises(PricingConfigError) as exc_info:
            load_pricing_config(str(config_file))

        assert "scaler_std" in str(exc_info.value).lower()

    def test_coefficients_missing_feature_raises(self, tmp_path):
        """Test that coefficients missing a required feature raises."""
        config_data = {
            "base_price": 30.0,
            "minimum_order_price": 30.0,
            "coefficients": {
                "volume": 0.001,
                "through_hole_count": 2.5,
                # Missing: blind_hole_count
                "blind_hole_avg_depth_to_diameter": 1.5,
                "blind_hole_max_depth_to_diameter": 2.0,
                "pocket_count": 5.0,
                "pocket_total_volume": 0.002,
                "pocket_avg_depth": 0.8,
                "pocket_max_depth": 1.2,
                "non_standard_hole_count": 5.0,
            },
            "r_squared": 0.85,
            "scaler_mean": [],
            "scaler_std": [],
        }

        config_file = tmp_path / "pricing_config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        with pytest.raises(PricingConfigError) as exc_info:
            load_pricing_config(str(config_file))

        assert "blind_hole_count" in str(exc_info.value)

    def test_coefficients_missing_multiple_features_raises(self, tmp_path):
        """Test that missing multiple features is reported."""
        config_data = {
            "base_price": 30.0,
            "minimum_order_price": 30.0,
            "coefficients": {
                "volume": 0.001,
                "through_hole_count": 2.5,
                # Missing: blind_hole_count, pocket_count, etc.
            },
            "r_squared": 0.85,
            "scaler_mean": [],
            "scaler_std": [],
        }

        config_file = tmp_path / "pricing_config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        with pytest.raises(PricingConfigError) as exc_info:
            load_pricing_config(str(config_file))

        error_msg = str(exc_info.value)
        # Should mention at least some of the missing features
        assert "blind_hole_count" in error_msg or "missing" in error_msg.lower()

    def test_file_not_found_raises(self):
        """Test that non-existent file raises appropriate error."""
        with pytest.raises((FileNotFoundError, PricingConfigError)):
            load_pricing_config("/nonexistent/path/config.json")

    def test_invalid_json_raises(self, tmp_path):
        """Test that invalid JSON raises appropriate error."""
        config_file = tmp_path / "invalid.json"
        with open(config_file, "w") as f:
            f.write("{invalid json content")

        with pytest.raises((json.JSONDecodeError, PricingConfigError)):
            load_pricing_config(str(config_file))

    def test_coefficients_not_dict_raises(self, tmp_path):
        """Test that coefficients must be a dict."""
        config_data = {
            "base_price": 30.0,
            "minimum_order_price": 30.0,
            "coefficients": "not a dict",
            "r_squared": 0.85,
            "scaler_mean": [],
            "scaler_std": [],
        }

        config_file = tmp_path / "pricing_config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        with pytest.raises(PricingConfigError) as exc_info:
            load_pricing_config(str(config_file))

        assert "coefficients" in str(exc_info.value).lower()


class TestRequiredCoefficientFeatures:
    """Test that REQUIRED_COEFFICIENT_FEATURES constant is correct."""

    def test_required_features_list_exists(self):
        """Test that REQUIRED_COEFFICIENT_FEATURES is defined."""
        assert REQUIRED_COEFFICIENT_FEATURES is not None
        assert isinstance(REQUIRED_COEFFICIENT_FEATURES, list)

    def test_required_features_includes_all_pricing_features(self):
        """Test that all pricing features are included."""
        expected_features = [
            "volume",
            "through_hole_count",
            "blind_hole_count",
            "blind_hole_avg_depth_to_diameter",
            "blind_hole_max_depth_to_diameter",
            "pocket_count",
            "pocket_total_volume",
            "pocket_avg_depth",
            "pocket_max_depth",
            "non_standard_hole_count",
        ]

        assert len(REQUIRED_COEFFICIENT_FEATURES) == len(expected_features)
        for feature in expected_features:
            assert feature in REQUIRED_COEFFICIENT_FEATURES
