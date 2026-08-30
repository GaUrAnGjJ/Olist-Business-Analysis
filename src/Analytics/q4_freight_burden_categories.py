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
print(f"Executing Q.4 analysis using database: {db_path.resolve()}")

# --- STEP 1: Query Population & Define Metrics ---
df_freight = pd.read_sql_query("""
SELECT 
    soi.product_category_name_english AS category,
    COUNT(DISTINCT soi.order_id) AS distinct_orders,
    COUNT(soi.order_item_id) AS total_items_sold,
    SUM(soi.price) AS total_product_sales,
    SUM(soi.freight_value) AS total_freight_charges,
    SUM(soi.item_total_value) AS gross_category_revenue,
    AVG(soi.price) AS avg_item_price,
    AVG(soi.freight_value) AS avg_item_freight,
    AVG(ds.review_score) AS avg_review_score,
    SUM(CASE WHEN ds.review_score <= 2 THEN 1 ELSE 0 END) * 100.0 / COUNT(ds.review_score) AS detractor_rate_pct
FROM v_sales_order_items soi
LEFT JOIN v_delivery_satisfaction ds ON soi.order_id = ds.order_id
WHERE soi.order_status = 'delivered'
GROUP BY soi.product_category_name_english
HAVING distinct_orders >= 50
ORDER BY total_freight_charges DESC;
""", conn)

# Freight Metrics
df_freight['freight_ratio_pct'] = (df_freight['total_freight_charges'] / df_freight['total_product_sales']) * 100
df_freight['freight_share_gross_pct'] = (df_freight['total_freight_charges'] / df_freight['gross_category_revenue']) * 100

# Top Categories by Relative Freight Burden (Freight Ratio %)
top_relative_freight = df_freight.sort_values(by='freight_ratio_pct', ascending=False).reset_index(drop=True)

# Top Categories by Absolute Freight per Item ($)
top_absolute_freight = df_freight.sort_values(by='avg_item_freight', ascending=False).reset_index(drop=True)

# Lowest Freight Burden (Best Freight Efficiency)
lowest_freight = df_freight.sort_values(by='freight_ratio_pct', ascending=True).reset_index(drop=True)

print("\n--- TOP 10 CATEGORIES BY RELATIVE FREIGHT BURDEN (Freight Ratio %) ---")
print(top_relative_freight.head(10)[['category', 'distinct_orders', 'avg_item_price', 'avg_item_freight', 'freight_ratio_pct', 'avg_review_score', 'detractor_rate_pct']])

print("\n--- TOP 10 CATEGORIES BY ABSOLUTE FREIGHT PER ITEM ($) ---")
print(top_absolute_freight.head(10)[['category', 'distinct_orders', 'avg_item_price', 'avg_item_freight', 'freight_ratio_pct', 'avg_review_score']])

print("\n--- TOP 5 LOWEST FREIGHT BURDEN CATEGORIES (Best Ratio %) ---")
print(lowest_freight.head(5)[['category', 'distinct_orders', 'avg_item_price', 'avg_item_freight', 'freight_ratio_pct', 'avg_review_score']])

# Statistical Correlation between Freight Ratio and Review Score
corr_freight_review = df_freight['freight_ratio_pct'].corr(df_freight['avg_review_score'])
corr_freight_detractor = df_freight['freight_ratio_pct'].corr(df_freight['detractor_rate_pct'])

print(f"\nCorrelation between Freight Ratio (%) and Avg Review Score: {corr_freight_review:.4f}")
print(f"Correlation between Freight Ratio (%) and Detractor Rate (%): {corr_freight_detractor:.4f}")

# --- STEP 2: Create Visualization ---
img_dir = Path("images")
img_dir.mkdir(exist_ok=True)
img_path = img_dir / "q4_freight_burden_categories.png"

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

# Plot 1: Top 10 Categories by Relative Freight Ratio (%)
top10_rel = top_relative_freight.head(10).sort_values(by='freight_ratio_pct', ascending=True)

bars1 = ax1.barh(top10_rel['category'], top10_rel['freight_ratio_pct'], color='#d62728', alpha=0.85)
ax1.set_title("Top 10 Categories by Relative Freight Burden (Freight % of Product Price)", fontsize=12, fontweight='bold', pad=12)
ax1.set_xlabel("Freight Ratio (%) = (Freight / Price) × 100", fontsize=11)

for bar, ratio, price, freight in zip(bars1, top10_rel['freight_ratio_pct'], top10_rel['avg_item_price'], top10_rel['avg_item_freight']):
    ax1.text(ratio + 0.8, bar.get_y() + bar.get_height()/2, f'{ratio:.1f}% (Fr: ${freight:.1f} / P: ${price:.1f})', 
             ha='left', va='center', fontsize=8.5, fontweight='bold')

ax1.grid(True, linestyle=':', alpha=0.6)
ax1.set_xlim(0, max(top10_rel['freight_ratio_pct']) * 1.35)

# Plot 2: Top 10 Categories by Absolute Freight per Item ($)
top10_abs = top_absolute_freight.head(10).sort_values(by='avg_item_freight', ascending=True)

bars2 = ax2.barh(top10_abs['category'], top10_abs['avg_item_freight'], color='#ff7f0e', alpha=0.85)
ax2.set_title("Top 10 Categories by Absolute Freight Cost per Item ($)", fontsize=12, fontweight='bold', pad=12)
ax2.set_xlabel("Average Freight per Item ($)", fontsize=11)

for bar, freight, price in zip(bars2, top10_abs['avg_item_freight'], top10_abs['avg_item_price']):
    ax2.text(freight + 1.2, bar.get_y() + bar.get_height()/2, f'${freight:.2f} (Price: ${price:.1f})', 
             ha='left', va='center', fontsize=8.5, fontweight='bold')

ax2.grid(True, linestyle=':', alpha=0.6)
ax2.set_xlim(0, max(top10_abs['avg_item_freight']) * 1.28)

plt.tight_layout()
plt.savefig(img_path, dpi=200)
plt.close()

print(f"\n[SUCCESS] Analysis complete. Chart saved to {img_path.resolve()}")
conn.close()
