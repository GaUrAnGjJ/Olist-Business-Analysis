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
print(f"Executing Q.7 analysis using database: {db_path.resolve()}")

# Define 5 Macro-Regions of Brazil
region_map = {
    'SP': 'Southeast', 'RJ': 'Southeast', 'MG': 'Southeast', 'ES': 'Southeast',
    'PR': 'South', 'RS': 'South', 'SC': 'South',
    'BA': 'Northeast', 'PE': 'Northeast', 'CE': 'Northeast', 'MA': 'Northeast', 
    'PB': 'Northeast', 'AL': 'Northeast', 'PI': 'Northeast', 'RN': 'Northeast', 'SE': 'Northeast',
    'DF': 'Midwest', 'GO': 'Midwest', 'MT': 'Midwest', 'MS': 'Midwest',
    'AM': 'North', 'PA': 'North', 'RO': 'North', 'TO': 'North', 'AC': 'North', 'AP': 'North', 'RR': 'North'
}

# --- STEP 1: Query Regional Delivery & Satisfaction Data ---
df_del = pd.read_sql_query("""
SELECT 
    co.customer_state AS state,
    ds.order_id,
    ds.delivery_days,
    CAST((JULIANDAY(ds.estimated_delivery_date) - JULIANDAY(ds.purchase_timestamp)) AS REAL) AS estimated_delivery_days,
    ds.delivery_delay_days,
    ds.is_late,
    ds.review_score
FROM v_delivery_satisfaction ds
JOIN v_customer_orders co ON ds.order_id = co.order_id
WHERE ds.order_status = 'delivered' AND ds.delivery_days IS NOT NULL;
""", conn)

# Map State to Region
df_del['region'] = df_del['state'].map(region_map)

# Add Detractor indicator (score <= 2)
df_del['is_detractor'] = df_del['review_score'].apply(lambda x: 1 if x <= 2 else (0 if pd.notnull(x) else np.nan))

# --- STEP 2: Aggregate Macro-Region Performance ---
df_region_perf = df_del.groupby('region').agg(
    total_orders=('order_id', 'count'),
    avg_delivery_days=('delivery_days', 'mean'),
    avg_estimated_days=('estimated_delivery_days', 'mean'),
    late_order_count=('is_late', 'sum'),
    late_delivery_rate_pct=('is_late', lambda x: (x.sum() / len(x)) * 100),
    avg_review_score=('review_score', 'mean'),
    detractor_rate_pct=('is_detractor', lambda x: (x.sum() / len(x)) * 100)
).reset_index()

df_region_perf['est_vs_actual_gap_days'] = df_region_perf['avg_estimated_days'] - df_region_perf['avg_delivery_days']
df_region_perf = df_region_perf.sort_values(by='avg_delivery_days', ascending=True).reset_index(drop=True)

print("\n--- BRAZILIAN MACRO-REGION DELIVERY PERFORMANCE ---")
print(df_region_perf[['region', 'total_orders', 'avg_delivery_days', 'avg_estimated_days', 'est_vs_actual_gap_days', 'late_delivery_rate_pct', 'avg_review_score', 'detractor_rate_pct']].to_string(index=False))

# --- STEP 3: Aggregate State-Level Performance ---
df_state_perf = df_del.groupby(['state', 'region']).agg(
    total_orders=('order_id', 'count'),
    avg_delivery_days=('delivery_days', 'mean'),
    avg_estimated_days=('estimated_delivery_days', 'mean'),
    late_delivery_rate_pct=('is_late', lambda x: (x.sum() / len(x)) * 100),
    avg_review_score=('review_score', 'mean'),
    detractor_rate_pct=('is_detractor', lambda x: (x.sum() / len(x)) * 100)
).reset_index()

df_state_perf['est_vs_actual_gap_days'] = df_state_perf['avg_estimated_days'] - df_state_perf['avg_delivery_days']

print("\n--- TOP 5 FASTEST DELIVERY STATES ---")
print(df_state_perf.sort_values(by='avg_delivery_days', ascending=True).head(5)[['state', 'region', 'total_orders', 'avg_delivery_days', 'late_delivery_rate_pct', 'avg_review_score']].to_string(index=False))

print("\n--- TOP 5 SLOWEST DELIVERY STATES ---")
print(df_state_perf.sort_values(by='avg_delivery_days', ascending=False).head(5)[['state', 'region', 'total_orders', 'avg_delivery_days', 'late_delivery_rate_pct', 'avg_review_score']].to_string(index=False))

print("\n--- TOP 5 HIGHEST LATE DELIVERY RATE STATES ---")
print(df_state_perf.sort_values(by='late_delivery_rate_pct', ascending=False).head(5)[['state', 'region', 'total_orders', 'avg_delivery_days', 'late_delivery_rate_pct', 'avg_review_score']].to_string(index=False))

# Correlation check
corr_duration_review = df_state_perf['avg_delivery_days'].corr(df_state_perf['avg_review_score'])
corr_late_detractor = df_state_perf['late_delivery_rate_pct'].corr(df_state_perf['detractor_rate_pct'])

print(f"\nCorrelation (State Delivery Duration vs Avg Review Score): {corr_duration_review:.4f}")
print(f"Correlation (State Late Delivery Rate % vs Detractor Rate %): {corr_late_detractor:.4f}")

# --- STEP 4: Create Visualization ---
img_dir = Path("images")
img_dir.mkdir(exist_ok=True)
img_path = img_dir / "q7_regional_delivery_performance.png"

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.5))

# Plot 1: Average Delivery Duration by Macro Region (Days)
bars1 = ax1.bar(df_region_perf['region'], df_region_perf['avg_delivery_days'], color=['#2ca02c', '#1f77b4', '#ff7f0e', '#d62728', '#9467bd'], alpha=0.85)

ax1.set_title("Average Delivery Duration (Days) by Macro Region", fontsize=13, fontweight='bold', pad=12)
ax1.set_ylabel("Average Delivery Duration (Days)", fontsize=11)
ax1.set_xlabel("Macro Region", fontsize=11)

for bar, days, est in zip(bars1, df_region_perf['avg_delivery_days'], df_region_perf['avg_estimated_days']):
    ax1.text(bar.get_x() + bar.get_width()/2, days + 0.4, f'{days:.1f} Days\n(Est: {est:.1f}d)', 
             ha='center', va='bottom', fontsize=9, fontweight='bold')

ax1.grid(True, linestyle=':', alpha=0.6)
ax1.set_ylim(0, max(df_region_perf['avg_delivery_days']) * 1.25)

# Plot 2: Late Delivery Rate (%) by Macro Region
df_region_late = df_region_perf.sort_values(by='late_delivery_rate_pct', ascending=False)
bars2 = ax2.bar(df_region_late['region'], df_region_late['late_delivery_rate_pct'], color='#d62728', alpha=0.85)

ax2.set_title("Late Delivery Rate (%) by Macro Region", fontsize=13, fontweight='bold', pad=12)
ax2.set_ylabel("Late Delivery Rate (%)", fontsize=11)
ax2.set_xlabel("Macro Region", fontsize=11)

for bar, rate, score in zip(bars2, df_region_late['late_delivery_rate_pct'], df_region_late['avg_review_score']):
    ax2.text(bar.get_x() + bar.get_width()/2, rate + 0.3, f'{rate:.1f}%\n(Score: {score:.2f}★)', 
             ha='center', va='bottom', fontsize=9, fontweight='bold')

ax2.grid(True, linestyle=':', alpha=0.6)
ax2.set_ylim(0, max(df_region_late['late_delivery_rate_pct']) * 1.28)

plt.tight_layout()
plt.savefig(img_path, dpi=200)
plt.close()

print(f"\n[SUCCESS] Analysis complete. Chart saved to {img_path.resolve()}")
conn.close()
