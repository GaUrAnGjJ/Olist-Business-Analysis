import sqlite3
import logging
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("load_database")

# Path Configuration
DEFAULT_DB_PATH = Path("data/olist_ecommerce.db")
RAW_PATH = Path("data/raw")
PROCESSED_PATH = Path("data/processed/cleaning")

# Datetime columns that need standardised formatting before insert
DATETIME_COLUMNS = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ],
    "order_items": ["shipping_limit_date"],
    "reviews": ["review_creation_date", "review_answer_timestamp"]
}

# Deletion order: child tables first (respects FK constraints)
DELETE_ORDER = [
    "reviews",
    "payments",
    "order_items",
    "orders",
    "products",
    "customers",
    "category_translation"
]

# Loading order: parent tables first (respects FK constraints)
LOAD_ORDER = [
    "category_translation",
    "customers",
    "products",
    "orders",
    "order_items",
    "payments",
    "reviews"
]

# Cleaned CSV file mapping
CLEANED_CSV_FILES = {
    "category_translation": RAW_PATH / "product_category_name_translation.csv",
    "customers":   PROCESSED_PATH / "olist_customers_cleaned.csv",
    "products":    PROCESSED_PATH / "olist_products_cleaned.csv",
    "orders":      PROCESSED_PATH / "olist_orders_cleaned.csv",
    "order_items": PROCESSED_PATH / "olist_order_items_cleaned.csv",
    "payments":    PROCESSED_PATH / "olist_order_payments_cleaned.csv",
    "reviews":     PROCESSED_PATH / "olist_order_reviews_cleaned.csv"
}


def load_csv(table_name):
    """Load cleaned CSV for given table name into a DataFrame."""
    csv_path = CLEANED_CSV_FILES[table_name]
    logger.info(f"  Loading CSV: {csv_path.name}")
    df = pd.read_csv(csv_path, dtype=str)  # Load all as str to preserve fidelity

    # Re-cast numeric columns after string load
    numeric_casts = {
        "order_items": {
            "order_item_id": int,
            "price": float,
            "freight_value": float
        },
        "payments": {
            "payment_sequential": int,
            "payment_installments": int,
            "payment_value": float
        },
        "reviews": {
            "review_score": int
        },
        "products": {
            "product_name_lenght": float,
            "product_description_lenght": float,
            "product_photos_qty": float,
            "product_weight_g": float,
            "product_length_cm": float,
            "product_height_cm": float,
            "product_width_cm": float
        }
    }

    if table_name in numeric_casts:
        for col, dtype in numeric_casts[table_name].items():
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").astype(dtype)

    # Standardise datetime columns to YYYY-MM-DD HH:MM:SS
    if table_name in DATETIME_COLUMNS:
        for col in DATETIME_COLUMNS[table_name]:
            if col in df.columns:
                parsed = pd.to_datetime(df[col], format="mixed", errors="coerce")
                df[col] = parsed.dt.strftime("%Y-%m-%d %H:%M:%S")

    # Replace NaN with None for SQLite NULL compatibility
    df = df.where(pd.notnull(df), None)

    return df


def clear_all_tables(cursor):
    """
    Clears all rows from all tables in child → parent order to respect
    foreign key constraints. Runs PRAGMA foreign_keys OFF only during
    deletion, then re-enables.
    """
    logger.info("Clearing existing data (child -> parent order)...")
    cursor.execute("PRAGMA foreign_keys = OFF;")
    for table in DELETE_ORDER:
        cursor.execute(f"DELETE FROM {table};")
        logger.info(f"  Cleared table: {table}")
    cursor.execute("PRAGMA foreign_keys = ON;")
    logger.info("Foreign key enforcement re-enabled.")


def get_db_row_count(cursor, table_name):
    """Return the current row count of a table from the SQLite database."""
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    return cursor.fetchone()[0]


def verify_row_counts(cursor, loaded_counts):
    """
    Verify that the number of rows loaded into each table matches the
    row count of the source cleaned CSV.
    """
    logger.info("\n" + "=" * 70)
    logger.info("ROW COUNT VERIFICATION (CSV vs SQLite Database)")
    logger.info("=" * 70)

    all_passed = True
    for table_name, csv_count in loaded_counts.items():
        db_count = get_db_row_count(cursor, table_name)
        status = "PASS" if csv_count == db_count else "FAIL"
        if status == "FAIL":
            all_passed = False
        logger.info(
            f"  {table_name:<25} | CSV rows: {csv_count:>7,} | "
            f"DB rows: {db_count:>7,} | {status}"
        )

    logger.info("=" * 70)
    if all_passed:
        logger.info("[SUCCESS] All row counts match. Database load verified.")
    else:
        logger.warning("[WARNING] Row count mismatch detected. Review errors above.")

    return all_passed


def load_database(db_path=DEFAULT_DB_PATH):
    """
    Main pipeline for loading cleaned CSV data into the SQLite database.

    Execution order:
    1. Enable foreign keys
    2. Clear existing data in child -> parent order
    3. Load cleaned CSV data in parent -> child order
    4. Commit only if all loads succeed
    5. Verify row counts
    """
    logger.info("=" * 70)
    logger.info("STARTING OLIST DATABASE LOAD PIPELINE")
    logger.info("=" * 70)

    if not db_path.exists():
        raise FileNotFoundError(
            f"Database not found at: {db_path.resolve()}. "
            "Please run create_database.py first."
        )

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Step 1: Enable foreign key enforcement
        cursor.execute("PRAGMA foreign_keys = ON;")
        logger.info("Foreign key enforcement enabled (PRAGMA foreign_keys = ON).")

        # Step 2: Clear existing data (child -> parent order for FK safety)
        clear_all_tables(cursor)

        # Step 3: Load CSV data (parent -> child order)
        logger.info("\nLoading cleaned CSVs into SQLite (parent -> child order)...")
        loaded_counts = {}

        for table_name in LOAD_ORDER:
            logger.info(f"\n[Table: {table_name}]")
            df = load_csv(table_name)

            # SQLite has a hard limit of 999 bound variables per statement.
            # Safe chunksize = floor(999 / number_of_columns)
            safe_chunksize = max(1, 999 // len(df.columns))

            df.to_sql(
                name=table_name,
                con=conn,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=safe_chunksize
            )


            loaded_counts[table_name] = len(df)
            logger.info(f"  Inserted {len(df):,} rows into '{table_name}'.")

        # Step 3b: Insert supplemental category_translation rows for known
        #  categories present in products but absent from the raw translation CSV.
        #  These were handled by data_cleaning.py in memory but were never written
        #  back into the translation source file, causing FK orphans in the DB.
        supplemental_categories = [
            ("unknown",                                     "unknown"),
            ("pc_gamer",                                    "pc gamer"),
            ("portateis_cozinha_e_preparadores_de_alimentos",
             "portable kitchen food preparers"),
        ]
        logger.info("\n[Supplemental] Inserting missing category_translation rows...")
        cursor.executemany(
            "INSERT OR IGNORE INTO category_translation "
            "(product_category_name, product_category_name_english) VALUES (?, ?);",
            supplemental_categories
        )
        inserted = cursor.rowcount
        loaded_counts["category_translation"] += len(supplemental_categories)
        logger.info(
            f"  Inserted {len(supplemental_categories)} supplemental rows "
            f"({inserted} new) into 'category_translation'."
        )



        # Step 4: Commit transaction
        conn.commit()
        logger.info("\n[OK] All tables loaded. Transaction committed.")

        # Step 5: Verify row counts
        verify_row_counts(cursor, loaded_counts)

    except Exception as e:
        logger.error(f"[ERROR] Load pipeline failed: {e}")
        logger.error("Rolling back transaction...")
        conn.rollback()
        raise e

    finally:
        conn.close()
        logger.info("\nDatabase connection closed.")


if __name__ == "__main__":
    load_database()
