"""
Domain models for Tiento Quote v0.1.
Shared dataclasses used across the application.
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Literal


@dataclass
class PartFeatures:
    """
    Detected features from CAD part analysis.
    All measurements in mm, volumes in mm³.
    Defaults to zero for all features.
    """

    # Bounding box dimensions (mm)
    bounding_box_x: float = 0.0
    bounding_box_y: float = 0.0
    bounding_box_z: float = 0.0

    # Volume (mm³)
    volume: float = 0.0

    # Through holes
    through_hole_count: int = 0

    # Blind holes
    blind_hole_count: int = 0
    blind_hole_avg_depth_to_diameter: float = 0.0
    blind_hole_max_depth_to_diameter: float = 0.0

    # Pockets/cavities
    pocket_count: int = 0
    pocket_total_volume: float = 0.0
    pocket_avg_depth: float = 0.0
    pocket_max_depth: float = 0.0

    # Non-standard features
    non_standard_hole_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PartFeatures":
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class FeatureConfidence:
    """
    Confidence scores for detected features.
    Scores range from 0.0 (no confidence) to 1.0 (100% confident).
    """

    bounding_box: float = 0.0
    volume: float = 0.0
    through_holes: float = 0.0
    blind_holes: float = 0.0
    pockets: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "FeatureConfidence":
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class DfmIssue:
    """
    Design for Manufacturing issue detected in part.

    Severity levels:
    - "critical": Red flag, requires manual review
    - "warning": Yellow flag, may increase cost
    - "info": Informational, no blocking issue
    """

    severity: Literal["critical", "warning", "info"]
    message: str

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "DfmIssue":
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class QuoteResult:
    """
    Calculated quote result from pricing engine.

    All prices in EUR.
    """

    price_per_unit: float
    total_price: float
    quantity: int
    breakdown: Dict[str, float]
    minimum_applied: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuoteResult":
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class ProcessingResult:
    """
    Complete result of processing a STEP file.

    Contains all extracted features, confidence scores, DFM issues,
    pricing quote, and any errors encountered.
    """

    part_id: str
    step_file_path: str
    stl_file_path: str
    features: PartFeatures
    confidence: FeatureConfidence
    dfm_issues: List[DfmIssue]
    quote: Optional[QuoteResult]
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "part_id": self.part_id,
            "step_file_path": self.step_file_path,
            "stl_file_path": self.stl_file_path,
            "features": self.features.to_dict(),
            "confidence": self.confidence.to_dict(),
            "dfm_issues": [issue.to_dict() for issue in self.dfm_issues],
            "quote": self.quote.to_dict() if self.quote else None,
            "errors": self.errors,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcessingResult":
        """Create instance from dictionary."""
        return cls(
            part_id=data["part_id"],
            step_file_path=data["step_file_path"],
            stl_file_path=data["stl_file_path"],
            features=PartFeatures.from_dict(data["features"]),
            confidence=FeatureConfidence.from_dict(data["confidence"]),
            dfm_issues=[DfmIssue.from_dict(issue) for issue in data["dfm_issues"]],
            quote=QuoteResult.from_dict(data["quote"]) if data["quote"] else None,
            errors=data.get("errors", []),
        )
