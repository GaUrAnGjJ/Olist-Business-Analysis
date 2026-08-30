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
print(f"Executing Q.3 analysis using database: {db_path.resolve()}")

# --- STEP 1: Query Population & Define Metrics ---
df_cat = pd.read_sql_query("""
SELECT 
    product_category_name_english AS category,
    COUNT(DISTINCT order_id) AS distinct_orders,
    COUNT(order_item_id) AS total_items_sold,
    SUM(price) AS product_sales_revenue,
    SUM(freight_value) AS freight_charges,
    SUM(item_total_value) AS gross_category_revenue,
    AVG(price) AS avg_item_price,
    AVG(freight_value) AS avg_item_freight
FROM v_sales_order_items
WHERE order_status = 'delivered'
GROUP BY product_category_name_english
ORDER BY gross_category_revenue DESC;
""", conn)

# Calculate total platform gross revenue & items
total_gross_rev = df_cat['gross_category_revenue'].sum()
total_items = df_cat['total_items_sold'].sum()
total_orders = pd.read_sql_query("SELECT COUNT(order_id) FROM v_sales_orders WHERE order_status = 'delivered';", conn).iloc[0,0]

df_cat['revenue_share_pct'] = (df_cat['gross_category_revenue'] / total_gross_rev) * 100
df_cat['items_share_pct'] = (df_cat['total_items_sold'] / total_items) * 100
df_cat['cum_revenue_share_pct'] = df_cat['revenue_share_pct'].cumsum()

# Category Ranks
df_cat['revenue_rank'] = np.arange(1, len(df_cat) + 1)
df_cat_volume = df_cat.sort_values(by='distinct_orders', ascending=False).reset_index(drop=True)
df_cat_volume['volume_rank'] = np.arange(1, len(df_cat_volume) + 1)

# Merge Ranks
df_merged = df_cat.merge(df_cat_volume[['category', 'volume_rank']], on='category')

print("\n--- TOP 10 CATEGORIES BY GROSS REVENUE ---")
print(df_merged.head(10)[['revenue_rank', 'category', 'distinct_orders', 'gross_category_revenue', 'revenue_share_pct', 'cum_revenue_share_pct', 'avg_item_price', 'volume_rank']])

print("\n--- TOP 10 CATEGORIES BY ORDER VOLUME ---")
print(df_cat_volume.head(10)[['volume_rank', 'category', 'distinct_orders', 'total_items_sold', 'gross_category_revenue', 'avg_item_price']])

# Pareto Summary
top_5_rev_share = df_cat.head(5)['revenue_share_pct'].sum()
top_10_rev_share = df_cat.head(10)['revenue_share_pct'].sum()
top_20_rev_share = df_cat.head(20)['revenue_share_pct'].sum()

print("\n--- REVENUE CONCENTRATION SUMMARY ---")
print(f"Top 5 Categories Revenue Share: {top_5_rev_share:.2f}%")
print(f"Top 10 Categories Revenue Share: {top_10_rev_share:.2f}%")
print(f"Top 20 Categories Revenue Share: {top_20_rev_share:.2f}%")

# High-Price / Niche Categories
df_high_price = df_cat[df_cat['distinct_orders'] >= 50].sort_values(by='avg_item_price', ascending=False).head(5)
print("\n--- TOP HIGH-TICKET CATEGORIES (Min 50 Orders) ---")
print(df_high_price[['category', 'distinct_orders', 'gross_category_revenue', 'avg_item_price']])

# --- STEP 2: Create Visualization ---
img_dir = Path("images")
img_dir.mkdir(exist_ok=True)
img_path = img_dir / "q3_top_categories.png"

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))

# Plot 1: Top 10 Categories by Gross Revenue ($k)
top10_rev = df_cat.head(10).sort_values(by='gross_category_revenue', ascending=True)

bars1 = ax1.barh(top10_rev['category'], top10_rev['gross_category_revenue'] / 1e3, color='#1f77b4', alpha=0.85)
ax1.set_title("Top 10 Product Categories by Gross Revenue ($k)", fontsize=13, fontweight='bold', pad=12)
ax1.set_xlabel("Gross Revenue ($k)", fontsize=11)

for bar, val, share in zip(bars1, top10_rev['gross_category_revenue'] / 1e3, top10_rev['revenue_share_pct']):
    ax1.text(val + 15, bar.get_y() + bar.get_height()/2, f'${val:.1f}k ({share:.1f}%)', 
             ha='left', va='center', fontsize=9, fontweight='bold')

ax1.grid(True, linestyle=':', alpha=0.6)
ax1.set_xlim(0, max(top10_rev['gross_category_revenue'] / 1e3) * 1.25)

# Plot 2: Top 10 Categories by Order Volume (Distinct Orders)
top10_vol = df_cat_volume.head(10).sort_values(by='distinct_orders', ascending=True)

bars2 = ax2.barh(top10_vol['category'], top10_vol['distinct_orders'], color='#2ca02c', alpha=0.85)
ax2.set_title("Top 10 Product Categories by Order Volume (Distinct Orders)", fontsize=13, fontweight='bold', pad=12)
ax2.set_xlabel("Distinct Order Count", fontsize=11)

for bar, val in zip(bars2, top10_vol['distinct_orders']):
    ax2.text(val + 100, bar.get_y() + bar.get_height()/2, f'{val:,} orders', 
             ha='left', va='center', fontsize=9, fontweight='bold')

ax2.grid(True, linestyle=':', alpha=0.6)
ax2.set_xlim(0, max(top10_vol['distinct_orders']) * 1.22)

plt.tight_layout()
plt.savefig(img_path, dpi=200)
plt.close()

print(f"\n[SUCCESS] Analysis complete. Chart saved to {img_path.resolve()}")
conn.close()
