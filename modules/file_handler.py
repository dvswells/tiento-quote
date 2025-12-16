"""
File handling utilities for Tiento Quote v0.1.

Provides validation helpers and upload storage for file uploads.
"""
import os
import uuid
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


def store_upload(file_bytes: bytes, original_filename: str, uploads_dir: str) -> Tuple[str, str]:
    """
    Store uploaded file with UUID-based naming.

    Preserves the original file extension (.step or .stp).
    Creates uploads directory if it doesn't exist.

    Args:
        file_bytes: File content as bytes
        original_filename: Original filename (used to extract extension)
        uploads_dir: Directory to store uploaded files

    Returns:
        Tuple of (part_id, stored_path):
        - part_id: Generated UUID v4 string
        - stored_path: Full path to stored file

    Example:
        >>> file_bytes = b"STEP file content"
        >>> part_id, path = store_upload(file_bytes, "part.step", "/uploads")
        >>> # part_id: "a3f5b2c1-1234-5678-9abc-def012345678"
        >>> # path: "/uploads/a3f5b2c1-1234-5678-9abc-def012345678.step"
    """
    # Generate UUID v4 for part ID
    part_id = str(uuid.uuid4())

    # Extract extension from original filename
    extension = os.path.splitext(original_filename)[1]

    # Create filename: UUID + extension
    filename = f"{part_id}{extension}"

    # Ensure uploads directory exists
    os.makedirs(uploads_dir, exist_ok=True)

    # Full path for stored file
    stored_path = os.path.join(uploads_dir, filename)

    # Write file bytes
    with open(stored_path, "wb") as f:
        f.write(file_bytes)

    return part_id, stored_path
