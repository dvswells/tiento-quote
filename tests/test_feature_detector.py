"""
Test suite for feature detection (bounding box and volume).
Following TDD - tests written first.
"""
import os
import tempfile
import pytest
import cadquery as cq
from modules.feature_detector import detect_bbox_and_volume
from modules.domain import PartFeatures, FeatureConfidence


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def box_10x20x30(temp_dir):
    """Create a 10×20×30mm box STEP file."""
    # Create box with precise dimensions
    box = cq.Workplane("XY").box(10, 20, 30)

    step_path = os.path.join(temp_dir, "box_10x20x30.step")
    cq.exporters.export(box, step_path)

    return step_path


@pytest.fixture
def box_5x5x5(temp_dir):
    """Create a 5×5×5mm cube STEP file."""
    cube = cq.Workplane("XY").box(5, 5, 5)

    step_path = os.path.join(temp_dir, "cube_5x5x5.step")
    cq.exporters.export(cube, step_path)

    return step_path


@pytest.fixture
def complex_shape(temp_dir):
    """Create a more complex shape for testing."""
    # Create a box with a hole (but we won't detect the hole yet)
    shape = (
        cq.Workplane("XY")
        .box(50, 40, 20)
        .faces(">Z")
        .workplane()
        .hole(5)
    )

    step_path = os.path.join(temp_dir, "complex.step")
    cq.exporters.export(shape, step_path)

    return step_path


class TestDetectBboxAndVolume:
    """Test bounding box and volume detection."""

    def test_returns_tuple_of_features_and_confidence(self, box_10x20x30):
        """Test that function returns (PartFeatures, FeatureConfidence) tuple."""
        result = detect_bbox_and_volume(box_10x20x30)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], PartFeatures)
        assert isinstance(result[1], FeatureConfidence)

    def test_box_10x20x30_dimensions(self, box_10x20x30):
        """Test that 10×20×30mm box has correct bounding box dimensions."""
        features, confidence = detect_bbox_and_volume(box_10x20x30)

        # Bounding box should match dimensions (within tolerance)
        tolerance = 0.1  # 0.1mm tolerance
        assert abs(features.bounding_box_x - 10.0) < tolerance
        assert abs(features.bounding_box_y - 20.0) < tolerance
        assert abs(features.bounding_box_z - 30.0) < tolerance

    def test_box_10x20x30_volume(self, box_10x20x30):
        """Test that 10×20×30mm box has volume of 6000mm³."""
        features, confidence = detect_bbox_and_volume(box_10x20x30)

        # Volume should be 10 × 20 × 30 = 6000 mm³
        expected_volume = 6000.0
        tolerance = 1.0  # 1mm³ tolerance
        assert abs(features.volume - expected_volume) < tolerance

    def test_cube_5x5x5_dimensions(self, box_5x5x5):
        """Test that 5×5×5mm cube has correct dimensions."""
        features, confidence = detect_bbox_and_volume(box_5x5x5)

        tolerance = 0.1
        assert abs(features.bounding_box_x - 5.0) < tolerance
        assert abs(features.bounding_box_y - 5.0) < tolerance
        assert abs(features.bounding_box_z - 5.0) < tolerance

    def test_cube_5x5x5_volume(self, box_5x5x5):
        """Test that 5×5×5mm cube has volume of 125mm³."""
        features, confidence = detect_bbox_and_volume(box_5x5x5)

        expected_volume = 125.0  # 5³
        tolerance = 1.0
        assert abs(features.volume - expected_volume) < tolerance

    def test_complex_shape_has_bbox(self, complex_shape):
        """Test that complex shape has valid bounding box."""
        features, confidence = detect_bbox_and_volume(complex_shape)

        # Should have dimensions around 50×40×20
        tolerance = 0.1
        assert abs(features.bounding_box_x - 50.0) < tolerance
        assert abs(features.bounding_box_y - 40.0) < tolerance
        assert abs(features.bounding_box_z - 20.0) < tolerance

    def test_complex_shape_volume_less_than_bbox_volume(self, complex_shape):
        """Test that shape with hole has volume less than bbox volume."""
        features, confidence = detect_bbox_and_volume(complex_shape)

        # Bbox volume would be 50×40×20 = 40000 mm³
        # But actual volume should be less (because of the hole)
        bbox_volume = 50.0 * 40.0 * 20.0
        assert features.volume < bbox_volume
        assert features.volume > 0

    def test_confidence_for_bbox_is_1_0(self, box_10x20x30):
        """Test that confidence for bounding box detection is 1.0."""
        features, confidence = detect_bbox_and_volume(box_10x20x30)

        assert confidence.bounding_box == 1.0

    def test_confidence_for_volume_is_1_0(self, box_10x20x30):
        """Test that confidence for volume detection is 1.0."""
        features, confidence = detect_bbox_and_volume(box_10x20x30)

        assert confidence.volume == 1.0

    def test_holes_remain_zero(self, box_10x20x30):
        """Test that hole counts remain zero (not detected yet)."""
        features, confidence = detect_bbox_and_volume(box_10x20x30)

        assert features.through_hole_count == 0
        assert features.blind_hole_count == 0
        assert features.blind_hole_avg_depth_to_diameter == 0.0
        assert features.blind_hole_max_depth_to_diameter == 0.0

    def test_pockets_remain_zero(self, box_10x20x30):
        """Test that pocket features remain zero (not detected yet)."""
        features, confidence = detect_bbox_and_volume(box_10x20x30)

        assert features.pocket_count == 0
        assert features.pocket_total_volume == 0.0
        assert features.pocket_avg_depth == 0.0
        assert features.pocket_max_depth == 0.0

    def test_non_standard_holes_remain_zero(self, box_10x20x30):
        """Test that non-standard hole count remains zero."""
        features, confidence = detect_bbox_and_volume(box_10x20x30)

        assert features.non_standard_hole_count == 0

    def test_other_confidences_remain_zero(self, box_10x20x30):
        """Test that confidences for undetected features remain 0.0."""
        features, confidence = detect_bbox_and_volume(box_10x20x30)

        assert confidence.through_holes == 0.0
        assert confidence.blind_holes == 0.0
        assert confidence.pockets == 0.0

    def test_nonexistent_file_raises_error(self, temp_dir):
        """Test that nonexistent file raises appropriate error."""
        nonexistent = os.path.join(temp_dir, "nonexistent.step")

        # Should raise an error (likely from cad_io.load_step)
        with pytest.raises(Exception):
            detect_bbox_and_volume(nonexistent)

    def test_bbox_values_are_positive(self, box_10x20x30):
        """Test that all bounding box values are positive."""
        features, confidence = detect_bbox_and_volume(box_10x20x30)

        assert features.bounding_box_x > 0
        assert features.bounding_box_y > 0
        assert features.bounding_box_z > 0

    def test_volume_is_positive(self, box_10x20x30):
        """Test that volume is positive."""
        features, confidence = detect_bbox_and_volume(box_10x20x30)

        assert features.volume > 0
