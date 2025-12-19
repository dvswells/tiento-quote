"""
Pricing engine for Tiento Quote v0.1.

Calculates quotes using trained linear model with feature normalization.
"""
from typing import Dict, Any
from modules.domain import PartFeatures, QuoteResult


class ModelNotReadyError(Exception):
    """Raised when pricing model is not trained (r_squared = 0.0)."""
    pass


class InvalidQuantityError(Exception):
    """Raised when quantity is outside valid range."""
    pass


def normalize_features(features_dict: Dict[str, float], mean: Dict[str, float], std: Dict[str, float]) -> Dict[str, float]:
    """
    Normalize features using standard scaler formula: (x - mean) / std.

    Args:
        features_dict: Raw feature values to normalize
        mean: Mean values for each feature (from training data)
        std: Standard deviation for each feature (from training data)

    Returns:
        Dictionary of normalized feature values

    Example:
        >>> features = {"volume": 1500.0, "through_hole_count": 3.0}
        >>> mean = {"volume": 1000.0, "through_hole_count": 2.0}
        >>> std = {"volume": 500.0, "through_hole_count": 1.0}
        >>> normalized = normalize_features(features, mean, std)
        >>> # volume: (1500 - 1000) / 500 = 1.0
        >>> # through_hole_count: (3 - 2) / 1 = 1.0
    """
    normalized = {}

    for key, value in features_dict.items():
        # Apply standard scaler: (x - mean) / std
        normalized[key] = (value - mean[key]) / std[key]

    return normalized


def calculate_quote(
    part_features: PartFeatures,
    quantity: int,
    pricing_config: dict
) -> QuoteResult:
    """
    Calculate quote for a part using trained pricing model.

    Applies linear model with feature normalization. Enforces minimum order price
    and quantity limits.

    Args:
        part_features: Detected part features
        quantity: Quantity of parts to quote (1-50)
        pricing_config: Pricing configuration with model parameters

    Returns:
        QuoteResult with pricing breakdown

    Raises:
        ModelNotReadyError: If model is not trained (r_squared = 0.0)
        InvalidQuantityError: If quantity is outside valid range (1-50)

    Example:
        >>> features = PartFeatures(volume=1000.0, through_hole_count=2)
        >>> config = load_pricing_config("config/pricing_coefficients.json")
        >>> quote = calculate_quote(features, 10, config)
        >>> print(f"Total: €{quote.total_price:.2f}")
    """
    # Check if model is trained
    if pricing_config["r_squared"] == 0.0:
        raise ModelNotReadyError(
            "System not ready - training required"
        )

    # Check quantity limits (1-50)
    if quantity < 1 or quantity > 50:
        raise InvalidQuantityError(
            f"Quantity must be between 1 and 50 (got {quantity})"
        )

    # Extract pricing features from PartFeatures
    # Only include features used in pricing model
    pricing_features = {
        "volume": part_features.volume,
        "through_hole_count": float(part_features.through_hole_count),
        "blind_hole_count": float(part_features.blind_hole_count),
        "blind_hole_avg_depth_to_diameter": part_features.blind_hole_avg_depth_to_diameter,
        "blind_hole_max_depth_to_diameter": part_features.blind_hole_max_depth_to_diameter,
        "pocket_count": float(part_features.pocket_count),
        "pocket_total_volume": part_features.pocket_total_volume,
        "pocket_avg_depth": part_features.pocket_avg_depth,
        "pocket_max_depth": part_features.pocket_max_depth,
        "non_standard_hole_count": float(part_features.non_standard_hole_count),
    }

    # Normalize features
    normalized_features = normalize_features(
        pricing_features,
        pricing_config["scaler_mean"],
        pricing_config["scaler_std"]
    )

    # Calculate predicted price using linear model
    # predicted_price = base_price + sum(coefficient * normalized_feature)
    base_price = pricing_config["base_price"]
    feature_contribution = 0.0

    for feature_name, normalized_value in normalized_features.items():
        coefficient = pricing_config["coefficients"][feature_name]
        feature_contribution += coefficient * normalized_value

    # Predicted price per unit
    predicted_price_per_unit = base_price + feature_contribution

    # Ensure price per unit is non-negative
    if predicted_price_per_unit < 0:
        predicted_price_per_unit = 0.0

    # Calculate total price before minimum
    calculated_total = predicted_price_per_unit * quantity

    # Apply minimum order price
    minimum_order_price = pricing_config["minimum_order_price"]
    minimum_applied = False

    if calculated_total < minimum_order_price:
        final_total_price = minimum_order_price
        minimum_applied = True
        # Recalculate price per unit when minimum applies
        final_price_per_unit = minimum_order_price / quantity
    else:
        final_total_price = calculated_total
        final_price_per_unit = predicted_price_per_unit

    # Create breakdown dictionary
    breakdown = {
        "base_price": base_price,
        "feature_contribution": feature_contribution,
        "predicted_price_per_unit": predicted_price_per_unit,
        "calculated_total": calculated_total,
        "minimum_order_price": minimum_order_price if minimum_applied else 0.0,
        "final_total": final_total_price,
    }

    # Create and return QuoteResult
    return QuoteResult(
        price_per_unit=final_price_per_unit,
        total_price=final_total_price,
        quantity=quantity,
        breakdown=breakdown,
        minimum_applied=minimum_applied,
    )
