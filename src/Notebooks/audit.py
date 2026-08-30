import pandas as pd
from pathlib import Path
from investigate_duplicate import investigate_duplicates
from data_quality_checks import (
    missing_value_summary,
    investigate_order_timestamp_missingness,
    investigate_uncategorized_products_impact,
    document_review_text_missingness,
    schema_audit,
    display_table_grain_and_relationships,
    check_referential_integrity
)


DATA_PATH = Path("data/raw")



def load_datasets(data_path):
    """Load all datasets and return them as a dictionary."""

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


def check_unique_id(df, dataset_name, id_columns):
    """Check whether candidate key columns are unique and complete."""

    if isinstance(id_columns, str):
        id_columns = [id_columns]

    total_rows = len(df)
    unique_ids = df[id_columns].drop_duplicates().shape[0]
    duplicate_ids = df.duplicated(subset=id_columns).sum()
    missing_ids = df[id_columns].isnull().any(axis=1).sum()

    print("=" * 60)
    print(f"Dataset: {dataset_name}")
    print(f"Candidate Key: {id_columns}")
    print("-" * 60)
    print(f"Total Rows:        {total_rows:,}")
    print(f"Unique ID Records: {unique_ids:,}")
    print(f"Duplicate IDs:     {duplicate_ids:,}")
    print(f"Missing IDs:       {missing_ids:,}")

    status = (
        "Key appears to be unique and complete."
        if duplicate_ids == 0 and missing_ids == 0
        else "Further investigation required."
    )

    print(f"Status: {status}")




def main():
    # Load datasets
    datasets = load_datasets(DATA_PATH)

    # Candidate keys
    dataset_keys = {
        "orders": ["order_id"],
        "customers": ["customer_id"],
        "order_items": ["order_id", "order_item_id"],
        "payments": ["order_id", "payment_sequential"],
        "products": ["product_id"],
        "reviews": ["review_id"],
        "category_translation": ["product_category_name"]
    }

    # ----------------------------------------
    # Candidate Key Audit
    # ----------------------------------------
    for dataset_name, id_columns in dataset_keys.items():

        if id_columns is None:
            print(f"\n{dataset_name.upper()}: No assumed unique key yet.")
            continue

        check_unique_id(
            datasets[dataset_name],
            dataset_name,
            id_columns
        )

    # ----------------------------------------
    # Duplicate Investigation
    # ----------------------------------------
    duplicate_reviews, review_duplicate_summary = investigate_duplicates(
        df=datasets["reviews"],
        dataset_name="reviews",
        columns=["review_id"]
    )

    # ----------------------------------------
    # Missing Value Audit
    # ----------------------------------------
    missing_value_results = {}

    for dataset_name, df in datasets.items():
        missing_value_results[dataset_name] = missing_value_summary(
            df,
            dataset_name
        )

    # ----------------------------------------
    # Targeted Missingness Investigation (Checks A, B, C)
    # ----------------------------------------
    timestamp_breakdown = investigate_order_timestamp_missingness(datasets["orders"])
    product_impact_summary = investigate_uncategorized_products_impact(
        datasets["products"],
        datasets["order_items"]
    )
    review_text_summary = document_review_text_missingness(datasets["reviews"])

    print("\n" + "=" * 60)
    print("MISSING-VALUE AUDIT COMPLETE")
    print("Distinction established: Legitimate business missingness vs data quality problems.")
    print("=" * 60)

    # ----------------------------------------
    # Schema & Data-Type Audit
    # ----------------------------------------
    schema_results = {}

    for dataset_name, df in datasets.items():
        schema_results[dataset_name] = schema_audit(
            df,
            dataset_name
        )

    # ----------------------------------------
    # Table Grain and Relationship Map
    # ----------------------------------------
    grain_map = display_table_grain_and_relationships()

    # ----------------------------------------
    # Cross-Table Referential Integrity Audit
    # ----------------------------------------
    referential_integrity_results = check_referential_integrity(datasets)

    return (
        duplicate_reviews,
        review_duplicate_summary,
        missing_value_results,
        timestamp_breakdown,
        product_impact_summary,
        review_text_summary,
        schema_results,
        grain_map,
        referential_integrity_results
    )


if __name__ == "__main__":
    (
        duplicate_reviews,
        review_duplicate_summary,
        missing_value_results,
        timestamp_breakdown,
        product_impact_summary,
        review_text_summary,
        schema_results,
        grain_map,
        referential_integrity_results
    ) = main()


