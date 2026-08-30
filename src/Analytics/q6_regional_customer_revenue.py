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
print(f"Executing Q.6 analysis using database: {db_path.resolve()}")

# Define 5 Macro-Regions of Brazil
region_map = {
    'SP': 'Southeast', 'RJ': 'Southeast', 'MG': 'Southeast', 'ES': 'Southeast',
    'PR': 'South', 'RS': 'South', 'SC': 'South',
    'BA': 'Northeast', 'PE': 'Northeast', 'CE': 'Northeast', 'MA': 'Northeast', 
    'PB': 'Northeast', 'AL': 'Northeast', 'PI': 'Northeast', 'RN': 'Northeast', 'SE': 'Northeast',
    'DF': 'Midwest', 'GO': 'Midwest', 'MT': 'Midwest', 'MS': 'Midwest',
    'AM': 'North', 'PA': 'North', 'RO': 'North', 'TO': 'North', 'AC': 'North', 'AP': 'North', 'RR': 'North'
}

# --- STEP 1: Query State-Level Data ---
df_state = pd.read_sql_query("""
SELECT 
    customer_state AS state,
    COUNT(DISTINCT customer_unique_id) AS unique_customers,
    COUNT(order_id) AS total_orders,
    SUM(product_sales_revenue) AS product_revenue,
    SUM(freight_charges) AS total_freight,
    SUM(gross_order_value) AS gross_revenue,
    AVG(gross_order_value) AS aov,
    AVG(freight_charges) AS avg_freight
FROM v_customer_orders
WHERE order_status = 'delivered'
GROUP BY customer_state
ORDER BY gross_revenue DESC;
""", conn)

# Add Region
df_state['region'] = df_state['state'].map(region_map)

# Calculate Totals
total_platform_rev = df_state['gross_revenue'].sum()
total_platform_cust = df_state['unique_customers'].sum()
total_platform_orders = df_state['total_orders'].sum()

df_state['revenue_share_pct'] = (df_state['gross_revenue'] / total_platform_rev) * 100
df_state['customer_share_pct'] = (df_state['unique_customers'] / total_platform_cust) * 100

# --- STEP 2: Aggregate Macro-Region Data ---
df_region = df_state.groupby('region').agg({
    'unique_customers': 'sum',
    'total_orders': 'sum',
    'gross_revenue': 'sum',
    'total_freight': 'sum',
    'aov': 'mean',
    'avg_freight': 'mean'
}).reset_index()

df_region['revenue_share_pct'] = (df_region['gross_revenue'] / total_platform_rev) * 100
df_region['customer_share_pct'] = (df_region['unique_customers'] / total_platform_cust) * 100
df_region['region_aov'] = df_region['gross_revenue'] / df_region['total_orders']
df_region['region_avg_freight'] = df_region['total_freight'] / df_region['total_orders']

df_region = df_region.sort_values(by='gross_revenue', ascending=False).reset_index(drop=True)

print("\n--- BRAZILIAN MACRO-REGION PERFORMANCE SUMMARY ---")
print(df_region[['region', 'unique_customers', 'customer_share_pct', 'total_orders', 'gross_revenue', 'revenue_share_pct', 'region_aov', 'region_avg_freight']].to_string(index=False))

# --- STEP 3: Top 10 States & Top 10 Cities ---
df_city = pd.read_sql_query("""
SELECT 
    customer_city AS city,
    customer_state AS state,
    COUNT(DISTINCT customer_unique_id) AS unique_customers,
    COUNT(order_id) AS total_orders,
    SUM(gross_order_value) AS gross_revenue,
    AVG(gross_order_value) AS aov,
    AVG(freight_charges) AS avg_freight
FROM v_customer_orders
WHERE order_status = 'delivered'
GROUP BY customer_city, customer_state
ORDER BY gross_revenue DESC;
""", conn)

df_city['revenue_share_pct'] = (df_city['gross_revenue'] / total_platform_rev) * 100

print("\n--- TOP 10 STATES BY REVENUE ---")
print(df_state.head(10)[['state', 'region', 'unique_customers', 'customer_share_pct', 'gross_revenue', 'revenue_share_pct', 'aov', 'avg_freight']].to_string(index=False))

print("\n--- TOP 10 CITIES BY REVENUE ---")
print(df_city.head(10)[['city', 'state', 'unique_customers', 'gross_revenue', 'revenue_share_pct', 'aov', 'avg_freight']].to_string(index=False))

# Pareto Summary (SP, RJ, MG)
top_3_states_rev = df_state.head(3)['revenue_share_pct'].sum()
top_3_states_cust = df_state.head(3)['customer_share_pct'].sum()

print("\n--- GEOGRAPHIC CONCENTRATION SUMMARY ---")
print(f"Top 3 States (SP, RJ, MG) Revenue Share: {top_3_states_rev:.2f}%")
print(f"Top 3 States (SP, RJ, MG) Customer Share: {top_3_states_cust:.2f}%")
print(f"Southeast Region Revenue Share: {df_region[df_region['region']=='Southeast']['revenue_share_pct'].values[0]:.2f}%")

# --- STEP 4: Create Visualization ---
img_dir = Path("images")
img_dir.mkdir(exist_ok=True)
img_path = img_dir / "q6_regional_customer_revenue.png"

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.5))

# Plot 1: Macro-Region Revenue & Customer Share Donut / Bar Chart
bars1 = ax1.bar(df_region['region'], df_region['gross_revenue'] / 1e6, color=['#1f77b4', '#2ca02c', '#ff7f0e', '#d62728', '#9467bd'], alpha=0.85)

ax1.set_title("Gross Revenue ($M) by Brazilian Macro-Region", fontsize=13, fontweight='bold', pad=12)
ax1.set_ylabel("Gross Revenue ($ Millions)", fontsize=11)
ax1.set_xlabel("Macro Region", fontsize=11)

for bar, val, share, cust_share in zip(bars1, df_region['gross_revenue'] / 1e6, df_region['revenue_share_pct'], df_region['customer_share_pct']):
    ax1.text(bar.get_x() + bar.get_width()/2, val + 0.2, f'${val:.2f}M\n({share:.1f}% Rev\n{cust_share:.1f}% Cust)', 
             ha='center', va='bottom', fontsize=9, fontweight='bold')

ax1.grid(True, linestyle=':', alpha=0.6)
ax1.set_ylim(0, max(df_region['gross_revenue'] / 1e6) * 1.25)

# Plot 2: Top 10 States by Gross Revenue ($k)
top10_states = df_state.head(10).sort_values(by='gross_revenue', ascending=True)

bars2 = ax2.barh(top10_states['state'], top10_states['gross_revenue'] / 1e3, color='#1f77b4', alpha=0.85)
ax2.set_title("Top 10 Brazilian States by Gross Revenue ($k)", fontsize=13, fontweight='bold', pad=12)
ax2.set_xlabel("Gross Revenue ($k)", fontsize=11)

for bar, val, share in zip(bars2, top10_states['gross_revenue'] / 1e3, top10_states['revenue_share_pct']):
    ax2.text(val + 80, bar.get_y() + bar.get_height()/2, f'${val:,.1f}k ({share:.1f}%)', 
             ha='left', va='center', fontsize=9, fontweight='bold')

ax2.grid(True, linestyle=':', alpha=0.6)
ax2.set_xlim(0, max(top10_states['gross_revenue'] / 1e3) * 1.25)

plt.tight_layout()
plt.savefig(img_path, dpi=200)
plt.close()

print(f"\n[SUCCESS] Analysis complete. Chart saved to {img_path.resolve()}")
conn.close()
