"""
Tests for Training Module

Tests the ML training pipeline that generates pricing_coefficients.json.
Following TDD - tests written before implementation.
"""

import pytest
import os
import json
import tempfile
import sqlite3
from datetime import datetime

from modules.db import connect, ensure_schema, insert_training_part
from modules.pricing_config import REQUIRED_COEFFICIENT_FEATURES


class TestTrainModel:
    """Test basic training functionality."""

    @pytest.fixture
    def temp_db_with_data(self, tmp_path):
        """Create a temp database with synthetic training data."""
        db_path = os.path.join(tmp_path, "test_training.db")
        conn = connect(db_path)
        ensure_schema(conn)

        # Insert synthetic training data with realistic patterns
        # Price roughly correlates with volume and features
        training_data = [
            {
                "file_path": "/path/to/part1.step",
                "quantity": 1,
                "pcbway_price_eur": 50.0,
                "price_per_unit": 50.0,
                "bounding_box_x": 100.0,
                "bounding_box_y": 50.0,
                "bounding_box_z": 25.0,
                "volume": 125000.0,
                "through_hole_count": 2,
                "blind_hole_count": 1,
                "blind_hole_avg_depth_to_diameter": 3.0,
                "blind_hole_max_depth_to_diameter": 3.0,
                "pocket_count": 0,
                "pocket_total_volume": 0.0,
                "pocket_avg_depth": 0.0,
                "pocket_max_depth": 0.0,
                "non_standard_hole_count": 0,
            },
            {
                "file_path": "/path/to/part2.step",
                "quantity": 1,
                "pcbway_price_eur": 75.0,
                "price_per_unit": 75.0,
                "bounding_box_x": 150.0,
                "bounding_box_y": 75.0,
                "bounding_box_z": 30.0,
                "volume": 337500.0,
                "through_hole_count": 4,
                "blind_hole_count": 2,
                "blind_hole_avg_depth_to_diameter": 4.0,
                "blind_hole_max_depth_to_diameter": 5.0,
                "pocket_count": 1,
                "pocket_total_volume": 5000.0,
                "pocket_avg_depth": 5.0,
                "pocket_max_depth": 5.0,
                "non_standard_hole_count": 1,
            },
            {
                "file_path": "/path/to/part3.step",
                "quantity": 1,
                "pcbway_price_eur": 100.0,
                "price_per_unit": 100.0,
                "bounding_box_x": 200.0,
                "bounding_box_y": 100.0,
                "bounding_box_z": 40.0,
                "volume": 800000.0,
                "through_hole_count": 6,
                "blind_hole_count": 3,
                "blind_hole_avg_depth_to_diameter": 5.0,
                "blind_hole_max_depth_to_diameter": 7.0,
                "pocket_count": 2,
                "pocket_total_volume": 10000.0,
                "pocket_avg_depth": 6.0,
                "pocket_max_depth": 8.0,
                "non_standard_hole_count": 2,
            },
            {
                "file_path": "/path/to/part4.step",
                "quantity": 1,
                "pcbway_price_eur": 35.0,
                "price_per_unit": 35.0,
                "bounding_box_x": 50.0,
                "bounding_box_y": 30.0,
                "bounding_box_z": 20.0,
                "volume": 30000.0,
                "through_hole_count": 1,
                "blind_hole_count": 0,
                "blind_hole_avg_depth_to_diameter": 0.0,
                "blind_hole_max_depth_to_diameter": 0.0,
                "pocket_count": 0,
                "pocket_total_volume": 0.0,
                "pocket_avg_depth": 0.0,
                "pocket_max_depth": 0.0,
                "non_standard_hole_count": 0,
            },
            {
                "file_path": "/path/to/part5.step",
                "quantity": 1,
                "pcbway_price_eur": 120.0,
                "price_per_unit": 120.0,
                "bounding_box_x": 250.0,
                "bounding_box_y": 120.0,
                "bounding_box_z": 50.0,
                "volume": 1500000.0,
                "through_hole_count": 8,
                "blind_hole_count": 4,
                "blind_hole_avg_depth_to_diameter": 6.0,
                "blind_hole_max_depth_to_diameter": 8.0,
                "pocket_count": 3,
                "pocket_total_volume": 15000.0,
                "pocket_avg_depth": 7.0,
                "pocket_max_depth": 10.0,
                "non_standard_hole_count": 3,
            },
        ]

        for row in training_data:
            insert_training_part(conn, row)

        conn.close()
        return db_path

    def test_train_model_function_exists(self):
        """Training module should have train_model function."""
        from training.train_model import train_model
        assert callable(train_model)

    def test_train_model_creates_output_file(self, temp_db_with_data, tmp_path):
        """train_model should create pricing_coefficients.json."""
        from training.train_model import train_model

        output_path = os.path.join(tmp_path, "pricing_coefficients.json")

        train_model(temp_db_with_data, output_path)

        assert os.path.exists(output_path)

    def test_output_is_valid_json(self, temp_db_with_data, tmp_path):
        """Output file should be valid JSON."""
        from training.train_model import train_model

        output_path = os.path.join(tmp_path, "pricing_coefficients.json")
        train_model(temp_db_with_data, output_path)

        with open(output_path, 'r') as f:
            config = json.load(f)

        assert isinstance(config, dict)

    def test_output_has_base_price(self, temp_db_with_data, tmp_path):
        """Output should have base_price field."""
        from training.train_model import train_model

        output_path = os.path.join(tmp_path, "pricing_coefficients.json")
        train_model(temp_db_with_data, output_path)

        with open(output_path, 'r') as f:
            config = json.load(f)

        assert "base_price" in config
        assert isinstance(config["base_price"], (int, float))

    def test_output_has_minimum_order_price(self, temp_db_with_data, tmp_path):
        """Output should have minimum_order_price field."""
        from training.train_model import train_model

        output_path = os.path.join(tmp_path, "pricing_coefficients.json")
        train_model(temp_db_with_data, output_path)

        with open(output_path, 'r') as f:
            config = json.load(f)

        assert "minimum_order_price" in config
        assert isinstance(config["minimum_order_price"], (int, float))

    def test_output_has_r_squared(self, temp_db_with_data, tmp_path):
        """Output should have r_squared field."""
        from training.train_model import train_model

        output_path = os.path.join(tmp_path, "pricing_coefficients.json")
        train_model(temp_db_with_data, output_path)

        with open(output_path, 'r') as f:
            config = json.load(f)

        assert "r_squared" in config
        assert isinstance(config["r_squared"], (int, float))

    def test_r_squared_is_positive_with_synthetic_data(self, temp_db_with_data, tmp_path):
        """R² should be > 0 with correlated synthetic data."""
        from training.train_model import train_model

        output_path = os.path.join(tmp_path, "pricing_coefficients.json")
        train_model(temp_db_with_data, output_path)

        with open(output_path, 'r') as f:
            config = json.load(f)

        assert config["r_squared"] > 0, "R² should be positive with correlated training data"

    def test_output_has_coefficients_dict(self, temp_db_with_data, tmp_path):
        """Output should have coefficients dictionary."""
        from training.train_model import train_model

        output_path = os.path.join(tmp_path, "pricing_coefficients.json")
        train_model(temp_db_with_data, output_path)

        with open(output_path, 'r') as f:
            config = json.load(f)

        assert "coefficients" in config
        assert isinstance(config["coefficients"], dict)

    def test_coefficients_includes_all_required_features(self, temp_db_with_data, tmp_path):
        """Coefficients should include all required features."""
        from training.train_model import train_model

        output_path = os.path.join(tmp_path, "pricing_coefficients.json")
        train_model(temp_db_with_data, output_path)

        with open(output_path, 'r') as f:
            config = json.load(f)

        coefficients = config["coefficients"]

        for feature in REQUIRED_COEFFICIENT_FEATURES:
            assert feature in coefficients, f"Missing coefficient for {feature}"

    def test_output_has_scaler_mean(self, temp_db_with_data, tmp_path):
        """Output should have scaler_mean dictionary."""
        from training.train_model import train_model

        output_path = os.path.join(tmp_path, "pricing_coefficients.json")
        train_model(temp_db_with_data, output_path)

        with open(output_path, 'r') as f:
            config = json.load(f)

        assert "scaler_mean" in config
        assert isinstance(config["scaler_mean"], dict)

    def test_output_has_scaler_std(self, temp_db_with_data, tmp_path):
        """Output should have scaler_std dictionary."""
        from training.train_model import train_model

        output_path = os.path.join(tmp_path, "pricing_coefficients.json")
        train_model(temp_db_with_data, output_path)

        with open(output_path, 'r') as f:
            config = json.load(f)

        assert "scaler_std" in config
        assert isinstance(config["scaler_std"], dict)

    def test_scaler_mean_includes_all_required_features(self, temp_db_with_data, tmp_path):
        """Scaler mean should include all required features."""
        from training.train_model import train_model

        output_path = os.path.join(tmp_path, "pricing_coefficients.json")
        train_model(temp_db_with_data, output_path)

        with open(output_path, 'r') as f:
            config = json.load(f)

        scaler_mean = config["scaler_mean"]

        for feature in REQUIRED_COEFFICIENT_FEATURES:
            assert feature in scaler_mean, f"Missing scaler_mean for {feature}"

    def test_scaler_std_includes_all_required_features(self, temp_db_with_data, tmp_path):
        """Scaler std should include all required features."""
        from training.train_model import train_model

        output_path = os.path.join(tmp_path, "pricing_coefficients.json")
        train_model(temp_db_with_data, output_path)

        with open(output_path, 'r') as f:
            config = json.load(f)

        scaler_std = config["scaler_std"]

        for feature in REQUIRED_COEFFICIENT_FEATURES:
            assert feature in scaler_std, f"Missing scaler_std for {feature}"

    def test_output_has_last_updated(self, temp_db_with_data, tmp_path):
        """Output should have last_updated timestamp."""
        from training.train_model import train_model

        output_path = os.path.join(tmp_path, "pricing_coefficients.json")
        train_model(temp_db_with_data, output_path)

        with open(output_path, 'r') as f:
            config = json.load(f)

        assert "last_updated" in config
        assert isinstance(config["last_updated"], str)

        # Verify it's a valid ISO timestamp
        datetime.fromisoformat(config["last_updated"].replace('Z', '+00:00'))

    def test_creates_output_directory_if_missing(self, temp_db_with_data, tmp_path):
        """train_model should create output directory if it doesn't exist."""
        from training.train_model import train_model

        nested_path = os.path.join(tmp_path, "nested", "dir", "pricing_coefficients.json")

        train_model(temp_db_with_data, nested_path)

        assert os.path.exists(nested_path)

    def test_minimum_order_price_set_to_30_eur(self, temp_db_with_data, tmp_path):
        """Minimum order price should be set to 30 EUR per spec."""
        from training.train_model import train_model

        output_path = os.path.join(tmp_path, "pricing_coefficients.json")
        train_model(temp_db_with_data, output_path)

        with open(output_path, 'r') as f:
            config = json.load(f)

        assert config["minimum_order_price"] == 30.0


class TestTrainModelErrors:
    """Test error handling in training."""

    def test_empty_database_raises_error(self, tmp_path):
        """Training with empty database should raise appropriate error."""
        from training.train_model import train_model

        # Create empty database
        db_path = os.path.join(tmp_path, "empty.db")
        conn = connect(db_path)
        ensure_schema(conn)
        conn.close()

        output_path = os.path.join(tmp_path, "pricing_coefficients.json")

        with pytest.raises(Exception):  # Should raise some kind of error
            train_model(db_path, output_path)

    def test_insufficient_data_raises_error(self, tmp_path):
        """Training with only 1 row should raise error."""
        from training.train_model import train_model

        # Create database with single row
        db_path = os.path.join(tmp_path, "insufficient.db")
        conn = connect(db_path)
        ensure_schema(conn)

        insert_training_part(conn, {
            "file_path": "/path/to/part.step",
            "quantity": 1,
            "pcbway_price_eur": 50.0,
            "price_per_unit": 50.0,
            "bounding_box_x": 100.0,
            "bounding_box_y": 50.0,
            "bounding_box_z": 25.0,
            "volume": 125000.0,
        })
        conn.close()

        output_path = os.path.join(tmp_path, "pricing_coefficients.json")

        with pytest.raises(Exception):  # Should raise error for insufficient data
            train_model(db_path, output_path)


class TestOutputCompatibility:
    """Test that output is compatible with pricing_config loader."""

    def test_output_can_be_loaded_by_pricing_config(self, tmp_path):
        """Generated config should be loadable by load_pricing_config."""
        from training.train_model import train_model
        from modules.pricing_config import load_pricing_config

        # Create temp database with data
        db_path = os.path.join(tmp_path, "test.db")
        conn = connect(db_path)
        ensure_schema(conn)

        for i in range(5):
            insert_training_part(conn, {
                "file_path": f"/path/to/part{i}.step",
                "quantity": 1,
                "pcbway_price_eur": 50.0 + i * 10,
                "price_per_unit": 50.0 + i * 10,
                "bounding_box_x": 100.0 + i * 20,
                "bounding_box_y": 50.0 + i * 10,
                "bounding_box_z": 25.0 + i * 5,
                "volume": 125000.0 + i * 50000,
                "through_hole_count": i,
                "blind_hole_count": i // 2,
                "pocket_count": i // 3,
            })

        conn.close()

        output_path = os.path.join(tmp_path, "pricing_coefficients.json")
        train_model(db_path, output_path)

        # Should load without error
        config = load_pricing_config(output_path)

        assert config is not None
        assert "base_price" in config
        assert "coefficients" in config
