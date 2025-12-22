#!/usr/bin/env python3
"""
View all training data in the database.

Usage:
    python scripts/view_training_data.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.db import connect, fetch_training_parts


def main():
    DB_PATH = "training/training_data.db"

    if not os.path.exists(DB_PATH):
        print(f"✗ Error: Training database not found: {DB_PATH}")
        print("  Add training data first using: python scripts/add_training_data.py")
        sys.exit(1)

    # Get training data
    conn = connect(DB_PATH)
    df = fetch_training_parts(conn)
    conn.close()

    if len(df) == 0:
        print("Database is empty. Add training data using:")
        print("  python scripts/add_training_data.py <step_file> <quantity> <price>")
        sys.exit(0)

    print(f"Training Database: {DB_PATH}")
    print(f"Total parts: {len(df)}")
    print("")

    # Summary statistics
    print("Summary Statistics:")
    print(f"  Price per unit range: €{df['price_per_unit'].min():.2f} - €{df['price_per_unit'].max():.2f}")
    print(f"  Average price per unit: €{df['price_per_unit'].mean():.2f}")
    print(f"  Quantity range: {df['quantity'].min()} - {df['quantity'].max()} units")
    print(f"  Volume range: {df['volume'].min():.0f} - {df['volume'].max():.0f} mm³")
    print("")

    # Feature statistics
    print("Feature Distribution:")
    print(f"  Parts with through holes: {(df['through_hole_count'] > 0).sum()} ({(df['through_hole_count'] > 0).sum() / len(df) * 100:.0f}%)")
    print(f"  Parts with blind holes: {(df['blind_hole_count'] > 0).sum()} ({(df['blind_hole_count'] > 0).sum() / len(df) * 100:.0f}%)")
    print(f"  Parts with pockets: {(df['pocket_count'] > 0).sum()} ({(df['pocket_count'] > 0).sum() / len(df) * 100:.0f}%)")
    print(f"  Parts with non-standard features: {(df['non_standard_hole_count'] > 0).sum()}")
    print("")

    # List all parts
    print("All Training Parts:")
    print("")
    print(f"{'ID':<5} {'File':<40} {'Qty':>5} {'Price/Unit':>12} {'Volume':>12} {'Holes':>8} {'Pockets':>8}")
    print("-" * 100)

    for idx, row in df.iterrows():
        part_name = os.path.basename(row['file_path'])
        holes = row['through_hole_count'] + row['blind_hole_count']
        print(f"{row['id']:<5} {part_name:<40} {row['quantity']:>5} €{row['price_per_unit']:>10.2f} {row['volume']:>11.0f} {holes:>8} {row['pocket_count']:>8}")

    print("-" * 100)
    print("")
    print("Next steps:")
    if len(df) < 20:
        print(f"  ⚠️ Only {len(df)} training parts. Recommended: 20+ for good accuracy")
        print(f"  Add more: python scripts/add_training_data.py <step_file> <quantity> <price>")
    else:
        print(f"  ✓ Good amount of training data ({len(df)} parts)")
        print(f"  Train model: python -m training.train_model")
        print(f"  Test accuracy: python scripts/test_model.py")


if __name__ == '__main__':
    main()
