#!/usr/bin/env python3
"""
Helper script to add training data to the database.

Usage:
    python scripts/add_training_data.py path/to/part.step 10 450.00

This will:
1. Process the STEP file to extract features
2. Add it to training database with the real price you provide
"""

import sys
import os

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.db import connect, ensure_schema, insert_training_part
from modules.pipeline import process_quote


def main():
    if len(sys.argv) != 4:
        print("Usage: python add_training_data.py <step_file> <quantity> <real_price>")
        print("")
        print("Example:")
        print("  python add_training_data.py parts/bracket.step 10 450.00")
        print("")
        print("Arguments:")
        print("  step_file: Path to STEP file")
        print("  quantity: Number of units ordered")
        print("  real_price: Total price from real quote (EUR)")
        sys.exit(1)

    step_file = sys.argv[1]
    quantity = int(sys.argv[2])
    real_total_price = float(sys.argv[3])
    real_price_per_unit = real_total_price / quantity

    # Configuration
    DB_PATH = "training/training_data.db"
    PRICING_CONFIG = "config/pricing_coefficients.json"

    # Validate STEP file exists
    if not os.path.exists(step_file):
        print(f"✗ Error: STEP file not found: {step_file}")
        sys.exit(1)

    # Validate pricing config exists
    if not os.path.exists(PRICING_CONFIG):
        print(f"✗ Error: Pricing config not found: {PRICING_CONFIG}")
        print(f"  Run 'python -m training.train_model' to create it first")
        sys.exit(1)

    print(f"Adding training data...")
    print(f"  STEP file: {step_file}")
    print(f"  Quantity: {quantity}")
    print(f"  Total price: €{real_total_price:.2f}")
    print(f"  Price per unit: €{real_price_per_unit:.2f}")
    print("")

    # Connect to database
    conn = connect(DB_PATH)
    ensure_schema(conn)

    # Process the STEP file to extract features
    print("Extracting features from STEP file...")
    result = process_quote(step_file, quantity, PRICING_CONFIG)

    if result.errors:
        print(f"✗ Error processing STEP file:")
        for error in result.errors:
            print(f"  - {error}")
        conn.close()
        sys.exit(1)

    print("✓ Features extracted successfully")
    print("")
    print("Features:")
    print(f"  Bounding box: {result.features.bounding_box_x:.1f} × {result.features.bounding_box_y:.1f} × {result.features.bounding_box_z:.1f} mm")
    print(f"  Volume: {result.features.volume:.0f} mm³")
    print(f"  Through holes: {result.features.through_hole_count}")
    print(f"  Blind holes: {result.features.blind_hole_count}")
    print(f"  Pockets: {result.features.pocket_count}")
    print(f"  Non-standard features: {result.features.non_standard_hole_count}")
    print("")

    # Build training row from extracted features
    training_row = {
        "file_path": step_file,
        "quantity": quantity,
        "pcbway_price_eur": real_total_price,
        "price_per_unit": real_price_per_unit,

        # Bounding box
        "bounding_box_x": result.features.bounding_box_x,
        "bounding_box_y": result.features.bounding_box_y,
        "bounding_box_z": result.features.bounding_box_z,

        # Volume
        "volume": result.features.volume,

        # Holes
        "through_hole_count": result.features.through_hole_count,
        "blind_hole_count": result.features.blind_hole_count,
        "blind_hole_avg_depth_to_diameter": result.features.blind_hole_avg_depth_to_diameter,
        "blind_hole_max_depth_to_diameter": result.features.blind_hole_max_depth_to_diameter,

        # Pockets
        "pocket_count": result.features.pocket_count,
        "pocket_total_volume": result.features.pocket_total_volume,
        "pocket_avg_depth": result.features.pocket_avg_depth,
        "pocket_max_depth": result.features.pocket_max_depth,

        # Non-standard features
        "non_standard_hole_count": result.features.non_standard_hole_count,
    }

    # Insert into database
    insert_training_part(conn, training_row)
    print(f"✓ Added to training database: {DB_PATH}")

    # Show current count
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM training_parts")
    count = cursor.fetchone()[0]
    print(f"✓ Total training parts in database: {count}")

    conn.close()

    print("")
    print("Next steps:")
    print("  1. Add more training parts (recommended: 20+ total)")
    print("  2. Train the model: python -m training.train_model")
    print("  3. Test accuracy: python scripts/test_model.py")


if __name__ == '__main__':
    main()
