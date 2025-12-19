"""
Pricing configuration loader and validator for Tiento Quote v0.1.

Loads and validates pricing coefficients from JSON config file.
Ensures all required features are present for pricing calculation.
"""
import json
from typing import Dict, Any, List


# Required coefficient feature names (must match PartFeatures fields used in pricing)
REQUIRED_COEFFICIENT_FEATURES = [
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


class PricingConfigError(Exception):
    """Raised when pricing configuration is invalid or missing required fields."""
    pass


def load_pricing_config(path: str) -> Dict[str, Any]:
    """
    Load and validate pricing configuration from JSON file.

    Required keys in config:
    - base_price: Base price for all parts
    - minimum_order_price: Minimum order price (e.g., 30 EUR)
    - coefficients: Dict mapping feature names to coefficients
    - r_squared: Model R² score (0.0 for untrained)
    - scaler_mean: List of feature means for normalization
    - scaler_std: List of feature standard deviations for normalization

    The coefficients dict must include all features in REQUIRED_COEFFICIENT_FEATURES.

    Args:
        path: Path to pricing_coefficients.json file

    Returns:
        Validated configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is not valid JSON
        PricingConfigError: If config is missing required keys or features
    """
    # Load JSON file
    try:
        with open(path, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Pricing config file not found: {path}")
    except json.JSONDecodeError as e:
        raise PricingConfigError(f"Invalid JSON in pricing config: {e}")

    # Validate required top-level keys
    required_keys = [
        "base_price",
        "minimum_order_price",
        "coefficients",
        "r_squared",
        "scaler_mean",
        "scaler_std",
    ]

    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise PricingConfigError(
            f"Missing required keys in pricing config: {', '.join(missing_keys)}"
        )

    # Validate coefficients is a dict
    if not isinstance(config["coefficients"], dict):
        raise PricingConfigError(
            "Invalid pricing config: 'coefficients' must be a dictionary"
        )

    # Validate all required features are present in coefficients
    coefficients = config["coefficients"]
    missing_features = [
        feature
        for feature in REQUIRED_COEFFICIENT_FEATURES
        if feature not in coefficients
    ]

    if missing_features:
        raise PricingConfigError(
            f"Missing required features in coefficients: {', '.join(missing_features)}"
        )

    return config
