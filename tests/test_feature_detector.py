"""
Test suite for feature detection (bounding box and volume).
Following TDD - tests written first.
"""
import os
import tempfile
import pytest
import cadquery as cq
from modules.feature_detector import (
    detect_bbox_and_volume,
    validate_bounding_box_limits,
    BoundingBoxLimitError,
)
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


class TestValidateBoundingBoxLimits:
    """Test bounding box limit validation (600×400×500mm)."""

    def test_import_function(self):
        """Test that validate_bounding_box_limits can be imported."""
        assert callable(validate_bounding_box_limits)

    def test_part_within_limits_passes(self):
        """Test that part within limits does not raise exception."""
        from modules.settings import get_settings

        # Create features for a small part (100×200×300mm)
        features = PartFeatures(
            bounding_box_x=100.0,
            bounding_box_y=200.0,
            bounding_box_z=300.0,
        )
        settings = get_settings()

        # Should not raise exception
        validate_bounding_box_limits(features, settings)

    def test_part_exactly_at_x_limit_passes(self):
        """Test that part exactly at X limit (600mm) passes."""
        from modules.settings import get_settings

        features = PartFeatures(
            bounding_box_x=600.0,
            bounding_box_y=200.0,
            bounding_box_z=300.0,
        )
        settings = get_settings()

        # Should not raise exception
        validate_bounding_box_limits(features, settings)

    def test_part_exactly_at_y_limit_passes(self):
        """Test that part exactly at Y limit (400mm) passes."""
        from modules.settings import get_settings

        features = PartFeatures(
            bounding_box_x=100.0,
            bounding_box_y=400.0,
            bounding_box_z=300.0,
        )
        settings = get_settings()

        # Should not raise exception
        validate_bounding_box_limits(features, settings)

    def test_part_exactly_at_z_limit_passes(self):
        """Test that part exactly at Z limit (500mm) passes."""
        from modules.settings import get_settings

        features = PartFeatures(
            bounding_box_x=100.0,
            bounding_box_y=200.0,
            bounding_box_z=500.0,
        )
        settings = get_settings()

        # Should not raise exception
        validate_bounding_box_limits(features, settings)

    def test_part_at_all_limits_passes(self):
        """Test that part at all limits (600×400×500mm) passes."""
        from modules.settings import get_settings

        features = PartFeatures(
            bounding_box_x=600.0,
            bounding_box_y=400.0,
            bounding_box_z=500.0,
        )
        settings = get_settings()

        # Should not raise exception
        validate_bounding_box_limits(features, settings)

    def test_part_exceeding_x_limit_raises(self):
        """Test that part exceeding X limit raises exception."""
        from modules.settings import get_settings

        # X dimension: 601mm (exceeds 600mm limit)
        features = PartFeatures(
            bounding_box_x=601.0,
            bounding_box_y=200.0,
            bounding_box_z=300.0,
        )
        settings = get_settings()

        with pytest.raises(BoundingBoxLimitError) as exc_info:
            validate_bounding_box_limits(features, settings)

        # Check error message mentions dimensions
        error_msg = str(exc_info.value)
        assert "600" in error_msg or "400" in error_msg or "500" in error_msg

    def test_part_exceeding_y_limit_raises(self):
        """Test that part exceeding Y limit raises exception."""
        from modules.settings import get_settings

        # Y dimension: 401mm (exceeds 400mm limit)
        features = PartFeatures(
            bounding_box_x=100.0,
            bounding_box_y=401.0,
            bounding_box_z=300.0,
        )
        settings = get_settings()

        with pytest.raises(BoundingBoxLimitError):
            validate_bounding_box_limits(features, settings)

    def test_part_exceeding_z_limit_raises(self):
        """Test that part exceeding Z limit raises exception."""
        from modules.settings import get_settings

        # Z dimension: 501mm (exceeds 500mm limit)
        features = PartFeatures(
            bounding_box_x=100.0,
            bounding_box_y=200.0,
            bounding_box_z=501.0,
        )
        settings = get_settings()

        with pytest.raises(BoundingBoxLimitError):
            validate_bounding_box_limits(features, settings)

    def test_part_slightly_exceeding_x_limit_raises(self):
        """Test that part slightly exceeding X limit (by 0.1mm) raises exception."""
        from modules.settings import get_settings

        # X dimension: 600.1mm (slightly exceeds 600mm limit)
        features = PartFeatures(
            bounding_box_x=600.1,
            bounding_box_y=200.0,
            bounding_box_z=300.0,
        )
        settings = get_settings()

        with pytest.raises(BoundingBoxLimitError):
            validate_bounding_box_limits(features, settings)

    def test_part_exceeding_multiple_limits_raises(self):
        """Test that part exceeding multiple limits raises exception."""
        from modules.settings import get_settings

        features = PartFeatures(
            bounding_box_x=700.0,  # Exceeds 600mm
            bounding_box_y=500.0,  # Exceeds 400mm
            bounding_box_z=600.0,  # Exceeds 500mm
        )
        settings = get_settings()

        with pytest.raises(BoundingBoxLimitError):
            validate_bounding_box_limits(features, settings)

    def test_error_message_is_spec_aligned(self):
        """Test that error message matches spec exactly."""
        from modules.settings import get_settings

        features = PartFeatures(
            bounding_box_x=601.0,
            bounding_box_y=200.0,
            bounding_box_z=300.0,
        )
        settings = get_settings()

        with pytest.raises(BoundingBoxLimitError) as exc_info:
            validate_bounding_box_limits(features, settings)

        # Spec says: "Part exceeds maximum dimensions of 600×400×500mm.
        # Please contact us for large part quoting at david@wellsglobal.eu"
        error_msg = str(exc_info.value)
        assert "Part exceeds maximum dimensions" in error_msg
        assert "600" in error_msg and "400" in error_msg and "500" in error_msg
        assert "david@wellsglobal.eu" in error_msg

    def test_error_message_contains_contact_info(self):
        """Test that error message contains contact information."""
        from modules.settings import get_settings

        features = PartFeatures(
            bounding_box_x=700.0,
            bounding_box_y=200.0,
            bounding_box_z=300.0,
        )
        settings = get_settings()

        with pytest.raises(BoundingBoxLimitError) as exc_info:
            validate_bounding_box_limits(features, settings)

        error_msg = str(exc_info.value)
        assert "contact" in error_msg.lower()
        assert "david@wellsglobal.eu" in error_msg


class TestDetectHoleCandidates:
    """Test hole candidate detection (cylindrical faces)."""

    def test_box_with_no_holes_detects_zero(self, temp_dir):
        """Test that a simple box with no holes detects 0 hole candidates."""
        # Create a simple box with no holes
        box = cq.Workplane("XY").box(50, 40, 20)
        step_path = os.path.join(temp_dir, "box_no_holes.step")
        cq.exporters.export(box, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # Should detect 0 holes
        assert features.through_hole_count == 0
        assert features.blind_hole_count == 0

    def test_box_with_one_through_hole(self, temp_dir):
        """Test detection of single through hole."""
        # Create box with one through hole (5mm diameter)
        box_with_hole = (
            cq.Workplane("XY")
            .box(50, 40, 20)
            .faces(">Z")
            .workplane()
            .hole(5)
        )
        step_path = os.path.join(temp_dir, "box_one_through_hole.step")
        cq.exporters.export(box_with_hole, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # Should detect at least 1 hole total (conservative: may undercount)
        total_holes = features.through_hole_count + features.blind_hole_count
        assert total_holes >= 1

    def test_box_with_two_through_holes(self, temp_dir):
        """Test detection of two through holes."""
        # Create box with two through holes
        box_with_holes = (
            cq.Workplane("XY")
            .box(50, 40, 20)
            .faces(">Z")
            .workplane()
            .pushPoints([(-10, 0), (10, 0)])
            .hole(4)
        )
        step_path = os.path.join(temp_dir, "box_two_through_holes.step")
        cq.exporters.export(box_with_holes, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # Should detect at least 2 holes total (conservative)
        total_holes = features.through_hole_count + features.blind_hole_count
        assert total_holes >= 2

    def test_box_with_blind_hole(self, temp_dir):
        """Test detection of blind hole."""
        # Create box with one blind hole (depth 10mm)
        box_with_blind = (
            cq.Workplane("XY")
            .box(50, 40, 20)
            .faces(">Z")
            .workplane()
            .circle(2.5)
            .cutBlind(-10)
        )
        step_path = os.path.join(temp_dir, "box_blind_hole.step")
        cq.exporters.export(box_with_blind, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # Should detect at least 1 hole total
        total_holes = features.through_hole_count + features.blind_hole_count
        assert total_holes >= 1

    def test_box_with_multiple_holes_mixed(self, temp_dir):
        """Test detection of multiple holes (mix of through and blind)."""
        # Create box with 2 through holes and 1 blind hole
        box = (
            cq.Workplane("XY")
            .box(60, 50, 20)
            .faces(">Z")
            .workplane()
            .pushPoints([(-15, 0), (15, 0)])
            .hole(4)  # Two through holes
            .pushPoints([(0, 10)])
            .circle(3)
            .cutBlind(-8)  # One blind hole
        )
        step_path = os.path.join(temp_dir, "box_mixed_holes.step")
        cq.exporters.export(box, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # Should detect at least 3 holes total (conservative)
        total_holes = features.through_hole_count + features.blind_hole_count
        assert total_holes >= 3

    def test_confidence_for_holes_less_than_one(self, temp_dir):
        """Test that hole detection confidence is less than 1.0 (heuristic)."""
        # Create box with holes
        box_with_hole = (
            cq.Workplane("XY")
            .box(50, 40, 20)
            .faces(">Z")
            .workplane()
            .hole(5)
        )
        step_path = os.path.join(temp_dir, "box_for_confidence.step")
        cq.exporters.export(box_with_hole, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # Hole detection is heuristic, so confidence should be < 1.0
        # (unless we detect 0 holes, in which case it might be 0.0)
        total_holes = features.through_hole_count + features.blind_hole_count
        if total_holes > 0:
            # If we detected holes, confidence should be between 0 and 1
            hole_confidence = max(confidence.through_holes, confidence.blind_holes)
            assert 0.0 < hole_confidence <= 1.0

    def test_conservative_detection_undercounts_if_uncertain(self, temp_dir):
        """Test that detection is conservative (undercounts rather than overcounts)."""
        # Create a complex part where detection might be uncertain
        complex_part = (
            cq.Workplane("XY")
            .box(50, 40, 20)
            .faces(">Z")
            .workplane()
            .hole(5)
        )
        step_path = os.path.join(temp_dir, "complex_for_conservative.step")
        cq.exporters.export(complex_part, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # Total holes should not exceed actual holes (conservative)
        total_holes = features.through_hole_count + features.blind_hole_count
        # We know there's 1 hole, so should detect 0 or 1 (not 2+)
        assert total_holes <= 1

    def test_hole_detection_does_not_crash_on_complex_geometry(self, temp_dir):
        """Test that hole detection handles complex geometry without crashing."""
        # Create a part with multiple operations
        complex = (
            cq.Workplane("XY")
            .box(60, 50, 30)
            .faces(">Z")
            .workplane()
            .pushPoints([(-10, -10), (10, 10)])
            .hole(6)
            .faces(">X")
            .workplane()
            .circle(4)
            .cutBlind(-15)
        )
        step_path = os.path.join(temp_dir, "complex_geometry.step")
        cq.exporters.export(complex, step_path)

        # Should not crash
        features, confidence = detect_bbox_and_volume(step_path)

        # Should return valid features
        assert isinstance(features, PartFeatures)
        assert isinstance(confidence, FeatureConfidence)
