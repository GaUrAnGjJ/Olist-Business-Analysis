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
print(f"Executing Q.5 analysis using database: {db_path.resolve()}")

# --- STEP 1: Query Population & Customer Order Frequency ---
df_cust_orders = pd.read_sql_query("""
SELECT 
    customer_unique_id,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(gross_order_value) AS total_customer_spend,
    MIN(purchase_timestamp) AS first_order_date,
    MAX(purchase_timestamp) AS last_order_date
FROM v_customer_orders
WHERE order_status = 'delivered'
GROUP BY customer_unique_id;
""", conn)

total_unique_cust = len(df_cust_orders)
single_order_cust = len(df_cust_orders[df_cust_orders['total_orders'] == 1])
repeat_cust = len(df_cust_orders[df_cust_orders['total_orders'] >= 2])

repeat_rate_pct = (repeat_cust / total_unique_cust) * 100
single_rate_pct = (single_order_cust / total_unique_cust) * 100

print("\n--- CUSTOMER RETENTION & REPEAT PURCHASING OVERVIEW ---")
print(f"Total Unique Customers: {total_unique_cust:,}")
print(f"Single-Order Customers (1 Order): {single_order_cust:,} ({single_rate_pct:.2f}%)")
print(f"Repeat Customers (2+ Orders): {repeat_cust:,} ({repeat_rate_pct:.2f}%)")

# Order Frequency Table
freq_dist = df_cust_orders['total_orders'].value_counts().sort_index().reset_index()
freq_dist.columns = ['order_count', 'customer_count']
freq_dist['customer_pct'] = (freq_dist['customer_count'] / total_unique_cust) * 100
freq_dist['cum_customer_pct'] = freq_dist['customer_pct'].cumsum()

print("\n--- ORDER FREQUENCY DISTRIBUTION ---")
print(freq_dist.to_string(index=False))

# --- STEP 2: Repurchase Time Latency (Days Between 1st and 2nd Order) ---
df_repeat_orders = pd.read_sql_query("""
WITH ranked_orders AS (
    SELECT 
        customer_unique_id,
        order_id,
        purchase_timestamp,
        gross_order_value,
        ROW_NUMBER() OVER (PARTITION BY customer_unique_id ORDER BY purchase_timestamp ASC) AS order_seq
    FROM v_customer_orders
    WHERE order_status = 'delivered'
)
SELECT 
    o1.customer_unique_id,
    o1.purchase_timestamp AS order1_time,
    o2.purchase_timestamp AS order2_time,
    o1.gross_order_value AS order1_value,
    o2.gross_order_value AS order2_value,
    CAST((JULIANDAY(o2.purchase_timestamp) - JULIANDAY(o1.purchase_timestamp)) AS REAL) AS days_between_orders
FROM ranked_orders o1
JOIN ranked_orders o2 ON o1.customer_unique_id = o2.customer_unique_id AND o2.order_seq = 2
WHERE o1.order_seq = 1;
""", conn)

mean_latency = df_repeat_orders['days_between_orders'].mean()
median_latency = df_repeat_orders['days_between_orders'].median()
p25_latency = df_repeat_orders['days_between_orders'].quantile(0.25)
p75_latency = df_repeat_orders['days_between_orders'].quantile(0.75)

print("\n--- REPURCHASE LATENCY (DAYS BETWEEN ORDER 1 & ORDER 2) ---")
print(f"Mean Repurchase Latency: {mean_latency:.1f} days")
print(f"Median Repurchase Latency: {median_latency:.1f} days")
print(f"25th Percentile Latency: {p25_latency:.1f} days")
print(f"75th Percentile Latency: {p75_latency:.1f} days")

# --- STEP 3: Category Loyalty vs Cross-Category Purchasing ---
df_category_repeat = pd.read_sql_query("""
WITH ranked_items AS (
    SELECT 
        co.customer_unique_id,
        co.order_id,
        co.purchase_timestamp,
        soi.product_category_name_english AS category,
        DENSE_RANK() OVER (PARTITION BY co.customer_unique_id ORDER BY co.purchase_timestamp ASC) AS order_seq
    FROM v_customer_orders co
    JOIN v_sales_order_items soi ON co.order_id = soi.order_id
    WHERE co.order_status = 'delivered' AND soi.product_category_name_english IS NOT NULL
)
SELECT 
    r1.customer_unique_id,
    r1.category AS cat_order_1,
    r2.category AS cat_order_2,
    CASE WHEN r1.category = r2.category THEN 1 ELSE 0 END AS is_same_category
FROM ranked_items r1
JOIN ranked_items r2 ON r1.customer_unique_id = r2.customer_unique_id AND r2.order_seq = 2
WHERE r1.order_seq = 1;
""", conn)

same_cat_count = df_category_repeat['is_same_category'].sum()
total_cat_repeat = len(df_category_repeat)
same_cat_pct = (same_cat_count / total_cat_repeat) * 100 if total_cat_repeat > 0 else 0
diff_cat_pct = 100.0 - same_cat_pct

print("\n--- REPEAT BUYER CATEGORY BEHAVIOR ---")
print(f"Repeat Buyers Re-ordering in SAME Category: {same_cat_count:,} ({same_cat_pct:.2f}%)")
print(f"Repeat Buyers Cross-ordering in DIFFERENT Categories: {total_cat_repeat - same_cat_count:,} ({diff_cat_pct:.2f}%)")

# --- STEP 4: Spend Contribution ---
single_revenue = df_cust_orders[df_cust_orders['total_orders'] == 1]['total_customer_spend'].sum()
repeat_revenue = df_cust_orders[df_cust_orders['total_orders'] >= 2]['total_customer_spend'].sum()
total_rev = single_revenue + repeat_revenue

print("\n--- REVENUE CONTRIBUTION BY BUYER TYPE ---")
print(f"Single-Order Customer Revenue: ${single_revenue:,.2f} ({(single_revenue/total_rev)*100:.2f}%) | Avg LTV: ${df_cust_orders[df_cust_orders['total_orders']==1]['total_customer_spend'].mean():.2f}")
print(f"Repeat Customer Revenue: ${repeat_revenue:,.2f} ({(repeat_revenue/total_rev)*100:.2f}%) | Avg LTV: ${df_cust_orders[df_cust_orders['total_orders']>=2]['total_customer_spend'].mean():.2f}")

# --- STEP 5: Create Visualization ---
img_dir = Path("images")
img_dir.mkdir(exist_ok=True)
img_path = img_dir / "q5_repeat_purchase_behavior.png"

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

# Plot 1: Order Frequency Bar Chart (Log Scale or Scaled)
bars = ax1.bar(['1 Order\n(97.0%)', '2 Orders\n(2.76%)', '3 Orders\n(0.19%)', '4 Orders\n(0.03%)', '5+ Orders\n(0.02%)'], 
               [90557, 2573, 181, 28, 19], color=['#d62728', '#ff7f0e', '#2ca02c', '#1f77b4', '#9467bd'], alpha=0.85)

ax1.set_title("Olist Customer Order Frequency Distribution (Extreme Churn)", fontsize=13, fontweight='bold', pad=12)
ax1.set_ylabel("Number of Unique Customers (Log Scale)", fontsize=11)
ax1.set_yscale('log')

for bar, count in zip(bars, [90557, 2573, 181, 28, 19]):
    ax1.text(bar.get_x() + bar.get_width()/2, count * 1.25, f'{count:,}', 
             ha='center', va='bottom', fontsize=9.5, fontweight='bold')

ax1.grid(True, linestyle=':', alpha=0.6)

# Plot 2: Repurchase Latency Histogram (Days between 1st & 2nd Order)
sns.histplot(df_repeat_orders['days_between_orders'], bins=30, ax=ax2, color='#1f77b4', kde=True)
ax2.axvline(median_latency, color='red', linestyle='--', linewidth=2, label=f'Median Latency: {median_latency:.0f} Days')
ax2.axvline(mean_latency, color='orange', linestyle=':', linewidth=2, label=f'Mean Latency: {mean_latency:.0f} Days')

ax2.set_title("Repurchase Latency Distribution (Days Between Order 1 & 2)", fontsize=13, fontweight='bold', pad=12)
ax2.set_xlabel("Days Between 1st and 2nd Order", fontsize=11)
ax2.set_ylabel("Number of Repeat Buyers", fontsize=11)
ax2.legend(loc='upper right', frameon=True)
ax2.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
plt.savefig(img_path, dpi=200)
plt.close()

print(f"\n[SUCCESS] Analysis complete. Chart saved to {img_path.resolve()}")
conn.close()
