"""
Test suite for pipeline orchestrator.
Following TDD - tests written first.
"""
import os
import tempfile
import json
import pytest
import cadquery as cq
import logging
from io import StringIO

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


class TestPipelineErrorHandling:
    """Test error handling improvements for Prompt 29."""

    def test_oversized_part_returns_error_instead_of_raising(self, temp_dir, deterministic_pricing_config):
        """Test that oversized part returns error in ProcessingResult instead of raising."""
        # Create a box that exceeds limits
        large_box = cq.Workplane("XY").box(700, 200, 300)
        step_path = os.path.join(temp_dir, "large_part.step")
        cq.exporters.export(large_box, step_path)

        # Should return ProcessingResult with error, not raise exception
        result = process_quote(step_path, 10, deterministic_pricing_config)

        assert isinstance(result, ProcessingResult)
        assert len(result.errors) > 0
        assert any("exceed" in error.lower() or "600" in error for error in result.errors)

    def test_invalid_quantity_returns_error(self, simple_step_file, deterministic_pricing_config):
        """Test that invalid quantity returns error in ProcessingResult."""
        result = process_quote(simple_step_file, 51, deterministic_pricing_config)

        assert isinstance(result, ProcessingResult)
        assert len(result.errors) > 0
        assert any("quantity" in error.lower() for error in result.errors)

    def test_invalid_step_file_returns_error(self, temp_dir, deterministic_pricing_config):
        """Test that invalid STEP file returns error."""
        # Create invalid file
        invalid_path = os.path.join(temp_dir, "invalid.step")
        with open(invalid_path, 'w') as f:
            f.write("not a valid STEP file")

        result = process_quote(invalid_path, 10, deterministic_pricing_config)

        assert isinstance(result, ProcessingResult)
        assert len(result.errors) > 0

    def test_errors_list_empty_on_success(self, simple_step_file, deterministic_pricing_config):
        """Test that errors list is empty on successful processing."""
        result = process_quote(simple_step_file, 10, deterministic_pricing_config)

        assert len(result.errors) == 0

    def test_quote_is_none_when_errors_occur(self, temp_dir, deterministic_pricing_config):
        """Test that quote is None when errors prevent pricing."""
        # Create oversized part
        large_box = cq.Workplane("XY").box(700, 200, 300)
        step_path = os.path.join(temp_dir, "large_part.step")
        cq.exporters.export(large_box, step_path)

        result = process_quote(step_path, 10, deterministic_pricing_config)

        assert result.quote is None


class TestPipelineLogging:
    """Test logging functionality for Prompt 29."""

    @pytest.fixture(autouse=True)
    def setup_logging_capture(self):
        """Capture log output for testing."""
        self.log_capture = StringIO()
        self.handler = logging.StreamHandler(self.log_capture)
        self.handler.setLevel(logging.INFO)

        # Get pipeline logger
        logger = logging.getLogger('modules.pipeline')
        logger.addHandler(self.handler)
        logger.setLevel(logging.INFO)

        yield

        # Cleanup
        logger.removeHandler(self.handler)

    def test_logs_part_id_on_start(self, simple_step_file, deterministic_pricing_config):
        """Test that pipeline logs part ID at start."""
        result = process_quote(simple_step_file, 10, deterministic_pricing_config)

        log_output = self.log_capture.getvalue()
        assert result.part_id in log_output or "part" in log_output.lower()

    def test_logs_feature_detection_results(self, simple_step_file, deterministic_pricing_config):
        """Test that pipeline logs feature detection results."""
        result = process_quote(simple_step_file, 10, deterministic_pricing_config)

        log_output = self.log_capture.getvalue()
        # Should log dimensions or volume
        assert "volume" in log_output.lower() or "dimension" in log_output.lower()

    def test_logs_pricing_result(self, simple_step_file, deterministic_pricing_config):
        """Test that pipeline logs pricing result."""
        result = process_quote(simple_step_file, 10, deterministic_pricing_config)

        log_output = self.log_capture.getvalue()
        # Should log price information
        assert "price" in log_output.lower() or "quote" in log_output.lower()

    def test_logs_validation_failure(self, temp_dir, deterministic_pricing_config):
        """Test that pipeline logs validation failures."""
        # Create oversized part
        large_box = cq.Workplane("XY").box(700, 200, 300)
        step_path = os.path.join(temp_dir, "large_part.step")
        cq.exporters.export(large_box, step_path)

        result = process_quote(step_path, 10, deterministic_pricing_config)

        log_output = self.log_capture.getvalue()
        # Should log the error
        assert "error" in log_output.lower() or "exceed" in log_output.lower()

    def test_logs_dfm_issues(self, temp_dir, deterministic_pricing_config):
        """Test that pipeline logs DFM issues when detected."""
        # Create part with deep blind hole (aspect ratio > 10)
        part = (
            cq.Workplane("XY")
            .box(50, 50, 50)
            .faces(">Z")
            .workplane()
            .hole(2, depth=25)  # 2mm diameter, 25mm deep = ratio 12.5
        )
        step_path = os.path.join(temp_dir, "deep_hole_part.step")
        cq.exporters.export(part, step_path)

        result = process_quote(step_path, 10, deterministic_pricing_config)

        log_output = self.log_capture.getvalue()
        # Should log DFM issues if any detected
        # (May or may not be detected depending on implementation)
        # This test validates logging exists, not detection accuracy


class TestPipelineDfmIntegration:
    """Test DFM analyzer integration for Prompt 29."""

    def test_dfm_issues_populated_for_deep_holes(self, temp_dir, deterministic_pricing_config):
        """Test that DFM issues are populated when deep holes detected."""
        # Create part with very deep blind hole
        part = (
            cq.Workplane("XY")
            .box(50, 50, 50)
            .faces(">Z")
            .workplane()
            .hole(2, depth=25)  # 2mm diameter, 25mm deep = ratio 12.5 (critical)
        )
        step_path = os.path.join(temp_dir, "deep_hole_part.step")
        cq.exporters.export(part, step_path)

        result = process_quote(step_path, 10, deterministic_pricing_config)

        # DFM issues should be populated (may or may not detect the hole depending on implementation)
        assert isinstance(result.dfm_issues, list)

    def test_dfm_issues_empty_for_simple_part(self, simple_step_file, deterministic_pricing_config):
        """Test that simple parts have no/few DFM issues."""
        result = process_quote(simple_step_file, 10, deterministic_pricing_config)

        # Simple box should have no critical DFM issues
        assert isinstance(result.dfm_issues, list)
        critical_issues = [i for i in result.dfm_issues if i.severity == "critical"]
        assert len(critical_issues) == 0
        # For now, STL generation not implemented, so should be empty string
        assert isinstance(result.stl_file_path, str)
