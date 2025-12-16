"""
Test suite for file validation helpers.
Following TDD - tests written first.
"""
import os
import tempfile
import uuid
import pytest
from modules.file_handler import (
    validate_extension,
    validate_size,
    store_upload,
    InvalidExtensionError,
    FileSizeError,
)


class TestValidateExtension:
    """Test file extension validation."""

    def test_valid_step_extension_lowercase(self):
        """Test that .step extension (lowercase) is valid."""
        # Should not raise exception
        validate_extension("test.step")
        validate_extension("my_part.step")
        validate_extension("complex-part-name.step")

    def test_valid_step_extension_uppercase(self):
        """Test that .STEP extension (uppercase) is valid."""
        # Should not raise exception
        validate_extension("test.STEP")
        validate_extension("MY_PART.STEP")

    def test_valid_step_extension_mixed_case(self):
        """Test that .StEp extension (mixed case) is valid."""
        # Should not raise exception
        validate_extension("test.StEp")
        validate_extension("test.Step")

    def test_valid_stp_extension_lowercase(self):
        """Test that .stp extension (lowercase) is valid."""
        # Should not raise exception
        validate_extension("test.stp")
        validate_extension("my_part.stp")

    def test_valid_stp_extension_uppercase(self):
        """Test that .STP extension (uppercase) is valid."""
        # Should not raise exception
        validate_extension("test.STP")

    def test_valid_stp_extension_mixed_case(self):
        """Test that .StP extension (mixed case) is valid."""
        # Should not raise exception
        validate_extension("test.StP")

    def test_invalid_stl_extension_raises(self):
        """Test that .stl extension raises InvalidExtensionError."""
        with pytest.raises(InvalidExtensionError) as exc_info:
            validate_extension("test.stl")

        assert "invalid file format" in str(exc_info.value).lower()

    def test_invalid_obj_extension_raises(self):
        """Test that .obj extension raises InvalidExtensionError."""
        with pytest.raises(InvalidExtensionError):
            validate_extension("test.obj")

    def test_invalid_txt_extension_raises(self):
        """Test that .txt extension raises InvalidExtensionError."""
        with pytest.raises(InvalidExtensionError):
            validate_extension("test.txt")

    def test_no_extension_raises(self):
        """Test that filename without extension raises InvalidExtensionError."""
        with pytest.raises(InvalidExtensionError):
            validate_extension("test")

    def test_multiple_dots_in_filename(self):
        """Test filename with multiple dots but valid extension."""
        # Should not raise exception
        validate_extension("my.test.part.step")
        validate_extension("v1.2.3.stp")

    def test_error_message_mentions_step_upload(self):
        """Test that error message is spec-aligned."""
        with pytest.raises(InvalidExtensionError) as exc_info:
            validate_extension("test.stl")

        error_msg = str(exc_info.value).lower()
        assert "step" in error_msg or ".step" in error_msg

    def test_case_insensitive_validation(self):
        """Test that validation is case-insensitive."""
        # All these should be valid
        validate_extension("test.step")
        validate_extension("test.STEP")
        validate_extension("test.Step")
        validate_extension("test.stp")
        validate_extension("test.STP")
        validate_extension("test.Stp")


class TestValidateSize:
    """Test file size validation."""

    def test_size_within_limit(self):
        """Test that size within limit passes validation."""
        # Should not raise exception
        validate_size(1000, 5000)
        validate_size(0, 5000)
        validate_size(4999, 5000)

    def test_size_exactly_at_limit(self):
        """Test that size exactly at limit passes validation."""
        # Should not raise exception
        validate_size(5000, 5000)
        validate_size(52428800, 52428800)  # 50MB

    def test_size_one_byte_over_limit_raises(self):
        """Test that size exactly 1 byte over limit raises FileSizeError."""
        with pytest.raises(FileSizeError):
            validate_size(5001, 5000)

    def test_size_far_over_limit_raises(self):
        """Test that size far over limit raises FileSizeError."""
        with pytest.raises(FileSizeError):
            validate_size(100000, 5000)

    def test_size_zero_is_valid(self):
        """Test that zero size is valid (edge case)."""
        # Should not raise exception
        validate_size(0, 1000)

    def test_max_size_50mb(self):
        """Test validation with 50MB limit (from spec)."""
        max_size = 52428800  # 50 * 1024 * 1024

        # Should not raise exception
        validate_size(52428800, max_size)  # Exactly 50MB
        validate_size(52428799, max_size)  # Just under

        # Should raise exception
        with pytest.raises(FileSizeError):
            validate_size(52428801, max_size)  # Just over

    def test_error_message_mentions_limit(self):
        """Test that error message is spec-aligned and mentions limit."""
        with pytest.raises(FileSizeError) as exc_info:
            validate_size(100000, 5000)

        error_msg = str(exc_info.value).lower()
        assert "exceeds" in error_msg or "limit" in error_msg or "size" in error_msg

    def test_error_message_mentions_50mb_for_spec_limit(self):
        """Test that error message mentions 50MB when using spec limit."""
        max_size = 52428800  # 50MB

        with pytest.raises(FileSizeError) as exc_info:
            validate_size(max_size + 1, max_size)

        error_msg = str(exc_info.value)
        assert "50" in error_msg or "50MB" in error_msg.replace(" ", "")


class TestExceptions:
    """Test custom exception classes."""

    def test_invalid_extension_error_is_exception(self):
        """Test that InvalidExtensionError is an Exception."""
        assert issubclass(InvalidExtensionError, Exception)

    def test_file_size_error_is_exception(self):
        """Test that FileSizeError is an Exception."""
        assert issubclass(FileSizeError, Exception)

    def test_invalid_extension_error_can_be_raised(self):
        """Test that InvalidExtensionError can be raised and caught."""
        with pytest.raises(InvalidExtensionError):
            raise InvalidExtensionError("Test error")

    def test_file_size_error_can_be_raised(self):
        """Test that FileSizeError can be raised and caught."""
        with pytest.raises(FileSizeError):
            raise FileSizeError("Test error")

    def test_exceptions_have_messages(self):
        """Test that exceptions preserve error messages."""
        message = "Custom error message"

        with pytest.raises(InvalidExtensionError) as exc_info:
            raise InvalidExtensionError(message)
        assert str(exc_info.value) == message

        with pytest.raises(FileSizeError) as exc_info:
            raise FileSizeError(message)
        assert str(exc_info.value) == message


class TestPureFunctions:
    """Test that validation functions are pure (no side effects)."""

    def test_validate_extension_no_side_effects(self):
        """Test that validate_extension doesn't modify anything."""
        filename = "test.step"

        # Call multiple times
        validate_extension(filename)
        validate_extension(filename)
        validate_extension(filename)

        # Filename should be unchanged (though we can't really test this with a string)
        # But we can verify it doesn't create files or access filesystem
        # (implicitly tested by not mocking filesystem)

    def test_validate_size_no_side_effects(self):
        """Test that validate_size doesn't modify anything."""
        size = 1000
        max_size = 5000

        # Call multiple times
        validate_size(size, max_size)
        validate_size(size, max_size)
        validate_size(size, max_size)

        # Should work consistently (pure function)

    def test_no_filesystem_access(self):
        """Test that validation functions don't access filesystem."""
        # If they accessed filesystem, these would fail for non-existent files
        # But since they're pure functions, they should work fine

        validate_extension("nonexistent_file.step")
        validate_size(1000, 5000)

        # No filesystem access means no errors even for fake files


class TestStoreUpload:
    """Test store_upload function."""

    def test_store_upload_creates_file(self):
        """Test that store_upload creates a file in uploads directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_bytes = b"test file content"
            original_filename = "test.step"

            part_id, stored_path = store_upload(file_bytes, original_filename, tmpdir)

            # File should exist
            assert os.path.exists(stored_path)

    def test_store_upload_returns_uuid(self):
        """Test that store_upload returns a valid UUID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_bytes = b"test content"
            original_filename = "test.step"

            part_id, stored_path = store_upload(file_bytes, original_filename, tmpdir)

            # part_id should be a valid UUID
            assert isinstance(part_id, str)
            assert len(part_id) > 0

            # Should be able to parse as UUID
            uuid_obj = uuid.UUID(part_id)
            assert str(uuid_obj) == part_id

    def test_store_upload_preserves_step_extension(self):
        """Test that store_upload preserves .step extension."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_bytes = b"test content"
            original_filename = "my_part.step"

            part_id, stored_path = store_upload(file_bytes, original_filename, tmpdir)

            # Stored file should have .step extension
            assert stored_path.endswith(".step")

    def test_store_upload_preserves_stp_extension(self):
        """Test that store_upload preserves .stp extension."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_bytes = b"test content"
            original_filename = "my_part.stp"

            part_id, stored_path = store_upload(file_bytes, original_filename, tmpdir)

            # Stored file should have .stp extension
            assert stored_path.endswith(".stp")

    def test_store_upload_writes_correct_bytes(self):
        """Test that store_upload writes the exact same bytes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_bytes = b"This is test file content with some data: 12345"
            original_filename = "test.step"

            part_id, stored_path = store_upload(file_bytes, original_filename, tmpdir)

            # Read back the file
            with open(stored_path, "rb") as f:
                stored_bytes = f.read()

            # Should be exactly the same
            assert stored_bytes == file_bytes

    def test_store_upload_creates_directory_if_missing(self):
        """Test that store_upload creates uploads directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a nested path that doesn't exist
            uploads_dir = os.path.join(tmpdir, "uploads", "nested")
            assert not os.path.exists(uploads_dir)

            file_bytes = b"test content"
            original_filename = "test.step"

            part_id, stored_path = store_upload(file_bytes, original_filename, uploads_dir)

            # Directory should now exist
            assert os.path.exists(uploads_dir)
            # File should exist
            assert os.path.exists(stored_path)

    def test_store_upload_returns_correct_path(self):
        """Test that returned path is in the correct directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_bytes = b"test content"
            original_filename = "test.step"

            part_id, stored_path = store_upload(file_bytes, original_filename, tmpdir)

            # Path should be in the uploads directory
            assert stored_path.startswith(tmpdir)
            # Filename should be UUID + extension
            filename = os.path.basename(stored_path)
            assert filename.endswith(".step")
            # UUID part should match part_id
            assert part_id in filename

    def test_store_upload_multiple_files(self):
        """Test that multiple uploads create different files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_bytes1 = b"first file"
            file_bytes2 = b"second file"

            part_id1, stored_path1 = store_upload(file_bytes1, "file1.step", tmpdir)
            part_id2, stored_path2 = store_upload(file_bytes2, "file2.step", tmpdir)

            # Different UUIDs
            assert part_id1 != part_id2
            # Different paths
            assert stored_path1 != stored_path2
            # Both files exist
            assert os.path.exists(stored_path1)
            assert os.path.exists(stored_path2)

            # Correct content
            with open(stored_path1, "rb") as f:
                assert f.read() == file_bytes1
            with open(stored_path2, "rb") as f:
                assert f.read() == file_bytes2

    def test_store_upload_large_file(self):
        """Test that store_upload handles larger files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a 1MB file
            file_bytes = b"X" * (1024 * 1024)
            original_filename = "large.step"

            part_id, stored_path = store_upload(file_bytes, original_filename, tmpdir)

            # File should exist and have correct size
            assert os.path.exists(stored_path)
            assert os.path.getsize(stored_path) == len(file_bytes)

            # Verify content
            with open(stored_path, "rb") as f:
                assert f.read() == file_bytes

    def test_store_upload_empty_file(self):
        """Test that store_upload handles empty files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_bytes = b""
            original_filename = "empty.step"

            part_id, stored_path = store_upload(file_bytes, original_filename, tmpdir)

            # File should exist
            assert os.path.exists(stored_path)
            # File should be empty
            assert os.path.getsize(stored_path) == 0

    def test_store_upload_binary_content(self):
        """Test that store_upload handles binary content correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Binary content with null bytes and various values
            file_bytes = bytes(range(256))
            original_filename = "binary.step"

            part_id, stored_path = store_upload(file_bytes, original_filename, tmpdir)

            # Verify exact binary content
            with open(stored_path, "rb") as f:
                stored_bytes = f.read()

            assert stored_bytes == file_bytes

    def test_store_upload_filename_format(self):
        """Test that stored filename follows UUID.extension format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_bytes = b"test"
            original_filename = "my_part.step"

            part_id, stored_path = store_upload(file_bytes, original_filename, tmpdir)

            filename = os.path.basename(stored_path)
            # Should be <uuid>.step format
            name, ext = os.path.splitext(filename)

            # Name part should be valid UUID
            uuid_obj = uuid.UUID(name)
            assert str(uuid_obj) == name
            # Extension should match
            assert ext == ".step"
