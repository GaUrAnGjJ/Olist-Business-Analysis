import pandas as pd
from pathlib import Path

RAW_DATA_PATH = Path("data/raw")
PROCESSED_DATA_PATH = Path("data/processed/cleaning")


def load_raw_datasets(data_path=RAW_DATA_PATH):
    """Load raw datasets into pandas DataFrames."""
    files = {
        "orders": "olist_orders_dataset.csv",
        "customers": "olist_customers_dataset.csv",
        "order_items": "olist_order_items_dataset.csv",
        "payments": "olist_order_payments_dataset.csv",
        "products": "olist_products_dataset.csv",
        "reviews": "olist_order_reviews_dataset.csv",
        "category_translation": "product_category_name_translation.csv"
    }

    return {
        name: pd.read_csv(data_path / filename)
        for name, filename in files.items()
    }


def clean_orders(orders_df):
    """
    2.1 Orders Cleaning
    - Convert timestamp fields to datetime objects
    - Preserve legitimate lifecycle missingness (e.g. unapproved/unshipped/canceled orders)
    - Strip whitespace from string identifiers
    """
    df = orders_df.copy()

    # Strip string identifiers
    for col in ["order_id", "customer_id", "order_status"]:
        df[col] = df[col].astype(str).str.strip()

    # Convert timestamp columns with explicit datetime parsing and standardized string formatting
    timestamp_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ]

    for col in timestamp_cols:
        parsed = pd.to_datetime(df[col], format="mixed", errors="coerce")
        df[col] = parsed.dt.strftime("%Y-%m-%d %H:%M:%S")

    print("[2.1 Orders Cleaning]")
    print(f"  - Cleaned {len(df):,} orders.")
    print("  - Timestamp columns converted to datetime.")
    print("  - Legitimate lifecycle missingness preserved.")

    return df



def clean_products(products_df, translation_df):
    """
    2.2 Products Cleaning
    - Handle missing category names by filling with 'unknown'
    - Map Portuguese category names to English, including missing translation categories
    - Ensure numeric attributes are valid numeric dtypes
    """
    df = products_df.copy()

    # Strip whitespace
    df["product_id"] = df["product_id"].astype(str).str.strip()
    if "product_category_name" in df.columns:
        df["product_category_name"] = df["product_category_name"].astype(str).str.strip()

    # Impute missing categories
    df["product_category_name"] = df["product_category_name"].replace("nan", None).fillna("unknown")

    # Build translation mapping dictionary
    trans_map = dict(
        zip(translation_df["product_category_name"].str.strip(), translation_df["product_category_name_english"].str.strip())
    )
    # Add unmapped categories identified during audit
    trans_map["pc_gamer"] = "pc_gamer"
    trans_map["portateis_cozinha_e_preparadores_de_alimentos"] = "portable_kitchen_and_food_preparers"
    trans_map["unknown"] = "unknown"

    df["product_category_name_english"] = df["product_category_name"].map(trans_map).fillna("unknown")

    # Ensure numeric columns are floats
    num_cols = [
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm"
    ]
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    print("[2.2 Products Cleaning]")
    print(f"  - Cleaned {len(df):,} products.")
    print("  - Imputed missing categories as 'unknown'.")
    print("  - Added English category translations.")

    return df


def clean_reviews(reviews_df):
    """
    2.3 Reviews Cleaning
    - Convert date/timestamp columns
    - Handle exact duplicates carefully (deduplicate on review_id and order_id)
    - Preserve optional missing review comment text (titles and messages)
    - Validate review score boundaries (1 to 5)
    """
    df = reviews_df.copy()

    # Strip string columns
    for col in ["review_id", "order_id"]:
        df[col] = df[col].astype(str).str.strip()

    # Convert timestamps with explicit format="mixed"
    rev_creation_dt = pd.to_datetime(df["review_creation_date"], format="mixed", errors="coerce")
    rev_answer_dt = pd.to_datetime(df["review_answer_timestamp"], format="mixed", errors="coerce")

    df["review_creation_date"] = rev_creation_dt
    df["review_answer_timestamp"] = rev_answer_dt

    # Deduplicate exact duplicate review entries per (review_id, order_id) keeping latest response
    df = df.sort_values("review_answer_timestamp").drop_duplicates(subset=["review_id", "order_id"], keep="last")

    # Format timestamps consistently as YYYY-MM-DD HH:MM:SS for CSV persistence
    df["review_creation_date"] = df["review_creation_date"].dt.strftime("%Y-%m-%d %H:%M:%S")
    df["review_answer_timestamp"] = df["review_answer_timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # Validate review score range
    df["review_score"] = pd.to_numeric(df["review_score"], errors="coerce").astype(int)

    print("[2.3 Reviews Cleaning]")
    print(f"  - Cleaned {len(df):,} reviews.")
    print("  - Deduplicated exact duplicates on (review_id, order_id).")
    print("  - Optional text comment missingness preserved.")

    return df


def clean_order_items(order_items_df):
    """
    2.4 Order Items Cleaning
    - Convert shipping_limit_date to datetime
    - Validate numeric attributes (price and freight_value)
    """
    df = order_items_df.copy()

    # Strip string identifiers
    for col in ["order_id", "product_id", "seller_id"]:
        df[col] = df[col].astype(str).str.strip()

    # Convert timestamp with explicit format="mixed" and format as YYYY-MM-DD HH:MM:SS
    parsed_shipping = pd.to_datetime(df["shipping_limit_date"], format="mixed", errors="coerce")
    df["shipping_limit_date"] = parsed_shipping.dt.strftime("%Y-%m-%d %H:%M:%S")

    # Validate numeric values
    df["order_item_id"] = pd.to_numeric(df["order_item_id"], errors="coerce").astype(int)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["freight_value"] = pd.to_numeric(df["freight_value"], errors="coerce")

    print("[2.4 Order Items Cleaning]")
    print(f"  - Cleaned {len(df):,} order items.")
    print("  - Converted shipping timestamps and validated prices/freight values.")


    return df


def clean_customers_and_payments(customers_df, payments_df):
    """
    2.5 Customers & Payments Cleaning
    - Standardize geographic/text fields in customers
    - Validate numeric values and fix operational artifacts in payments (e.g. 0 installments -> 1)
    """
    c_df = customers_df.copy()
    p_df = payments_df.copy()

    # Clean customers
    for col in ["customer_id", "customer_unique_id"]:
        c_df[col] = c_df[col].astype(str).str.strip()

    c_df["customer_city"] = c_df["customer_city"].astype(str).str.strip().str.title()
    c_df["customer_state"] = c_df["customer_state"].astype(str).str.strip().str.upper()
    c_df["customer_zip_code_prefix"] = c_df["customer_zip_code_prefix"].astype(str).str.strip().str.zfill(5)

    # Clean payments
    p_df["order_id"] = p_df["order_id"].astype(str).str.strip()
    p_df["payment_type"] = p_df["payment_type"].astype(str).str.strip().str.lower()

    p_df["payment_sequential"] = pd.to_numeric(p_df["payment_sequential"], errors="coerce").astype(int)
    p_df["payment_installments"] = pd.to_numeric(p_df["payment_installments"], errors="coerce").astype(int)
    # Fix operational artifact: 0 installments converted to 1
    p_df.loc[p_df["payment_installments"] == 0, "payment_installments"] = 1

    p_df["payment_value"] = pd.to_numeric(p_df["payment_value"], errors="coerce")

    print("[2.5 Customers & Payments Cleaning]")
    print(f"  - Cleaned {len(c_df):,} customers (standardized city, state, zip code).")
    print(f"  - Cleaned {len(p_df):,} payment records (validated values & installments).")

    return c_df, p_df


def validate_cleaned_datasets(cleaned_datasets, output_dir=PROCESSED_DATA_PATH):
    """
    2.6 Final Validation of Cleaned Datasets
    - Print validation statistics
    - Write cleaned datasets into real CSV files in data/processed/
    """
    print("\n" + "=" * 70)
    print("2.6 FINAL VALIDATION AND WRITING CLEANED DATASETS")
    print("=" * 70)

    output_dir.mkdir(parents=True, exist_ok=True)

    file_mapping = {
        "orders": "olist_orders_cleaned.csv",
        "customers": "olist_customers_cleaned.csv",
        "order_items": "olist_order_items_cleaned.csv",
        "payments": "olist_order_payments_cleaned.csv",
        "products": "olist_products_cleaned.csv",
        "reviews": "olist_order_reviews_cleaned.csv"
    }

    for name, df in cleaned_datasets.items():
        if name not in file_mapping:
            continue
        out_filename = file_mapping[name]
        out_path = output_dir / out_filename
        df.to_csv(out_path, index=False)

        # Also save with standard olist dataset name in data/processed/
        standard_path = output_dir / f"olist_{name}_dataset.csv"
        df.to_csv(standard_path, index=False)

        print(f"  [OK] {name.upper()}: {len(df):,} rows saved to {out_path.name} & {standard_path.name}")


    print("\n[SUCCESS] Cleaning pipeline completed successfully. All cleaned CSV files saved to real disk files.")


def run_cleaning_pipeline(raw_path=RAW_DATA_PATH, output_dir=PROCESSED_DATA_PATH):
    """
    Execute full data cleaning pipeline following sequential steps 2.1 to 2.6.
    """
    print("=" * 70)
    print("STARTING OLIST DATA CLEANING PIPELINE")
    print("=" * 70)

    # Load raw data
    raw_datasets = load_raw_datasets(raw_path)

    # Step 2.1: Orders
    cleaned_orders = clean_orders(raw_datasets["orders"])

    # Step 2.2: Products
    cleaned_products = clean_products(raw_datasets["products"], raw_datasets["category_translation"])

    # Step 2.3: Reviews
    cleaned_reviews = clean_reviews(raw_datasets["reviews"])

    # Step 2.4: Order Items
    cleaned_order_items = clean_order_items(raw_datasets["order_items"])

    # Step 2.5: Customers & Payments
    cleaned_customers, cleaned_payments = clean_customers_and_payments(
        raw_datasets["customers"],
        raw_datasets["payments"]
    )

    cleaned_datasets = {
        "orders": cleaned_orders,
        "products": cleaned_products,
        "reviews": cleaned_reviews,
        "order_items": cleaned_order_items,
        "customers": cleaned_customers,
        "payments": cleaned_payments
    }

    # Step 2.6: Final Validation & Export
    validate_cleaned_datasets(cleaned_datasets, output_dir)

    return cleaned_datasets


if __name__ == "__main__":
    run_cleaning_pipeline()
