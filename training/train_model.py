"""
Training Module

Trains pricing model from training_parts database and outputs pricing_coefficients.json.
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any

import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

from modules.pricing_config import REQUIRED_COEFFICIENT_FEATURES


class InsufficientTrainingDataError(Exception):
    """Raised when there is insufficient training data."""
    pass


def train_model(db_path: str, output_path: str) -> None:
    """
    Train pricing model from database and save to JSON config file.

    Reads training_parts table, trains StandardScaler + LinearRegression,
    and writes pricing_coefficients.json with all required fields.

    Args:
        db_path: Path to SQLite database with training_parts table
        output_path: Path to write pricing_coefficients.json

    Raises:
        InsufficientTrainingDataError: If database has < 2 rows
        sqlite3.Error: If database connection fails
        IOError: If output file cannot be written
    """
    # Connect to database and read training data
    conn = sqlite3.connect(db_path)

    try:
        # Read all training data into pandas DataFrame
        df = pd.read_sql_query("SELECT * FROM training_parts", conn)
    finally:
        conn.close()

    # Validate sufficient data
    if len(df) == 0:
        raise InsufficientTrainingDataError(
            "No training data found in database. At least 2 rows required for training."
        )

    if len(df) < 2:
        raise InsufficientTrainingDataError(
            f"Insufficient training data: {len(df)} rows found, at least 2 required for training."
        )

    # Extract features (X) and target (y)
    X = df[REQUIRED_COEFFICIENT_FEATURES].values
    y = df['price_per_unit'].values

    # Train StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train LinearRegression
    model = LinearRegression()
    model.fit(X_scaled, y)

    # Calculate R² score
    y_pred = model.predict(X_scaled)
    r_squared = r2_score(y, y_pred)

    # Build output configuration
    config = {
        "base_price": float(model.intercept_),
        "minimum_order_price": 30.0,  # Per spec
        "r_squared": float(r_squared),
        "coefficients": {
            feature: float(coef)
            for feature, coef in zip(REQUIRED_COEFFICIENT_FEATURES, model.coef_)
        },
        "scaler_mean": {
            feature: float(mean)
            for feature, mean in zip(REQUIRED_COEFFICIENT_FEATURES, scaler.mean_)
        },
        "scaler_std": {
            feature: float(std)
            for feature, std in zip(REQUIRED_COEFFICIENT_FEATURES, scaler.scale_)
        },
        "last_updated": datetime.utcnow().isoformat() + 'Z'
    }

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Write configuration to JSON file
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)


def main():
    """
    Main entry point for training script.

    Usage:
        python -m training.train_model
    """
    import argparse

    parser = argparse.ArgumentParser(description='Train pricing model from database')
    parser.add_argument(
        '--db',
        default='data/training_parts.db',
        help='Path to SQLite database (default: data/training_parts.db)'
    )
    parser.add_argument(
        '--output',
        default='config/pricing_coefficients.json',
        help='Path to output JSON file (default: config/pricing_coefficients.json)'
    )

    args = parser.parse_args()

    print(f"Training pricing model...")
    print(f"  Database: {args.db}")
    print(f"  Output: {args.output}")

    try:
        train_model(args.db, args.output)
        print(f"✓ Training complete!")

        # Load and display results
        with open(args.output, 'r') as f:
            config = json.load(f)

        print(f"  R² score: {config['r_squared']:.4f}")
        print(f"  Base price: €{config['base_price']:.2f}")
        print(f"  Minimum order: €{config['minimum_order_price']:.2f}")
        print(f"  Last updated: {config['last_updated']}")

    except InsufficientTrainingDataError as e:
        print(f"✗ Error: {e}")
        exit(1)
    except Exception as e:
        print(f"✗ Training failed: {e}")
        exit(1)


if __name__ == '__main__':
    main()
