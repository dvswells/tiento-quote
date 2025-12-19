"""
Test suite for SQLite database module.
Following TDD - tests written first.
"""
import os
import tempfile
import pytest
import pandas as pd
from modules.db import (
    connect,
    ensure_schema,
    insert_training_part,
    fetch_training_parts,
)


@pytest.fixture
def temp_db():
    """Create a temporary database file for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    # Cleanup
    if os.path.exists(path):
        os.remove(path)


class TestConnect:
    """Test database connection."""

    def test_connect_creates_file(self, temp_db):
        """Test that connect creates database file."""
        conn = connect(temp_db)
        assert conn is not None
        assert os.path.exists(temp_db)
        conn.close()

    def test_connect_returns_connection(self, temp_db):
        """Test that connect returns a valid connection object."""
        conn = connect(temp_db)
        assert conn is not None
        # Should be able to execute queries
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1
        conn.close()

    def test_connect_to_existing_db(self, temp_db):
        """Test connecting to existing database."""
        # Create initial connection
        conn1 = connect(temp_db)
        conn1.close()

        # Connect again to existing file
        conn2 = connect(temp_db)
        assert conn2 is not None
        conn2.close()


class TestEnsureSchema:
    """Test schema creation."""

    def test_ensure_schema_creates_table(self, temp_db):
        """Test that ensure_schema creates training_parts table."""
        conn = connect(temp_db)
        ensure_schema(conn)

        # Check that table exists
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='training_parts'"
        )
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == "training_parts"
        conn.close()

    def test_ensure_schema_creates_correct_columns(self, temp_db):
        """Test that table has all required columns from spec."""
        conn = connect(temp_db)
        ensure_schema(conn)

        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(training_parts)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        # Required columns from spec
        expected_columns = [
            "id",
            "file_path",
            "upload_date",
            "quantity",
            "pcbway_price_eur",
            "price_per_unit",
            "bounding_box_x",
            "bounding_box_y",
            "bounding_box_z",
            "volume",
            "through_hole_count",
            "blind_hole_count",
            "blind_hole_avg_depth_to_diameter",
            "blind_hole_max_depth_to_diameter",
            "pocket_count",
            "pocket_total_volume",
            "pocket_avg_depth",
            "pocket_max_depth",
            "non_standard_hole_count",
        ]

        for col in expected_columns:
            assert col in column_names, f"Column {col} missing from schema"

        conn.close()

    def test_ensure_schema_idempotent(self, temp_db):
        """Test that calling ensure_schema multiple times is safe."""
        conn = connect(temp_db)
        ensure_schema(conn)
        ensure_schema(conn)  # Should not raise error
        ensure_schema(conn)  # Should not raise error

        # Table should still exist and be usable
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM training_parts")
        result = cursor.fetchone()
        assert result[0] == 0
        conn.close()


class TestInsertTrainingPart:
    """Test inserting training parts."""

    def test_insert_minimal_part(self, temp_db):
        """Test inserting a part with minimal required fields."""
        conn = connect(temp_db)
        ensure_schema(conn)

        part_data = {
            "file_path": "uploads/test-part.step",
            "quantity": 5,
            "pcbway_price_eur": 150.0,
            "price_per_unit": 30.0,
            "bounding_box_x": 100.0,
            "bounding_box_y": 80.0,
            "bounding_box_z": 30.0,
            "volume": 12500.0,
        }

        insert_training_part(conn, part_data)

        # Verify insertion
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM training_parts")
        count = cursor.fetchone()[0]
        assert count == 1

        cursor.execute("SELECT * FROM training_parts")
        row = cursor.fetchone()
        assert row is not None
        conn.close()

    def test_insert_part_with_all_features(self, temp_db):
        """Test inserting a part with all feature fields."""
        conn = connect(temp_db)
        ensure_schema(conn)

        part_data = {
            "file_path": "uploads/complex-part.step",
            "quantity": 10,
            "pcbway_price_eur": 500.0,
            "price_per_unit": 50.0,
            "bounding_box_x": 200.0,
            "bounding_box_y": 150.0,
            "bounding_box_z": 75.0,
            "volume": 50000.0,
            "through_hole_count": 8,
            "blind_hole_count": 4,
            "blind_hole_avg_depth_to_diameter": 3.5,
            "blind_hole_max_depth_to_diameter": 5.0,
            "pocket_count": 2,
            "pocket_total_volume": 1000.0,
            "pocket_avg_depth": 15.0,
            "pocket_max_depth": 20.0,
            "non_standard_hole_count": 2,
        }

        insert_training_part(conn, part_data)

        # Verify all data stored correctly
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM training_parts WHERE id = 1")
        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()
        row_dict = dict(zip(columns, row))

        assert row_dict["file_path"] == "uploads/complex-part.step"
        assert row_dict["quantity"] == 10
        assert row_dict["through_hole_count"] == 8
        assert row_dict["blind_hole_count"] == 4
        assert row_dict["pocket_count"] == 2
        assert row_dict["non_standard_hole_count"] == 2
        conn.close()

    def test_insert_multiple_parts(self, temp_db):
        """Test inserting multiple parts."""
        conn = connect(temp_db)
        ensure_schema(conn)

        part1 = {
            "file_path": "uploads/part1.step",
            "quantity": 1,
            "pcbway_price_eur": 30.0,
            "price_per_unit": 30.0,
            "bounding_box_x": 50.0,
            "bounding_box_y": 50.0,
            "bounding_box_z": 50.0,
            "volume": 1000.0,
        }

        part2 = {
            "file_path": "uploads/part2.step",
            "quantity": 5,
            "pcbway_price_eur": 200.0,
            "price_per_unit": 40.0,
            "bounding_box_x": 100.0,
            "bounding_box_y": 100.0,
            "bounding_box_z": 100.0,
            "volume": 10000.0,
        }

        insert_training_part(conn, part1)
        insert_training_part(conn, part2)

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM training_parts")
        count = cursor.fetchone()[0]
        assert count == 2
        conn.close()

    def test_insert_auto_increments_id(self, temp_db):
        """Test that ID auto-increments correctly."""
        conn = connect(temp_db)
        ensure_schema(conn)

        part_data = {
            "file_path": "uploads/test.step",
            "quantity": 1,
            "pcbway_price_eur": 30.0,
            "price_per_unit": 30.0,
            "bounding_box_x": 50.0,
            "bounding_box_y": 50.0,
            "bounding_box_z": 50.0,
            "volume": 1000.0,
        }

        insert_training_part(conn, part_data)
        insert_training_part(conn, part_data)
        insert_training_part(conn, part_data)

        cursor = conn.cursor()
        cursor.execute("SELECT id FROM training_parts ORDER BY id")
        ids = [row[0] for row in cursor.fetchall()]
        assert ids == [1, 2, 3]
        conn.close()


class TestFetchTrainingParts:
    """Test fetching training parts."""

    def test_fetch_empty_table(self, temp_db):
        """Test fetching from empty table returns empty DataFrame."""
        conn = connect(temp_db)
        ensure_schema(conn)

        df = fetch_training_parts(conn)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        conn.close()

    def test_fetch_returns_dataframe(self, temp_db):
        """Test that fetch returns pandas DataFrame."""
        conn = connect(temp_db)
        ensure_schema(conn)

        part_data = {
            "file_path": "uploads/test.step",
            "quantity": 1,
            "pcbway_price_eur": 30.0,
            "price_per_unit": 30.0,
            "bounding_box_x": 50.0,
            "bounding_box_y": 50.0,
            "bounding_box_z": 50.0,
            "volume": 1000.0,
        }
        insert_training_part(conn, part_data)

        df = fetch_training_parts(conn)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        conn.close()

    def test_fetch_has_expected_columns(self, temp_db):
        """Test that fetched DataFrame has all expected columns."""
        conn = connect(temp_db)
        ensure_schema(conn)

        part_data = {
            "file_path": "uploads/test.step",
            "quantity": 1,
            "pcbway_price_eur": 30.0,
            "price_per_unit": 30.0,
            "bounding_box_x": 50.0,
            "bounding_box_y": 50.0,
            "bounding_box_z": 50.0,
            "volume": 1000.0,
        }
        insert_training_part(conn, part_data)

        df = fetch_training_parts(conn)

        expected_columns = [
            "id",
            "file_path",
            "upload_date",
            "quantity",
            "pcbway_price_eur",
            "price_per_unit",
            "bounding_box_x",
            "bounding_box_y",
            "bounding_box_z",
            "volume",
            "through_hole_count",
            "blind_hole_count",
            "blind_hole_avg_depth_to_diameter",
            "blind_hole_max_depth_to_diameter",
            "pocket_count",
            "pocket_total_volume",
            "pocket_avg_depth",
            "pocket_max_depth",
            "non_standard_hole_count",
        ]

        for col in expected_columns:
            assert col in df.columns, f"Column {col} missing from DataFrame"

        conn.close()

    def test_fetch_returns_correct_data(self, temp_db):
        """Test that fetched data matches inserted data."""
        conn = connect(temp_db)
        ensure_schema(conn)

        part_data = {
            "file_path": "uploads/complex-part.step",
            "quantity": 10,
            "pcbway_price_eur": 500.0,
            "price_per_unit": 50.0,
            "bounding_box_x": 200.0,
            "bounding_box_y": 150.0,
            "bounding_box_z": 75.0,
            "volume": 50000.0,
            "through_hole_count": 8,
            "blind_hole_count": 4,
            "pocket_count": 2,
            "non_standard_hole_count": 2,
        }
        insert_training_part(conn, part_data)

        df = fetch_training_parts(conn)

        assert df.iloc[0]["file_path"] == "uploads/complex-part.step"
        assert df.iloc[0]["quantity"] == 10
        assert df.iloc[0]["through_hole_count"] == 8
        assert df.iloc[0]["blind_hole_count"] == 4
        assert df.iloc[0]["pocket_count"] == 2
        conn.close()

    def test_fetch_multiple_rows(self, temp_db):
        """Test fetching multiple training parts."""
        conn = connect(temp_db)
        ensure_schema(conn)

        for i in range(5):
            part_data = {
                "file_path": f"uploads/part{i}.step",
                "quantity": i + 1,
                "pcbway_price_eur": (i + 1) * 30.0,
                "price_per_unit": 30.0,
                "bounding_box_x": 50.0,
                "bounding_box_y": 50.0,
                "bounding_box_z": 50.0,
                "volume": 1000.0,
            }
            insert_training_part(conn, part_data)

        df = fetch_training_parts(conn)

        assert len(df) == 5
        assert df.iloc[0]["quantity"] == 1
        assert df.iloc[4]["quantity"] == 5
        conn.close()


class TestIntegration:
    """Integration tests for database module."""

    def test_full_workflow(self, temp_db):
        """Test complete workflow: connect, create schema, insert, fetch."""
        # Connect
        conn = connect(temp_db)
        assert conn is not None

        # Create schema
        ensure_schema(conn)

        # Insert multiple parts
        parts = [
            {
                "file_path": f"uploads/part{i}.step",
                "quantity": i + 1,
                "pcbway_price_eur": (i + 1) * 40.0,
                "price_per_unit": 40.0,
                "bounding_box_x": 100.0,
                "bounding_box_y": 100.0,
                "bounding_box_z": 100.0,
                "volume": 10000.0,
                "through_hole_count": i * 2,
            }
            for i in range(3)
        ]

        for part in parts:
            insert_training_part(conn, part)

        # Fetch and verify
        df = fetch_training_parts(conn)
        assert len(df) == 3
        assert df.iloc[0]["through_hole_count"] == 0
        assert df.iloc[1]["through_hole_count"] == 2
        assert df.iloc[2]["through_hole_count"] == 4

        conn.close()
