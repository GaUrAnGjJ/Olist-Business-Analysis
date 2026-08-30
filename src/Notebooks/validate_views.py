import sqlite3
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("validate_views")

DEFAULT_DB_PATH = Path("data/olist_ecommerce.db")


def validate_v_sales_order_items(conn):
    """
    Step 4.1 Validation: v_sales_order_items
    Checks:
    1. View existence
    2. Total row count matches order_items table (112,650)
    3. Grain uniqueness: composite key (order_id, order_item_id) distinct count = 112,650
    4. Zero NULLs in required join keys (order_id, customer_id, product_id, seller_id)
    5. English category translation completeness (0 NULLs)
    6. Calculation check: item_total_value == price + freight_value
    """
    logger.info("\n" + "=" * 70)
    logger.info("VALIDATING VIEW: v_sales_order_items (Step 4.1)")
    logger.info("=" * 70)

    cursor = conn.cursor()

    # 1. Existence check
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name='v_sales_order_items';")
    exists = cursor.fetchone() is not None
    logger.info(f"1. View Existence: {'PASS' if exists else 'FAIL'}")
    if not exists:
        return False

    # 2. Row count match check
    cursor.execute("SELECT COUNT(*) FROM order_items;")
    expected_rows = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM v_sales_order_items;")
    actual_rows = cursor.fetchone()[0]

    row_count_match = (expected_rows == actual_rows)
    logger.info(f"2. Row Count Match: {'PASS' if row_count_match else 'FAIL'} (Expected: {expected_rows:,}, Actual: {actual_rows:,})")

    # 3. Grain validation check (distinct composite key)
    cursor.execute("SELECT COUNT(*) FROM (SELECT DISTINCT order_id, order_item_id FROM v_sales_order_items);")
    distinct_grain = cursor.fetchone()[0]

    grain_match = (distinct_grain == actual_rows)
    logger.info(f"3. Grain Uniqueness (order_id, order_item_id): {'PASS' if grain_match else 'FAIL'} (Distinct pairs: {distinct_grain:,})")

    # 4. Zero nulls in join keys check
    cursor.execute("""
        SELECT COUNT(*)
        FROM v_sales_order_items
        WHERE order_id IS NULL
           OR order_item_id IS NULL
           OR customer_id IS NULL
           OR product_id IS NULL
           OR seller_id IS NULL;
    """)
    null_keys = cursor.fetchone()[0]
    keys_clean = (null_keys == 0)
    logger.info(f"4. Join Key Completeness: {'PASS' if keys_clean else 'FAIL'} (Null key records: {null_keys})")

    # 5. Category translation completeness
    cursor.execute("""
        SELECT COUNT(*)
        FROM v_sales_order_items
        WHERE product_category_name_english IS NULL OR product_category_name_english = '';
    """)
    null_translations = cursor.fetchone()[0]
    trans_clean = (null_translations == 0)
    logger.info(f"5. Category Translation Completeness: {'PASS' if trans_clean else 'FAIL'} (Unmapped categories: {null_translations})")

    # 6. Calculation check
    cursor.execute("""
        SELECT COUNT(*)
        FROM v_sales_order_items
        WHERE ABS(item_total_value - (price + freight_value)) > 0.001;
    """)
    calc_errors = cursor.fetchone()[0]
    calc_correct = (calc_errors == 0)
    logger.info(f"6. Item Total Value Calculation (price + freight): {'PASS' if calc_correct else 'FAIL'} (Errors: {calc_errors})")

    all_passed = all([exists, row_count_match, grain_match, keys_clean, trans_clean, calc_correct])
    logger.info("-" * 70)
    logger.info(f"Step 4.1 v_sales_order_items Validation Status: {'[SUCCESS] ALL PASSED' if all_passed else '[FAILURE] CHECKS FAILED'}")

    return all_passed


def validate_v_sales_orders(conn):
    """
    Step 4.2 Validation: v_sales_orders
    Checks:
    1. View existence
    2. Row count equals total distinct orders in orders table (99,441)
    3. Grain uniqueness: order_id is strictly unique (distinct order_id = row count = 99,441)
    4. Revenue reconciliation: SUM(product_sales_revenue) == SUM(price) in v_sales_order_items
    5. Freight reconciliation: SUM(freight_charges) == SUM(freight_value) in v_sales_order_items
    6. Gross order value reconciliation: SUM(gross_order_value) == SUM(item_total_value) in v_sales_order_items
    7. Zero NULL order_id or customer_id values
    """
    logger.info("\n" + "=" * 70)
    logger.info("VALIDATING VIEW: v_sales_orders (Step 4.2)")
    logger.info("=" * 70)

    cursor = conn.cursor()

    # 1. Existence check
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name='v_sales_orders';")
    exists = cursor.fetchone() is not None
    logger.info(f"1. View Existence: {'PASS' if exists else 'FAIL'}")
    if not exists:
        return False

    # 2. Row count check vs orders table
    cursor.execute("SELECT COUNT(*) FROM orders;")
    expected_rows = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM v_sales_orders;")
    actual_rows = cursor.fetchone()[0]

    row_count_match = (expected_rows == actual_rows)
    logger.info(f"2. Row Count Match: {'PASS' if row_count_match else 'FAIL'} (Expected: {expected_rows:,}, Actual: {actual_rows:,})")

    # 3. Grain uniqueness check (order_id)
    cursor.execute("SELECT COUNT(*) FROM (SELECT DISTINCT order_id FROM v_sales_orders);")
    distinct_order_ids = cursor.fetchone()[0]

    grain_match = (distinct_order_ids == actual_rows)
    logger.info(f"3. Grain Uniqueness (order_id): {'PASS' if grain_match else 'FAIL'} (Distinct order_id: {distinct_order_ids:,})")

    # 4, 5, 6. Financial Reconciliation checks against v_sales_order_items
    cursor.execute("SELECT SUM(price), SUM(freight_value), SUM(item_total_value) FROM v_sales_order_items;")
    items_rev, items_freight, items_gross = cursor.fetchone()

    cursor.execute("SELECT SUM(product_sales_revenue), SUM(freight_charges), SUM(gross_order_value) FROM v_sales_orders;")
    orders_rev, orders_freight, orders_gross = cursor.fetchone()

    rev_reconciles = abs(items_rev - orders_rev) < 0.01
    freight_reconciles = abs(items_freight - orders_freight) < 0.01
    gross_reconciles = abs(items_gross - orders_gross) < 0.01

    logger.info(f"4. Product Revenue Reconciliation: {'PASS' if rev_reconciles else 'FAIL'} (Items: ${items_rev:,.2f}, Orders: ${orders_rev:,.2f})")
    logger.info(f"5. Freight Charges Reconciliation: {'PASS' if freight_reconciles else 'FAIL'} (Items: ${items_freight:,.2f}, Orders: ${orders_freight:,.2f})")
    logger.info(f"6. Gross Order Value Reconciliation: {'PASS' if gross_reconciles else 'FAIL'} (Items: ${items_gross:,.2f}, Orders: ${orders_gross:,.2f})")

    # 7. Null key check
    cursor.execute("SELECT COUNT(*) FROM v_sales_orders WHERE order_id IS NULL OR customer_id IS NULL;")
    null_keys = cursor.fetchone()[0]
    keys_clean = (null_keys == 0)
    logger.info(f"7. Key Completeness (order_id, customer_id): {'PASS' if keys_clean else 'FAIL'} (Null keys: {null_keys})")

    all_passed = all([
        exists, row_count_match, grain_match,
        rev_reconciles, freight_reconciles, gross_reconciles,
        keys_clean
    ])
    logger.info("-" * 70)
    logger.info(f"Step 4.2 v_sales_orders Validation Status: {'[SUCCESS] ALL PASSED' if all_passed else '[FAILURE] CHECKS FAILED'}")

    return all_passed


def validate_v_customer_orders(conn):
    """
    Step 4.3 Validation: v_customer_orders
    Checks:
    1. View existence
    2. View row count matches v_sales_orders (99,441)
    3. Grain uniqueness: order_id remains strictly unique (distinct order_id = 99,441)
    4. customer_unique_id completeness (0 NULLs)
    5. Zero revenue shifts: product_sales_revenue, freight_charges, and gross_order_value sums match v_sales_orders
    6. Customer location fields available (0 NULLs for customer_city, customer_state)
    7. Customer grain sanity: distinct customer_unique_id count (96,096) <= order count (99,441)
    """
    logger.info("\n" + "=" * 70)
    logger.info("VALIDATING VIEW: v_customer_orders (Step 4.3)")
    logger.info("=" * 70)

    cursor = conn.cursor()

    # 1. Existence check
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name='v_customer_orders';")
    exists = cursor.fetchone() is not None
    logger.info(f"1. View Existence: {'PASS' if exists else 'FAIL'}")
    if not exists:
        return False

    # 2. Row count match check vs v_sales_orders
    cursor.execute("SELECT COUNT(*) FROM v_sales_orders;")
    expected_rows = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM v_customer_orders;")
    actual_rows = cursor.fetchone()[0]

    row_count_match = (expected_rows == actual_rows)
    logger.info(f"2. Row Count Match: {'PASS' if row_count_match else 'FAIL'} (Expected: {expected_rows:,}, Actual: {actual_rows:,})")

    # 3. Grain uniqueness check (order_id)
    cursor.execute("SELECT COUNT(*) FROM (SELECT DISTINCT order_id FROM v_customer_orders);")
    distinct_order_ids = cursor.fetchone()[0]

    grain_match = (distinct_order_ids == actual_rows)
    logger.info(f"3. Grain Uniqueness (order_id): {'PASS' if grain_match else 'FAIL'} (Distinct order_id: {distinct_order_ids:,})")

    # 4. customer_unique_id completeness check
    cursor.execute("SELECT COUNT(*) FROM v_customer_orders WHERE customer_unique_id IS NULL OR customer_unique_id = '';")
    null_unique_cust = cursor.fetchone()[0]
    unique_cust_clean = (null_unique_cust == 0)
    logger.info(f"4. customer_unique_id Completeness: {'PASS' if unique_cust_clean else 'FAIL'} (Null records: {null_unique_cust})")

    # 5. Financial Reconciliation checks against v_sales_orders
    cursor.execute("SELECT SUM(product_sales_revenue), SUM(freight_charges), SUM(gross_order_value) FROM v_sales_orders;")
    so_rev, so_freight, so_gross = cursor.fetchone()

    cursor.execute("SELECT SUM(product_sales_revenue), SUM(freight_charges), SUM(gross_order_value) FROM v_customer_orders;")
    co_rev, co_freight, co_gross = cursor.fetchone()

    rev_no_shift = abs(so_rev - co_rev) < 0.01
    freight_no_shift = abs(so_freight - co_freight) < 0.01
    gross_no_shift = abs(so_gross - co_gross) < 0.01

    logger.info(f"5. Revenue Shift Check: {'PASS' if (rev_no_shift and freight_no_shift and gross_no_shift) else 'FAIL'} (Diffs: rev=${abs(so_rev - co_rev):.4f})")

    # 6. Customer location fields availability
    cursor.execute("SELECT COUNT(*) FROM v_customer_orders WHERE customer_city IS NULL OR customer_state IS NULL OR customer_city = '' OR customer_state = '';")
    null_locs = cursor.fetchone()[0]
    locs_clean = (null_locs == 0)
    logger.info(f"6. Location Demographics Availability: {'PASS' if locs_clean else 'FAIL'} (Missing loc records: {null_locs})")

    # 7. Customer grain sanity check
    cursor.execute("SELECT COUNT(DISTINCT customer_unique_id) FROM v_customer_orders;")
    distinct_unique_custs = cursor.fetchone()[0]

    cust_grain_sane = (distinct_unique_custs <= actual_rows) and (distinct_unique_custs > 0)
    logger.info(f"7. Customer Grain Sanity: {'PASS' if cust_grain_sane else 'FAIL'} (Distinct real-world customers: {distinct_unique_custs:,} <= {actual_rows:,} orders)")

    all_passed = all([
        exists, row_count_match, grain_match,
        unique_cust_clean, rev_no_shift, freight_no_shift, gross_no_shift,
        locs_clean, cust_grain_sane
    ])
    logger.info("-" * 70)
    logger.info(f"Step 4.3 v_customer_orders Validation Status: {'[SUCCESS] ALL PASSED' if all_passed else '[FAILURE] CHECKS FAILED'}")

    return all_passed


def validate_v_delivery_satisfaction(conn):
    """
    Step 4.4 Validation: v_delivery_satisfaction
    Checks:
    1. View existence
    2. Row count matches orders table (99,441)
    3. Grain uniqueness: order_id is strictly unique (distinct order_id = 99,441)
    4. Review score validity (review_score in range [1, 5] when present)
    5. Delivered orders have valid delivery calculations (non-NULL delivery_days/delay/is_late when actual_delivery_date present)
    6. Non-delivered orders don't get fake delivery metrics (0 non-NULL delivery metrics when actual_delivery_date IS NULL)
    7. Late-delivery calculation accuracy (is_late == 1 iff actual_delivery_date > estimated_delivery_date)
    8. Customer location fields available (0 NULL customer_city/state)
    """
    logger.info("\n" + "=" * 70)
    logger.info("VALIDATING VIEW: v_delivery_satisfaction (Step 4.4)")
    logger.info("=" * 70)

    cursor = conn.cursor()

    # 1. Existence check
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name='v_delivery_satisfaction';")
    exists = cursor.fetchone() is not None
    logger.info(f"1. View Existence: {'PASS' if exists else 'FAIL'}")
    if not exists:
        return False

    # 2. Row count check vs orders table
    cursor.execute("SELECT COUNT(*) FROM orders;")
    expected_rows = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM v_delivery_satisfaction;")
    actual_rows = cursor.fetchone()[0]

    row_count_match = (expected_rows == actual_rows)
    logger.info(f"2. Row Count Match: {'PASS' if row_count_match else 'FAIL'} (Expected: {expected_rows:,}, Actual: {actual_rows:,})")

    # 3. Grain uniqueness check (order_id)
    cursor.execute("SELECT COUNT(*) FROM (SELECT DISTINCT order_id FROM v_delivery_satisfaction);")
    distinct_order_ids = cursor.fetchone()[0]

    grain_match = (distinct_order_ids == actual_rows)
    logger.info(f"3. Grain Uniqueness (order_id): {'PASS' if grain_match else 'FAIL'} (Distinct order_id: {distinct_order_ids:,})")

    # 4. Review score range check
    cursor.execute("SELECT COUNT(*) FROM v_delivery_satisfaction WHERE review_score IS NOT NULL AND (review_score < 1 OR review_score > 5);")
    invalid_scores = cursor.fetchone()[0]
    scores_valid = (invalid_scores == 0)
    logger.info(f"4. Review Score Range Validity [1, 5]: {'PASS' if scores_valid else 'FAIL'} (Invalid score records: {invalid_scores})")

    # 5. Delivered orders delivery calculation check
    cursor.execute("""
        SELECT COUNT(*)
        FROM v_delivery_satisfaction
        WHERE actual_delivery_date IS NOT NULL
          AND (delivery_days IS NULL OR delivery_delay_days IS NULL OR is_late IS NULL);
    """)
    missing_delivered_metrics = cursor.fetchone()[0]
    delivered_metrics_valid = (missing_delivered_metrics == 0)
    logger.info(f"5. Delivered Orders Calculation Completeness: {'PASS' if delivered_metrics_valid else 'FAIL'} (Missing metrics: {missing_delivered_metrics})")

    # 6. Non-delivered orders metric preservation (must be NULL)
    cursor.execute("""
        SELECT COUNT(*)
        FROM v_delivery_satisfaction
        WHERE actual_delivery_date IS NULL
          AND (delivery_days IS NOT NULL OR delivery_delay_days IS NOT NULL OR is_late IS NOT NULL);
    """)
    fake_metrics = cursor.fetchone()[0]
    non_delivered_clean = (fake_metrics == 0)
    logger.info(f"6. Non-Delivered Orders NULL Metric Preservation: {'PASS' if non_delivered_clean else 'FAIL'} (Fake metric records: {fake_metrics})")

    # 7. Late delivery timestamp logic check
    cursor.execute("""
        SELECT COUNT(*)
        FROM v_delivery_satisfaction
        WHERE actual_delivery_date IS NOT NULL
          AND (
              (actual_delivery_date > estimated_delivery_date AND is_late != 1)
              OR (actual_delivery_date <= estimated_delivery_date AND is_late != 0)
          );
    """)
    late_mismatches = cursor.fetchone()[0]
    late_logic_valid = (late_mismatches == 0)
    logger.info(f"7. Late Delivery Timestamp Logic Check: {'PASS' if late_logic_valid else 'FAIL'} (Logic mismatches: {late_mismatches})")

    # 8. Location fields availability
    cursor.execute("SELECT COUNT(*) FROM v_delivery_satisfaction WHERE customer_city IS NULL OR customer_state IS NULL OR customer_city = '' OR customer_state = '';")
    null_locs = cursor.fetchone()[0]
    locs_clean = (null_locs == 0)
    logger.info(f"8. Location Demographics Availability: {'PASS' if locs_clean else 'FAIL'} (Missing loc records: {null_locs})")

    all_passed = all([
        exists, row_count_match, grain_match,
        scores_valid, delivered_metrics_valid, non_delivered_clean,
        late_logic_valid, locs_clean
    ])
    logger.info("-" * 70)
    logger.info(f"Step 4.4 v_delivery_satisfaction Validation Status: {'[SUCCESS] ALL PASSED' if all_passed else '[FAILURE] CHECKS FAILED'}")

    return all_passed


def validate_all_views(db_path=DEFAULT_DB_PATH):
    """Run view validations."""
    logger.info("=" * 70)
    logger.info("STARTING SQL VIEW VALIDATION SUITE")
    logger.info("=" * 70)

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at {db_path.resolve()}.")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    try:
        pass_4_1 = validate_v_sales_order_items(conn)
        pass_4_2 = validate_v_sales_orders(conn)
        pass_4_3 = validate_v_customer_orders(conn)
        pass_4_4 = validate_v_delivery_satisfaction(conn)

        if pass_4_1 and pass_4_2 and pass_4_3 and pass_4_4:
            logger.info("\n[SUCCESS] Steps 4.1, 4.2, 4.3 & 4.4 fully validated.")
        else:
            logger.error("\n[ERROR] View validation failed.")
    finally:
        conn.close()


if __name__ == "__main__":
    validate_all_views()



