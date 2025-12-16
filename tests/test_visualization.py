"""
Test suite for STEP to STL conversion and visualization.
Following TDD - tests written first.
"""
import os
import tempfile
import pytest
import cadquery as cq
from modules.visualization import step_to_stl, compute_adaptive_deflection
from modules.domain import PartFeatures


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def simple_step_file(temp_dir):
    """Create a simple STEP file (10×20×30mm box)."""
    box = cq.Workplane("XY").box(10, 20, 30)
    step_path = os.path.join(temp_dir, "test_box.step")
    cq.exporters.export(box, step_path)
    return step_path


@pytest.fixture
def complex_step_file(temp_dir):
    """Create a more complex STEP file with features."""
    shape = (
        cq.Workplane("XY")
        .box(50, 40, 20)
        .faces(">Z")
        .workplane()
        .hole(5)
    )
    step_path = os.path.join(temp_dir, "test_complex.step")
    cq.exporters.export(shape, step_path)
    return step_path


class TestComputeAdaptiveDeflection:
    """Test adaptive deflection calculation."""

    def test_returns_tuple(self):
        """Test that function returns tuple of (linear, angular)."""
        features = PartFeatures(
            bounding_box_x=100.0,
            bounding_box_y=200.0,
            bounding_box_z=150.0
        )

        result = compute_adaptive_deflection(features)

        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_linear_deflection_is_0_1_percent_of_max_dimension(self):
        """Test that linear deflection is 0.1% of largest dimension."""
        features = PartFeatures(
            bounding_box_x=100.0,
            bounding_box_y=200.0,  # Max dimension
            bounding_box_z=150.0
        )

        linear, angular = compute_adaptive_deflection(features)

        # Linear deflection should be 200 * 0.001 = 0.2
        expected_linear = 200.0 * 0.001
        assert abs(linear - expected_linear) < 0.001

    def test_angular_deflection_is_0_5_degrees(self):
        """Test that angular deflection is 0.5 degrees."""
        features = PartFeatures(
            bounding_box_x=100.0,
            bounding_box_y=200.0,
            bounding_box_z=150.0
        )

        linear, angular = compute_adaptive_deflection(features)

        # Angular deflection should always be 0.5 degrees
        assert angular == 0.5

    def test_uses_max_of_xyz_dimensions(self):
        """Test that max dimension is correctly selected."""
        # Test with X as max
        features_x = PartFeatures(bounding_box_x=300.0, bounding_box_y=100.0, bounding_box_z=50.0)
        linear_x, _ = compute_adaptive_deflection(features_x)
        assert abs(linear_x - 0.3) < 0.001  # 300 * 0.001

        # Test with Y as max
        features_y = PartFeatures(bounding_box_x=100.0, bounding_box_y=400.0, bounding_box_z=50.0)
        linear_y, _ = compute_adaptive_deflection(features_y)
        assert abs(linear_y - 0.4) < 0.001  # 400 * 0.001

        # Test with Z as max
        features_z = PartFeatures(bounding_box_x=100.0, bounding_box_y=50.0, bounding_box_z=500.0)
        linear_z, _ = compute_adaptive_deflection(features_z)
        assert abs(linear_z - 0.5) < 0.001  # 500 * 0.001

    def test_small_part_deflection(self):
        """Test deflection for small part (10×20×30mm)."""
        features = PartFeatures(
            bounding_box_x=10.0,
            bounding_box_y=20.0,
            bounding_box_z=30.0
        )

        linear, angular = compute_adaptive_deflection(features)

        # Max dimension is 30, so linear = 30 * 0.001 = 0.03
        assert abs(linear - 0.03) < 0.001
        assert angular == 0.5

    def test_large_part_deflection(self):
        """Test deflection for large part (600×400×500mm)."""
        features = PartFeatures(
            bounding_box_x=600.0,
            bounding_box_y=400.0,
            bounding_box_z=500.0
        )

        linear, angular = compute_adaptive_deflection(features)

        # Max dimension is 600, so linear = 600 * 0.001 = 0.6
        assert abs(linear - 0.6) < 0.001
        assert angular == 0.5


class TestStepToStl:
    """Test STEP to STL conversion."""

    def test_creates_stl_file(self, simple_step_file, temp_dir):
        """Test that STL file is created."""
        stl_path = os.path.join(temp_dir, "output.stl")

        step_to_stl(simple_step_file, stl_path, 0.1, 0.5)

        assert os.path.exists(stl_path)

    def test_stl_file_has_content(self, simple_step_file, temp_dir):
        """Test that STL file has non-zero size."""
        stl_path = os.path.join(temp_dir, "output.stl")

        step_to_stl(simple_step_file, stl_path, 0.1, 0.5)

        assert os.path.getsize(stl_path) > 0

    def test_stl_file_size_reasonable(self, simple_step_file, temp_dir):
        """Test that STL file size is reasonable (not too small)."""
        stl_path = os.path.join(temp_dir, "output.stl")

        step_to_stl(simple_step_file, stl_path, 0.1, 0.5)

        # STL files should be at least a few hundred bytes for simple geometry
        assert os.path.getsize(stl_path) > 100

    def test_converts_complex_shape(self, complex_step_file, temp_dir):
        """Test that complex shapes can be converted."""
        stl_path = os.path.join(temp_dir, "complex.stl")

        step_to_stl(complex_step_file, stl_path, 0.1, 0.5)

        assert os.path.exists(stl_path)
        assert os.path.getsize(stl_path) > 0

    def test_smaller_deflection_produces_larger_file(self, simple_step_file, temp_dir):
        """Test that smaller deflection produces more detailed (larger) STL."""
        stl_coarse = os.path.join(temp_dir, "coarse.stl")
        stl_fine = os.path.join(temp_dir, "fine.stl")

        # Coarse mesh
        step_to_stl(simple_step_file, stl_coarse, 1.0, 1.0)
        size_coarse = os.path.getsize(stl_coarse)

        # Fine mesh
        step_to_stl(simple_step_file, stl_fine, 0.01, 0.1)
        size_fine = os.path.getsize(stl_fine)

        # Fine mesh should be larger or equal (for simple geometry, might be same)
        # Simple boxes may not show difference, but shouldn't be smaller
        assert size_fine >= size_coarse

    def test_nonexistent_step_file_raises_error(self, temp_dir):
        """Test that nonexistent STEP file raises error."""
        nonexistent = os.path.join(temp_dir, "nonexistent.step")
        stl_path = os.path.join(temp_dir, "output.stl")

        with pytest.raises(Exception):
            step_to_stl(nonexistent, stl_path, 0.1, 0.5)

    def test_stl_file_is_valid_format(self, simple_step_file, temp_dir):
        """Test that STL file is in valid format (binary or ASCII)."""
        stl_path = os.path.join(temp_dir, "output.stl")

        step_to_stl(simple_step_file, stl_path, 0.1, 0.5)

        # Check if file can be read as binary (binary STL format)
        # Binary STL has 80-byte header followed by 4-byte triangle count
        with open(stl_path, 'rb') as f:
            header = f.read(80)  # Read header
            # Should have 80 bytes
            assert len(header) == 80

    def test_creates_parent_directories(self, simple_step_file, temp_dir):
        """Test that parent directories are created if they don't exist."""
        nested_path = os.path.join(temp_dir, "subdir", "nested", "output.stl")

        step_to_stl(simple_step_file, nested_path, 0.1, 0.5)

        assert os.path.exists(nested_path)
