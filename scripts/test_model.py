#!/usr/bin/env python3
"""
Test model accuracy by comparing predictions vs actual prices.

Usage:
    python scripts/test_model.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.pipeline import process_quote
from modules.db import connect, fetch_training_parts


def main():
    PRICING_CONFIG = "config/pricing_coefficients.json"
    DB_PATH = "training/training_data.db"

    # Validate files exist
    if not os.path.exists(DB_PATH):
        print(f"✗ Error: Training database not found: {DB_PATH}")
        print("  Add training data first using: python scripts/add_training_data.py")
        sys.exit(1)

    if not os.path.exists(PRICING_CONFIG):
        print(f"✗ Error: Pricing config not found: {PRICING_CONFIG}")
        print("  Train the model first using: python -m training.train_model")
        sys.exit(1)

    # Get training data
    print("Loading training data...")
    conn = connect(DB_PATH)
    df = fetch_training_parts(conn)
    conn.close()

    if len(df) == 0:
        print("✗ No training data found in database")
        sys.exit(1)

    print(f"✓ Loaded {len(df)} training parts")
    print("")
    print("Testing model predictions vs actual prices:")
    print("")
    print(f"{'Part':<40} {'Actual':>10} {'Predicted':>10} {'Error':>10} {'Error %':>10}")
    print("-" * 90)

    errors = []
    skipped = 0

    for idx, row in df.iterrows():
        # Get prediction
        result = process_quote(row['file_path'], int(row['quantity']), PRICING_CONFIG)

        if result.errors:
            print(f"{row['file_path']:<40} {'SKIPPED':<10} (processing error)")
            skipped += 1
            continue

        actual = row['price_per_unit']
        predicted = result.quote.price_per_unit if result.quote else 0
        error = predicted - actual
        error_pct = (error / actual) * 100 if actual > 0 else 0

        errors.append(abs(error_pct))

        # Color code errors
        error_indicator = ""
        if abs(error_pct) > 20:
            error_indicator = " ⚠️ HIGH"
        elif abs(error_pct) > 10:
            error_indicator = " ⚠️"

        part_name = os.path.basename(row['file_path'])
        print(f"{part_name:<40} €{actual:>8.2f} €{predicted:>8.2f} €{error:>8.2f} {error_pct:>8.1f}%{error_indicator}")

    print("-" * 90)

    if len(errors) > 0:
        avg_error = sum(errors) / len(errors)
        max_error = max(errors)
        min_error = min(errors)

        print(f"Average absolute error: {avg_error:.1f}%")
        print(f"Max error: {max_error:.1f}%")
        print(f"Min error: {min_error:.1f}%")
        print(f"Parts tested: {len(errors)}")
        if skipped > 0:
            print(f"Parts skipped: {skipped}")
        print("")

        # Interpretation
        if avg_error < 5:
            print("✓ Excellent accuracy! Model is production-ready.")
        elif avg_error < 10:
            print("✓ Good accuracy. Model is suitable for production use.")
        elif avg_error < 15:
            print("⚠️ Acceptable accuracy. Consider adding more training data.")
        elif avg_error < 25:
            print("⚠️ Poor accuracy. Add more diverse training data.")
        else:
            print("✗ Very poor accuracy. Check training data quality and add more samples.")

        # High error warnings
        high_errors = [e for e in errors if e > 20]
        if len(high_errors) > 0:
            print(f"\n⚠️ {len(high_errors)} parts have >20% error - investigate these cases")

    else:
        print("✗ No parts could be tested successfully")


if __name__ == '__main__':
    main()
