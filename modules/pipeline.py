"""
Pipeline orchestrator for Tiento Quote v0.1.

Coordinates end-to-end processing: feature detection, validation, and pricing.
"""
import uuid
from modules.settings import get_settings
from modules.feature_detector import detect_bbox_and_volume, validate_bounding_box_limits
from modules.pricing_config import load_pricing_config
from modules.pricing_engine import calculate_quote
from modules.domain import ProcessingResult


def process_quote(step_path: str, quantity: int, pricing_config_path: str) -> ProcessingResult:
    """
    Process a STEP file end-to-end to generate a quote.

    Pipeline sequence:
    1. Load settings
    2. Detect bounding box and volume
    3. Validate bounding box limits (reject oversized parts)
    4. Load pricing configuration
    5. Calculate quote

    Args:
        step_path: Path to STEP file to process
        quantity: Quantity of parts to quote (1-50)
        pricing_config_path: Path to pricing configuration JSON

    Returns:
        ProcessingResult with all detected features, confidence, and quote

    Raises:
        BoundingBoxLimitError: If part exceeds maximum dimensions
        InvalidQuantityError: If quantity is outside valid range
        ModelNotReadyError: If pricing model is not trained

    Example:
        >>> result = process_quote("part.step", 10, "config/pricing_coefficients.json")
        >>> print(f"Total: €{result.quote.total_price:.2f}")
        >>> print(f"Dimensions: {result.features.bounding_box_x}×{result.features.bounding_box_y}×{result.features.bounding_box_z} mm")
    """
    # Generate unique part ID
    part_id = str(uuid.uuid4())

    # Step 1: Load settings
    settings = get_settings()

    # Step 2: Detect bounding box and volume
    features, confidence = detect_bbox_and_volume(step_path)

    # Step 3: Validate bounding box limits
    # This will raise BoundingBoxLimitError if part is oversized
    validate_bounding_box_limits(features, settings)

    # Step 4: Load pricing configuration
    pricing_config = load_pricing_config(pricing_config_path)

    # Step 5: Calculate quote
    # This will raise InvalidQuantityError if quantity invalid
    # This will raise ModelNotReadyError if r_squared = 0.0
    quote = calculate_quote(features, quantity, pricing_config)

    # Create and return ProcessingResult
    return ProcessingResult(
        part_id=part_id,
        step_file_path=step_path,
        stl_file_path="",  # STL export not yet implemented
        features=features,
        confidence=confidence,
        dfm_issues=[],  # DFM checks not yet implemented
        quote=quote,
        errors=[],  # No errors if we reached here
    )
