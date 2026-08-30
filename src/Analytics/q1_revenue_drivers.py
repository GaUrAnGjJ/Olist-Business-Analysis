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

print(f"Executing Q.1 analysis using database: {db_path.resolve()}")

# --- STEP 1: Query Population & Define Metrics ---
# Population: Delivered orders in v_sales_orders
# Aggregation: Weekly and Monthly time series

df_weekly = pd.read_sql_query("""
SELECT 
    strftime('%Y-%W', order_purchase_timestamp) AS year_week,
    MIN(DATE(order_purchase_timestamp)) AS week_start,
    COUNT(order_id) AS order_volume,
    SUM(gross_order_value) AS gross_revenue,
    AVG(gross_order_value) AS aov
FROM v_sales_orders
WHERE order_status = 'delivered' AND order_purchase_timestamp >= '2017-01-09' AND order_purchase_timestamp <= '2018-08-20'
GROUP BY year_week
ORDER BY week_start;
""", conn)

df_monthly = pd.read_sql_query("""
SELECT 
    strftime('%Y-%m', order_purchase_timestamp) AS year_month,
    COUNT(order_id) AS order_volume,
    SUM(gross_order_value) AS gross_revenue,
    AVG(gross_order_value) AS aov
FROM v_sales_orders
WHERE order_status = 'delivered' AND order_purchase_timestamp >= '2017-01-01' AND order_purchase_timestamp <= '2018-08-31'
GROUP BY year_month
ORDER BY year_month;
""", conn)

# Convert dates
df_weekly['week_start'] = pd.to_datetime(df_weekly['week_start'])

# --- STEP 2: Mathematical Decomposition ---
# Logarithmic decomposition: ln(Revenue) = ln(Volume) + ln(AOV)
df_weekly['ln_rev'] = np.log(df_weekly['gross_revenue'])
df_weekly['ln_vol'] = np.log(df_weekly['order_volume'])
df_weekly['ln_aov'] = np.log(df_weekly['aov'])

df_weekly['d_ln_rev'] = df_weekly['ln_rev'].diff()
df_weekly['d_ln_vol'] = df_weekly['ln_vol'].diff()
df_weekly['d_ln_aov'] = df_weekly['ln_aov'].diff()

# Additive Decomposition of Period-over-Period Revenue Changes
# Delta_R = Delta_N * AOV_{t-1} + Delta_AOV * N_{t-1} + Delta_N * Delta_AOV
df_weekly['rev_change'] = df_weekly['gross_revenue'].diff()
df_weekly['prev_vol'] = df_weekly['order_volume'].shift(1)
df_weekly['prev_aov'] = df_weekly['aov'].shift(1)
df_weekly['d_vol'] = df_weekly['order_volume'].diff()
df_weekly['d_aov'] = df_weekly['aov'].diff()

df_weekly['volume_effect'] = df_weekly['d_vol'] * df_weekly['prev_aov']
df_weekly['aov_effect'] = df_weekly['d_aov'] * df_weekly['prev_vol']
df_weekly['interaction_effect'] = df_weekly['d_vol'] * df_weekly['d_aov']

# Clean diff dataframe (drop first row NaN)
df_clean = df_weekly.dropna().copy()

# Correlations
corr_vol = df_clean['d_ln_rev'].corr(df_clean['d_ln_vol'])
corr_aov = df_clean['d_ln_rev'].corr(df_clean['d_ln_aov'])

# Variance Decomposition of Log Growth Rates
var_rev = np.var(df_clean['d_ln_rev'])
var_vol = np.var(df_clean['d_ln_vol'])
var_aov = np.var(df_clean['d_ln_aov'])
cov_vol_aov = np.cov(df_clean['d_ln_vol'], df_clean['d_ln_aov'])[0, 1]

# Share of Variance Explained
# Var(d_ln_rev) = Var(d_ln_vol) + Var(d_ln_aov) + 2*Cov(vol, aov)
vol_var_share = (var_vol + cov_vol_aov) / var_rev * 100
aov_var_share = (var_aov + cov_vol_aov) / var_rev * 100

# Mean Absolute Contribution to Change
total_abs_vol = df_clean['volume_effect'].abs().sum()
total_abs_aov = df_clean['aov_effect'].abs().sum()
vol_contrib_pct = (total_abs_vol / (total_abs_vol + total_abs_aov)) * 100
aov_contrib_pct = (total_abs_aov / (total_abs_vol + total_abs_aov)) * 100

print("\n--- STATISTICAL RESULTS ---")
print(f"Weekly Revenue vs Order Volume Growth Correlation (r): {corr_vol:.4f}")
print(f"Weekly Revenue vs AOV Growth Correlation (r): {corr_aov:.4f}")
print(f"Log Variance Share Driven by Volume: {vol_var_share:.2f}%")
print(f"Log Variance Share Driven by AOV: {aov_var_share:.2f}%")
print(f"Mean Absolute Change Contribution - Volume Effect: {vol_contrib_pct:.2f}%")
print(f"Mean Absolute Change Contribution - AOV Effect: {aov_contrib_pct:.2f}%")

# Summary Coefficients
aov_min = df_weekly['aov'].min()
aov_max = df_weekly['aov'].max()
aov_mean = df_weekly['aov'].mean()
aov_std = df_weekly['aov'].std()
aov_cv = (aov_std / aov_mean) * 100

vol_min = df_weekly['order_volume'].min()
vol_max = df_weekly['order_volume'].max()
vol_mean = df_weekly['order_volume'].mean()
vol_std = df_weekly['order_volume'].std()
vol_cv = (vol_std / vol_mean) * 100

print(f"\nAOV Summary: Mean=${aov_mean:.2f}, Std=${aov_std:.2f}, CV={aov_cv:.2f}%, Range=[${aov_min:.2f}, ${aov_max:.2f}]")
print(f"Volume Summary: Mean={vol_mean:.1f}, Std={vol_std:.1f}, CV={vol_cv:.2f}%, Range=[{vol_min}, {vol_max}]")

# Save numerical stats for report
summary_stats = {
    'corr_vol': round(corr_vol, 4),
    'corr_aov': round(corr_aov, 4),
    'vol_var_share': round(vol_var_share, 2),
    'aov_var_share': round(aov_var_share, 2),
    'vol_contrib_pct': round(vol_contrib_pct, 2),
    'aov_contrib_pct': round(aov_contrib_pct, 2),
    'aov_mean': round(aov_mean, 2),
    'aov_std': round(aov_std, 2),
    'aov_cv': round(aov_cv, 2),
    'aov_min': round(aov_min, 2),
    'aov_max': round(aov_max, 2),
    'vol_mean': round(vol_mean, 1),
    'vol_std': round(vol_std, 1),
    'vol_cv': round(vol_cv, 2),
    'vol_min': int(vol_min),
    'vol_max': int(vol_max),
}

# --- STEP 3: Create Visualization ---
img_dir = Path("images")
img_dir.mkdir(exist_ok=True)
img_path = img_dir / "q1_revenue_drivers.png"

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

# Plot 1: Revenue, Order Volume, and AOV over time (Normalized / Dual Axis)
color_rev = '#1f77b4'
color_vol = '#2ca02c'
color_aov = '#d62728'

ax1.set_title("Olist Weekly Revenue ($) vs Order Volume (N) and AOV ($)", fontsize=14, fontweight='bold', pad=12)
ax1.plot(df_weekly['week_start'], df_weekly['gross_revenue'] / 1e3, color=color_rev, linewidth=2.5, label='Gross Revenue ($k)')
ax1.plot(df_weekly['week_start'], df_weekly['order_volume'], color=color_vol, linewidth=2.0, linestyle='--', label='Order Volume (Count)')
ax1.set_ylabel("Revenue ($k) / Order Count", fontsize=11)
ax1.legend(loc='upper left', frameon=True)

ax1_twin = ax1.twinx()
ax1_twin.plot(df_weekly['week_start'], df_weekly['aov'], color=color_aov, linewidth=2.0, linestyle=':', label='Average Order Value ($)')
ax1_twin.set_ylabel("AOV ($)", color=color_aov, fontsize=11)
ax1_twin.tick_params(axis='y', labelcolor=color_aov)
ax1_twin.set_ylim(100, 250)
ax1_twin.legend(loc='upper right', frameon=True)
ax1.grid(True, linestyle=':', alpha=0.6)

# Annotate Black Friday Spike
bf_row = df_weekly[df_weekly['week_start'] == '2017-11-20']
if not bf_row.empty:
    bf_date = bf_row['week_start'].values[0]
    bf_rev = bf_row['gross_revenue'].values[0] / 1e3
    ax1.annotate('Black Friday Spike\n($474.6k, 3,008 orders)', xy=(bf_date, bf_rev), xytext=(pd.to_datetime('2017-07-01'), 420),
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=6),
                 fontweight='bold', bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="black", lw=1))

# Plot 2: Additive Contribution Breakdown (Volume Effect vs AOV Effect)
ax2.set_title("Period-over-Period Weekly Revenue Change Breakdown: Volume Effect vs AOV Effect", fontsize=13, fontweight='bold', pad=10)
ax2.bar(df_clean['week_start'], df_clean['volume_effect'] / 1e3, color='#2ca02c', alpha=0.7, label='Volume Effect ($\Delta N \cdot AOV_{t-1}$)', width=5)
ax2.bar(df_clean['week_start'], df_clean['aov_effect'] / 1e3, bottom=df_clean['volume_effect'] / 1e3, color='#d62728', alpha=0.7, label='AOV Effect ($\Delta AOV \cdot N_{t-1}$)', width=5)
ax2.plot(df_clean['week_start'], df_clean['rev_change'] / 1e3, color='black', linewidth=1.5, label='Net Revenue Change ($\Delta R$)')

ax2.set_ylabel("Revenue Change ($k)", fontsize=11)
ax2.set_xlabel("Week Start Date", fontsize=11)
ax2.legend(loc='upper left', frameon=True)
ax2.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
plt.savefig(img_path, dpi=200)
plt.close()

print(f"\n[SUCCESS] Analysis complete. Chart saved to {img_path.resolve()}")

conn.close()
