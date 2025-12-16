"""
Visualization utilities for Tiento Quote v0.1.

Handles STEP to STL conversion for 3D visualization.
"""
import os
from typing import Tuple
import cadquery as cq
from modules.domain import PartFeatures


def compute_adaptive_deflection(features: PartFeatures) -> Tuple[float, float]:
    """
    Compute adaptive deflection parameters based on part size.

    Uses 0.1% of the largest bounding box dimension for linear deflection
    and 0.5 degrees for angular deflection (per spec).

    Args:
        features: Part features with bounding box dimensions

    Returns:
        Tuple of (linear_deflection, angular_deflection)
        - linear_deflection: 0.1% of max dimension (mm)
        - angular_deflection: 0.5 degrees

    Example:
        >>> features = PartFeatures(bounding_box_x=100, bounding_box_y=200, bounding_box_z=150)
        >>> linear, angular = compute_adaptive_deflection(features)
        >>> # linear = 200 * 0.001 = 0.2 (0.1% of 200mm)
        >>> # angular = 0.5 (degrees)
    """
    # Find maximum dimension
    max_dimension = max(
        features.bounding_box_x,
        features.bounding_box_y,
        features.bounding_box_z
    )

    # Linear deflection: 0.1% of largest dimension
    linear_deflection = max_dimension * 0.001

    # Angular deflection: fixed at 0.5 degrees
    angular_deflection = 0.5

    return linear_deflection, angular_deflection


def step_to_stl(
    step_path: str,
    stl_path: str,
    linear_deflection: float,
    angular_deflection: float
) -> None:
    """
    Convert STEP file to STL format for visualization.

    Uses cadquery to load STEP geometry and export as ASCII STL with
    specified mesh resolution parameters.

    Args:
        step_path: Path to input STEP file
        stl_path: Path where STL file should be saved
        linear_deflection: Maximum linear deviation from surface (mm)
        angular_deflection: Maximum angular deviation from surface (degrees)

    Raises:
        Exception: If STEP file cannot be loaded or STL export fails

    Example:
        >>> step_to_stl("part.step", "part.stl", 0.1, 0.5)
        >>> # Creates ASCII STL file with adaptive mesh resolution
    """
    # Create parent directories if they don't exist
    os.makedirs(os.path.dirname(os.path.abspath(stl_path)), exist_ok=True)

    # Load STEP file
    try:
        result = cq.importers.importStep(step_path)
    except Exception as e:
        raise Exception(f"Failed to load STEP file: {step_path}. Error: {str(e)}")

    # Ensure result is a Workplane
    if not isinstance(result, cq.Workplane):
        result = cq.Workplane("XY").add(result)

    # Export to STL with specified deflection parameters
    # exportStl() uses linearDeflection and angularDeflection for mesh resolution
    try:
        cq.exporters.export(
            result,
            stl_path,
            exportType=cq.exporters.ExportTypes.STL,
            tolerance=linear_deflection,
            angularTolerance=angular_deflection
        )
    except Exception as e:
        raise Exception(f"Failed to export STL file: {stl_path}. Error: {str(e)}")
