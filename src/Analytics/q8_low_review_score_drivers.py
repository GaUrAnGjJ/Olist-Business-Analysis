import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style
sns.set_theme(style="whitegrid")
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['figure.dpi'] = 150

# Database path
db_path = Path("database/olist_ecommerce.db")
if not db_path.exists():
    db_path = Path("data/olist_ecommerce.db")

conn = sqlite3.connect(db_path)
print(f"Executing Q.8 analysis using database: {db_path.resolve()}")

# --- STEP 1: Query Population & Define Characteristics ---
df_reviews = pd.read_sql_query("""
SELECT 
    ds.order_id,
    ds.review_score,
    ds.delivery_days,
    ds.delivery_delay_days,
    ds.is_late,
    soi.product_category_name_english AS category,
    soi.price,
    soi.freight_value,
    (soi.freight_value / soi.price) * 100 AS freight_ratio_pct
FROM v_delivery_satisfaction ds
LEFT JOIN v_sales_order_items soi ON ds.order_id = soi.order_id
WHERE ds.order_status = 'delivered' AND ds.review_score IS NOT NULL;
""", conn)

# Classify Review Score Cohorts
df_reviews['cohort'] = df_reviews['review_score'].apply(
    lambda x: 'Detractor (1-2 Stars)' if x <= 2 else ('Passive (3 Stars)' if x == 3 else 'Promoter (4-5 Stars)')
)
df_reviews['is_detractor'] = df_reviews['review_score'].apply(lambda x: 1 if x <= 2 else 0)

total_reviews = len(df_reviews)
detractor_count = df_reviews['is_detractor'].sum()
overall_detractor_rate = (detractor_count / total_reviews) * 100

print("\n--- OVERALL REVIEW SCORE DISTRIBUTION ---")
print(f"Total Reviewed Items: {total_reviews:,}")
print(f"Detractors (1-2 Stars): {detractor_count:,} ({overall_detractor_rate:.2f}%)")
print(df_reviews['cohort'].value_counts(normalize=True) * 100)

# --- STEP 2: Characteristics Analysis ---

# 1. Delivery Promptness (On-Time vs Late)
late_perf = df_reviews.groupby('is_late').agg(
    total_items=('order_id', 'count'),
    avg_review_score=('review_score', 'mean'),
    detractors=('is_detractor', 'sum'),
    detractor_rate_pct=('is_detractor', lambda x: (x.sum() / len(x)) * 100)
).reset_index()
late_perf['status'] = late_perf['is_late'].map({0: 'On-Time Delivery', 1: 'Late Delivery'})

print("\n--- DETRACTOR RATE BY DELIVERY PROMPTNESS ---")
print(late_perf[['status', 'total_items', 'avg_review_score', 'detractors', 'detractor_rate_pct']].to_string(index=False))

# 2. Delay Severity Buckets (The "Delay Cliff")
def get_delay_bucket(days):
    if pd.isnull(days) or days <= 0:
        return '0. On-Time (<=0d)'
    elif days <= 3:
        return '1. 1-3 Days Late'
    elif days <= 7:
        return '2. 4-7 Days Late'
    elif days <= 14:
        return '3. 8-14 Days Late'
    else:
        return '4. 15+ Days Late'

df_reviews['delay_bucket'] = df_reviews['delivery_delay_days'].apply(get_delay_bucket)

delay_cliff = df_reviews.groupby('delay_bucket').agg(
    total_items=('order_id', 'count'),
    avg_review_score=('review_score', 'mean'),
    detractor_rate_pct=('is_detractor', lambda x: (x.sum() / len(x)) * 100)
).reset_index()

print("\n--- THE DELIVERY DELAY CLIFF ---")
print(delay_cliff.to_string(index=False))

# 3. Delivery Duration Buckets
def get_duration_bucket(days):
    if pd.isnull(days):
        return 'Unknown'
    elif days <= 7:
        return '1. Fast (<=7d)'
    elif days <= 14:
        return '2. Moderate (8-14d)'
    elif days <= 21:
        return '3. Slow (15-21d)'
    elif days <= 30:
        return '4. Very Slow (22-30d)'
    else:
        return '5. Extreme (30+d)'

df_reviews['duration_bucket'] = df_reviews['delivery_days'].apply(get_duration_bucket)

duration_perf = df_reviews.groupby('duration_bucket').agg(
    total_items=('order_id', 'count'),
    avg_review_score=('review_score', 'mean'),
    detractor_rate_pct=('is_detractor', lambda x: (x.sum() / len(x)) * 100)
).reset_index()

print("\n--- DETRACTOR RATE BY DELIVERY DURATION TIERS ---")
print(duration_perf.to_string(index=False))

# 4. Top 10 Product Categories with Highest Detractor Rate (Min 100 Items)
cat_detractor = df_reviews.groupby('category').filter(lambda x: len(x) >= 100).groupby('category').agg(
    total_items=('order_id', 'count'),
    avg_review_score=('review_score', 'mean'),
    late_rate_pct=('is_late', lambda x: (x.sum() / len(x)) * 100),
    detractor_rate_pct=('is_detractor', lambda x: (x.sum() / len(x)) * 100)
).reset_index().sort_values(by='detractor_rate_pct', ascending=False)

print("\n--- TOP 10 CATEGORIES WITH HIGHEST DETRACTOR RATE (Min 100 items) ---")
print(cat_detractor.head(10)[['category', 'total_items', 'avg_review_score', 'late_rate_pct', 'detractor_rate_pct']].to_string(index=False))

# --- STEP 3: Create Visualization ---
img_dir = Path("images")
img_dir.mkdir(exist_ok=True)
img_path = img_dir / "q8_low_review_score_drivers.png"

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.5))

# Plot 1: The Delivery Delay Cliff (Detractor Rate % by Days Late)
bars1 = ax1.bar(delay_cliff['delay_bucket'], delay_cliff['detractor_rate_pct'], 
                color=['#2ca02c', '#ff7f0e', '#d62728', '#9467bd', '#8c564b'], alpha=0.85)

ax1.set_title("The Delivery Delay Cliff: Detractor Rate (%) vs Days Late", fontsize=13, fontweight='bold', pad=12)
ax1.set_ylabel("Detractor Rate (%) [1-2 Star Reviews]", fontsize=11)
ax1.set_xlabel("Delay Severity Bucket", fontsize=11)
ax1.tick_params(axis='x', rotation=15)

for bar, rate, score in zip(bars1, delay_cliff['detractor_rate_pct'], delay_cliff['avg_review_score']):
    ax1.text(bar.get_x() + bar.get_width()/2, rate + 1.2, f'{rate:.1f}%\n({score:.2f} stars)', 
             ha='center', va='bottom', fontsize=9, fontweight='bold')

ax1.grid(True, linestyle=':', alpha=0.6)
ax1.set_ylim(0, max(delay_cliff['detractor_rate_pct']) * 1.22)

# Plot 2: Top 10 High-Detractor Categories
top10_cat = cat_detractor.head(10).sort_values(by='detractor_rate_pct', ascending=True)

bars2 = ax2.barh(top10_cat['category'], top10_cat['detractor_rate_pct'], color='#d62728', alpha=0.85)
ax2.set_title("Top 10 Categories with Highest Customer Detractor Rate (%)", fontsize=13, fontweight='bold', pad=12)
ax2.set_xlabel("Detractor Rate (%) [1-2 Star Reviews]", fontsize=11)

for bar, rate, score in zip(bars2, top10_cat['detractor_rate_pct'], top10_cat['avg_review_score']):
    ax2.text(rate + 0.5, bar.get_y() + bar.get_height()/2, f'{rate:.1f}% ({score:.2f} stars)', 
             ha='left', va='center', fontsize=8.5, fontweight='bold')

ax2.grid(True, linestyle=':', alpha=0.6)
ax2.set_xlim(0, max(top10_cat['detractor_rate_pct']) * 1.30)

plt.tight_layout()
plt.savefig(img_path, dpi=200)
plt.close()

print(f"\n[SUCCESS] Analysis complete. Chart saved to {img_path.resolve()}")
conn.close()
