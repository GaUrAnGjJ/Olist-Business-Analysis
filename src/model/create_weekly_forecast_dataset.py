import sqlite3
import logging
from pathlib import Path
import pandas as pd
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("create_weekly_forecast_dataset")

DB_PATH = Path("data/olist_ecommerce.db")
OUTPUT_DIR = Path("data/processed/forecast")
OUTPUT_FILE = OUTPUT_DIR / "weekly_forecasting_data.csv"

CLEAN_START_WEEK = "2017-01-09"  # First full ISO Monday week
CLEAN_END_WEEK = "2018-08-20"    # Last full ISO Monday week (covering up to 2018-08-26)


def extract_weekly_aggregated_data(conn=None):
    """
    Extract and aggregate order revenue data by ISO Monday week start.
    Filters strictly for the continuous operational window of 85 full weeks (2017-01-09 to 2018-08-20).
    """
    should_close = False
    if conn is None:
        if not DB_PATH.exists():
            raise FileNotFoundError(f"Database not found at {DB_PATH.resolve()}.")
        conn = sqlite3.connect(DB_PATH)
        should_close = True

    logger.info("Reading order-level data from v_sales_orders...")
    query = """
        SELECT 
            order_id, 
            order_purchase_timestamp, 
            product_sales_revenue,
            freight_charges,
            gross_order_value 
        FROM v_sales_orders;
    """
    df_orders = pd.read_sql_query(query, conn)
    if should_close:
        conn.close()

    df_orders['ts'] = pd.to_datetime(df_orders['order_purchase_timestamp'])
    
    # ISO week start (Monday)
    df_orders['week_start'] = df_orders['ts'].dt.to_period('W-SUN').dt.start_time.dt.strftime('%Y-%m-%d')

    logger.info("Aggregating orders by ISO week start date...")
    weekly = df_orders.groupby('week_start').agg(
        order_count=('order_id', 'count'),
        product_revenue=('product_sales_revenue', 'sum'),
        freight_charges=('freight_charges', 'sum'),
        gross_revenue=('gross_order_value', 'sum')
    ).reset_index()

    weekly['gross_aov'] = weekly['gross_revenue'] / weekly['order_count']

    # Filter strictly for the 85 continuous full operational ISO weeks
    weekly_clean = weekly[(weekly['week_start'] >= CLEAN_START_WEEK) & (weekly['week_start'] <= CLEAN_END_WEEK)].copy()
    weekly_clean = weekly_clean.sort_values('week_start').reset_index(drop=True)

    return df_orders, weekly_clean


def validate_weekly_dataset(df_orders, df_weekly):
    """
    Validate dataset against all 7 strict quality requirements:
    1. Exactly 85 rows/weeks
    2. No missing week_start
    3. No duplicate weeks
    4. No missing target values
    5. Continuous 7-day weekly intervals
    6. Component identity check (gross_revenue == product_revenue + freight_charges)
    7. Reconciliation against underlying orders in the 85-week timeframe
    """
    logger.info("=" * 70)
    logger.info("STARTING WEEKLY FORECASTING DATASET VALIDATION")
    logger.info("=" * 70)

    validation_results = {}

    # Check 1: Exactly 85 rows/weeks
    expected_rows = 85
    actual_rows = len(df_weekly)
    check1 = (actual_rows == expected_rows)
    validation_results['check_85_rows'] = check1
    logger.info(f"1. Row Count Check (Expected: {expected_rows}, Actual: {actual_rows}): {'[PASS]' if check1 else '[FAIL]'}")

    # Check 2: No missing week_start
    missing_weeks = df_weekly['week_start'].isna().sum() + (df_weekly['week_start'] == "").sum()
    check2 = (missing_weeks == 0)
    validation_results['check_no_missing_week_start'] = check2
    logger.info(f"2. No Missing week_start Check (Missing: {missing_weeks}): {'[PASS]' if check2 else '[FAIL]'}")

    # Check 3: No duplicate weeks
    duplicates = df_weekly['week_start'].duplicated().sum()
    check3 = (duplicates == 0)
    validation_results['check_no_duplicate_weeks'] = check3
    logger.info(f"3. No Duplicate Weeks Check (Duplicates: {duplicates}): {'[PASS]' if check3 else '[FAIL]'}")

    # Check 4: No missing target values
    target_cols = ['order_count', 'product_revenue', 'freight_charges', 'gross_revenue', 'gross_aov']
    missing_targets = df_weekly[target_cols].isna().sum().sum()
    check4 = (missing_targets == 0)
    validation_results['check_no_missing_targets'] = check4
    logger.info(f"4. No Missing Target Values Check (Missing values: {missing_targets}): {'[PASS]' if check4 else '[FAIL]'}")

    # Check 5: Continuous 7-day weekly intervals
    week_dt = pd.to_datetime(df_weekly['week_start'])
    day_diffs = week_dt.diff().dropna().dt.days
    is_continuous_7day = (day_diffs == 7).all()
    check5 = is_continuous_7day
    validation_results['check_continuous_7day'] = check5
    logger.info(f"5. Continuous 7-day Interval Check (Intervals strictly 7 days): {'[PASS]' if check5 else '[FAIL]'}")

    # Check 6: Component identity check (gross = product + freight)
    identity_diff = np.abs(df_weekly['gross_revenue'] - (df_weekly['product_revenue'] + df_weekly['freight_charges']))
    max_diff = identity_diff.max()
    check6 = (max_diff < 1e-4)
    validation_results['check_component_identity'] = check6
    logger.info(f"6. Revenue Component Identity Check (gross = product + freight, max diff={max_diff:.6f}): {'[PASS]' if check6 else '[FAIL]'}")

    # Check 7: Reconciliation against underlying orders
    # Orders within the window: from CLEAN_START_WEEK (2017-01-09 00:00:00) to 2018-08-27 00:00:00
    df_orders_clean = df_orders[(df_orders['ts'] >= CLEAN_START_WEEK) & (df_orders['ts'] < '2018-08-27')]
    orders_sum_gross = df_orders_clean['gross_order_value'].sum()
    orders_sum_product = df_orders_clean['product_sales_revenue'].sum()
    orders_sum_freight = df_orders_clean['freight_charges'].sum()
    orders_count = len(df_orders_clean)

    weekly_sum_gross = df_weekly['gross_revenue'].sum()
    weekly_sum_product = df_weekly['product_revenue'].sum()
    weekly_sum_freight = df_weekly['freight_charges'].sum()
    weekly_count_orders = df_weekly['order_count'].sum()

    diff_gross = abs(orders_sum_gross - weekly_sum_gross)
    diff_product = abs(orders_sum_product - weekly_sum_product)
    diff_freight = abs(orders_sum_freight - weekly_sum_freight)
    diff_count = abs(orders_count - weekly_count_orders)

    check7 = (diff_gross < 0.01 and diff_product < 0.01 and diff_freight < 0.01 and diff_count == 0)
    validation_results['check_reconciliation'] = check7
    logger.info(f"7. Order-Level Reconciliation Check (Orders count diff: {diff_count}, Gross diff: ${diff_gross:.4f}): {'[PASS]' if check7 else '[FAIL]'}")

    all_passed = all(validation_results.values())
    logger.info("=" * 70)
    logger.info(f"FINAL WEEKLY DATASET VALIDATION RESULT: {'[SUCCESS - ALL CHECKS PASSED]' if all_passed else '[FAILURE]'}")
    logger.info("=" * 70)

    if not all_passed:
        raise ValueError("Weekly forecasting dataset failed validation checks.")

    return validation_results


def create_and_save_weekly_dataset():
    """Main execution function to build, validate, and save the dataset."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    df_orders, df_weekly = extract_weekly_aggregated_data()
    validate_weekly_dataset(df_orders, df_weekly)

    df_weekly.to_csv(OUTPUT_FILE, index=False)
    logger.info(f"Successfully saved validated weekly forecasting dataset to: {OUTPUT_FILE.resolve()}")
    return df_weekly


if __name__ == "__main__":
    create_and_save_weekly_dataset()
