import sqlite3
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("create_views")

DEFAULT_DB_PATH = Path("data/olist_ecommerce.db")


def create_v_sales_order_items(conn):
    """
    Step 4.1: Create v_sales_order_items view.
    Grain: Exactly one row per (order_id, order_item_id).
    Joins order_items, orders, products, and category_translation.
    """
    logger.info("Creating view: v_sales_order_items...")
    cursor = conn.cursor()

    cursor.execute("DROP VIEW IF EXISTS v_sales_order_items;")

    query = """
    CREATE VIEW v_sales_order_items AS
    SELECT
        oi.order_id,
        oi.order_item_id,
        o.customer_id,
        oi.product_id,
        oi.seller_id,
        o.order_status,
        o.order_purchase_timestamp,
        oi.shipping_limit_date,
        oi.price,
        oi.freight_value,
        (oi.price + oi.freight_value) AS item_total_value,
        p.product_category_name,
        COALESCE(p.product_category_name_english, ct.product_category_name_english, 'unknown') AS product_category_name_english
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    LEFT JOIN products p ON oi.product_id = p.product_id
    LEFT JOIN category_translation ct ON p.product_category_name = ct.product_category_name;
    """

    cursor.execute(query)
    conn.commit()
    logger.info("  [OK] View v_sales_order_items created successfully.")


def create_v_sales_orders(conn):
    """
    Step 4.2: Create v_sales_orders view.
    Grain: Exactly one row per order_id.
    Aggregates order items without joining payments to avoid double-counting.
    """
    logger.info("Creating view: v_sales_orders...")
    cursor = conn.cursor()

    cursor.execute("DROP VIEW IF EXISTS v_sales_orders;")

    query = """
    CREATE VIEW v_sales_orders AS
    SELECT
        o.order_id,
        o.customer_id,
        o.order_status,
        o.order_purchase_timestamp,
        o.order_approved_at,
        o.order_delivered_carrier_date,
        o.order_delivered_customer_date,
        o.order_estimated_delivery_date,
        COALESCE(COUNT(soi.order_item_id), 0) AS total_items_count,
        COALESCE(SUM(soi.price), 0.0) AS product_sales_revenue,
        COALESCE(SUM(soi.freight_value), 0.0) AS freight_charges,
        COALESCE(SUM(soi.item_total_value), 0.0) AS gross_order_value
    FROM orders o
    LEFT JOIN v_sales_order_items soi ON o.order_id = soi.order_id
    GROUP BY
        o.order_id,
        o.customer_id,
        o.order_status,
        o.order_purchase_timestamp,
        o.order_approved_at,
        o.order_delivered_carrier_date,
        o.order_delivered_customer_date,
        o.order_estimated_delivery_date;
    """

    cursor.execute(query)
    conn.commit()
    logger.info("  [OK] View v_sales_orders created successfully.")


def create_v_customer_orders(conn):
    """
    Step 4.3: Create v_customer_orders view.
    Grain: One row per order, associated with one real-world customer.
    Joins v_sales_orders with customers to attach customer_unique_id and demographics.
    """
    logger.info("Creating view: v_customer_orders...")
    cursor = conn.cursor()

    cursor.execute("DROP VIEW IF EXISTS v_customer_orders;")

    query = """
    CREATE VIEW v_customer_orders AS
    SELECT
        so.order_id,
        so.customer_id,
        c.customer_unique_id,
        c.customer_city,
        c.customer_state,
        so.order_purchase_timestamp AS purchase_timestamp,
        so.order_status,
        so.total_items_count AS item_count,
        so.product_sales_revenue,
        so.freight_charges,
        so.gross_order_value
    FROM v_sales_orders so
    JOIN customers c ON so.customer_id = c.customer_id;
    """

    cursor.execute(query)
    conn.commit()
    logger.info("  [OK] View v_customer_orders created successfully.")


def create_v_delivery_satisfaction(conn):
    """
    Step 4.4: Create v_delivery_satisfaction view.
    Grain: Exactly one row per order_id.
    Joins orders, customers, and aggregated reviews (subquery grouped by order_id)
    to prevent row multiplication caused by multiple reviews per order.
    Calculates delivery_days, delivery_delay_days, and is_late indicator.
    """
    logger.info("Creating view: v_delivery_satisfaction...")
    cursor = conn.cursor()

    cursor.execute("DROP VIEW IF EXISTS v_delivery_satisfaction;")

    query = """
    CREATE VIEW v_delivery_satisfaction AS
    SELECT
        o.order_id,
        o.order_status,
        o.order_purchase_timestamp AS purchase_timestamp,
        o.order_estimated_delivery_date AS estimated_delivery_date,
        o.order_delivered_customer_date AS actual_delivery_date,

        CASE
            WHEN o.order_delivered_customer_date IS NOT NULL AND o.order_purchase_timestamp IS NOT NULL
            THEN ROUND(JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_purchase_timestamp), 2)
            ELSE NULL
        END AS delivery_days,

        CASE
            WHEN o.order_delivered_customer_date IS NOT NULL AND o.order_estimated_delivery_date IS NOT NULL
            THEN ROUND(JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_estimated_delivery_date), 2)
            ELSE NULL
        END AS delivery_delay_days,

        CASE
            WHEN o.order_delivered_customer_date IS NULL OR o.order_estimated_delivery_date IS NULL THEN NULL
            WHEN JULIANDAY(o.order_delivered_customer_date) > JULIANDAY(o.order_estimated_delivery_date) THEN 1
            ELSE 0
        END AS is_late,

        c.customer_city,
        c.customer_state,
        r.review_score
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    LEFT JOIN (
        SELECT order_id, AVG(review_score) AS review_score
        FROM reviews
        GROUP BY order_id
    ) r ON o.order_id = r.order_id;
    """

    cursor.execute(query)
    conn.commit()
    logger.info("  [OK] View v_delivery_satisfaction created successfully.")


def create_all_views(db_path=DEFAULT_DB_PATH):
    """Orchestrate view creation step by step."""
    logger.info("=" * 70)
    logger.info("STARTING SQL VIEW CREATION")
    logger.info("=" * 70)

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at {db_path.resolve()}. Please run create_database.py and load_database.py first.")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    try:
        # Step 4.1
        create_v_sales_order_items(conn)

        # Step 4.2
        create_v_sales_orders(conn)

        # Step 4.3
        create_v_customer_orders(conn)

        # Step 4.4
        create_v_delivery_satisfaction(conn)

        logger.info("\n[SUCCESS] Steps 4.1, 4.2, 4.3 & 4.4 view creation complete.")
        return conn
    except Exception as e:
        logger.error(f"[ERROR] Failed to create views: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()


if __name__ == "__main__":
    create_all_views()



