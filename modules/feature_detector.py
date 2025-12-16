"""
Feature detection utilities for Tiento Quote v0.1.

Detects geometric features from STEP files for pricing calculations.
"""
from typing import Tuple, List
import cadquery as cq
from modules.cad_io import load_step
from modules.domain import PartFeatures, FeatureConfidence
from modules.settings import Settings


class BoundingBoxLimitError(Exception):
    """Raised when part exceeds maximum bounding box dimensions."""
    pass


def _find_cylindrical_faces(solid) -> List:
    """
    Find all cylindrical faces in a solid.

    Internal utility for hole detection. Cylindrical faces are potential hole candidates.

    Args:
        solid: OCC solid object from cadquery

    Returns:
        List of cylindrical faces
    """
    cylindrical_faces = []

    try:
        # Iterate through all faces in the solid
        for face in solid.Faces():
            # Check if face is cylindrical
            if face.geomType() == "CYLINDER":
                cylindrical_faces.append(face)
    except Exception:
        # If face iteration fails, return empty list (conservative)
        pass

    return cylindrical_faces


def _estimate_hole_diameter(face) -> float:
    """
    Estimate diameter of a cylindrical face (potential hole).

    Internal utility for hole detection. Returns conservative estimate.

    Args:
        face: Cylindrical face from OCC solid

    Returns:
        Estimated diameter in mm, or 0.0 if cannot estimate
    """
    try:
        # Use bounding box to estimate diameter
        # For a cylindrical face, the X and Y spans approximate the diameter
        bbox = face.BoundingBox()

        # Get spans in each direction
        x_span = bbox.xmax - bbox.xmin
        y_span = bbox.ymax - bbox.ymin
        z_span = bbox.zmax - bbox.zmin

        # The two smaller spans should be similar for a cylinder
        # Use the average of the two smallest spans as diameter
        spans = sorted([x_span, y_span, z_span])
        # Average of two smallest (should be the circular cross-section)
        diameter = (spans[0] + spans[1]) / 2.0

        return diameter

    except Exception:
        # If estimation fails, return 0.0 (conservative)
        return 0.0


def _detect_holes(solid) -> Tuple[int, int, float]:
    """
    Detect hole candidates from cylindrical faces.

    Internal utility for hole detection. Uses conservative heuristics:
    - Finds cylindrical faces
    - Filters by diameter (must be < 50mm to be a hole)
    - Returns counts (classification of through vs blind comes in Prompt 19)

    Args:
        solid: OCC solid object from cadquery

    Returns:
        Tuple of (through_hole_count, blind_hole_count, confidence):
        - For v1, all holes counted as through_hole_count
        - blind_hole_count set to 0 (classification comes in Prompt 19)
        - confidence < 1.0 (heuristic detection)
    """
    try:
        # Find all cylindrical faces
        cylindrical_faces = _find_cylindrical_faces(solid)

        # Filter to hole candidates
        # Heuristic: holes typically have diameter < 50mm
        hole_candidates = []
        for face in cylindrical_faces:
            diameter = _estimate_hole_diameter(face)
            # Conservative: only count if diameter is reasonable for a hole
            if 0.5 < diameter < 50.0:  # 0.5mm to 50mm
                hole_candidates.append(face)

        # Count holes
        # In cadquery's representation, each hole typically has 1 cylindrical face
        # Count each cylindrical face as a hole candidate
        hole_count = len(hole_candidates)

        # Set confidence based on detection method
        # Heuristic detection -> confidence < 1.0
        confidence = 0.7 if hole_count > 0 else 0.0

        # For v1, put all holes in through_hole_count
        # Classification comes in Prompt 19
        return hole_count, 0, confidence

    except Exception:
        # If detection fails, return zeros (conservative)
        return 0, 0, 0.0


def detect_bbox_and_volume(step_path: str) -> Tuple[PartFeatures, FeatureConfidence]:
    """
    Detect bounding box, volume, and hole candidates from STEP file.

    Feature detector v1 computes:
    - Bounding box dimensions (x, y, z) in mm
    - Volume in mm³
    - Hole candidates from cylindrical faces

    Pockets and other features remain at default values (zero).

    Args:
        step_path: Path to STEP file to analyze

    Returns:
        Tuple of (PartFeatures, FeatureConfidence):
        - PartFeatures: Detected features (bbox, volume, holes)
        - FeatureConfidence: Confidence scores (1.0 for bbox/volume, <1.0 for holes)

    Raises:
        StepLoadError: If STEP file cannot be loaded (propagated from cad_io.load_step)

    Example:
        >>> features, confidence = detect_bbox_and_volume("part.step")
        >>> print(f"Bounding box: {features.bounding_box_x} × {features.bounding_box_y} × {features.bounding_box_z} mm")
        >>> print(f"Volume: {features.volume} mm³")
        >>> print(f"Holes: {features.through_hole_count}")
        >>> print(f"Confidence: {confidence.bounding_box}, {confidence.through_holes}")
    """
    # Load STEP file using cad_io module
    workplane = load_step(step_path)

    # Get the solid from the workplane
    solid = workplane.val()

    # Compute bounding box
    # BoundingBox() returns a bounding box with xmin, xmax, ymin, ymax, zmin, zmax
    bbox = solid.BoundingBox()

    # Calculate dimensions (max - min for each axis)
    bbox_x = bbox.xmax - bbox.xmin
    bbox_y = bbox.ymax - bbox.ymin
    bbox_z = bbox.zmax - bbox.zmin

    # Calculate volume
    volume = solid.Volume()

    # Detect hole candidates
    through_hole_count, blind_hole_count, hole_confidence = _detect_holes(solid)

    # Create PartFeatures with detected values
    features = PartFeatures(
        bounding_box_x=bbox_x,
        bounding_box_y=bbox_y,
        bounding_box_z=bbox_z,
        volume=volume,
        through_hole_count=through_hole_count,
        blind_hole_count=blind_hole_count,
        # Pockets remain at default (zero)
    )

    # Create FeatureConfidence
    # Set confidence to 1.0 for bbox and volume (deterministic geometric calculations)
    # Set hole confidence based on detection (heuristic, <1.0)
    confidence = FeatureConfidence(
        bounding_box=1.0,
        volume=1.0,
        through_holes=hole_confidence,
        blind_holes=hole_confidence,
        # pockets remain 0.0
    )

    return features, confidence


def validate_bounding_box_limits(features: PartFeatures, settings: Settings) -> None:
    """
    Validate that part dimensions don't exceed maximum bounding box limits.

    Maximum dimensions are defined in settings (default: 600×400×500mm).
    This validation should be performed before expensive feature detection operations.

    Args:
        features: Part features including bounding box dimensions
        settings: Application settings with bounding box limits

    Raises:
        BoundingBoxLimitError: If any dimension exceeds the maximum limits

    Example:
        >>> features = PartFeatures(bounding_box_x=100, bounding_box_y=200, bounding_box_z=300)
        >>> settings = get_settings()
        >>> validate_bounding_box_limits(features, settings)  # Passes
        >>>
        >>> large_features = PartFeatures(bounding_box_x=700, bounding_box_y=200, bounding_box_z=300)
        >>> validate_bounding_box_limits(large_features, settings)  # Raises BoundingBoxLimitError
    """
    # Check if any dimension exceeds limits
    if (features.bounding_box_x > settings.BOUNDING_BOX_MAX_X or
        features.bounding_box_y > settings.BOUNDING_BOX_MAX_Y or
        features.bounding_box_z > settings.BOUNDING_BOX_MAX_Z):

        # Raise error with spec-aligned message
        raise BoundingBoxLimitError(
            f"Part exceeds maximum dimensions of "
            f"{int(settings.BOUNDING_BOX_MAX_X)}×"
            f"{int(settings.BOUNDING_BOX_MAX_Y)}×"
            f"{int(settings.BOUNDING_BOX_MAX_Z)}mm. "
            f"Please contact us for large part quoting at david@wellsglobal.eu"
        )
