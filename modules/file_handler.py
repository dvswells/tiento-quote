"""
File handling utilities for Tiento Quote v0.1.

Provides validation helpers for file uploads.
Pure functions with no filesystem access.
"""
import os
from typing import Tuple


class InvalidExtensionError(Exception):
    """Raised when file has invalid extension (not .step or .stp)."""
    pass


class FileSizeError(Exception):
    """Raised when file size exceeds maximum allowed size."""
    pass


def validate_extension(filename: str) -> None:
    """
    Validate that filename has .step or .stp extension.

    Case-insensitive validation. Raises exception if extension is invalid.

    Args:
        filename: Name of file to validate

    Raises:
        InvalidExtensionError: If extension is not .step or .stp

    Example:
        >>> validate_extension("part.step")  # OK
        >>> validate_extension("part.STEP")  # OK
        >>> validate_extension("part.stp")   # OK
        >>> validate_extension("part.stl")   # Raises InvalidExtensionError
    """
    # Extract extension (everything after last dot)
    if '.' not in filename:
        raise InvalidExtensionError(
            "Invalid file format - please upload .STEP file"
        )

    extension = filename.rsplit('.', 1)[-1].lower()

    # Check if extension is valid
    valid_extensions = ['step', 'stp']

    if extension not in valid_extensions:
        raise InvalidExtensionError(
            "Invalid file format - please upload .STEP file"
        )


def validate_size(num_bytes: int, max_bytes: int) -> None:
    """
    Validate that file size doesn't exceed maximum.

    Args:
        num_bytes: Size of file in bytes
        max_bytes: Maximum allowed size in bytes

    Raises:
        FileSizeError: If file size exceeds maximum

    Example:
        >>> validate_size(1000, 5000)  # OK
        >>> validate_size(5000, 5000)  # OK (exactly at limit)
        >>> validate_size(5001, 5000)  # Raises FileSizeError
    """
    if num_bytes > max_bytes:
        # Convert to MB for error message if it's the 50MB limit
        if max_bytes == 52428800:  # 50 * 1024 * 1024
            raise FileSizeError("File size exceeds 50MB limit")
        else:
            # Generic message for other limits
            max_mb = max_bytes / (1024 * 1024)
            raise FileSizeError(
                f"File size exceeds {max_mb:.1f}MB limit"
            )
