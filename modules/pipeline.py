"""
Pipeline orchestrator for Tiento Quote v0.1.

Coordinates end-to-end processing: feature detection, validation, and pricing.
"""
import logging
import uuid
from typing import List

from modules.settings import get_settings
from modules.feature_detector import detect_bbox_and_volume, validate_bounding_box_limits, BoundingBoxLimitError
from modules.pricing_config import load_pricing_config
from modules.pricing_engine import calculate_quote, ModelNotReadyError, InvalidQuantityError
from modules.dfm_analyzer import analyze_dfm
from modules.domain import ProcessingResult, PartFeatures, FeatureConfidence, DfmIssue

# Configure logging
logger = logging.getLogger(__name__)


def process_quote(step_path: str, quantity: int, pricing_config_path: str) -> ProcessingResult:
    """
    Process a STEP file end-to-end to generate a quote.

    Pipeline sequence:
    1. Load settings
    2. Detect features (bounding box, volume, holes, pockets)
    3. Validate bounding box limits (reject oversized parts)
    4. Analyze DFM issues
    5. Load pricing configuration
    6. Calculate quote

    Errors are caught and returned in ProcessingResult.errors instead of being raised.
    This allows the UI to display user-friendly error messages.

    Args:
        step_path: Path to STEP file to process
        quantity: Quantity of parts to quote (1-50)
        pricing_config_path: Path to pricing configuration JSON

    Returns:
        ProcessingResult with features, confidence, DFM issues, quote, and any errors

    Example:
        >>> result = process_quote("part.step", 10, "config/pricing_coefficients.json")
        >>> if result.errors:
        ...     print(f"Errors: {result.errors}")
        >>> else:
        ...     print(f"Total: €{result.quote.total_price:.2f}")
    """
    # Generate unique part ID
    part_id = str(uuid.uuid4())
    errors: List[str] = []

    logger.info(f"Processing quote for part {part_id}")
    logger.info(f"  STEP file: {step_path}")
    logger.info(f"  Quantity: {quantity}")

    # Initialize variables
    features = None
    confidence = None
    dfm_issues = []
    quote = None
    settings = None

    # Step 1: Load settings
    try:
        settings = get_settings()
        logger.info(f"Loaded settings: max bbox {settings.BOUNDING_BOX_MAX_X}×{settings.BOUNDING_BOX_MAX_Y}×{settings.BOUNDING_BOX_MAX_Z}mm")
    except Exception as e:
        error_msg = f"Failed to load settings: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)

    # Step 2: Detect features
    try:
        features, confidence = detect_bbox_and_volume(step_path)
        logger.info(f"Feature detection complete:")
        logger.info(f"  Bounding box: {features.bounding_box_x:.1f} × {features.bounding_box_y:.1f} × {features.bounding_box_z:.1f} mm")
        logger.info(f"  Volume: {features.volume:.1f} mm³")
        logger.info(f"  Through holes: {features.through_hole_count}, Blind holes: {features.blind_hole_count}, Pockets: {features.pocket_count}")
    except Exception as e:
        error_msg = f"Failed to detect features from STEP file. Please ensure the file is valid STEP format. Error: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)

        # Create minimal features for error case
        features = PartFeatures(
            bounding_box_x=0.0,
            bounding_box_y=0.0,
            bounding_box_z=0.0,
            volume=0.0,
            through_hole_count=0,
            blind_hole_count=0,
            blind_hole_avg_depth_to_diameter=0.0,
            blind_hole_max_depth_to_diameter=0.0,
            pocket_count=0,
            pocket_total_volume=0.0,
            pocket_avg_depth=0.0,
            pocket_max_depth=0.0,
            non_standard_hole_count=0
        )
        confidence = FeatureConfidence(
            bounding_box=0.0,
            volume=0.0,
            through_holes=0.0,
            blind_holes=0.0,
            pockets=0.0
        )

    # Step 3: Validate bounding box limits (only if we have features)
    if not errors and settings:
        try:
            validate_bounding_box_limits(features, settings)
            logger.info("Bounding box validation passed")
        except BoundingBoxLimitError as e:
            error_msg = str(e)
            logger.error(f"Bounding box validation failed: {error_msg}")
            errors.append(error_msg)

    # Step 4: Analyze DFM issues (only if we have features)
    if not errors:
        try:
            dfm_issues = analyze_dfm(features)
            if dfm_issues:
                logger.warning(f"DFM issues detected: {len(dfm_issues)}")
                for issue in dfm_issues:
                    logger.warning(f"  [{issue.severity.upper()}] {issue.message}")
            else:
                logger.info("No DFM issues detected")
        except Exception as e:
            # DFM analysis failure shouldn't block quoting
            logger.warning(f"DFM analysis failed (non-blocking): {str(e)}")

    # Step 5: Load pricing configuration (only if no errors so far)
    pricing_config = None
    if not errors:
        try:
            pricing_config = load_pricing_config(pricing_config_path)
            logger.info(f"Loaded pricing model: R² = {pricing_config.get('r_squared', 0):.4f}")
        except Exception as e:
            error_msg = f"Failed to load pricing configuration: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

    # Step 6: Calculate quote (only if no errors so far)
    if not errors and pricing_config:
        try:
            quote = calculate_quote(features, quantity, pricing_config)
            logger.info(f"Quote calculated:")
            logger.info(f"  Price per unit: €{quote.price_per_unit:.2f}")
            logger.info(f"  Total price: €{quote.total_price:.2f}")
            logger.info(f"  Quantity: {quote.quantity}")
            if quote.minimum_applied:
                logger.info(f"  Minimum order price (€{pricing_config.get('minimum_order_price', 30):.2f}) applied")
        except (ModelNotReadyError, InvalidQuantityError) as e:
            error_msg = str(e)
            logger.error(f"Quote calculation failed: {error_msg}")
            errors.append(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during quote calculation: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

    # Log final status
    if errors:
        logger.error(f"Processing completed with {len(errors)} error(s)")
    else:
        logger.info(f"Processing completed successfully")

    # Create and return ProcessingResult
    return ProcessingResult(
        part_id=part_id,
        step_file_path=step_path,
        stl_file_path="",  # STL export handled separately by app.py
        features=features,
        confidence=confidence,
        dfm_issues=dfm_issues,
        quote=quote,
        errors=errors,
    )
