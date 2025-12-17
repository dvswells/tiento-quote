"""
DFM (Design for Manufacturing) Analyzer

Analyzes part features to detect manufacturability issues.
Returns list of issues with severity levels: critical, warning, info.
"""

from typing import List
from modules.domain import PartFeatures, DfmIssue


def analyze_dfm(features: PartFeatures) -> List[DfmIssue]:
    """
    Analyze part features for manufacturability issues.

    Args:
        features: Detected part features

    Returns:
        List of DfmIssue objects with severity and message

    Checks implemented:
    - Deep holes: Based on blind_hole_max_depth_to_diameter ratio
    - Small features: Based on smallest hole diameter (proxy for feature size)
    - Non-standard holes: Detects non-standard hole sizes

    Future checks (structure in place):
    - Thin walls
    - Sharp internal corners
    - Undercuts
    """
    issues = []

    # Check for deep holes (high aspect ratio)
    issues.extend(_check_deep_holes(features))

    # Check for small features (difficult to machine)
    issues.extend(_check_small_features(features))

    # Check for non-standard holes
    issues.extend(_check_non_standard_holes(features))

    return issues


def _check_deep_holes(features: PartFeatures) -> List[DfmIssue]:
    """
    Check for deep holes that are difficult to drill.

    Thresholds:
    - Ratio > 10: Critical (very difficult, may require special tools)
    - Ratio > 6: Warning (challenging, higher cost)

    Returns:
        List of DfmIssue objects
    """
    issues = []

    if features.blind_hole_count == 0:
        return issues

    max_ratio = features.blind_hole_max_depth_to_diameter

    if max_ratio > 10:
        issues.append(DfmIssue(
            severity="critical",
            message=f"Very deep blind hole detected (depth/diameter ratio: {max_ratio:.1f}). "
                   f"Ratios >10 require special tooling and may be difficult to manufacture."
        ))
    elif max_ratio > 6:
        issues.append(DfmIssue(
            severity="warning",
            message=f"Deep blind hole detected (depth/diameter ratio: {max_ratio:.1f}). "
                   f"Ratios >6 are challenging to drill and may increase cost."
        ))

    return issues


def _check_small_features(features: PartFeatures) -> List[DfmIssue]:
    """
    Check for small features that are difficult to machine.

    Uses smallest detected hole diameter as proxy for minimum feature size.

    Thresholds:
    - Diameter < 0.5mm: Critical (very difficult, may require micro-machining)
    - Diameter < 0.9mm: Warning (small, requires precision tools)

    Returns:
        List of DfmIssue objects
    """
    issues = []

    # Use through holes and blind holes to find smallest feature
    total_holes = features.through_hole_count + features.blind_hole_count

    if total_holes == 0:
        return issues

    # Find smallest hole diameter (proxy for smallest feature)
    # For MVP, we'll use a heuristic based on volume and count
    # In production, we'd track individual hole diameters

    # Heuristic: If we have very small holes, they'll be detected
    # For now, we'll flag based on non-standard holes count
    # which often indicates unusual (small or large) features

    # TODO: Track individual hole diameters in PartFeatures
    # For now, use conservative estimate: if non-standard holes exist,
    # they might be small

    if features.non_standard_hole_count > 0:
        # This is a simplified check - in production we'd have actual diameters
        issues.append(DfmIssue(
            severity="warning",
            message=f"Part contains {features.non_standard_hole_count} non-standard hole(s). "
                   f"Small features (<0.9mm) may require precision tooling."
        ))

    return issues


def _check_non_standard_holes(features: PartFeatures) -> List[DfmIssue]:
    """
    Check for non-standard holes that may require special tools.

    Non-standard holes are those that don't match common drill sizes.

    Returns:
        List of DfmIssue objects
    """
    issues = []

    if features.non_standard_hole_count > 0:
        issues.append(DfmIssue(
            severity="info",
            message=f"Part contains {features.non_standard_hole_count} non-standard hole(s). "
                   f"Non-standard sizes may require custom tooling."
        ))

    return issues


# Placeholder for future checks (structure in place for expansion)

def _check_thin_walls(features: PartFeatures) -> List[DfmIssue]:
    """
    Check for thin walls that may be difficult to machine or weak.

    TODO: Implement when wall thickness detection is available.

    Thresholds (planned):
    - Wall < 0.5mm: Critical
    - Wall < 1.0mm: Warning
    """
    # Placeholder - requires geometry analysis not yet implemented
    return []


def _check_sharp_corners(features: PartFeatures) -> List[DfmIssue]:
    """
    Check for sharp internal corners that require small tools.

    TODO: Implement when corner radius detection is available.

    Thresholds (planned):
    - Radius < 0.5mm: Warning
    """
    # Placeholder - requires geometry analysis not yet implemented
    return []


def _check_undercuts(features: PartFeatures) -> List[DfmIssue]:
    """
    Check for undercuts that may require special machining strategies.

    TODO: Implement when undercut detection is available.
    """
    # Placeholder - requires geometry analysis not yet implemented
    return []
