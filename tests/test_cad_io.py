"""
Test suite for CAD I/O utilities (STEP file loading).
Following TDD - tests written first.
"""
import os
import tempfile
import pytest
import cadquery as cq
from modules.cad_io import load_step, StepLoadError


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def valid_step_file(temp_dir):
    """Create a valid STEP file for testing."""
    # Create a simple box using cadquery
    box = cq.Workplane("XY").box(10, 10, 10)

    # Export to STEP
    step_path = os.path.join(temp_dir, "test_box.step")
    cq.exporters.export(box, step_path)

    return step_path


class TestLoadStep:
    """Test STEP file loading."""

    def test_load_valid_step_file(self, valid_step_file):
        """Test that a valid STEP file loads successfully."""
        result = load_step(valid_step_file)
        assert result is not None

    def test_loaded_step_is_workplane(self, valid_step_file):
        """Test that loaded STEP returns a cadquery Workplane."""
        result = load_step(valid_step_file)
        assert isinstance(result, cq.Workplane)

    def test_loaded_step_has_solid(self, valid_step_file):
        """Test that loaded STEP contains a valid solid."""
        result = load_step(valid_step_file)
        # Should have a solid in the workplane
        assert result.val() is not None
        # Should be a solid
        assert hasattr(result.val(), 'Volume')

    def test_loaded_step_has_correct_volume(self, valid_step_file):
        """Test that loaded STEP preserves geometry (volume check)."""
        result = load_step(valid_step_file)
        # 10x10x10 box should have volume of 1000
        volume = result.val().Volume()
        assert abs(volume - 1000.0) < 1.0  # Allow small tolerance

    def test_load_nonexistent_file_raises_error(self, temp_dir):
        """Test that loading non-existent file raises StepLoadError."""
        nonexistent_path = os.path.join(temp_dir, "does_not_exist.step")

        with pytest.raises(StepLoadError) as exc_info:
            load_step(nonexistent_path)

        assert "does_not_exist.step" in str(exc_info.value) or "not found" in str(exc_info.value).lower()

    def test_load_invalid_step_file_raises_error(self, temp_dir):
        """Test that loading invalid STEP file raises StepLoadError."""
        # Create a file with invalid content
        invalid_path = os.path.join(temp_dir, "invalid.step")
        with open(invalid_path, "w") as f:
            f.write("This is not a valid STEP file\n")
            f.write("Just some random text\n")

        with pytest.raises(StepLoadError) as exc_info:
            load_step(invalid_path)

        error_msg = str(exc_info.value).lower()
        assert "invalid" in error_msg or "parse" in error_msg or "load" in error_msg

    def test_load_non_step_file_raises_error(self, temp_dir):
        """Test that loading non-STEP file raises StepLoadError."""
        # Create a text file
        txt_path = os.path.join(temp_dir, "test.txt")
        with open(txt_path, "w") as f:
            f.write("This is a text file, not a STEP file\n")

        with pytest.raises(StepLoadError):
            load_step(txt_path)

    def test_load_empty_file_raises_error(self, temp_dir):
        """Test that loading empty file raises StepLoadError."""
        empty_path = os.path.join(temp_dir, "empty.step")
        with open(empty_path, "w") as f:
            pass  # Create empty file

        with pytest.raises(StepLoadError):
            load_step(empty_path)

    def test_step_load_error_has_helpful_message(self, temp_dir):
        """Test that StepLoadError provides helpful error messages."""
        nonexistent_path = os.path.join(temp_dir, "missing.step")

        with pytest.raises(StepLoadError) as exc_info:
            load_step(nonexistent_path)

        # Error message should be helpful
        error_msg = str(exc_info.value)
        assert len(error_msg) > 10  # Not just empty or cryptic
        assert error_msg  # Not empty


class TestStepLoadError:
    """Test StepLoadError exception."""

    def test_step_load_error_is_exception(self):
        """Test that StepLoadError is an Exception."""
        assert issubclass(StepLoadError, Exception)

    def test_step_load_error_can_be_raised(self):
        """Test that StepLoadError can be raised and caught."""
        with pytest.raises(StepLoadError):
            raise StepLoadError("Test error message")

    def test_step_load_error_has_message(self):
        """Test that StepLoadError preserves error message."""
        message = "Custom error message"

        with pytest.raises(StepLoadError) as exc_info:
            raise StepLoadError(message)

        assert str(exc_info.value) == message


class TestComplexGeometry:
    """Test loading more complex STEP files."""

    def test_load_step_with_holes(self, temp_dir):
        """Test loading STEP file with holes."""
        # Create a box with holes
        box_with_holes = (
            cq.Workplane("XY")
            .box(20, 20, 10)
            .faces(">Z")
            .workplane()
            .hole(5)
        )

        step_path = os.path.join(temp_dir, "box_with_holes.step")
        cq.exporters.export(box_with_holes, step_path)

        result = load_step(step_path)
        assert result is not None
        assert isinstance(result, cq.Workplane)

    def test_load_step_with_multiple_operations(self, temp_dir):
        """Test loading STEP file with multiple operations."""
        # Create a more complex shape
        complex_part = (
            cq.Workplane("XY")
            .box(30, 30, 5)
            .faces(">Z")
            .workplane()
            .rect(20, 20, forConstruction=True)
            .vertices()
            .hole(3)
        )

        step_path = os.path.join(temp_dir, "complex_part.step")
        cq.exporters.export(complex_part, step_path)

        result = load_step(step_path)
        assert result is not None
        # Should have a valid solid
        assert result.val() is not None
