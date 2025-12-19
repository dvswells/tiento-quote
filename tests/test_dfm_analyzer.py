"""
Tests for DFM (Design for Manufacturing) Analyzer

Tests manufacturability issue detection and severity thresholds.
"""

import pytest
from modules.dfm_analyzer import analyze_dfm
from modules.domain import PartFeatures, DfmIssue


class TestDeepHoleChecks:
    """Test deep hole detection based on depth-to-diameter ratio."""

    def test_no_holes_returns_no_issues(self):
        """No holes should return empty issue list."""
        features = PartFeatures(
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
        )

        issues = analyze_dfm(features)
        deep_hole_issues = [i for i in issues if "deep" in i.message.lower()]

        assert len(deep_hole_issues) == 0

    def test_shallow_holes_no_issue(self):
        """Shallow holes (ratio < 6) should not trigger warnings."""
        features = PartFeatures(
            bounding_box_x=100.0,
            bounding_box_y=100.0,
            bounding_box_z=50.0,
            volume=500000.0,
            through_hole_count=0,
            blind_hole_count=2,
            blind_hole_avg_depth_to_diameter=3.0,
            blind_hole_max_depth_to_diameter=4.5,  # Below 6
            pocket_count=0,
            pocket_total_volume=0.0,
            pocket_avg_depth=0.0,
            pocket_max_depth=0.0,
            non_standard_hole_count=0
        )

        issues = analyze_dfm(features)
        deep_hole_issues = [i for i in issues if "deep" in i.message.lower()]

        assert len(deep_hole_issues) == 0

    def test_medium_deep_hole_warning(self):
        """Holes with ratio 6-10 should trigger warning."""
        features = PartFeatures(
            bounding_box_x=100.0,
            bounding_box_y=100.0,
            bounding_box_z=50.0,
            volume=500000.0,
            through_hole_count=0,
            blind_hole_count=1,
            blind_hole_avg_depth_to_diameter=7.5,
            blind_hole_max_depth_to_diameter=7.5,  # Between 6 and 10
            pocket_count=0,
            pocket_total_volume=0.0,
            pocket_avg_depth=0.0,
            pocket_max_depth=0.0,
            non_standard_hole_count=0
        )

        issues = analyze_dfm(features)
        deep_hole_issues = [i for i in issues if "deep" in i.message.lower()]

        assert len(deep_hole_issues) == 1
        assert deep_hole_issues[0].severity == "warning"
        assert "7.5" in deep_hole_issues[0].message
        assert "challenging" in deep_hole_issues[0].message.lower() or "6" in deep_hole_issues[0].message

    def test_very_deep_hole_critical(self):
        """Holes with ratio > 10 should trigger critical."""
        features = PartFeatures(
            bounding_box_x=100.0,
            bounding_box_y=100.0,
            bounding_box_z=50.0,
            volume=500000.0,
            through_hole_count=0,
            blind_hole_count=1,
            blind_hole_avg_depth_to_diameter=8.0,
            blind_hole_max_depth_to_diameter=12.0,  # Above 10
            pocket_count=0,
            pocket_total_volume=0.0,
            pocket_avg_depth=0.0,
            pocket_max_depth=0.0,
            non_standard_hole_count=0
        )

        issues = analyze_dfm(features)
        deep_hole_issues = [i for i in issues if "deep" in i.message.lower()]

        assert len(deep_hole_issues) == 1
        assert deep_hole_issues[0].severity == "critical"
        assert "12.0" in deep_hole_issues[0].message
        assert "special tooling" in deep_hole_issues[0].message.lower() or "10" in deep_hole_issues[0].message

    def test_exactly_at_warning_threshold(self):
        """Ratio exactly at 6.0 should trigger warning."""
        features = PartFeatures(
            bounding_box_x=100.0,
            bounding_box_y=100.0,
            bounding_box_z=50.0,
            volume=500000.0,
            through_hole_count=0,
            blind_hole_count=1,
            blind_hole_avg_depth_to_diameter=6.0,
            blind_hole_max_depth_to_diameter=6.0,
            pocket_count=0,
            pocket_total_volume=0.0,
            pocket_avg_depth=0.0,
            pocket_max_depth=0.0,
            non_standard_hole_count=0
        )

        issues = analyze_dfm(features)
        deep_hole_issues = [i for i in issues if "deep" in i.message.lower()]

        # At threshold, should NOT trigger (threshold is >, not >=)
        assert len(deep_hole_issues) == 0

    def test_just_above_warning_threshold(self):
        """Ratio just above 6.0 should trigger warning."""
        features = PartFeatures(
            bounding_box_x=100.0,
            bounding_box_y=100.0,
            bounding_box_z=50.0,
            volume=500000.0,
            through_hole_count=0,
            blind_hole_count=1,
            blind_hole_avg_depth_to_diameter=6.1,
            blind_hole_max_depth_to_diameter=6.1,
            pocket_count=0,
            pocket_total_volume=0.0,
            pocket_avg_depth=0.0,
            pocket_max_depth=0.0,
            non_standard_hole_count=0
        )

        issues = analyze_dfm(features)
        deep_hole_issues = [i for i in issues if "deep" in i.message.lower()]

        assert len(deep_hole_issues) == 1
        assert deep_hole_issues[0].severity == "warning"

    def test_exactly_at_critical_threshold(self):
        """Ratio exactly at 10.0 should not trigger critical (threshold is >)."""
        features = PartFeatures(
            bounding_box_x=100.0,
            bounding_box_y=100.0,
            bounding_box_z=50.0,
            volume=500000.0,
            through_hole_count=0,
            blind_hole_count=1,
            blind_hole_avg_depth_to_diameter=10.0,
            blind_hole_max_depth_to_diameter=10.0,
            pocket_count=0,
            pocket_total_volume=0.0,
            pocket_avg_depth=0.0,
            pocket_max_depth=0.0,
            non_standard_hole_count=0
        )

        issues = analyze_dfm(features)
        deep_hole_issues = [i for i in issues if "very deep" in i.message.lower()]

        # At threshold should not trigger critical
        assert len(deep_hole_issues) == 0

        # But should trigger warning
        warning_issues = [i for i in issues if i.severity == "warning" and "deep" in i.message.lower()]
        assert len(warning_issues) == 1

    def test_just_above_critical_threshold(self):
        """Ratio just above 10.0 should trigger critical."""
        features = PartFeatures(
            bounding_box_x=100.0,
            bounding_box_y=100.0,
            bounding_box_z=50.0,
            volume=500000.0,
            through_hole_count=0,
            blind_hole_count=1,
            blind_hole_avg_depth_to_diameter=10.1,
            blind_hole_max_depth_to_diameter=10.1,
            pocket_count=0,
            pocket_total_volume=0.0,
            pocket_avg_depth=0.0,
            pocket_max_depth=0.0,
            non_standard_hole_count=0
        )

        issues = analyze_dfm(features)
        deep_hole_issues = [i for i in issues if "deep" in i.message.lower()]

        assert len(deep_hole_issues) == 1
        assert deep_hole_issues[0].severity == "critical"


class TestSmallFeatureChecks:
    """Test small feature detection (using hole diameter as proxy)."""

    def test_no_holes_no_small_feature_warning(self):
        """No holes should not trigger small feature warnings."""
        features = PartFeatures(
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
        )

        issues = analyze_dfm(features)
        small_feature_issues = [i for i in issues if "small" in i.message.lower() or "precision" in i.message.lower()]

        assert len(small_feature_issues) == 0

    def test_non_standard_holes_trigger_warning(self):
        """Non-standard holes might indicate small features (MVP heuristic)."""
        features = PartFeatures(
            bounding_box_x=100.0,
            bounding_box_y=100.0,
            bounding_box_z=50.0,
            volume=500000.0,
            through_hole_count=2,
            blind_hole_count=1,
            blind_hole_avg_depth_to_diameter=3.0,
            blind_hole_max_depth_to_diameter=4.0,
            pocket_count=0,
            pocket_total_volume=0.0,
            pocket_avg_depth=0.0,
            pocket_max_depth=0.0,
            non_standard_hole_count=2
        )

        issues = analyze_dfm(features)
        small_feature_issues = [i for i in issues if "precision" in i.message.lower() or "small" in i.message.lower()]

        # Should have warning about non-standard holes potentially being small
        assert len(small_feature_issues) >= 1
        assert any(i.severity == "warning" for i in small_feature_issues)


class TestNonStandardHoleChecks:
    """Test non-standard hole detection."""

    def test_no_non_standard_holes_no_issue(self):
        """No non-standard holes should not trigger issues."""
        features = PartFeatures(
            bounding_box_x=100.0,
            bounding_box_y=100.0,
            bounding_box_z=50.0,
            volume=500000.0,
            through_hole_count=3,
            blind_hole_count=2,
            blind_hole_avg_depth_to_diameter=3.0,
            blind_hole_max_depth_to_diameter=4.0,
            pocket_count=0,
            pocket_total_volume=0.0,
            pocket_avg_depth=0.0,
            pocket_max_depth=0.0,
            non_standard_hole_count=0
        )

        issues = analyze_dfm(features)
        non_standard_issues = [i for i in issues if "non-standard" in i.message.lower()]

        assert len(non_standard_issues) == 0

    def test_non_standard_holes_info_message(self):
        """Non-standard holes should trigger info message."""
        features = PartFeatures(
            bounding_box_x=100.0,
            bounding_box_y=100.0,
            bounding_box_z=50.0,
            volume=500000.0,
            through_hole_count=2,
            blind_hole_count=1,
            blind_hole_avg_depth_to_diameter=3.0,
            blind_hole_max_depth_to_diameter=4.0,
            pocket_count=0,
            pocket_total_volume=0.0,
            pocket_avg_depth=0.0,
            pocket_max_depth=0.0,
            non_standard_hole_count=1
        )

        issues = analyze_dfm(features)
        non_standard_issues = [i for i in issues if "non-standard" in i.message.lower()]

        assert len(non_standard_issues) >= 1
        # At least one should be info severity
        assert any(i.severity == "info" for i in non_standard_issues)

    def test_multiple_non_standard_holes_reported(self):
        """Multiple non-standard holes should be mentioned in message."""
        features = PartFeatures(
            bounding_box_x=100.0,
            bounding_box_y=100.0,
            bounding_box_z=50.0,
            volume=500000.0,
            through_hole_count=5,
            blind_hole_count=2,
            blind_hole_avg_depth_to_diameter=3.0,
            blind_hole_max_depth_to_diameter=4.0,
            pocket_count=0,
            pocket_total_volume=0.0,
            pocket_avg_depth=0.0,
            pocket_max_depth=0.0,
            non_standard_hole_count=3
        )

        issues = analyze_dfm(features)
        non_standard_issues = [i for i in issues if "non-standard" in i.message.lower()]

        assert len(non_standard_issues) >= 1
        # Should mention the count
        assert any("3" in i.message for i in non_standard_issues)


class TestMultipleIssues:
    """Test handling of multiple simultaneous issues."""

    def test_multiple_issues_all_reported(self):
        """Part with multiple issues should report all of them."""
        features = PartFeatures(
            bounding_box_x=100.0,
            bounding_box_y=100.0,
            bounding_box_z=50.0,
            volume=500000.0,
            through_hole_count=2,
            blind_hole_count=2,
            blind_hole_avg_depth_to_diameter=8.0,
            blind_hole_max_depth_to_diameter=11.0,  # Critical deep hole
            pocket_count=0,
            pocket_total_volume=0.0,
            pocket_avg_depth=0.0,
            pocket_max_depth=0.0,
            non_standard_hole_count=2  # Non-standard holes
        )

        issues = analyze_dfm(features)

        # Should have at least 2 issues (deep hole + non-standard)
        assert len(issues) >= 2

        # Check for deep hole critical issue
        critical_issues = [i for i in issues if i.severity == "critical"]
        assert len(critical_issues) >= 1

        # Check for non-standard hole info
        info_issues = [i for i in issues if i.severity == "info"]
        assert len(info_issues) >= 1

    def test_clean_part_no_issues(self):
        """Part with no manufacturability concerns should return empty list."""
        features = PartFeatures(
            bounding_box_x=100.0,
            bounding_box_y=100.0,
            bounding_box_z=50.0,
            volume=500000.0,
            through_hole_count=3,
            blind_hole_count=2,
            blind_hole_avg_depth_to_diameter=2.5,
            blind_hole_max_depth_to_diameter=3.0,  # Shallow, no issue
            pocket_count=1,
            pocket_total_volume=5000.0,
            pocket_avg_depth=10.0,
            pocket_max_depth=10.0,
            non_standard_hole_count=0  # All standard
        )

        issues = analyze_dfm(features)

        assert len(issues) == 0


class TestDfmIssueFormat:
    """Test that DfmIssue objects are properly formatted."""

    def test_issue_has_required_fields(self):
        """Each issue should have severity and message."""
        features = PartFeatures(
            bounding_box_x=100.0,
            bounding_box_y=100.0,
            bounding_box_z=50.0,
            volume=500000.0,
            through_hole_count=0,
            blind_hole_count=1,
            blind_hole_avg_depth_to_diameter=7.0,
            blind_hole_max_depth_to_diameter=7.0,
            pocket_count=0,
            pocket_total_volume=0.0,
            pocket_avg_depth=0.0,
            pocket_max_depth=0.0,
            non_standard_hole_count=1
        )

        issues = analyze_dfm(features)

        for issue in issues:
            assert hasattr(issue, 'severity')
            assert hasattr(issue, 'message')
            assert issue.severity in ['critical', 'warning', 'info']
            assert isinstance(issue.message, str)
            assert len(issue.message) > 0

    def test_severity_levels_are_valid(self):
        """All severity levels should be valid literals."""
        features = PartFeatures(
            bounding_box_x=100.0,
            bounding_box_y=100.0,
            bounding_box_z=50.0,
            volume=500000.0,
            through_hole_count=2,
            blind_hole_count=2,
            blind_hole_avg_depth_to_diameter=8.0,
            blind_hole_max_depth_to_diameter=15.0,  # Critical
            pocket_count=0,
            pocket_total_volume=0.0,
            pocket_avg_depth=0.0,
            pocket_max_depth=0.0,
            non_standard_hole_count=3
        )

        issues = analyze_dfm(features)

        valid_severities = {'critical', 'warning', 'info'}
        for issue in issues:
            assert issue.severity in valid_severities
