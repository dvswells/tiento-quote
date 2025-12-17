"""
Feature detection utilities for Tiento Quote v0.1.

Detects geometric features from STEP files for pricing calculations.
"""
from typing import Tuple, List, Dict
import cadquery as cq
from modules.cad_io import load_step
from modules.domain import PartFeatures, FeatureConfidence
from modules.settings import Settings


class BoundingBoxLimitError(Exception):
    """Raised when part exceeds maximum bounding box dimensions."""
    pass


# Standard hole sizes (metric, in mm) with ±0.1mm tolerance
# M3, M4, M5, M6, M8, M10, M12
STANDARD_HOLE_SIZES = [3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0]
HOLE_SIZE_TOLERANCE = 0.1  # mm


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


def _is_standard_hole_size(diameter: float) -> bool:
    """
    Check if diameter matches a standard hole size within tolerance.

    Args:
        diameter: Hole diameter in mm

    Returns:
        True if diameter is within ±0.1mm of a standard size
    """
    for standard_size in STANDARD_HOLE_SIZES:
        if abs(diameter - standard_size) <= HOLE_SIZE_TOLERANCE:
            return True
    return False


def _estimate_hole_depth(face, solid_bbox) -> float:
    """
    Estimate depth of a hole from its cylindrical face.

    Args:
        face: Cylindrical face
        solid_bbox: Bounding box of the solid

    Returns:
        Estimated depth in mm, or 0.0 if cannot estimate
    """
    try:
        bbox = face.BoundingBox()
        # Get spans in each direction
        x_span = bbox.xmax - bbox.xmin
        y_span = bbox.ymax - bbox.ymin
        z_span = bbox.zmax - bbox.zmin

        # Depth is the largest span (cylinder height)
        # The two smaller spans form the circular cross-section
        spans = sorted([x_span, y_span, z_span])
        depth = spans[2]  # Largest span is the depth

        return depth
    except Exception:
        return 0.0


def _classify_hole_type(face, solid_bbox) -> str:
    """
    Classify hole as through or blind.

    Heuristic: Through holes span most of a dimension of the part.
    Blind holes are shorter than the part dimension.

    Args:
        face: Cylindrical face
        solid_bbox: Bounding box of the solid

    Returns:
        "through" or "blind"
    """
    try:
        bbox = face.BoundingBox()

        # Get face spans
        x_span = bbox.xmax - bbox.xmin
        y_span = bbox.ymax - bbox.ymin
        z_span = bbox.zmax - bbox.zmin

        # Get solid dimensions
        solid_x = solid_bbox.xmax - solid_bbox.xmin
        solid_y = solid_bbox.ymax - solid_bbox.ymin
        solid_z = solid_bbox.zmax - solid_bbox.zmin

        # Check if hole spans most of any dimension (>90%)
        # If so, it's likely a through hole
        threshold = 0.9
        if (x_span > solid_x * threshold or
            y_span > solid_y * threshold or
            z_span > solid_z * threshold):
            return "through"
        else:
            return "blind"
    except Exception:
        # Default to through if uncertain
        return "through"


def _detect_holes(solid) -> Tuple[int, int, float, float, float, int]:
    """
    Detect and classify holes from cylindrical faces.

    Detects holes, classifies through vs blind, computes depth ratios,
    and identifies non-standard hole sizes.

    Args:
        solid: OCC solid object from cadquery

    Returns:
        Tuple of (through_count, blind_count, avg_ratio, max_ratio, confidence, non_standard_count):
        - through_count: Number of through holes
        - blind_count: Number of blind holes
        - avg_ratio: Average blind hole depth:diameter ratio
        - max_ratio: Maximum blind hole depth:diameter ratio
        - confidence: Detection confidence (0.85-0.90 for heuristic)
        - non_standard_count: Number of non-standard hole sizes
    """
    try:
        # Get solid bounding box for classification
        solid_bbox = solid.BoundingBox()

        # Find all cylindrical faces
        cylindrical_faces = _find_cylindrical_faces(solid)

        # Analyze each hole candidate
        through_holes = []
        blind_holes = []
        non_standard_count = 0

        for face in cylindrical_faces:
            diameter = _estimate_hole_diameter(face)

            # Filter: only consider reasonable hole sizes
            if not (0.5 < diameter < 50.0):
                continue

            # Classify hole type
            hole_type = _classify_hole_type(face, solid_bbox)

            # Check if standard size
            if not _is_standard_hole_size(diameter):
                non_standard_count += 1

            # Store hole info
            hole_info = {
                'face': face,
                'diameter': diameter,
                'depth': _estimate_hole_depth(face, solid_bbox),
            }

            if hole_type == "through":
                through_holes.append(hole_info)
            else:
                blind_holes.append(hole_info)

        # Compute blind hole depth ratios
        depth_ratios = []
        for hole in blind_holes:
            if hole['diameter'] > 0:
                ratio = hole['depth'] / hole['diameter']
                depth_ratios.append(ratio)

        avg_ratio = sum(depth_ratios) / len(depth_ratios) if depth_ratios else 0.0
        max_ratio = max(depth_ratios) if depth_ratios else 0.0

        # Set improved confidence (0.85-0.90 for heuristic classification)
        total_holes = len(through_holes) + len(blind_holes)
        if total_holes > 0:
            # Higher confidence with classification logic
            confidence = 0.85
        else:
            confidence = 0.0

        return len(through_holes), len(blind_holes), avg_ratio, max_ratio, confidence, non_standard_count

    except Exception:
        # If detection fails, return zeros (conservative)
        return 0, 0, 0.0, 0.0, 0.0, 0


def detect_bbox_and_volume(step_path: str) -> Tuple[PartFeatures, FeatureConfidence]:
    """
    Detect bounding box, volume, and classified holes from STEP file.

    Feature detector v2 computes:
    - Bounding box dimensions (x, y, z) in mm
    - Volume in mm³
    - Hole detection with through/blind classification
    - Blind hole depth:diameter ratios
    - Non-standard hole sizes (not matching M3, M4, M5, M6, M8, M10, M12 ±0.1mm)

    Pockets and other features remain at default values (zero).

    Args:
        step_path: Path to STEP file to analyze

    Returns:
        Tuple of (PartFeatures, FeatureConfidence):
        - PartFeatures: Detected features (bbox, volume, classified holes, ratios)
        - FeatureConfidence: Confidence scores (1.0 for bbox/volume, 0.85 for holes)

    Raises:
        StepLoadError: If STEP file cannot be loaded (propagated from cad_io.load_step)

    Example:
        >>> features, confidence = detect_bbox_and_volume("part.step")
        >>> print(f"Bounding box: {features.bounding_box_x} × {features.bounding_box_y} × {features.bounding_box_z} mm")
        >>> print(f"Volume: {features.volume} mm³")
        >>> print(f"Through holes: {features.through_hole_count}, Blind: {features.blind_hole_count}")
        >>> print(f"Non-standard: {features.non_standard_hole_count}")
        >>> print(f"Confidence: bbox={confidence.bounding_box}, holes={confidence.through_holes}")
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

    # Detect holes with classification and ratios
    (through_hole_count, blind_hole_count, blind_avg_ratio, blind_max_ratio,
     hole_confidence, non_standard_count) = _detect_holes(solid)

    # Create PartFeatures with detected values
    features = PartFeatures(
        bounding_box_x=bbox_x,
        bounding_box_y=bbox_y,
        bounding_box_z=bbox_z,
        volume=volume,
        through_hole_count=through_hole_count,
        blind_hole_count=blind_hole_count,
        blind_hole_avg_depth_to_diameter=blind_avg_ratio,
        blind_hole_max_depth_to_diameter=blind_max_ratio,
        non_standard_hole_count=non_standard_count,
        # Pockets remain at default (zero)
    )

    # Create FeatureConfidence
    # Set confidence to 1.0 for bbox and volume (deterministic geometric calculations)
    # Set hole confidence based on detection (heuristic, 0.85-0.90)
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
