import sqlite3
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("create_database")

# Database Path Configuration
DEFAULT_DB_PATH = Path("data/olist_ecommerce.db")



def create_sqlite_database(db_path=DEFAULT_DB_PATH):
    """
    Creates the SQLite database, enables foreign keys, defines 7 core tables
    with primary and foreign keys, data types, and performance indexes.
    """
    logger.info(f"Initializing SQLite database creation at: {db_path.resolve()}")

    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Establish SQLite connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Step 1: Enable Foreign Key Enforcement
        logger.info("Enabling Foreign Key constraint enforcement (PRAGMA foreign_keys = ON)...")
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Step 2: Define Core Schema Tables (Sequence respects Parent -> Child dependency)

        # Table 1: Category Translation
        logger.info("Creating table: category_translation...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS category_translation (
                product_category_name TEXT PRIMARY KEY,
                product_category_name_english TEXT NOT NULL
            );
        """)

        # Table 2: Customers
        logger.info("Creating table: customers...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id TEXT PRIMARY KEY,
                customer_unique_id TEXT NOT NULL,
                customer_zip_code_prefix TEXT,
                customer_city TEXT,
                customer_state TEXT
            );
        """)

        # Table 3: Products
        logger.info("Creating table: products...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id TEXT PRIMARY KEY,
                product_category_name TEXT,
                product_category_name_english TEXT,
                product_name_lenght REAL,
                product_description_lenght REAL,
                product_photos_qty REAL,
                product_weight_g REAL,
                product_length_cm REAL,
                product_height_cm REAL,
                product_width_cm REAL,
                FOREIGN KEY (product_category_name) REFERENCES category_translation(product_category_name)
                    ON DELETE SET NULL ON UPDATE CASCADE
            );
        """)

        # Table 4: Orders
        logger.info("Creating table: orders...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                order_status TEXT NOT NULL,
                order_purchase_timestamp TEXT NOT NULL,
                order_approved_at TEXT,
                order_delivered_carrier_date TEXT,
                order_delivered_customer_date TEXT,
                order_estimated_delivery_date TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                    ON DELETE CASCADE ON UPDATE CASCADE
            );
        """)

        # Table 5: Order Items
        logger.info("Creating table: order_items...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                order_id TEXT NOT NULL,
                order_item_id INTEGER NOT NULL,
                product_id TEXT NOT NULL,
                seller_id TEXT NOT NULL,
                shipping_limit_date TEXT NOT NULL,
                price REAL NOT NULL,
                freight_value REAL NOT NULL,
                PRIMARY KEY (order_id, order_item_id),
                FOREIGN KEY (order_id) REFERENCES orders(order_id)
                    ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(product_id)
                    ON DELETE SET NULL ON UPDATE CASCADE
            );
        """)

        # Table 6: Payments
        logger.info("Creating table: payments...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                order_id TEXT NOT NULL,
                payment_sequential INTEGER NOT NULL,
                payment_type TEXT NOT NULL,
                payment_installments INTEGER NOT NULL,
                payment_value REAL NOT NULL,
                PRIMARY KEY (order_id, payment_sequential),
                FOREIGN KEY (order_id) REFERENCES orders(order_id)
                    ON DELETE CASCADE ON UPDATE CASCADE
            );
        """)

        # Table 7: Reviews
        logger.info("Creating table: reviews...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                review_id TEXT NOT NULL,
                order_id TEXT NOT NULL,
                review_score INTEGER NOT NULL,
                review_comment_title TEXT,
                review_comment_message TEXT,
                review_creation_date TEXT NOT NULL,
                review_answer_timestamp TEXT NOT NULL,
                PRIMARY KEY (review_id, order_id),
                FOREIGN KEY (order_id) REFERENCES orders(order_id)
                    ON DELETE CASCADE ON UPDATE CASCADE
            );
        """)

        # Step 3: Create Useful Performance Indexes
        logger.info("Creating performance indexes...")
        index_queries = [
            "CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);",
            "CREATE INDEX IF NOT EXISTS idx_orders_order_purchase_timestamp ON orders(order_purchase_timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_orders_order_status ON orders(order_status);",
            "CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);",
            "CREATE INDEX IF NOT EXISTS idx_order_items_seller_id ON order_items(seller_id);",
            "CREATE INDEX IF NOT EXISTS idx_payments_order_id ON payments(order_id);",
            "CREATE INDEX IF NOT EXISTS idx_reviews_order_id ON reviews(order_id);",
            "CREATE INDEX IF NOT EXISTS idx_customers_customer_unique_id ON customers(customer_unique_id);",
            "CREATE INDEX IF NOT EXISTS idx_products_product_category_name ON products(product_category_name);"
        ]

        for query in index_queries:
            cursor.execute(query)

        conn.commit()

        # Step 4: Verification & Reporting
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        created_tables = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT name FROM sqlite_master WHERE type='index';")
        created_indexes = [row[0] for row in cursor.fetchall()]

        logger.info(f"[SUCCESS] Database created with {len(created_tables)} tables and {len(created_indexes)} indexes.")
        logger.info(f"Tables: {', '.join(created_tables)}")

        return db_path, created_tables, created_indexes

    except Exception as e:
        logger.error(f"[ERROR] Failed to create database schema: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()


if __name__ == "__main__":
    create_sqlite_database()
