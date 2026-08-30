import sqlite3
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("validate_database")

DEFAULT_DB_PATH = Path("data/olist_ecommerce.db")

# ─────────────────────────────────────────────────────────────────────────────
# Expected metadata for validation
# ─────────────────────────────────────────────────────────────────────────────

EXPECTED_ROW_COUNTS = {
    "category_translation": 74,   # 71 raw + 3 supplemental (unknown, pc_gamer, portateis_...)
    "customers":            99_441,
    "products":             32_951,
    "orders":               99_441,
    "order_items":          112_650,
    "payments":             103_886,
    "reviews":              99_224
}


# (table, column_or_tuple_of_columns)
PRIMARY_KEYS = {
    "category_translation": ["product_category_name"],
    "customers":            ["customer_id"],
    "products":             ["product_id"],
    "orders":               ["order_id"],
    "order_items":          ["order_id", "order_item_id"],
    "payments":             ["order_id", "payment_sequential"],
    "reviews":              ["review_id", "order_id"]
}

# (child_table, child_fk_col, parent_table, parent_pk_col)
FOREIGN_KEY_CHECKS = [
    ("orders",      "customer_id",           "customers",            "customer_id"),
    ("products",    "product_category_name", "category_translation", "product_category_name"),
    ("order_items", "order_id",              "orders",               "order_id"),
    ("order_items", "product_id",            "products",             "product_id"),
    ("payments",    "order_id",              "orders",               "order_id"),
    ("reviews",     "order_id",              "orders",               "order_id")
]

EXPECTED_INDEXES = [
    "idx_orders_customer_id",
    "idx_orders_order_purchase_timestamp",
    "idx_orders_order_status",
    "idx_order_items_product_id",
    "idx_order_items_seller_id",
    "idx_payments_order_id",
    "idx_reviews_order_id",
    "idx_customers_customer_unique_id",
    "idx_products_product_category_name"
]

BUSINESS_RULE_CHECKS = [
    ("order_items", "price < 0",             "price >= 0"),
    ("order_items", "freight_value < 0",     "freight_value >= 0"),
    ("payments",    "payment_value < 0",     "payment_value >= 0"),
    ("payments",    "payment_installments < 1", "payment_installments >= 1"),
    ("reviews",     "review_score < 1 OR review_score > 5", "review_score in [1,5]")
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def section(title):
    logger.info("")
    logger.info("=" * 70)
    logger.info(title)
    logger.info("=" * 70)


def result(label, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    msg = f"  [{status}] {label}"
    if detail:
        msg += f"  ({detail})"
    if passed:
        logger.info(msg)
    else:
        logger.error(msg)
    return passed


# ─────────────────────────────────────────────────────────────────────────────
# Validation Functions
# ─────────────────────────────────────────────────────────────────────────────

def check_fk_pragma(cursor):
    """Verify PRAGMA foreign_keys = ON is active for this connection."""
    section("CHECK 0 — PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA foreign_keys;")
    val = cursor.fetchone()[0]
    passed = val == 1
    result("PRAGMA foreign_keys = ON", passed, f"returned {val}")
    return passed


def check_row_counts(cursor):
    """Verify expected row counts per table."""
    section("CHECK 1 — ROW COUNTS")
    all_ok = True
    for table, expected in EXPECTED_ROW_COUNTS.items():
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        actual = cursor.fetchone()[0]
        ok = actual == expected
        result(
            f"{table:<25}  expected={expected:>7,}  actual={actual:>7,}",
            ok
        )
        all_ok = all_ok and ok
    return all_ok


def check_primary_keys(cursor):
    """
    Verify PK uniqueness by comparing COUNT(*) vs COUNT(DISTINCT pk).
    Works for both single and composite PKs.
    """
    section("CHECK 2 — PRIMARY KEY UNIQUENESS")
    all_ok = True
    for table, pk_cols in PRIMARY_KEYS.items():
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        total = cursor.fetchone()[0]

        # Build DISTINCT expression for composite keys
        distinct_expr = ", ".join(pk_cols)
        cursor.execute(f"SELECT COUNT(*) FROM (SELECT DISTINCT {distinct_expr} FROM {table});")
        distinct_count = cursor.fetchone()[0]

        duplicates = total - distinct_count
        ok = duplicates == 0
        result(
            f"{table:<25}  PK=({', '.join(pk_cols)})  duplicates={duplicates}",
            ok
        )
        all_ok = all_ok and ok
    return all_ok


def check_null_primary_keys(cursor):
    """Verify that no PK columns contain NULL values."""
    section("CHECK 3 — NULL IN PRIMARY KEY COLUMNS")
    all_ok = True
    for table, pk_cols in PRIMARY_KEYS.items():
        for col in pk_cols:
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL;")
            null_count = cursor.fetchone()[0]
            ok = null_count == 0
            result(
                f"{table}.{col}  null_count={null_count}",
                ok
            )
            all_ok = all_ok and ok
    return all_ok


def check_foreign_keys_integrity(cursor):
    """
    For each FK relationship, count child rows whose FK value does not
    exist in the parent PK column (orphan records).
    Also runs SQLite's built-in integrity_check.
    """
    section("CHECK 4 — FOREIGN KEY INTEGRITY (ORPHAN RECORDS)")
    all_ok = True
    for child_tbl, child_col, parent_tbl, parent_col in FOREIGN_KEY_CHECKS:
        # Allow NULL FKs (SET NULL action is valid)
        sql = f"""
            SELECT COUNT(*)
            FROM {child_tbl}
            WHERE {child_col} IS NOT NULL
              AND {child_col} NOT IN (SELECT {parent_col} FROM {parent_tbl});
        """
        cursor.execute(sql)
        orphans = cursor.fetchone()[0]
        ok = orphans == 0
        result(
            f"{child_tbl}.{child_col} → {parent_tbl}.{parent_col}  orphans={orphans}",
            ok
        )
        all_ok = all_ok and ok
    return all_ok


def check_sqlite_integrity(cursor):
    """Run SQLite's own PRAGMA integrity_check and foreign_key_check."""
    section("CHECK 5 — SQLITE PRAGMA integrity_check & foreign_key_check")

    # integrity_check
    cursor.execute("PRAGMA integrity_check;")
    rows = [r[0] for r in cursor.fetchall()]
    integrity_ok = rows == ["ok"]
    result(
        f"PRAGMA integrity_check  result={rows}",
        integrity_ok
    )

    # foreign_key_check (requires FK pragma ON)
    cursor.execute("PRAGMA foreign_key_check;")
    fk_violations = cursor.fetchall()
    fk_ok = len(fk_violations) == 0
    result(
        f"PRAGMA foreign_key_check  violations={len(fk_violations)}",
        fk_ok
    )
    if not fk_ok:
        for v in fk_violations[:10]:   # Show first 10 violations
            logger.error(f"    Violation: {v}")

    return integrity_ok and fk_ok


def check_indexes(cursor):
    """Verify all expected indexes are present in sqlite_master."""
    section("CHECK 6 — INDEX EXISTENCE")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index';")
    actual_indexes = {row[0] for row in cursor.fetchall()}

    all_ok = True
    for idx_name in EXPECTED_INDEXES:
        ok = idx_name in actual_indexes
        result(f"Index  {idx_name}", ok)
        all_ok = all_ok and ok
    return all_ok


def check_business_rules(cursor):
    """Run business-rule SQL checks directly in the database."""
    section("CHECK 7 — BUSINESS RULE VALIDATION (IN-DATABASE)")
    all_ok = True
    for table, where_clause, rule_desc in BUSINESS_RULE_CHECKS:
        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {where_clause};")
        violations = cursor.fetchone()[0]
        ok = violations == 0
        result(
            f"{table}: {rule_desc}  violations={violations}",
            ok
        )
        all_ok = all_ok and ok
    return all_ok


def check_no_empty_tables(cursor):
    """Flag any table that has zero rows (sanity check for load failures)."""
    section("CHECK 8 — NO EMPTY TABLES")
    all_ok = True
    for table in EXPECTED_ROW_COUNTS:
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        count = cursor.fetchone()[0]
        ok = count > 0
        result(f"{table:<25}  row_count={count:,}", ok)
        all_ok = all_ok and ok
    return all_ok


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def validate_database(db_path=DEFAULT_DB_PATH):
    """Run all database-level validation checks against the SQLite database."""
    logger.info("=" * 70)
    logger.info("STARTING SQLITE DATABASE VALIDATION SUITE")
    logger.info(f"Database: {db_path.resolve()}")
    logger.info("=" * 70)

    if not db_path.exists():
        logger.error(f"Database file not found: {db_path}")
        raise FileNotFoundError(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Enable FK enforcement for this validation connection
    cursor.execute("PRAGMA foreign_keys = ON;")

    checks = {
        "PRAGMA foreign_keys ON":   check_fk_pragma(cursor),
        "Row Counts":               check_row_counts(cursor),
        "PK Uniqueness":            check_primary_keys(cursor),
        "NULL in PK Columns":       check_null_primary_keys(cursor),
        "FK Orphan Records":        check_foreign_keys_integrity(cursor),
        "SQLite Integrity Check":   check_sqlite_integrity(cursor),
        "Index Existence":          check_indexes(cursor),
        "Business Rules":           check_business_rules(cursor),
        "No Empty Tables":          check_no_empty_tables(cursor),
    }

    conn.close()

    # ── Final Summary ──────────────────────────────────────────────────────
    section("VALIDATION SUMMARY")
    passed = sum(1 for v in checks.values() if v)
    failed = len(checks) - passed

    for check_name, ok in checks.items():
        status = "PASS" if ok else "FAIL"
        logger.info(f"  [{status}]  {check_name}")

    logger.info("")
    if failed == 0:
        logger.info(f"[SUCCESS] All {passed}/{len(checks)} checks PASSED. Database is valid.")
    else:
        logger.error(
            f"[FAILURE] {failed}/{len(checks)} checks FAILED. Review errors above."
        )

    return checks


if __name__ == "__main__":
    validate_database()
