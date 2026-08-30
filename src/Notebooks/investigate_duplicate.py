import pandas as pd



def get_duplicate_records(df, columns):
    """
    Return all rows involved in duplicate combinations
    based on the specified column(s).
    """
    return (
        df[df.duplicated(subset=columns, keep=False)]
        .sort_values(by=columns)
        .copy()
    )


def duplicate_summary(df, columns):
    """
    Return a summary of duplicate values.
    """
    return (
        df.groupby(columns)
        .size()
        .reset_index(name="count")
        .query("count > 1")
        .sort_values("count", ascending=False)
    )


def investigate_duplicates(df, dataset_name, columns, sample_size=10):
    """
    Investigate duplicate values and print a concise report.
    Returns both duplicate records and duplicate summary.
    """

    duplicate_records = get_duplicate_records(df, columns)
    summary = duplicate_summary(df, columns)

    print("=" * 60)
    print(f"DATASET: {dataset_name.upper()}")
    print(f"DUPLICATE CHECK: {columns}")
    print("-" * 60)
    print(f"Total rows: {len(df):,}")
    print(f"Duplicate groups: {len(summary):,}")
    print(f"Rows involved in duplicates: {len(duplicate_records):,}")

    if duplicate_records.empty:
        print("Status: No duplicates found.")
    else:
        print("\nSample duplicate records:")
        print(duplicate_records.head(sample_size))

    return duplicate_records, summary