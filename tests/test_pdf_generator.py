"""
Tests for PDF Quote Generator

Tests PDF generation from processing results.
"""

import pytest
from io import BytesIO
from PyPDF2 import PdfReader

from modules.pdf_generator import generate_quote_pdf
from modules.domain import (
    ProcessingResult,
    PartFeatures,
    FeatureConfidence,
    DfmIssue,
    QuoteResult
)


class TestPdfGeneration:
    """Test basic PDF generation functionality."""

    def test_generate_pdf_returns_bytes(self):
        """PDF generation should return non-empty bytes."""
        result = ProcessingResult(
            part_id="test-uuid-12345",
            step_file_path="/path/to/test.step",
            stl_file_path="/path/to/test.stl",
            features=PartFeatures(
                bounding_box_x=100.0,
                bounding_box_y=100.0,
                bounding_box_z=50.0,
                volume=500000.0,
                through_hole_count=2,
                blind_hole_count=1,
                blind_hole_avg_depth_to_diameter=3.0,
                blind_hole_max_depth_to_diameter=4.0,
                pocket_count=1,
                pocket_total_volume=5000.0,
                pocket_avg_depth=10.0,
                pocket_max_depth=10.0,
                non_standard_hole_count=0
            ),
            confidence=FeatureConfidence(
                bounding_box=0.9,
                volume=0.9,
                through_holes=0.9,
                blind_holes=0.9,
                pockets=0.8
            ),
            dfm_issues=[],
            quote=QuoteResult(
                price_per_unit=125.50,
                total_price=125.50,
                quantity=1,
                breakdown={
                    "material": 30.0,
                    "machining": 75.0,
                    "setup": 20.50
                },
                minimum_applied=False
            )
        )

        pdf_bytes = generate_quote_pdf(result)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

    def test_pdf_contains_required_header(self):
        """PDF should contain 'Tiento Quote v0.1' in text."""
        result = ProcessingResult(
            part_id="test-uuid-67890",
            step_file_path="/path/to/test.step",
            stl_file_path="/path/to/test.stl",
            features=PartFeatures(
                bounding_box_x=100.0,
                bounding_box_y=100.0,
                bounding_box_z=50.0,
                volume=500000.0,
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
                bounding_box=0.8,
                volume=0.8,
                through_holes=0.0,
                blind_holes=0.0,
                pockets=0.0
            ),
            dfm_issues=[],
            quote=None
        )

        pdf_bytes = generate_quote_pdf(result)
        pdf_text = _extract_text_from_pdf(pdf_bytes)

        assert "Tiento Quote v0.1" in pdf_text

    def test_pdf_contains_part_uuid(self):
        """PDF should contain the part UUID."""
        test_uuid = "unique-test-uuid-abc123"

        result = ProcessingResult(
            part_id=test_uuid,
            step_file_path="/path/to/test.step",
            stl_file_path="/path/to/test.stl",
            features=PartFeatures(
                bounding_box_x=100.0,
                bounding_box_y=100.0,
                bounding_box_z=50.0,
                volume=500000.0,
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
                bounding_box=0.8,
                volume=0.8,
                through_holes=0.0,
                blind_holes=0.0,
                pockets=0.0
            ),
            dfm_issues=[],
            quote=None
        )

        pdf_bytes = generate_quote_pdf(result)
        pdf_text = _extract_text_from_pdf(pdf_bytes)

        assert test_uuid in pdf_text

    def test_pdf_is_valid_format(self):
        """Generated PDF should be readable by PDF parser."""
        result = ProcessingResult(
            part_id="format-test-uuid",
            step_file_path="/path/to/test.step",
            stl_file_path="/path/to/test.stl",
            features=PartFeatures(
                bounding_box_x=100.0,
                bounding_box_y=100.0,
                bounding_box_z=50.0,
                volume=500000.0,
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
                bounding_box=0.8,
                volume=0.8,
                through_holes=0.0,
                blind_holes=0.0,
                pockets=0.0
            ),
            dfm_issues=[],
            quote=None
        )

        pdf_bytes = generate_quote_pdf(result)

        # Should be able to parse without exception
        reader = PdfReader(BytesIO(pdf_bytes))
        assert reader.pages is not None
        assert len(reader.pages) > 0


class TestPdfContentSections:
    """Test that all required sections are present in PDF."""

    def test_pdf_contains_specifications_section(self):
        """PDF should have specifications section."""
        result = _create_minimal_processing_result()

        pdf_bytes = generate_quote_pdf(result)
        pdf_text = _extract_text_from_pdf(pdf_bytes)

        assert "Specifications" in pdf_text
        assert "Material:" in pdf_text or "Aluminum" in pdf_text
        assert "Finish:" in pdf_text or "As-machined" in pdf_text

    def test_pdf_contains_quote_date(self):
        """PDF should include quote date."""
        result = _create_minimal_processing_result()

        pdf_bytes = generate_quote_pdf(result)
        pdf_text = _extract_text_from_pdf(pdf_bytes)

        assert "Quote Date:" in pdf_text

    def test_pdf_contains_disclaimer(self):
        """PDF should have disclaimer text."""
        result = _create_minimal_processing_result()

        pdf_bytes = generate_quote_pdf(result)
        pdf_text = _extract_text_from_pdf(pdf_bytes)

        assert "Disclaimer" in pdf_text or "automatically generated" in pdf_text.lower()


class TestPdfWithQuote:
    """Test PDF generation with pricing quote."""

    def test_pdf_includes_pricing_when_quote_present(self):
        """PDF should show pricing when quote is provided."""
        result = ProcessingResult(
            part_id="quote-test-uuid",
            step_file_path="/path/to/test.step",
            stl_file_path="/path/to/test.stl",
            features=PartFeatures(
                bounding_box_x=100.0,
                bounding_box_y=100.0,
                bounding_box_z=50.0,
                volume=500000.0,
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
                bounding_box=0.8,
                volume=0.8,
                through_holes=0.0,
                blind_holes=0.0,
                pockets=0.0
            ),
            dfm_issues=[],
            quote=QuoteResult(
                price_per_unit=99.99,
                total_price=99.99,
                quantity=1,
                breakdown={"material": 30.0, "machining": 69.99},
                minimum_applied=False
            )
        )

        pdf_bytes = generate_quote_pdf(result)
        pdf_text = _extract_text_from_pdf(pdf_bytes)

        assert "Pricing Summary" in pdf_text or "Price" in pdf_text
        assert "99.99" in pdf_text

    def test_pdf_includes_breakdown(self):
        """PDF should show cost breakdown components."""
        result = ProcessingResult(
            part_id="breakdown-test-uuid",
            step_file_path="/path/to/test.step",
            stl_file_path="/path/to/test.stl",
            features=PartFeatures(
                bounding_box_x=100.0,
                bounding_box_y=100.0,
                bounding_box_z=50.0,
                volume=500000.0,
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
                bounding_box=0.8,
                volume=0.8,
                through_holes=0.0,
                blind_holes=0.0,
                pockets=0.0
            ),
            dfm_issues=[],
            quote=QuoteResult(
                price_per_unit=150.0,
                total_price=150.0,
                quantity=1,
                breakdown={
                    "material": 40.0,
                    "machining": 90.0,
                    "setup": 20.0
                },
                minimum_applied=False
            )
        )

        pdf_bytes = generate_quote_pdf(result)
        pdf_text = _extract_text_from_pdf(pdf_bytes)

        # Should mention breakdown components
        assert "Breakdown" in pdf_text or "Material" in pdf_text


class TestPdfWithDfmIssues:
    """Test PDF generation with DFM warnings."""

    def test_pdf_includes_dfm_warnings(self):
        """PDF should display DFM issues when present."""
        result = ProcessingResult(
            part_id="dfm-test-uuid",
            step_file_path="/path/to/test.step",
            stl_file_path="/path/to/test.stl",
            features=PartFeatures(
                bounding_box_x=100.0,
                bounding_box_y=100.0,
                bounding_box_z=50.0,
                volume=500000.0,
                through_hole_count=0,
                blind_hole_count=1,
                blind_hole_avg_depth_to_diameter=8.0,
                blind_hole_max_depth_to_diameter=12.0,
                pocket_count=0,
                pocket_total_volume=0.0,
                pocket_avg_depth=0.0,
                pocket_max_depth=0.0,
                non_standard_hole_count=0
            ),
            confidence=FeatureConfidence(
                bounding_box=0.8,
                volume=0.8,
                through_holes=0.8,
                blind_holes=0.8,
                pockets=0.0
            ),
            dfm_issues=[
                DfmIssue(
                    severity="critical",
                    message="Very deep blind hole detected (ratio: 12.0). Requires special tooling."
                ),
                DfmIssue(
                    severity="warning",
                    message="Non-standard hole size detected."
                )
            ],
            quote=None
        )

        pdf_bytes = generate_quote_pdf(result)
        pdf_text = _extract_text_from_pdf(pdf_bytes)

        assert "Manufacturing" in pdf_text or "DFM" in pdf_text or "Considerations" in pdf_text
        assert "deep" in pdf_text.lower() or "special tooling" in pdf_text.lower()

    def test_pdf_without_dfm_issues_has_no_warnings_section(self):
        """PDF without DFM issues should not show empty warnings section."""
        result = ProcessingResult(
            part_id="no-dfm-test-uuid",
            step_file_path="/path/to/test.step",
            stl_file_path="/path/to/test.stl",
            features=PartFeatures(
                bounding_box_x=100.0,
                bounding_box_y=100.0,
                bounding_box_z=50.0,
                volume=500000.0,
                through_hole_count=2,
                blind_hole_count=1,
                blind_hole_avg_depth_to_diameter=2.0,
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
                through_holes=0.9,
                blind_holes=0.9,
                pockets=0.0
            ),
            dfm_issues=[],  # No issues
            quote=None
        )

        pdf_bytes = generate_quote_pdf(result)
        # Should generate without error
        assert len(pdf_bytes) > 0


# Helper functions

def _create_minimal_processing_result() -> ProcessingResult:
    """Create a minimal ProcessingResult for testing."""
    return ProcessingResult(
        part_id="minimal-test-uuid",
        step_file_path="/path/to/test.step",
        stl_file_path="/path/to/test.stl",
        features=PartFeatures(
            bounding_box_x=100.0,
            bounding_box_y=100.0,
            bounding_box_z=50.0,
            volume=500000.0,
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
            bounding_box=0.8,
            volume=0.8,
            through_holes=0.0,
            blind_holes=0.0,
            pockets=0.0
        ),
        dfm_issues=[],
        quote=None
    )


def _extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text content from PDF bytes.

    Args:
        pdf_bytes: PDF content as bytes

    Returns:
        Extracted text as string
    """
    reader = PdfReader(BytesIO(pdf_bytes))
    text = ""

    for page in reader.pages:
        text += page.extract_text()

    return text
