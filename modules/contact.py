"""
Contact Module

Generates mailto links for manual review requests.
"""

from urllib.parse import quote
from typing import Optional

from modules.domain import ProcessingResult


def build_mailto_link(
    processing_result: ProcessingResult,
    to: str = "david@wellsglobal.eu"
) -> str:
    """
    Build a mailto link for manual review of a quote.

    Args:
        processing_result: Complete processing result with features and quote
        to: Email recipient address

    Returns:
        Properly formatted mailto: URL with encoded subject and body

    Example:
        mailto:david@wellsglobal.eu?subject=Manual%20Review...&body=Part%20ID...
    """
    # Build subject
    subject = f"Manual Review Request - Part {processing_result.part_id}"

    # Build email body with key information
    body_parts = []
    body_parts.append(f"Part ID: {processing_result.part_id}")
    body_parts.append("")
    body_parts.append("=== Part Specifications ===")
    body_parts.append(f"Bounding Box: {processing_result.features.bounding_box_x:.1f} × "
                     f"{processing_result.features.bounding_box_y:.1f} × "
                     f"{processing_result.features.bounding_box_z:.1f} mm")
    body_parts.append(f"Volume: {processing_result.features.volume:.1f} mm³")
    body_parts.append(f"Through Holes: {processing_result.features.through_hole_count}")
    body_parts.append(f"Blind Holes: {processing_result.features.blind_hole_count}")
    body_parts.append(f"Pockets: {processing_result.features.pocket_count}")
    body_parts.append("")

    # Add quote information if available
    if processing_result.quote:
        body_parts.append("=== Quote Information ===")
        body_parts.append(f"Quantity: {processing_result.quote.quantity}")
        body_parts.append(f"Price per Unit: €{processing_result.quote.price_per_unit:.2f}")
        body_parts.append(f"Total Price: €{processing_result.quote.total_price:.2f}")
        if processing_result.quote.minimum_applied:
            body_parts.append("(Minimum order price applied)")
        body_parts.append("")

    # Add DFM issues if any
    if processing_result.dfm_issues:
        body_parts.append("=== DFM Issues ===")
        for issue in processing_result.dfm_issues:
            severity_label = issue.severity.upper()
            body_parts.append(f"[{severity_label}] {issue.message}")
        body_parts.append("")

    body_parts.append("=== Request ===")
    body_parts.append("Please review this quote and provide a manual assessment.")
    body_parts.append("")
    body_parts.append("Thank you,")
    body_parts.append("Tiento Quote System")

    body = "\n".join(body_parts)

    # URL encode subject and body
    encoded_subject = quote(subject)
    encoded_body = quote(body)

    # Build mailto URL
    mailto_url = f"mailto:{to}?subject={encoded_subject}&body={encoded_body}"

    return mailto_url
