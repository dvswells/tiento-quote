"""
Feature detection utilities for Tiento Quote v0.1.

Detects geometric features from STEP files for pricing calculations.
"""
from typing import Tuple
from modules.cad_io import load_step
from modules.domain import PartFeatures, FeatureConfidence


def detect_bbox_and_volume(step_path: str) -> Tuple[PartFeatures, FeatureConfidence]:
    """
    Detect bounding box dimensions and volume from STEP file.

    This is the initial feature detector (v0) that only computes:
    - Bounding box dimensions (x, y, z) in mm
    - Volume in mm³

    All other features (holes, pockets, etc.) remain at default values (zero).

    Args:
        step_path: Path to STEP file to analyze

    Returns:
        Tuple of (PartFeatures, FeatureConfidence):
        - PartFeatures: Detected features (bbox and volume set, others zero)
        - FeatureConfidence: Confidence scores (1.0 for bbox/volume, 0.0 for others)

    Raises:
        StepLoadError: If STEP file cannot be loaded (propagated from cad_io.load_step)

    Example:
        >>> features, confidence = detect_bbox_and_volume("part.step")
        >>> print(f"Bounding box: {features.bounding_box_x} × {features.bounding_box_y} × {features.bounding_box_z} mm")
        >>> print(f"Volume: {features.volume} mm³")
        >>> print(f"Confidence: {confidence.bounding_box}")
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

    # Create PartFeatures with detected values
    # All hole/pocket features remain at default (zero)
    features = PartFeatures(
        bounding_box_x=bbox_x,
        bounding_box_y=bbox_y,
        bounding_box_z=bbox_z,
        volume=volume,
        # All other fields use defaults (zeros)
    )

    # Create FeatureConfidence
    # Set confidence to 1.0 for bbox and volume (deterministic geometric calculations)
    # All other confidences remain at default (0.0)
    confidence = FeatureConfidence(
        bounding_box=1.0,
        volume=1.0,
        # through_holes, blind_holes, pockets remain 0.0
    )

    return features, confidence
