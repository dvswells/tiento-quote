"""
SQLite database module for Tiento Quote v0.1.

Handles training data storage and retrieval.
Schema matches specification in spec.md section 3.
"""
import sqlite3
from typing import Dict, Any
import pandas as pd


def connect(db_path: str) -> sqlite3.Connection:
    """
    Connect to SQLite database.

    Creates the database file if it doesn't exist.

    Args:
        db_path: Path to SQLite database file

    Returns:
        SQLite connection object
    """
    conn = sqlite3.connect(db_path)
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    """
    Create training_parts table if it doesn't exist.

    Table schema matches specification from spec.md section 3.1.
    Safe to call multiple times (idempotent).

    Args:
        conn: SQLite connection object
    """
    cursor = conn.cursor()

    # Create training_parts table per spec
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS training_parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            -- User inputs
            quantity INTEGER NOT NULL,

            -- PCBWay pricing
            pcbway_price_eur REAL NOT NULL,
            price_per_unit REAL NOT NULL,

            -- Bounding box
            bounding_box_x REAL NOT NULL,
            bounding_box_y REAL NOT NULL,
            bounding_box_z REAL NOT NULL,

            -- Volume
            volume REAL NOT NULL,

            -- Through holes
            through_hole_count INTEGER DEFAULT 0,

            -- Blind holes
            blind_hole_count INTEGER DEFAULT 0,
            blind_hole_avg_depth_to_diameter REAL DEFAULT 0,
            blind_hole_max_depth_to_diameter REAL DEFAULT 0,

            -- Pockets
            pocket_count INTEGER DEFAULT 0,
            pocket_total_volume REAL DEFAULT 0,
            pocket_avg_depth REAL DEFAULT 0,
            pocket_max_depth REAL DEFAULT 0,

            -- Non-standard features
            non_standard_hole_count INTEGER DEFAULT 0
        )
    """)

    conn.commit()


def insert_training_part(conn: sqlite3.Connection, row_dict: Dict[str, Any]) -> None:
    """
    Insert a training part into the database.

    Required fields in row_dict:
    - file_path, quantity, pcbway_price_eur, price_per_unit
    - bounding_box_x, bounding_box_y, bounding_box_z
    - volume

    Optional fields (default to 0):
    - through_hole_count, blind_hole_count
    - blind_hole_avg_depth_to_diameter, blind_hole_max_depth_to_diameter
    - pocket_count, pocket_total_volume, pocket_avg_depth, pocket_max_depth
    - non_standard_hole_count

    Args:
        conn: SQLite connection object
        row_dict: Dictionary containing part data
    """
    cursor = conn.cursor()

    # Build column list and values from row_dict
    columns = []
    values = []
    placeholders = []

    for key, value in row_dict.items():
        columns.append(key)
        values.append(value)
        placeholders.append("?")

    columns_str = ", ".join(columns)
    placeholders_str = ", ".join(placeholders)

    query = f"INSERT INTO training_parts ({columns_str}) VALUES ({placeholders_str})"
    cursor.execute(query, values)

    conn.commit()


def fetch_training_parts(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Fetch all training parts from database as pandas DataFrame.

    Returns DataFrame with all columns from training_parts table.
    Returns empty DataFrame if table is empty.

    Args:
        conn: SQLite connection object

    Returns:
        pandas DataFrame with all training parts
    """
    query = "SELECT * FROM training_parts"
    df = pd.read_sql_query(query, conn)
    return df
