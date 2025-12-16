"""
CAD I/O utilities for Tiento Quote v0.1.

Handles loading and processing STEP files using cadquery.
"""
import os
import cadquery as cq
from typing import Any


class StepLoadError(Exception):
    """
    Raised when a STEP file cannot be loaded or parsed.

    This exception provides helpful error messages to guide users
    when STEP file loading fails.
    """
    pass


def load_step(step_path: str) -> cq.Workplane:
    """
    Load a STEP file and return a cadquery Workplane.

    This is the single entrypoint for STEP parsing in the application.

    Args:
        step_path: Path to STEP file (.step or .stp)

    Returns:
        cadquery Workplane containing the loaded geometry

    Raises:
        StepLoadError: If file doesn't exist, is invalid, or cannot be parsed

    Example:
        >>> wp = load_step("path/to/part.step")
        >>> volume = wp.val().Volume()
    """
    # Check if file exists
    if not os.path.exists(step_path):
        raise StepLoadError(
            f"STEP file not found: {step_path}"
        )

    # Check if file is empty
    if os.path.getsize(step_path) == 0:
        raise StepLoadError(
            f"STEP file is empty: {step_path}"
        )

    # Attempt to import STEP file
    try:
        # Use cadquery's importers to load STEP file
        result = cq.importers.importStep(step_path)

        # Verify we got a valid result
        if result is None:
            raise StepLoadError(
                f"Failed to load STEP file (returned None): {step_path}"
            )

        # If result is not already a Workplane, wrap it
        if not isinstance(result, cq.Workplane):
            # Try to create a Workplane from the shape
            try:
                result = cq.Workplane("XY").add(result)
            except Exception as e:
                raise StepLoadError(
                    f"Loaded STEP file but could not create Workplane: {step_path}. "
                    f"Error: {str(e)}"
                )

        return result

    except StepLoadError:
        # Re-raise our custom errors as-is
        raise

    except Exception as e:
        # Catch any other errors from cadquery and wrap them
        error_msg = str(e).lower()

        # Provide helpful error messages based on the error type
        if "parse" in error_msg or "syntax" in error_msg:
            raise StepLoadError(
                f"Invalid STEP file format (parse error): {step_path}. "
                f"Error: {str(e)}"
            )
        elif "read" in error_msg or "open" in error_msg:
            raise StepLoadError(
                f"Could not read STEP file: {step_path}. "
                f"Error: {str(e)}"
            )
        else:
            # Generic error
            raise StepLoadError(
                f"Failed to load STEP file: {step_path}. "
                f"Error: {str(e)}"
            )
