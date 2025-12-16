"""
Test suite for domain models (dataclasses).
Following TDD - tests written first.
"""
import pytest
from modules.domain import (
    PartFeatures,
    FeatureConfidence,
    DfmIssue,
    QuoteResult,
    ProcessingResult,
)


class TestPartFeatures:
    """Test PartFeatures dataclass."""

    def test_default_values(self):
        """Test that PartFeatures has correct default values (zeros)."""
        features = PartFeatures()

        # Bounding box defaults
        assert features.bounding_box_x == 0.0
        assert features.bounding_box_y == 0.0
        assert features.bounding_box_z == 0.0

        # Volume default
        assert features.volume == 0.0

        # Hole defaults
        assert features.through_hole_count == 0
        assert features.blind_hole_count == 0
        assert features.blind_hole_avg_depth_to_diameter == 0.0
        assert features.blind_hole_max_depth_to_diameter == 0.0

        # Pocket defaults
        assert features.pocket_count == 0
        assert features.pocket_total_volume == 0.0
        assert features.pocket_avg_depth == 0.0
        assert features.pocket_max_depth == 0.0

        # Non-standard features
        assert features.non_standard_hole_count == 0

    def test_custom_values(self):
        """Test PartFeatures with custom values."""
        features = PartFeatures(
            bounding_box_x=100.0,
            bounding_box_y=80.0,
            bounding_box_z=30.0,
            volume=12500.0,
            through_hole_count=4,
            blind_hole_count=2,
            blind_hole_avg_depth_to_diameter=3.5,
            blind_hole_max_depth_to_diameter=5.0,
            pocket_count=1,
            pocket_total_volume=500.0,
            pocket_avg_depth=10.0,
            pocket_max_depth=10.0,
            non_standard_hole_count=1,
        )

        assert features.bounding_box_x == 100.0
        assert features.through_hole_count == 4
        assert features.blind_hole_avg_depth_to_diameter == 3.5

    def test_to_dict(self):
        """Test conversion to dictionary."""
        features = PartFeatures(
            bounding_box_x=100.0,
            bounding_box_y=80.0,
            volume=12500.0,
            through_hole_count=4,
        )

        result = features.to_dict()

        assert isinstance(result, dict)
        assert result["bounding_box_x"] == 100.0
        assert result["bounding_box_y"] == 80.0
        assert result["volume"] == 12500.0
        assert result["through_hole_count"] == 4
        assert result["blind_hole_count"] == 0  # Default value

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "bounding_box_x": 150.0,
            "bounding_box_y": 100.0,
            "bounding_box_z": 50.0,
            "volume": 25000.0,
            "through_hole_count": 8,
            "blind_hole_count": 3,
            "blind_hole_avg_depth_to_diameter": 4.2,
            "blind_hole_max_depth_to_diameter": 6.0,
            "pocket_count": 2,
            "pocket_total_volume": 1000.0,
            "pocket_avg_depth": 15.0,
            "pocket_max_depth": 20.0,
            "non_standard_hole_count": 2,
        }

        features = PartFeatures.from_dict(data)

        assert features.bounding_box_x == 150.0
        assert features.volume == 25000.0
        assert features.through_hole_count == 8
        assert features.blind_hole_avg_depth_to_diameter == 4.2

    def test_round_trip(self):
        """Test to_dict() and from_dict() round-trip."""
        original = PartFeatures(
            bounding_box_x=200.0,
            bounding_box_y=150.0,
            bounding_box_z=75.0,
            volume=50000.0,
            through_hole_count=10,
            blind_hole_count=5,
            pocket_count=3,
            non_standard_hole_count=1,
        )

        # Convert to dict and back
        data = original.to_dict()
        restored = PartFeatures.from_dict(data)

        # Verify all fields match
        assert restored.bounding_box_x == original.bounding_box_x
        assert restored.bounding_box_y == original.bounding_box_y
        assert restored.bounding_box_z == original.bounding_box_z
        assert restored.volume == original.volume
        assert restored.through_hole_count == original.through_hole_count
        assert restored.blind_hole_count == original.blind_hole_count
        assert restored.pocket_count == original.pocket_count
        assert restored.non_standard_hole_count == original.non_standard_hole_count


class TestFeatureConfidence:
    """Test FeatureConfidence dataclass."""

    def test_default_values(self):
        """Test default confidence scores are 0.0."""
        confidence = FeatureConfidence()

        assert confidence.bounding_box == 0.0
        assert confidence.volume == 0.0
        assert confidence.through_holes == 0.0
        assert confidence.blind_holes == 0.0
        assert confidence.pockets == 0.0

    def test_custom_values(self):
        """Test FeatureConfidence with custom values."""
        confidence = FeatureConfidence(
            bounding_box=1.0,
            volume=1.0,
            through_holes=0.92,
            blind_holes=0.85,
            pockets=0.78,
        )

        assert confidence.bounding_box == 1.0
        assert confidence.through_holes == 0.92
        assert confidence.blind_holes == 0.85
        assert confidence.pockets == 0.78

    def test_to_dict(self):
        """Test conversion to dictionary."""
        confidence = FeatureConfidence(
            bounding_box=1.0,
            volume=1.0,
            through_holes=0.90,
            blind_holes=0.80,
            pockets=0.75,
        )

        result = confidence.to_dict()

        assert isinstance(result, dict)
        assert result["bounding_box"] == 1.0
        assert result["through_holes"] == 0.90
        assert result["blind_holes"] == 0.80

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "bounding_box": 1.0,
            "volume": 1.0,
            "through_holes": 0.95,
            "blind_holes": 0.88,
            "pockets": 0.82,
        }

        confidence = FeatureConfidence.from_dict(data)

        assert confidence.bounding_box == 1.0
        assert confidence.through_holes == 0.95
        assert confidence.pockets == 0.82

    def test_round_trip(self):
        """Test to_dict() and from_dict() round-trip."""
        original = FeatureConfidence(
            bounding_box=1.0,
            volume=1.0,
            through_holes=0.93,
            blind_holes=0.87,
            pockets=0.79,
        )

        data = original.to_dict()
        restored = FeatureConfidence.from_dict(data)

        assert restored.bounding_box == original.bounding_box
        assert restored.volume == original.volume
        assert restored.through_holes == original.through_holes
        assert restored.blind_holes == original.blind_holes
        assert restored.pockets == original.pockets


class TestDfmIssue:
    """Test DfmIssue dataclass."""

    def test_critical_issue(self):
        """Test creating a critical DFM issue."""
        issue = DfmIssue(
            severity="critical",
            message="Thin walls detected (<0.5mm) - Part requires manual review",
        )

        assert issue.severity == "critical"
        assert "Thin walls" in issue.message

    def test_warning_issue(self):
        """Test creating a warning DFM issue."""
        issue = DfmIssue(
            severity="warning",
            message="Deep blind holes (depth:diameter > 5:1) detected",
        )

        assert issue.severity == "warning"
        assert "Deep blind holes" in issue.message

    def test_info_issue(self):
        """Test creating an info DFM issue."""
        issue = DfmIssue(
            severity="info",
            message="Non-standard hole sizes detected",
        )

        assert issue.severity == "info"
        assert "Non-standard" in issue.message

    def test_to_dict(self):
        """Test conversion to dictionary."""
        issue = DfmIssue(severity="critical", message="Test message")

        result = issue.to_dict()

        assert isinstance(result, dict)
        assert result["severity"] == "critical"
        assert result["message"] == "Test message"

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "severity": "warning",
            "message": "Warning message",
        }

        issue = DfmIssue.from_dict(data)

        assert issue.severity == "warning"
        assert issue.message == "Warning message"

    def test_round_trip(self):
        """Test to_dict() and from_dict() round-trip."""
        original = DfmIssue(
            severity="critical",
            message="Sharp internal corners detected",
        )

        data = original.to_dict()
        restored = DfmIssue.from_dict(data)

        assert restored.severity == original.severity
        assert restored.message == original.message


class TestQuoteResult:
    """Test QuoteResult dataclass."""

    def test_simple_quote(self):
        """Test creating a simple quote result."""
        quote = QuoteResult(
            price_per_unit=45.50,
            total_price=227.50,
            quantity=5,
            breakdown={"Base cost": 30.0, "Volume": 10.0, "Holes": 5.50},
            minimum_applied=False,
        )

        assert quote.price_per_unit == 45.50
        assert quote.total_price == 227.50
        assert quote.quantity == 5
        assert quote.minimum_applied is False
        assert "Base cost" in quote.breakdown

    def test_minimum_applied_quote(self):
        """Test quote with minimum order applied."""
        quote = QuoteResult(
            price_per_unit=20.0,
            total_price=30.0,
            quantity=1,
            breakdown={"Base cost": 20.0},
            minimum_applied=True,
        )

        assert quote.total_price == 30.0
        assert quote.minimum_applied is True

    def test_to_dict(self):
        """Test conversion to dictionary."""
        quote = QuoteResult(
            price_per_unit=50.0,
            total_price=250.0,
            quantity=5,
            breakdown={"Base cost": 30.0, "Volume": 20.0},
            minimum_applied=False,
        )

        result = quote.to_dict()

        assert isinstance(result, dict)
        assert result["price_per_unit"] == 50.0
        assert result["total_price"] == 250.0
        assert result["quantity"] == 5
        assert result["minimum_applied"] is False
        assert isinstance(result["breakdown"], dict)

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "price_per_unit": 60.0,
            "total_price": 300.0,
            "quantity": 5,
            "breakdown": {"Base cost": 40.0, "Features": 20.0},
            "minimum_applied": False,
        }

        quote = QuoteResult.from_dict(data)

        assert quote.price_per_unit == 60.0
        assert quote.total_price == 300.0
        assert quote.quantity == 5
        assert quote.breakdown["Base cost"] == 40.0

    def test_round_trip(self):
        """Test to_dict() and from_dict() round-trip."""
        original = QuoteResult(
            price_per_unit=75.25,
            total_price=376.25,
            quantity=5,
            breakdown={"Base cost": 30.0, "Volume": 25.0, "Holes": 20.25},
            minimum_applied=False,
        )

        data = original.to_dict()
        restored = QuoteResult.from_dict(data)

        assert restored.price_per_unit == original.price_per_unit
        assert restored.total_price == original.total_price
        assert restored.quantity == original.quantity
        assert restored.minimum_applied == original.minimum_applied
        assert restored.breakdown == original.breakdown


class TestProcessingResult:
    """Test ProcessingResult dataclass."""

    def test_successful_result(self):
        """Test creating a successful processing result."""
        features = PartFeatures(bounding_box_x=100.0, volume=12500.0)
        confidence = FeatureConfidence(bounding_box=1.0, volume=1.0)
        quote = QuoteResult(
            price_per_unit=50.0,
            total_price=250.0,
            quantity=5,
            breakdown={},
            minimum_applied=False,
        )

        result = ProcessingResult(
            part_id="test-uuid-123",
            step_file_path="/uploads/test.step",
            stl_file_path="/temp/test.stl",
            features=features,
            confidence=confidence,
            dfm_issues=[],
            quote=quote,
            errors=[],
        )

        assert result.part_id == "test-uuid-123"
        assert result.step_file_path == "/uploads/test.step"
        assert result.stl_file_path == "/temp/test.stl"
        assert isinstance(result.features, PartFeatures)
        assert isinstance(result.confidence, FeatureConfidence)
        assert isinstance(result.quote, QuoteResult)
        assert len(result.errors) == 0

    def test_result_with_dfm_issues(self):
        """Test processing result with DFM issues."""
        features = PartFeatures()
        confidence = FeatureConfidence()
        quote = QuoteResult(
            price_per_unit=40.0,
            total_price=40.0,
            quantity=1,
            breakdown={},
            minimum_applied=True,
        )
        dfm_issues = [
            DfmIssue(severity="warning", message="Deep holes detected"),
            DfmIssue(severity="critical", message="Thin walls detected"),
        ]

        result = ProcessingResult(
            part_id="test-uuid-456",
            step_file_path="/uploads/test2.step",
            stl_file_path="/temp/test2.stl",
            features=features,
            confidence=confidence,
            dfm_issues=dfm_issues,
            quote=quote,
            errors=[],
        )

        assert len(result.dfm_issues) == 2
        assert result.dfm_issues[0].severity == "warning"
        assert result.dfm_issues[1].severity == "critical"

    def test_result_with_errors(self):
        """Test processing result with errors."""
        result = ProcessingResult(
            part_id="test-uuid-789",
            step_file_path="/uploads/test3.step",
            stl_file_path="",
            features=PartFeatures(),
            confidence=FeatureConfidence(),
            dfm_issues=[],
            quote=None,
            errors=["Invalid file format", "Parse error"],
        )

        assert len(result.errors) == 2
        assert "Invalid file format" in result.errors
        assert result.quote is None

    def test_to_dict(self):
        """Test conversion to dictionary."""
        features = PartFeatures(volume=1000.0)
        confidence = FeatureConfidence(volume=1.0)
        quote = QuoteResult(
            price_per_unit=30.0,
            total_price=30.0,
            quantity=1,
            breakdown={},
            minimum_applied=True,
        )

        result = ProcessingResult(
            part_id="test-uuid",
            step_file_path="/uploads/test.step",
            stl_file_path="/temp/test.stl",
            features=features,
            confidence=confidence,
            dfm_issues=[],
            quote=quote,
            errors=[],
        )

        data = result.to_dict()

        assert isinstance(data, dict)
        assert data["part_id"] == "test-uuid"
        assert isinstance(data["features"], dict)
        assert isinstance(data["confidence"], dict)
        assert isinstance(data["quote"], dict)
        assert isinstance(data["dfm_issues"], list)
        assert isinstance(data["errors"], list)

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "part_id": "test-uuid-999",
            "step_file_path": "/uploads/test.step",
            "stl_file_path": "/temp/test.stl",
            "features": {
                "bounding_box_x": 100.0,
                "bounding_box_y": 80.0,
                "bounding_box_z": 30.0,
                "volume": 12000.0,
                "through_hole_count": 4,
                "blind_hole_count": 0,
                "blind_hole_avg_depth_to_diameter": 0.0,
                "blind_hole_max_depth_to_diameter": 0.0,
                "pocket_count": 0,
                "pocket_total_volume": 0.0,
                "pocket_avg_depth": 0.0,
                "pocket_max_depth": 0.0,
                "non_standard_hole_count": 0,
            },
            "confidence": {
                "bounding_box": 1.0,
                "volume": 1.0,
                "through_holes": 0.9,
                "blind_holes": 0.0,
                "pockets": 0.0,
            },
            "dfm_issues": [
                {"severity": "warning", "message": "Test warning"}
            ],
            "quote": {
                "price_per_unit": 35.0,
                "total_price": 35.0,
                "quantity": 1,
                "breakdown": {"Base cost": 30.0},
                "minimum_applied": True,
            },
            "errors": [],
        }

        result = ProcessingResult.from_dict(data)

        assert result.part_id == "test-uuid-999"
        assert isinstance(result.features, PartFeatures)
        assert isinstance(result.confidence, FeatureConfidence)
        assert isinstance(result.quote, QuoteResult)
        assert len(result.dfm_issues) == 1
        assert isinstance(result.dfm_issues[0], DfmIssue)

    def test_round_trip(self):
        """Test to_dict() and from_dict() round-trip."""
        original = ProcessingResult(
            part_id="round-trip-test",
            step_file_path="/uploads/round_trip.step",
            stl_file_path="/temp/round_trip.stl",
            features=PartFeatures(
                bounding_box_x=150.0,
                volume=20000.0,
                through_hole_count=6,
            ),
            confidence=FeatureConfidence(
                bounding_box=1.0,
                volume=1.0,
                through_holes=0.92,
            ),
            dfm_issues=[
                DfmIssue(severity="warning", message="Warning 1"),
                DfmIssue(severity="info", message="Info 1"),
            ],
            quote=QuoteResult(
                price_per_unit=55.0,
                total_price=275.0,
                quantity=5,
                breakdown={"Base cost": 30.0, "Features": 25.0},
                minimum_applied=False,
            ),
            errors=[],
        )

        data = original.to_dict()
        restored = ProcessingResult.from_dict(data)

        assert restored.part_id == original.part_id
        assert restored.step_file_path == original.step_file_path
        assert restored.features.bounding_box_x == original.features.bounding_box_x
        assert restored.features.volume == original.features.volume
        assert restored.confidence.bounding_box == original.confidence.bounding_box
        assert len(restored.dfm_issues) == len(original.dfm_issues)
        assert restored.dfm_issues[0].severity == original.dfm_issues[0].severity
        assert restored.quote.price_per_unit == original.quote.price_per_unit
        assert restored.quote.total_price == original.quote.total_price
