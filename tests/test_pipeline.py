"""
Test suite for pipeline orchestrator.
Following TDD - tests written first.
"""
import os
import tempfile
import json
import pytest
import cadquery as cq
from modules.pipeline import process_quote
from modules.domain import ProcessingResult


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def simple_step_file(temp_dir):
    """Create a simple STEP file (10×20×30mm box)."""
    box = cq.Workplane("XY").box(10, 20, 30)
    step_path = os.path.join(temp_dir, "test_part.step")
    cq.exporters.export(box, step_path)
    return step_path


@pytest.fixture
def deterministic_pricing_config(temp_dir):
    """Create a deterministic pricing config file for testing."""
    config = {
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

    config_path = os.path.join(temp_dir, "pricing_config.json")
    with open(config_path, "w") as f:
        json.dump(config, f)

    return config_path


class TestProcessQuote:
    """Test end-to-end pipeline orchestration."""

    def test_returns_processing_result(self, simple_step_file, deterministic_pricing_config):
        """Test that process_quote returns a ProcessingResult."""
        result = process_quote(simple_step_file, 10, deterministic_pricing_config)

        assert isinstance(result, ProcessingResult)

    def test_result_has_part_id(self, simple_step_file, deterministic_pricing_config):
        """Test that result includes a part_id."""
        result = process_quote(simple_step_file, 10, deterministic_pricing_config)

        assert hasattr(result, "part_id")
        assert isinstance(result.part_id, str)
        assert len(result.part_id) > 0

    def test_result_has_step_file_path(self, simple_step_file, deterministic_pricing_config):
        """Test that result includes step_file_path."""
        result = process_quote(simple_step_file, 10, deterministic_pricing_config)

        assert result.step_file_path == simple_step_file

    def test_result_has_features(self, simple_step_file, deterministic_pricing_config):
        """Test that result includes detected features."""
        result = process_quote(simple_step_file, 10, deterministic_pricing_config)

        assert hasattr(result, "features")
        assert hasattr(result.features, "bounding_box_x")
        assert hasattr(result.features, "volume")

    def test_features_detected_correctly(self, simple_step_file, deterministic_pricing_config):
        """Test that features are detected correctly (10×20×30mm box)."""
        result = process_quote(simple_step_file, 10, deterministic_pricing_config)

        # Box is 10×20×30mm
        tolerance = 0.1
        assert abs(result.features.bounding_box_x - 10.0) < tolerance
        assert abs(result.features.bounding_box_y - 20.0) < tolerance
        assert abs(result.features.bounding_box_z - 30.0) < tolerance

        # Volume is 10×20×30 = 6000 mm³
        assert abs(result.features.volume - 6000.0) < 10.0

    def test_result_has_confidence(self, simple_step_file, deterministic_pricing_config):
        """Test that result includes confidence scores."""
        result = process_quote(simple_step_file, 10, deterministic_pricing_config)

        assert hasattr(result, "confidence")
        # Bbox and volume should have confidence 1.0
        assert result.confidence.bounding_box == 1.0
        assert result.confidence.volume == 1.0

    def test_result_has_quote(self, simple_step_file, deterministic_pricing_config):
        """Test that result includes pricing quote."""
        result = process_quote(simple_step_file, 10, deterministic_pricing_config)

        assert hasattr(result, "quote")
        assert result.quote is not None
        assert hasattr(result.quote, "total_price")
        assert hasattr(result.quote, "price_per_unit")

    def test_quote_respects_minimum_order(self, simple_step_file, deterministic_pricing_config):
        """Test that minimum order price is applied when needed."""
        result = process_quote(simple_step_file, 1, deterministic_pricing_config)

        # With quantity 1 and small part, minimum (€30) should apply
        assert result.quote.total_price >= 30.0
        assert result.quote.minimum_applied is True

    def test_result_has_dfm_issues(self, simple_step_file, deterministic_pricing_config):
        """Test that result includes dfm_issues list."""
        result = process_quote(simple_step_file, 10, deterministic_pricing_config)

        assert hasattr(result, "dfm_issues")
        assert isinstance(result.dfm_issues, list)

    def test_result_has_errors_list(self, simple_step_file, deterministic_pricing_config):
        """Test that result includes errors list."""
        result = process_quote(simple_step_file, 10, deterministic_pricing_config)

        assert hasattr(result, "errors")
        assert isinstance(result.errors, list)

    def test_successful_processing_has_no_errors(self, simple_step_file, deterministic_pricing_config):
        """Test that successful processing has empty errors list."""
        result = process_quote(simple_step_file, 10, deterministic_pricing_config)

        assert len(result.errors) == 0

    def test_oversized_part_raises_error(self, temp_dir, deterministic_pricing_config):
        """Test that oversized part (>600×400×500mm) is rejected."""
        # Create a box that exceeds X limit
        large_box = cq.Workplane("XY").box(700, 200, 300)
        step_path = os.path.join(temp_dir, "large_part.step")
        cq.exporters.export(large_box, step_path)

        # Should raise BoundingBoxLimitError
        with pytest.raises(Exception) as exc_info:
            process_quote(step_path, 10, deterministic_pricing_config)

        error_msg = str(exc_info.value)
        assert "600" in error_msg or "exceed" in error_msg.lower()

    def test_invalid_quantity_raises_error(self, simple_step_file, deterministic_pricing_config):
        """Test that invalid quantity (>50) raises error."""
        with pytest.raises(Exception) as exc_info:
            process_quote(simple_step_file, 51, deterministic_pricing_config)

        error_msg = str(exc_info.value)
        assert "quantity" in error_msg.lower() or "50" in error_msg

    def test_result_serializable(self, simple_step_file, deterministic_pricing_config):
        """Test that result can be serialized to dict."""
        result = process_quote(simple_step_file, 10, deterministic_pricing_config)

        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert "part_id" in result_dict
        assert "features" in result_dict
        assert "quote" in result_dict

    def test_multiple_quantities(self, simple_step_file, deterministic_pricing_config):
        """Test processing with different quantities."""
        result_qty_1 = process_quote(simple_step_file, 1, deterministic_pricing_config)
        result_qty_10 = process_quote(simple_step_file, 10, deterministic_pricing_config)

        # Both should succeed
        assert result_qty_1.quote is not None
        assert result_qty_10.quote is not None

        # Quantity should be stored correctly
        assert result_qty_1.quote.quantity == 1
        assert result_qty_10.quote.quantity == 10

    def test_stl_file_path_present(self, simple_step_file, deterministic_pricing_config):
        """Test that stl_file_path field is present (even if empty for now)."""
        result = process_quote(simple_step_file, 10, deterministic_pricing_config)

        assert hasattr(result, "stl_file_path")
        # For now, STL generation not implemented, so should be empty string
        assert isinstance(result.stl_file_path, str)
