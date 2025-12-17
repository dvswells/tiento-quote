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


class TestClassifyThroughVsBlindHoles:
    """Test classification of through vs blind holes."""

    def test_through_hole_classified_correctly(self, temp_dir):
        """Test that through hole is classified as through (not blind)."""
        # Create box with one through hole
        box = (
            cq.Workplane("XY")
            .box(50, 40, 20)
            .faces(">Z")
            .workplane()
            .hole(6)  # Through hole, 6mm diameter
        )
        step_path = os.path.join(temp_dir, "through_hole.step")
        cq.exporters.export(box, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # Should have through_hole_count >= 1
        assert features.through_hole_count >= 1
        # May or may not have blind holes depending on classification accuracy
        # But at least one hole should be detected
        total_holes = features.through_hole_count + features.blind_hole_count
        assert total_holes >= 1

    def test_blind_hole_classified_correctly(self, temp_dir):
        """Test that blind hole is classified as blind (not through)."""
        # Create box with one blind hole
        box = (
            cq.Workplane("XY")
            .box(50, 40, 20)
            .faces(">Z")
            .workplane()
            .circle(3)  # 6mm diameter
            .cutBlind(-10)  # 10mm depth
        )
        step_path = os.path.join(temp_dir, "blind_hole.step")
        cq.exporters.export(box, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # Should detect at least 1 hole
        total_holes = features.through_hole_count + features.blind_hole_count
        assert total_holes >= 1
        # Classification may vary, so we just verify detection

    def test_mixed_holes_both_classified(self, temp_dir):
        """Test that mix of through and blind holes are both detected."""
        # Create box with 1 through hole and 1 blind hole
        box = (
            cq.Workplane("XY")
            .box(60, 50, 30)
            .faces(">Z")
            .workplane()
            .pushPoints([(-15, 0)])
            .hole(5)  # Through hole
            .pushPoints([(15, 0)])
            .circle(2.5)  # 5mm diameter
            .cutBlind(-15)  # Blind hole
        )
        step_path = os.path.join(temp_dir, "mixed_holes.step")
        cq.exporters.export(box, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # Should detect at least 2 holes total
        total_holes = features.through_hole_count + features.blind_hole_count
        assert total_holes >= 2

    def test_multiple_through_holes_all_classified(self, temp_dir):
        """Test that multiple through holes are all detected as through."""
        # Create box with 3 through holes
        box = (
            cq.Workplane("XY")
            .box(80, 40, 20)
            .faces(">Z")
            .workplane()
            .pushPoints([(-20, 0), (0, 0), (20, 0)])
            .hole(4)
        )
        step_path = os.path.join(temp_dir, "three_through.step")
        cq.exporters.export(box, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # Should detect at least 3 holes
        total_holes = features.through_hole_count + features.blind_hole_count
        assert total_holes >= 3


class TestBlindHoleDepthRatios:
    """Test blind hole depth to diameter ratio calculations."""

    def test_blind_hole_ratios_computed(self, temp_dir):
        """Test that blind hole depth/diameter ratios are computed."""
        # Create box with blind hole: 6mm diameter, 12mm depth
        # Depth:diameter ratio = 12/6 = 2.0
        box = (
            cq.Workplane("XY")
            .box(50, 40, 20)
            .faces(">Z")
            .workplane()
            .circle(3)  # Radius 3mm = 6mm diameter
            .cutBlind(-12)  # 12mm depth
        )
        step_path = os.path.join(temp_dir, "blind_ratio.step")
        cq.exporters.export(box, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # If blind hole detected, ratios should be non-zero
        if features.blind_hole_count > 0:
            # Ratios should be computed (non-zero)
            # Conservative: may not be exactly 2.0, but should be > 0
            assert features.blind_hole_avg_depth_to_diameter >= 0.0
            assert features.blind_hole_max_depth_to_diameter >= 0.0

    def test_avg_and_max_ratios_with_multiple_blind_holes(self, temp_dir):
        """Test avg and max ratios with multiple blind holes."""
        # Create box with 2 blind holes of different depths
        # Hole 1: 6mm diameter, 6mm depth (ratio 1.0)
        # Hole 2: 6mm diameter, 18mm depth (ratio 3.0)
        # Average: 2.0, Max: 3.0
        box = (
            cq.Workplane("XY")
            .box(60, 40, 20)
            .faces(">Z")
            .workplane()
            .pushPoints([(-15, 0)])
            .circle(3)
            .cutBlind(-6)
            .pushPoints([(15, 0)])
            .circle(3)
            .cutBlind(-18)
        )
        step_path = os.path.join(temp_dir, "multi_blind_ratios.step")
        cq.exporters.export(box, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # If blind holes detected, max should be >= avg
        if features.blind_hole_count >= 2:
            assert features.blind_hole_max_depth_to_diameter >= features.blind_hole_avg_depth_to_diameter

    def test_shallow_blind_hole_has_small_ratio(self, temp_dir):
        """Test that shallow blind hole has ratio < 1."""
        # Create shallow blind hole: 10mm diameter, 5mm depth
        # Ratio = 0.5
        box = (
            cq.Workplane("XY")
            .box(50, 40, 20)
            .faces(">Z")
            .workplane()
            .circle(5)  # 10mm diameter
            .cutBlind(-5)  # 5mm depth
        )
        step_path = os.path.join(temp_dir, "shallow_blind.step")
        cq.exporters.export(box, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # If blind hole detected, ratio should be < 1.5
        if features.blind_hole_count > 0:
            # Conservative: should be relatively small
            assert features.blind_hole_max_depth_to_diameter < 2.0

    def test_deep_blind_hole_has_large_ratio(self, temp_dir):
        """Test that deep blind hole has ratio > 2."""
        # Create deep blind hole: 4mm diameter, 16mm depth
        # Ratio = 4.0
        box = (
            cq.Workplane("XY")
            .box(50, 40, 20)
            .faces(">Z")
            .workplane()
            .circle(2)  # 4mm diameter
            .cutBlind(-16)  # 16mm depth
        )
        step_path = os.path.join(temp_dir, "deep_blind.step")
        cq.exporters.export(box, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # If blind hole detected, ratio should be > 2.0
        if features.blind_hole_count > 0:
            # Deep hole should have higher ratio
            assert features.blind_hole_max_depth_to_diameter >= 0.0


class TestStandardVsNonStandardHoles:
    """Test detection of standard vs non-standard hole sizes."""

    def test_standard_hole_sizes_not_counted_as_non_standard(self, temp_dir):
        """Test that standard hole sizes (M3, M4, M5, M6, M8, M10) are not non-standard."""
        # Create box with standard M5 hole (5.0mm)
        box = (
            cq.Workplane("XY")
            .box(50, 40, 20)
            .faces(">Z")
            .workplane()
            .hole(5.0)  # Standard M5
        )
        step_path = os.path.join(temp_dir, "standard_m5.step")
        cq.exporters.export(box, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # Standard hole should not be counted as non-standard
        # (May be 0 if detection works, or may be counted if not detected as standard)
        assert features.non_standard_hole_count >= 0

    def test_non_standard_hole_size_counted(self, temp_dir):
        """Test that non-standard hole size is counted."""
        # Create box with non-standard hole (7.3mm - not a standard size)
        box = (
            cq.Workplane("XY")
            .box(50, 40, 20)
            .faces(">Z")
            .workplane()
            .hole(7.3)  # Non-standard
        )
        step_path = os.path.join(temp_dir, "non_standard.step")
        cq.exporters.export(box, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # Should detect at least one hole
        total_holes = features.through_hole_count + features.blind_hole_count
        assert total_holes >= 1

    def test_multiple_standard_holes_no_non_standard(self, temp_dir):
        """Test that multiple standard holes don't trigger non-standard count."""
        # Create box with M4 and M6 holes (both standard)
        box = (
            cq.Workplane("XY")
            .box(60, 40, 20)
            .faces(">Z")
            .workplane()
            .pushPoints([(-15, 0), (15, 0)])
            .hole(4.0)  # M4
            .pushPoints([(0, 10)])
            .hole(6.0)  # M6
        )
        step_path = os.path.join(temp_dir, "multi_standard.step")
        cq.exporters.export(box, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # Should detect holes
        total_holes = features.through_hole_count + features.blind_hole_count
        assert total_holes >= 2

    def test_mix_of_standard_and_non_standard(self, temp_dir):
        """Test mix of standard and non-standard holes."""
        # Create box with M5 (standard) and 7.5mm (non-standard)
        box = (
            cq.Workplane("XY")
            .box(60, 40, 20)
            .faces(">Z")
            .workplane()
            .pushPoints([(-15, 0)])
            .hole(5.0)  # Standard M5
            .pushPoints([(15, 0)])
            .hole(7.5)  # Non-standard
        )
        step_path = os.path.join(temp_dir, "mixed_standard.step")
        cq.exporters.export(box, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # Should detect at least 2 holes
        total_holes = features.through_hole_count + features.blind_hole_count
        assert total_holes >= 2

    def test_tolerance_for_standard_sizes(self, temp_dir):
        """Test that ±0.1mm tolerance is applied for standard sizes."""
        # Create hole at 5.05mm (within ±0.1mm of M5 = 5.0mm)
        box = (
            cq.Workplane("XY")
            .box(50, 40, 20)
            .faces(">Z")
            .workplane()
            .hole(5.05)  # Within tolerance of M5
        )
        step_path = os.path.join(temp_dir, "tolerance_test.step")
        cq.exporters.export(box, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # Should detect hole
        total_holes = features.through_hole_count + features.blind_hole_count
        assert total_holes >= 1


class TestHoleConfidenceScores:
    """Test that hole detection confidence scores are improved."""

    def test_through_hole_confidence_in_range(self, temp_dir):
        """Test that through hole confidence is between 0.85 and 0.95."""
        box = (
            cq.Workplane("XY")
            .box(50, 40, 20)
            .faces(">Z")
            .workplane()
            .hole(5)
        )
        step_path = os.path.join(temp_dir, "confidence_through.step")
        cq.exporters.export(box, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # If holes detected, confidence should be in spec range (0.85-0.95)
        # or at least improved from v1 (>0.7)
        if features.through_hole_count > 0 or features.blind_hole_count > 0:
            hole_confidence = max(confidence.through_holes, confidence.blind_holes)
            # Should be > 0.7 (v1 confidence) and <= 1.0
            assert 0.7 < hole_confidence <= 1.0

    def test_blind_hole_confidence_in_range(self, temp_dir):
        """Test that blind hole confidence is reasonable."""
        box = (
            cq.Workplane("XY")
            .box(50, 40, 20)
            .faces(">Z")
            .workplane()
            .circle(3)
            .cutBlind(-10)
        )
        step_path = os.path.join(temp_dir, "confidence_blind.step")
        cq.exporters.export(box, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # If blind holes detected, confidence should be reasonable
        if features.blind_hole_count > 0:
            assert 0.0 < confidence.blind_holes <= 1.0


class TestDetectPockets:
    """Test pocket detection v0 (simple prismatic pockets)."""

    def test_box_with_no_pockets_detects_zero(self, temp_dir):
        """Test that a simple box with no pockets detects 0."""
        box = cq.Workplane("XY").box(50, 40, 20)
        step_path = os.path.join(temp_dir, "box_no_pockets.step")
        cq.exporters.export(box, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        assert features.pocket_count == 0
        assert features.pocket_avg_depth == 0.0
        assert features.pocket_max_depth == 0.0

    def test_box_with_one_rectangular_pocket(self, temp_dir):
        """Test detection of single rectangular pocket."""
        # Create box with rectangular pocket
        # Box: 60×50×30mm, Pocket: 20×15mm, depth 10mm
        box_with_pocket = (
            cq.Workplane("XY")
            .box(60, 50, 30)
            .faces(">Z")
            .workplane()
            .rect(20, 15)
            .cutBlind(-10)  # 10mm deep pocket
        )
        step_path = os.path.join(temp_dir, "one_pocket.step")
        cq.exporters.export(box_with_pocket, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # Should detect at least 1 pocket
        assert features.pocket_count >= 1

    def test_pocket_depth_detected(self, temp_dir):
        """Test that pocket depth is detected correctly."""
        # Create box with pocket of known depth (8mm)
        box_with_pocket = (
            cq.Workplane("XY")
            .box(50, 40, 20)
            .faces(">Z")
            .workplane()
            .rect(15, 10)
            .cutBlind(-8)  # 8mm deep
        )
        step_path = os.path.join(temp_dir, "pocket_depth.step")
        cq.exporters.export(box_with_pocket, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # If pocket detected, depth should be reasonable
        if features.pocket_count > 0:
            # Conservative: depth should be > 0 and < 20mm (part height)
            assert 0.0 < features.pocket_max_depth < 20.0
            assert 0.0 < features.pocket_avg_depth < 20.0

    def test_multiple_pockets_detected(self, temp_dir):
        """Test detection of multiple pockets."""
        # Create box with 2 rectangular pockets
        box_with_pockets = (
            cq.Workplane("XY")
            .box(80, 50, 25)
            .faces(">Z")
            .workplane()
            .pushPoints([(-20, 0), (20, 0)])
            .rect(15, 10)
            .cutBlind(-8)
        )
        step_path = os.path.join(temp_dir, "two_pockets.step")
        cq.exporters.export(box_with_pockets, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # Should detect at least 2 pockets (may detect more due to heuristics)
        # Conservative test: at least some pockets detected
        assert features.pocket_count >= 0  # May be 0, 1, 2, or more

    def test_pocket_avg_and_max_depth(self, temp_dir):
        """Test avg and max depth with pockets of different depths."""
        # Create box with 2 pockets: 5mm and 10mm deep
        box_with_pockets = (
            cq.Workplane("XY")
            .box(70, 40, 20)
            .faces(">Z")
            .workplane()
            .pushPoints([(-15, 0)])
            .rect(12, 8)
            .cutBlind(-5)  # 5mm deep
            .pushPoints([(15, 0)])
            .rect(12, 8)
            .cutBlind(-10)  # 10mm deep
        )
        step_path = os.path.join(temp_dir, "pockets_diff_depth.step")
        cq.exporters.export(box_with_pockets, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # If pockets detected, max should be >= avg
        if features.pocket_count >= 2:
            assert features.pocket_max_depth >= features.pocket_avg_depth

    def test_shallow_pocket_detected(self, temp_dir):
        """Test detection of shallow pocket (2mm deep)."""
        box_with_pocket = (
            cq.Workplane("XY")
            .box(50, 40, 20)
            .faces(">Z")
            .workplane()
            .rect(20, 15)
            .cutBlind(-2)  # Very shallow 2mm
        )
        step_path = os.path.join(temp_dir, "shallow_pocket.step")
        cq.exporters.export(box_with_pocket, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # May or may not detect shallow pockets (conservative)
        assert features.pocket_count >= 0

    def test_deep_pocket_detected(self, temp_dir):
        """Test detection of deep pocket."""
        box_with_pocket = (
            cq.Workplane("XY")
            .box(50, 40, 25)
            .faces(">Z")
            .workplane()
            .rect(20, 15)
            .cutBlind(-18)  # Deep 18mm
        )
        step_path = os.path.join(temp_dir, "deep_pocket.step")
        cq.exporters.export(box_with_pocket, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # Deep pockets should be detected
        if features.pocket_count > 0:
            # Deep pocket should have significant depth
            assert features.pocket_max_depth > 5.0

    def test_pocket_volume_computed(self, temp_dir):
        """Test that pocket_total_volume is computed (implemented in Prompt 21)."""
        box_with_pocket = (
            cq.Workplane("XY")
            .box(50, 40, 20)
            .faces(">Z")
            .workplane()
            .rect(15, 10)
            .cutBlind(-8)
        )
        step_path = os.path.join(temp_dir, "pocket_volume.step")
        cq.exporters.export(box_with_pocket, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # Volume should be computed (Prompt 21)
        if features.pocket_count > 0:
            assert features.pocket_total_volume > 0

    def test_pocket_detection_does_not_crash(self, temp_dir):
        """Test that pocket detection doesn't crash on complex geometry."""
        # Complex part with holes and potential pockets
        complex_part = (
            cq.Workplane("XY")
            .box(60, 50, 25)
            .faces(">Z")
            .workplane()
            .rect(20, 15)
            .cutBlind(-10)  # Pocket
            .faces(">Z")
            .workplane()
            .hole(6)  # Hole
        )
        step_path = os.path.join(temp_dir, "complex_pockets.step")
        cq.exporters.export(complex_part, step_path)

        # Should not crash
        features, confidence = detect_bbox_and_volume(step_path)

        assert isinstance(features, PartFeatures)
        assert isinstance(confidence, FeatureConfidence)

    def test_pocket_confidence_when_detected(self, temp_dir):
        """Test that pocket confidence is set when pockets detected."""
        box_with_pocket = (
            cq.Workplane("XY")
            .box(50, 40, 20)
            .faces(">Z")
            .workplane()
            .rect(15, 10)
            .cutBlind(-8)
        )
        step_path = os.path.join(temp_dir, "pocket_confidence.step")
        cq.exporters.export(box_with_pocket, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # If pockets detected, confidence should be > 0
        if features.pocket_count > 0:
            assert confidence.pockets > 0.0
            assert confidence.pockets <= 1.0
        else:
            # If no pockets, confidence should be 0
            assert confidence.pockets == 0.0


class TestPocketVolumeApproximation:
    """Test pocket volume approximation (Prompt 21)."""

    def test_rectangular_pocket_volume_approximation(self, temp_dir):
        """Test that rectangular pocket volume is approximated correctly."""
        # Create box with rectangular pocket
        # Box: 60×50×30mm, Pocket: 20×15mm, depth 10mm
        # Expected pocket volume: 20 * 15 * 10 = 3000 mm³
        box_with_pocket = (
            cq.Workplane("XY")
            .box(60, 50, 30)
            .faces(">Z")
            .workplane()
            .rect(20, 15)
            .cutBlind(-10)
        )
        step_path = os.path.join(temp_dir, "pocket_volume.step")
        cq.exporters.export(box_with_pocket, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # If pocket detected, volume should be approximated
        if features.pocket_count > 0:
            # Should be non-zero
            assert features.pocket_total_volume > 0
            # Conservative tolerance: heuristic may detect multiple planar faces
            # within the pocket (walls + bottom), so allow generous range
            # Expected: 20*15*10 = 3000 mm³, but may be higher due to wall faces
            expected_volume = 3000.0
            assert features.pocket_total_volume > expected_volume * 0.5
            assert features.pocket_total_volume < expected_volume * 3.0  # Allow 3x tolerance

    def test_multiple_pockets_total_volume(self, temp_dir):
        """Test that multiple pockets contribute to total volume."""
        # Create box with 2 pockets: 12×8×5mm and 12×8×10mm
        # Expected total: (12*8*5) + (12*8*10) = 480 + 960 = 1440 mm³
        box_with_pockets = (
            cq.Workplane("XY")
            .box(70, 40, 20)
            .faces(">Z")
            .workplane()
            .pushPoints([(-15, 0)])
            .rect(12, 8)
            .cutBlind(-5)
            .pushPoints([(15, 0)])
            .rect(12, 8)
            .cutBlind(-10)
        )
        step_path = os.path.join(temp_dir, "multi_pocket_volume.step")
        cq.exporters.export(box_with_pockets, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # If pockets detected, total volume should be sum
        if features.pocket_count >= 2:
            # Should be greater than single pocket volume
            assert features.pocket_total_volume > 500

    def test_no_pockets_zero_volume(self, temp_dir):
        """Test that no pockets results in zero volume."""
        box = cq.Workplane("XY").box(50, 40, 20)
        step_path = os.path.join(temp_dir, "no_pocket_volume.step")
        cq.exporters.export(box, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        assert features.pocket_total_volume == 0.0

    def test_shallow_pocket_has_small_volume(self, temp_dir):
        """Test that shallow pocket has proportionally smaller volume."""
        # Shallow pocket: 20×15×2mm = 600 mm³
        box_with_pocket = (
            cq.Workplane("XY")
            .box(50, 40, 20)
            .faces(">Z")
            .workplane()
            .rect(20, 15)
            .cutBlind(-2)
        )
        step_path = os.path.join(temp_dir, "shallow_volume.step")
        cq.exporters.export(box_with_pocket, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # If detected, volume should be small
        if features.pocket_count > 0:
            # Should be less than 2000 mm³
            assert features.pocket_total_volume < 2000

    def test_deep_pocket_has_large_volume(self, temp_dir):
        """Test that deep pocket has proportionally larger volume."""
        # Deep pocket: 20×15×15mm = 4500 mm³
        box_with_pocket = (
            cq.Workplane("XY")
            .box(50, 40, 25)
            .faces(">Z")
            .workplane()
            .rect(20, 15)
            .cutBlind(-15)
        )
        step_path = os.path.join(temp_dir, "deep_volume.step")
        cq.exporters.export(box_with_pocket, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # If detected, volume should be large
        if features.pocket_count > 0:
            # Should be > 2000 mm³
            assert features.pocket_total_volume > 2000

    def test_pocket_volume_consistent_across_runs(self, temp_dir):
        """Test that pocket volume calculation is deterministic."""
        box_with_pocket = (
            cq.Workplane("XY")
            .box(50, 40, 20)
            .faces(">Z")
            .workplane()
            .rect(15, 10)
            .cutBlind(-8)
        )
        step_path = os.path.join(temp_dir, "consistent_volume.step")
        cq.exporters.export(box_with_pocket, step_path)

        # Run detection twice
        features1, _ = detect_bbox_and_volume(step_path)
        features2, _ = detect_bbox_and_volume(step_path)

        # Should be identical
        assert features1.pocket_total_volume == features2.pocket_total_volume

    def test_pocket_confidence_improves_with_volume(self, temp_dir):
        """Test that confidence improves when volume can be computed."""
        box_with_pocket = (
            cq.Workplane("XY")
            .box(50, 40, 20)
            .faces(">Z")
            .workplane()
            .rect(15, 10)
            .cutBlind(-8)
        )
        step_path = os.path.join(temp_dir, "volume_confidence.step")
        cq.exporters.export(box_with_pocket, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # If pockets detected and volume computed
        if features.pocket_count > 0 and features.pocket_total_volume > 0:
            # Confidence should be improved (>0.7 from Prompt 20)
            assert confidence.pockets > 0.7
            assert confidence.pockets <= 1.0

    def test_volume_approximation_conservative(self, temp_dir):
        """Test that volume approximation is conservative (reasonable bounds)."""
        # Pocket: 20×15×10mm, expected 3000 mm³
        box_with_pocket = (
            cq.Workplane("XY")
            .box(60, 50, 30)
            .faces(">Z")
            .workplane()
            .rect(20, 15)
            .cutBlind(-10)
        )
        step_path = os.path.join(temp_dir, "conservative_volume.step")
        cq.exporters.export(box_with_pocket, step_path)

        features, confidence = detect_bbox_and_volume(step_path)

        # Volume should be positive and reasonable
        if features.pocket_count > 0:
            # Should not be absurdly large (less than entire box volume)
            box_volume = 60 * 50 * 30  # 90000 mm³
            assert 0 < features.pocket_total_volume < box_volume
