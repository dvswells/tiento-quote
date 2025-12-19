"""
Test suite for pricing engine.
Following TDD - tests written first.
"""
import pytest
from modules.pricing_engine import normalize_features, calculate_quote
from modules.domain import PartFeatures, QuoteResult


@pytest.fixture
def simple_pricing_config():
    """Create a simple deterministic pricing config for testing."""
    return {
        "base_price": 10.0,
        "minimum_order_price": 30.0,
        "r_squared": 0.85,
        "coefficients": {
            "volume": 0.001,
            "through_hole_count": 2.0,
            "blind_hole_count": 3.0,
            "blind_hole_avg_depth_to_diameter": 1.0,
            "blind_hole_max_depth_to_diameter": 0.5,
            "pocket_count": 5.0,
            "pocket_total_volume": 0.002,
            "pocket_avg_depth": 0.5,
            "pocket_max_depth": 0.3,
            "non_standard_hole_count": 10.0,
        },
        "scaler_mean": {
            "volume": 1000.0,
            "through_hole_count": 2.0,
            "blind_hole_count": 1.0,
            "blind_hole_avg_depth_to_diameter": 3.0,
            "blind_hole_max_depth_to_diameter": 5.0,
            "pocket_count": 1.0,
            "pocket_total_volume": 100.0,
            "pocket_avg_depth": 5.0,
            "pocket_max_depth": 10.0,
            "non_standard_hole_count": 0.0,
        },
        "scaler_std": {
            "volume": 500.0,
            "through_hole_count": 1.0,
            "blind_hole_count": 0.5,
            "blind_hole_avg_depth_to_diameter": 1.0,
            "blind_hole_max_depth_to_diameter": 2.0,
            "pocket_count": 0.5,
            "pocket_total_volume": 50.0,
            "pocket_avg_depth": 2.0,
            "pocket_max_depth": 5.0,
            "non_standard_hole_count": 1.0,
        },
    }


@pytest.fixture
def untrained_pricing_config():
    """Create a pricing config for untrained model (r_squared = 0.0)."""
    return {
        "base_price": 10.0,
        "minimum_order_price": 30.0,
        "r_squared": 0.0,  # Untrained model
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
        "scaler_mean": {
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
        "scaler_std": {
            "volume": 1.0,
            "through_hole_count": 1.0,
            "blind_hole_count": 1.0,
            "blind_hole_avg_depth_to_diameter": 1.0,
            "blind_hole_max_depth_to_diameter": 1.0,
            "pocket_count": 1.0,
            "pocket_total_volume": 1.0,
            "pocket_avg_depth": 1.0,
            "pocket_max_depth": 1.0,
            "non_standard_hole_count": 1.0,
        },
    }


class TestNormalizeFeatures:
    """Test feature normalization."""

    def test_normalize_simple_features(self):
        """Test that features are normalized using (x - mean) / std."""
        features_dict = {"volume": 1500.0, "through_hole_count": 3.0}
        mean = {"volume": 1000.0, "through_hole_count": 2.0}
        std = {"volume": 500.0, "through_hole_count": 1.0}

        normalized = normalize_features(features_dict, mean, std)

        # volume: (1500 - 1000) / 500 = 1.0
        assert abs(normalized["volume"] - 1.0) < 0.001
        # through_hole_count: (3 - 2) / 1 = 1.0
        assert abs(normalized["through_hole_count"] - 1.0) < 0.001

    def test_normalize_returns_dict(self):
        """Test that normalize_features returns a dictionary."""
        features_dict = {"volume": 1000.0}
        mean = {"volume": 1000.0}
        std = {"volume": 500.0}

        normalized = normalize_features(features_dict, mean, std)

        assert isinstance(normalized, dict)

    def test_normalize_handles_zero_mean(self):
        """Test normalization when mean is zero."""
        features_dict = {"volume": 100.0}
        mean = {"volume": 0.0}
        std = {"volume": 50.0}

        normalized = normalize_features(features_dict, mean, std)

        # (100 - 0) / 50 = 2.0
        assert abs(normalized["volume"] - 2.0) < 0.001

    def test_normalize_handles_multiple_features(self):
        """Test normalization with multiple features."""
        features_dict = {
            "volume": 1500.0,
            "through_hole_count": 4.0,
            "blind_hole_count": 2.0,
        }
        mean = {
            "volume": 1000.0,
            "through_hole_count": 2.0,
            "blind_hole_count": 1.0,
        }
        std = {
            "volume": 500.0,
            "through_hole_count": 1.0,
            "blind_hole_count": 0.5,
        }

        normalized = normalize_features(features_dict, mean, std)

        assert "volume" in normalized
        assert "through_hole_count" in normalized
        assert "blind_hole_count" in normalized


class TestCalculateQuote:
    """Test quote calculation."""

    def test_untrained_model_raises_error(self, untrained_pricing_config):
        """Test that untrained model (r_squared = 0.0) raises error."""
        features = PartFeatures(volume=1000.0)
        quantity = 10

        with pytest.raises(Exception) as exc_info:
            calculate_quote(features, quantity, untrained_pricing_config)

        error_msg = str(exc_info.value)
        assert "training" in error_msg.lower() or "not ready" in error_msg.lower()

    def test_quantity_over_50_raises_error(self, simple_pricing_config):
        """Test that quantity > 50 raises error."""
        features = PartFeatures(volume=1000.0)
        quantity = 51

        with pytest.raises(Exception) as exc_info:
            calculate_quote(features, quantity, simple_pricing_config)

        error_msg = str(exc_info.value)
        assert "50" in error_msg or "quantity" in error_msg.lower()

    def test_returns_quote_result(self, simple_pricing_config):
        """Test that calculate_quote returns a QuoteResult."""
        features = PartFeatures(volume=1000.0)
        quantity = 10

        result = calculate_quote(features, quantity, simple_pricing_config)

        assert isinstance(result, QuoteResult)

    def test_quote_has_required_fields(self, simple_pricing_config):
        """Test that quote has all required fields."""
        features = PartFeatures(volume=1000.0)
        quantity = 10

        result = calculate_quote(features, quantity, simple_pricing_config)

        assert hasattr(result, "price_per_unit")
        assert hasattr(result, "total_price")
        assert hasattr(result, "quantity")
        assert hasattr(result, "breakdown")
        assert hasattr(result, "minimum_applied")

    def test_minimum_order_applies_for_small_order(self, simple_pricing_config):
        """Test that minimum order price (€30) applies for small orders."""
        # Simple part with low calculated price
        features = PartFeatures(volume=100.0)
        quantity = 1

        result = calculate_quote(features, quantity, simple_pricing_config)

        # Total should be at least €30
        assert result.total_price >= 30.0
        # minimum_applied flag should be True
        assert result.minimum_applied is True

    def test_minimum_not_applied_for_large_order(self, simple_pricing_config):
        """Test that minimum doesn't apply when price exceeds minimum."""
        # Use features close to mean values with high quantity to exceed €30
        # This ensures positive prediction
        features = PartFeatures(
            volume=1000.0,  # At mean
            through_hole_count=2,  # At mean
            blind_hole_count=1,  # At mean
            pocket_count=1,  # At mean
        )
        quantity = 50  # High quantity

        result = calculate_quote(features, quantity, simple_pricing_config)

        # With quantity=50 and price ~€10/unit, total should be ~€500 > €30
        # minimum_applied should be False
        assert result.minimum_applied is False

    def test_quantity_scaling_works(self, simple_pricing_config):
        """Test that quantity affects total price correctly."""
        features = PartFeatures(volume=5000.0)

        result_qty_1 = calculate_quote(features, 1, simple_pricing_config)
        result_qty_10 = calculate_quote(features, 10, simple_pricing_config)

        # Total price should scale with quantity (if not limited by minimum)
        # Price per unit should be the same
        if not result_qty_1.minimum_applied and not result_qty_10.minimum_applied:
            assert abs(result_qty_1.price_per_unit - result_qty_10.price_per_unit) < 0.01
            assert abs(result_qty_10.total_price - result_qty_1.total_price * 10) < 0.1

    def test_breakdown_dict_exists(self, simple_pricing_config):
        """Test that breakdown dict is included in result."""
        features = PartFeatures(volume=1000.0)
        quantity = 10

        result = calculate_quote(features, quantity, simple_pricing_config)

        assert isinstance(result.breakdown, dict)

    def test_breakdown_has_base_price(self, simple_pricing_config):
        """Test that breakdown includes base price."""
        features = PartFeatures(volume=1000.0)
        quantity = 10

        result = calculate_quote(features, quantity, simple_pricing_config)

        assert "base_price" in result.breakdown

    def test_breakdown_stable(self, simple_pricing_config):
        """Test that breakdown dict has stable keys."""
        features = PartFeatures(volume=1000.0)
        quantity = 10

        result1 = calculate_quote(features, quantity, simple_pricing_config)
        result2 = calculate_quote(features, quantity, simple_pricing_config)

        # Same features should produce same breakdown keys
        assert set(result1.breakdown.keys()) == set(result2.breakdown.keys())

    def test_quantity_stored_in_result(self, simple_pricing_config):
        """Test that quantity is stored in result."""
        features = PartFeatures(volume=1000.0)
        quantity = 5

        result = calculate_quote(features, quantity, simple_pricing_config)

        assert result.quantity == 5

    def test_price_per_unit_calculated(self, simple_pricing_config):
        """Test that price_per_unit is calculated."""
        features = PartFeatures(volume=1000.0)
        quantity = 10

        result = calculate_quote(features, quantity, simple_pricing_config)

        # price_per_unit should be total_price / quantity
        expected_per_unit = result.total_price / quantity
        assert abs(result.price_per_unit - expected_per_unit) < 0.01

    def test_quantity_1_passes(self, simple_pricing_config):
        """Test that quantity = 1 is valid."""
        features = PartFeatures(volume=1000.0)
        quantity = 1

        result = calculate_quote(features, quantity, simple_pricing_config)

        assert result.quantity == 1

    def test_quantity_50_passes(self, simple_pricing_config):
        """Test that quantity = 50 is valid (at limit)."""
        features = PartFeatures(volume=1000.0)
        quantity = 50

        result = calculate_quote(features, quantity, simple_pricing_config)

        assert result.quantity == 50
