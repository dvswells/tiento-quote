"""
Tests for Contact Module

Tests mailto link generation for manual review requests.
"""

import pytest
from urllib.parse import unquote

from modules.contact import build_mailto_link
from modules.domain import (
    ProcessingResult,
    PartFeatures,
    FeatureConfidence,
    DfmIssue,
    QuoteResult
)


class TestBuildMailtoLink:
    """Test mailto link generation."""

    def test_returns_mailto_url(self):
        """Mailto link should start with mailto:."""
        result = ProcessingResult(
            part_id="test-uuid-123",
            step_file_path="/path/to/test.step",
            stl_file_path="/path/to/test.stl",
            features=PartFeatures(
                bounding_box_x=100.0,
                bounding_box_y=50.0,
                bounding_box_z=25.0,
                volume=125000.0,
                through_hole_count=2,
                blind_hole_count=1,
                blind_hole_avg_depth_to_diameter=3.0,
                blind_hole_max_depth_to_diameter=3.0,
                pocket_count=0,
                pocket_total_volume=0.0,
                pocket_avg_depth=0.0,
                pocket_max_depth=0.0,
                non_standard_hole_count=0
            ),
            confidence=FeatureConfidence(
                bounding_box=0.9,
                volume=0.9,
                through_holes=0.8,
                blind_holes=0.8,
                pockets=0.0
            ),
            dfm_issues=[],
            quote=None
        )

        mailto_link = build_mailto_link(result)

        assert mailto_link.startswith("mailto:")

    def test_contains_default_recipient(self):
        """Mailto link should contain default recipient."""
        result = ProcessingResult(
            part_id="test-uuid-123",
            step_file_path="/path/to/test.step",
            stl_file_path="/path/to/test.stl",
            features=PartFeatures(
                bounding_box_x=100.0,
                bounding_box_y=50.0,
                bounding_box_z=25.0,
                volume=125000.0,
                through_hole_count=0,
                blind_hole_count=0,
                blind_hole_avg_depth_to_diameter=0.0,
                blind_hole_max_depth_to_diameter=0.0,
                pocket_count=0,
                pocket_total_volume=0.0,
                pocket_avg_depth=0.0,
                pocket_max_depth=0.0,
                non_standard_hole_count=0
            ),
            confidence=FeatureConfidence(
                bounding_box=0.9,
                volume=0.9,
                through_holes=0.0,
                blind_holes=0.0,
                pockets=0.0
            ),
            dfm_issues=[],
            quote=None
        )

        mailto_link = build_mailto_link(result)

        assert "mailto:david@wellsglobal.eu" in mailto_link

    def test_accepts_custom_recipient(self):
        """Mailto link should accept custom recipient."""
        result = ProcessingResult(
            part_id="test-uuid-123",
            step_file_path="/path/to/test.step",
            stl_file_path="/path/to/test.stl",
            features=PartFeatures(
                bounding_box_x=100.0,
                bounding_box_y=50.0,
                bounding_box_z=25.0,
                volume=125000.0,
                through_hole_count=0,
                blind_hole_count=0,
                blind_hole_avg_depth_to_diameter=0.0,
                blind_hole_max_depth_to_diameter=0.0,
                pocket_count=0,
                pocket_total_volume=0.0,
                pocket_avg_depth=0.0,
                pocket_max_depth=0.0,
                non_standard_hole_count=0
            ),
            confidence=FeatureConfidence(
                bounding_box=0.9,
                volume=0.9,
                through_holes=0.0,
                blind_holes=0.0,
                pockets=0.0
            ),
            dfm_issues=[],
            quote=None
        )

        mailto_link = build_mailto_link(result, to="custom@example.com")

        assert "mailto:custom@example.com" in mailto_link

    def test_contains_part_uuid_in_subject(self):
        """Subject should contain part UUID."""
        test_uuid = "unique-part-uuid-abc123"
        result = ProcessingResult(
            part_id=test_uuid,
            step_file_path="/path/to/test.step",
            stl_file_path="/path/to/test.stl",
            features=PartFeatures(
                bounding_box_x=100.0,
                bounding_box_y=50.0,
                bounding_box_z=25.0,
                volume=125000.0,
                through_hole_count=0,
                blind_hole_count=0,
                blind_hole_avg_depth_to_diameter=0.0,
                blind_hole_max_depth_to_diameter=0.0,
                pocket_count=0,
                pocket_total_volume=0.0,
                pocket_avg_depth=0.0,
                pocket_max_depth=0.0,
                non_standard_hole_count=0
            ),
            confidence=FeatureConfidence(
                bounding_box=0.9,
                volume=0.9,
                through_holes=0.0,
                blind_holes=0.0,
                pockets=0.0
            ),
            dfm_issues=[],
            quote=None
        )

        mailto_link = build_mailto_link(result)

        # Decode the URL to check for UUID
        decoded = unquote(mailto_link)
        assert test_uuid in decoded

    def test_contains_part_uuid_in_body(self):
        """Body should contain part UUID."""
        test_uuid = "unique-part-uuid-xyz789"
        result = ProcessingResult(
            part_id=test_uuid,
            step_file_path="/path/to/test.step",
            stl_file_path="/path/to/test.stl",
            features=PartFeatures(
                bounding_box_x=100.0,
                bounding_box_y=50.0,
                bounding_box_z=25.0,
                volume=125000.0,
                through_hole_count=0,
                blind_hole_count=0,
                blind_hole_avg_depth_to_diameter=0.0,
                blind_hole_max_depth_to_diameter=0.0,
                pocket_count=0,
                pocket_total_volume=0.0,
                pocket_avg_depth=0.0,
                pocket_max_depth=0.0,
                non_standard_hole_count=0
            ),
            confidence=FeatureConfidence(
                bounding_box=0.9,
                volume=0.9,
                through_holes=0.0,
                blind_holes=0.0,
                pockets=0.0
            ),
            dfm_issues=[],
            quote=None
        )

        mailto_link = build_mailto_link(result)

        # Decode the URL to check for UUID in body
        decoded = unquote(mailto_link)
        assert f"Part ID: {test_uuid}" in decoded

    def test_contains_bbox_dimensions(self):
        """Body should contain bounding box dimensions."""
        result = ProcessingResult(
            part_id="test-uuid-123",
            step_file_path="/path/to/test.step",
            stl_file_path="/path/to/test.stl",
            features=PartFeatures(
                bounding_box_x=100.5,
                bounding_box_y=50.3,
                bounding_box_z=25.7,
                volume=125000.0,
                through_hole_count=0,
                blind_hole_count=0,
                blind_hole_avg_depth_to_diameter=0.0,
                blind_hole_max_depth_to_diameter=0.0,
                pocket_count=0,
                pocket_total_volume=0.0,
                pocket_avg_depth=0.0,
                pocket_max_depth=0.0,
                non_standard_hole_count=0
            ),
            confidence=FeatureConfidence(
                bounding_box=0.9,
                volume=0.9,
                through_holes=0.0,
                blind_holes=0.0,
                pockets=0.0
            ),
            dfm_issues=[],
            quote=None
        )

        mailto_link = build_mailto_link(result)
        decoded = unquote(mailto_link)

        assert "100.5" in decoded
        assert "50.3" in decoded
        assert "25.7" in decoded

    def test_contains_feature_counts(self):
        """Body should contain feature counts."""
        result = ProcessingResult(
            part_id="test-uuid-123",
            step_file_path="/path/to/test.step",
            stl_file_path="/path/to/test.stl",
            features=PartFeatures(
                bounding_box_x=100.0,
                bounding_box_y=50.0,
                bounding_box_z=25.0,
                volume=125000.0,
                through_hole_count=3,
                blind_hole_count=2,
                blind_hole_avg_depth_to_diameter=3.0,
                blind_hole_max_depth_to_diameter=3.0,
                pocket_count=1,
                pocket_total_volume=5000.0,
                pocket_avg_depth=5.0,
                pocket_max_depth=5.0,
                non_standard_hole_count=0
            ),
            confidence=FeatureConfidence(
                bounding_box=0.9,
                volume=0.9,
                through_holes=0.8,
                blind_holes=0.8,
                pockets=0.7
            ),
            dfm_issues=[],
            quote=None
        )

        mailto_link = build_mailto_link(result)
        decoded = unquote(mailto_link)

        assert "Through Holes: 3" in decoded
        assert "Blind Holes: 2" in decoded
        assert "Pockets: 1" in decoded

    def test_contains_quote_info_when_present(self):
        """Body should contain quote information when available."""
        result = ProcessingResult(
            part_id="test-uuid-123",
            step_file_path="/path/to/test.step",
            stl_file_path="/path/to/test.stl",
            features=PartFeatures(
                bounding_box_x=100.0,
                bounding_box_y=50.0,
                bounding_box_z=25.0,
                volume=125000.0,
                through_hole_count=0,
                blind_hole_count=0,
                blind_hole_avg_depth_to_diameter=0.0,
                blind_hole_max_depth_to_diameter=0.0,
                pocket_count=0,
                pocket_total_volume=0.0,
                pocket_avg_depth=0.0,
                pocket_max_depth=0.0,
                non_standard_hole_count=0
            ),
            confidence=FeatureConfidence(
                bounding_box=0.9,
                volume=0.9,
                through_holes=0.0,
                blind_holes=0.0,
                pockets=0.0
            ),
            dfm_issues=[],
            quote=QuoteResult(
                price_per_unit=125.50,
                total_price=125.50,
                quantity=1,
                breakdown={"material": 30.0, "machining": 75.0, "setup": 20.50},
                minimum_applied=False
            )
        )

        mailto_link = build_mailto_link(result)
        decoded = unquote(mailto_link)

        assert "Quote Information" in decoded
        assert "125.50" in decoded
        assert "Quantity: 1" in decoded

    def test_contains_dfm_issues_when_present(self):
        """Body should contain DFM issues when present."""
        result = ProcessingResult(
            part_id="test-uuid-123",
            step_file_path="/path/to/test.step",
            stl_file_path="/path/to/test.stl",
            features=PartFeatures(
                bounding_box_x=100.0,
                bounding_box_y=50.0,
                bounding_box_z=25.0,
                volume=125000.0,
                through_hole_count=0,
                blind_hole_count=0,
                blind_hole_avg_depth_to_diameter=0.0,
                blind_hole_max_depth_to_diameter=0.0,
                pocket_count=0,
                pocket_total_volume=0.0,
                pocket_avg_depth=0.0,
                pocket_max_depth=0.0,
                non_standard_hole_count=0
            ),
            confidence=FeatureConfidence(
                bounding_box=0.9,
                volume=0.9,
                through_holes=0.0,
                blind_holes=0.0,
                pockets=0.0
            ),
            dfm_issues=[
                DfmIssue(severity="critical", message="Very deep blind hole detected."),
                DfmIssue(severity="warning", message="Non-standard hole size found.")
            ],
            quote=None
        )

        mailto_link = build_mailto_link(result)
        decoded = unquote(mailto_link)

        assert "DFM Issues" in decoded
        assert "CRITICAL" in decoded
        assert "Very deep blind hole" in decoded
        assert "WARNING" in decoded
        assert "Non-standard hole" in decoded

    def test_url_encoding_is_valid(self):
        """Mailto link should have properly encoded URL components."""
        result = ProcessingResult(
            part_id="test-uuid-123",
            step_file_path="/path/to/test.step",
            stl_file_path="/path/to/test.stl",
            features=PartFeatures(
                bounding_box_x=100.0,
                bounding_box_y=50.0,
                bounding_box_z=25.0,
                volume=125000.0,
                through_hole_count=0,
                blind_hole_count=0,
                blind_hole_avg_depth_to_diameter=0.0,
                blind_hole_max_depth_to_diameter=0.0,
                pocket_count=0,
                pocket_total_volume=0.0,
                pocket_avg_depth=0.0,
                pocket_max_depth=0.0,
                non_standard_hole_count=0
            ),
            confidence=FeatureConfidence(
                bounding_box=0.9,
                volume=0.9,
                through_holes=0.0,
                blind_holes=0.0,
                pockets=0.0
            ),
            dfm_issues=[],
            quote=None
        )

        mailto_link = build_mailto_link(result)

        # Should have subject and body parameters
        assert "?subject=" in mailto_link
        assert "&body=" in mailto_link

        # Spaces should be encoded as %20
        assert " " not in mailto_link.split("?")[1]  # No spaces in query string
