import pandas as pd


def missing_value_summary(df, dataset_name):
    """
    Generate and print a summary of missing values
    for a given DataFrame.
    """

    total_rows = len(df)

    summary = pd.DataFrame({
        "missing_count": df.isnull().sum(),
        "missing_percentage": (
            df.isnull().sum() / total_rows * 100
        ).round(2)
    })

    # Show only columns containing missing values
    summary = summary[
        summary["missing_count"] > 0
    ].sort_values(
        by="missing_percentage",
        ascending=False
    )

    print("=" * 60)
    print(f"MISSING VALUE AUDIT: {dataset_name.upper()}")
    print("-" * 60)

    if summary.empty:
        print("Status: No missing values found.")
    else:
        print(summary)

    return summary


def investigate_order_timestamp_missingness(orders_df):
    """
    Investigate missing timestamps in the orders dataset against order status.
    Determines whether missing timestamps represent expected business lifecycle states
    (e.g., canceled or processing orders) or actual data quality anomalies.
    """
    timestamp_cols = [
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date"
    ]

    print("\n" + "=" * 60)
    print("TARGETED CHECK A: ORDERS MISSING TIMESTAMPS VS ORDER STATUS")
    print("-" * 60)

    breakdown_list = []
    for col in timestamp_cols:
        missing_mask = orders_df[col].isnull()
        missing_count = missing_mask.sum()
        status_counts = orders_df[missing_mask]["order_status"].value_counts().to_dict()

        delivered_anomalies = status_counts.get("delivered", 0)

        breakdown_list.append({
            "timestamp_column": col,
            "total_missing": missing_count,
            "missing_pct": round(missing_count / len(orders_df) * 100, 2),
            "missing_by_status": status_counts,
            "delivered_anomalies": delivered_anomalies
        })

        print(f"\nTimestamp Field: {col}")
        print(f"Total Missing: {missing_count:,} ({missing_count / len(orders_df) * 100:.2f}%)")
        print("Breakdown by Order Status:")
        for status, count in status_counts.items():
            print(f"  - {status}: {count:,}")
        if delivered_anomalies > 0:
            print(f"  [!] Potential Anomalies ('delivered' status but timestamp missing): {delivered_anomalies:,}")
        else:
            print("  [OK] All missing values explained by non-delivered order lifecycle statuses.")


    return pd.DataFrame(breakdown_list)


def investigate_uncategorized_products_impact(products_df, order_items_df):
    """
    Investigate the impact of missing product categories on order volume and revenue.
    Determines how many products, order items, unique orders, and total revenue
    are associated with uncategorized products.
    """
    print("\n" + "=" * 60)
    print("TARGETED CHECK B: PRODUCTS IMPACT OF MISSING CATEGORIES")
    print("-" * 60)

    total_products = len(products_df)
    uncat_products = products_df[products_df["product_category_name"].isnull()]
    uncat_products_count = len(uncat_products)

    # Merge order items with products to assess operational & financial impact
    merged_items = order_items_df.merge(
        products_df[["product_id", "product_category_name"]],
        on="product_id",
        how="left"
    )

    uncat_items = merged_items[merged_items["product_category_name"].isnull()]

    total_items = len(order_items_df)
    uncat_items_count = len(uncat_items)

    total_orders = order_items_df["order_id"].nunique()
    uncat_orders_count = uncat_items["order_id"].nunique()

    total_revenue = order_items_df["price"].sum()
    uncat_revenue = uncat_items["price"].sum()

    impact_summary = {
        "total_products": total_products,
        "uncategorized_products": uncat_products_count,
        "uncategorized_products_pct": round(uncat_products_count / total_products * 100, 2),
        "total_order_items": total_items,
        "uncategorized_order_items": uncat_items_count,
        "uncategorized_order_items_pct": round(uncat_items_count / total_items * 100, 2),
        "total_orders": total_orders,
        "affected_orders": uncat_orders_count,
        "affected_orders_pct": round(uncat_orders_count / total_orders * 100, 2),
        "total_revenue": round(total_revenue, 2),
        "uncategorized_revenue": round(uncat_revenue, 2),
        "uncategorized_revenue_pct": round(uncat_revenue / total_revenue * 100, 2)
    }

    print(f"Total Products:                  {total_products:,}")
    print(f"Uncategorized Products:          {uncat_products_count:,} ({impact_summary['uncategorized_products_pct']}%)")
    print(f"Affected Order Items:            {uncat_items_count:,} out of {total_items:,} ({impact_summary['uncategorized_order_items_pct']}%)")
    print(f"Affected Unique Orders:          {uncat_orders_count:,} out of {total_orders:,} ({impact_summary['affected_orders_pct']}%)")
    print(f"Total Revenue (Items Price):     R$ {total_revenue:,.2f}")
    print(f"Uncategorized Product Revenue:   R$ {uncat_revenue:,.2f} ({impact_summary['uncategorized_revenue_pct']}%)")
    print(
    f"Conclusion: Uncategorized products account for "
    f"{impact_summary['uncategorized_revenue_pct']}% of total item revenue."
    )

    return impact_summary


def document_review_text_missingness(reviews_df):
    """
    Document missing text fields in the reviews dataset.
    Text analysis is out of scope for this project, so missing comments are documented as optional customer feedback.
    """
    print("\n" + "=" * 60)
    print("TARGETED CHECK C: REVIEWS TEXT-FIELD MISSINGNESS")
    print("-" * 60)

    total_reviews = len(reviews_df)
    missing_title = reviews_df["review_comment_title"].isnull().sum()
    missing_message = reviews_df["review_comment_message"].isnull().sum()
    missing_both = (
        reviews_df["review_comment_title"].isnull() & 
        reviews_df["review_comment_message"].isnull()
    ).sum()

    doc_summary = {
        "total_reviews": total_reviews,
        "missing_comment_title": missing_title,
        "missing_comment_title_pct": round(missing_title / total_reviews * 100, 2),
        "missing_comment_message": missing_message,
        "missing_comment_message_pct": round(missing_message / total_reviews * 100, 2),
        "missing_both_title_and_message": missing_both,
        "missing_both_pct": round(missing_both / total_reviews * 100, 2)
    }

    print(f"Total Reviews:               {total_reviews:,}")
    print(f"Missing Comment Title:       {missing_title:,} ({doc_summary['missing_comment_title_pct']}%)")
    print(f"Missing Comment Message:     {missing_message:,} ({doc_summary['missing_comment_message_pct']}%)")
    print(f"Missing Both Title & Msg:    {missing_both:,} ({doc_summary['missing_both_pct']}%)")
    print("Documented Note: Review text fields are optional for customers who only provide numerical star ratings. "
          "No further text missingness investigation required (Text Analysis is out of scope).")

    return doc_summary


def schema_audit(df, dataset_name):
    """
    Generate a schema summary for a DataFrame.
    Shows column names, data types, non-null counts,
    unique values, and sample values.
    """

    summary = pd.DataFrame({
        "column": df.columns,
        "dtype": df.dtypes.astype(str).values,
        "non_null_count": df.notnull().sum().values,
        "missing_count": df.isnull().sum().values,
        "unique_values": df.nunique(dropna=True).values,
        "sample_value": [
            df[col].dropna().iloc[0]
            if df[col].notna().any()
            else None
            for col in df.columns
        ]
    })

    print("\n" + "=" * 80)
    print(f"SCHEMA AUDIT: {dataset_name.upper()}")
    print("-" * 80)
    print(summary.to_string(index=False))

    return summary


def display_table_grain_and_relationships():
    """
    Display the Table Grain and Relationship Map for all datasets in the Olist project.
    """
    grain_map = pd.DataFrame([
        {
            "Dataset": "orders",
            "Grain / Primary Key": "order_id",
            "Description": "One record per customer order",
            "Foreign Keys": "customer_id -> customers.customer_id",
            "Cardinality": "1:1 with customer record; 1:N with order_items & payments"
        },
        {
            "Dataset": "customers",
            "Grain / Primary Key": "customer_id",
            "Description": "One record per order-customer location snapshot",
            "Foreign Keys": "None (Parent table for orders)",
            "Cardinality": "1:1 with orders (customer_unique_id links repeating customers)"
        },
        {
            "Dataset": "order_items",
            "Grain / Primary Key": "(order_id, order_item_id)",
            "Description": "One record per individual item line in an order",
            "Foreign Keys": "order_id -> orders.order_id, product_id -> products.product_id, seller_id -> sellers",
            "Cardinality": "N:1 with orders; N:1 with products"
        },
        {
            "Dataset": "payments",
            "Grain / Primary Key": "(order_id, payment_sequential)",
            "Description": "One record per payment transaction installment/method",
            "Foreign Keys": "order_id -> orders.order_id",
            "Cardinality": "N:1 with orders"
        },
        {
            "Dataset": "products",
            "Grain / Primary Key": "product_id",
            "Description": "One record per unique product SKU",
            "Foreign Keys": "product_category_name -> category_translation.product_category_name",
            "Cardinality": "1:N with order_items; N:1 with category_translation"
        },
        {
            "Dataset": "reviews",
            "Grain / Primary Key": "review_id (or review_id, order_id)",
            "Description": "One record per customer satisfaction survey response",
            "Foreign Keys": "order_id -> orders.order_id",
            "Cardinality": "N:1 with orders (multiple reviews possible per order)"
        },
        {
            "Dataset": "category_translation",
            "Grain / Primary Key": "product_category_name",
            "Description": "One record per Portuguese to English category translation",
            "Foreign Keys": "None (Parent reference table)",
            "Cardinality": "1:N with products"
        }
    ])

    print("\n" + "=" * 90)
    print("TABLE GRAIN AND RELATIONSHIP MAP")
    print("=" * 90)
    print(grain_map.to_string(index=False))

    return grain_map


def check_referential_integrity(datasets):
    """
    Perform cross-table referential-integrity checks across all datasets.
    Validates foreign key completeness (child FK -> parent PK) and reverse parent completeness.
    """
    print("\n" + "=" * 90)
    print("CROSS-TABLE REFERENTIAL INTEGRITY AUDIT")
    print("=" * 90)

    fk_relationships = [
        {"child": "orders", "fk": "customer_id", "parent": "customers", "pk": "customer_id"},
        {"child": "order_items", "fk": "order_id", "parent": "orders", "pk": "order_id"},
        {"child": "order_items", "fk": "product_id", "parent": "products", "pk": "product_id"},
        {"child": "payments", "fk": "order_id", "parent": "orders", "pk": "order_id"},
        {"child": "reviews", "fk": "order_id", "parent": "orders", "pk": "order_id"},
        {"child": "products", "fk": "product_category_name", "parent": "category_translation", "pk": "product_category_name"}
    ]

    fk_results = []

    for rel in fk_relationships:
        child_df = datasets[rel["child"]]
        parent_df = datasets[rel["parent"]]

        child_fks = child_df[rel["fk"]].dropna()
        parent_pks = set(parent_df[rel["pk"]].dropna())

        orphans = child_fks[~child_fks.isin(parent_pks)]
        orphan_count = len(orphans)
        total_child = len(child_fks)
        orphan_pct = round(orphan_count / total_child * 100, 2) if total_child > 0 else 0.0

        status = "PASS (100% Valid FKs)" if orphan_count == 0 else f"WARNING ({orphan_count} Orphan FKs)"

        fk_results.append({
            "Child Table": rel["child"],
            "FK Column": rel["fk"],
            "Parent Table": rel["parent"],
            "PK Column": rel["pk"],
            "Total Non-Null FKs": total_child,
            "Orphan Count": orphan_count,
            "Orphan Pct (%)": orphan_pct,
            "Status": status
        })

    fk_df = pd.DataFrame(fk_results)
    print("\n1. FOREIGN KEY INTEGRITY CHECKS (Child FK -> Parent PK):")
    print("-" * 90)
    print(fk_df.to_string(index=False))

    # Details for any warnings
    for res in fk_results:
        if res["Orphan Count"] > 0:
            child = res["Child Table"]
            fk = res["FK Column"]
            parent = res["Parent Table"]
            pk = res["PK Column"]
            c_df = datasets[child]
            p_df = datasets[parent]
            missing_vals = set(c_df[fk].dropna()) - set(p_df[pk].dropna())
            print(f"\n[!] Note: {child}.{fk} has {len(missing_vals)} distinct values missing from {parent}.{pk}:")
            print(f"    Missing values: {missing_vals}")

    # Reverse parent completeness checks
    print("\n2. REVERSE PARENT COMPLETENESS CHECKS (Parent PK -> Child FK Existence):")
    print("-" * 90)

    orders_df = datasets["orders"]
    order_ids = set(orders_df["order_id"])

    items_orders = set(datasets["order_items"]["order_id"])
    payments_orders = set(datasets["payments"]["order_id"])
    reviews_orders = set(datasets["reviews"]["order_id"])
    customers_df = datasets["customers"]
    orders_customers = set(orders_df["customer_id"])

    orders_no_items = orders_df[~orders_df["order_id"].isin(items_orders)]
    orders_no_payments = orders_df[~orders_df["order_id"].isin(payments_orders)]
    orders_no_reviews = orders_df[~orders_df["order_id"].isin(reviews_orders)]
    cust_no_orders = len(set(customers_df["customer_id"]) - orders_customers)

    print(f"- Orders without order_items: {len(orders_no_items):,} ({len(orders_no_items)/len(orders_df)*100:.2f}%)")
    if len(orders_no_items) > 0:
        print("  Breakdown by status:", orders_no_items["order_status"].value_counts().to_dict())

    print(f"- Orders without payments:    {len(orders_no_payments):,} ({len(orders_no_payments)/len(orders_df)*100:.2f}%)")
    if len(orders_no_payments) > 0:
        print("  Details:", orders_no_payments[["order_id", "order_status"]].to_dict(orient="records"))

    print(f"- Orders without reviews:     {len(orders_no_reviews):,} ({len(orders_no_reviews)/len(orders_df)*100:.2f}%)")
    print(f"- Customers without orders:   {cust_no_orders:,}")

    return {
        "fk_integrity": fk_df,
        "orders_without_items": len(orders_no_items),
        "orders_without_payments": len(orders_no_payments),
        "orders_without_reviews": len(orders_no_reviews),
        "customers_without_orders": cust_no_orders
    }