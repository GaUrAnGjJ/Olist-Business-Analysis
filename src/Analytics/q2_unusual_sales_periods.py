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
print(f"Executing Q.2 analysis using database: {db_path.resolve()}")

# --- STEP 1: Query Population & Define Metrics ---
# Weekly Time Series
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

df_weekly['week_start'] = pd.to_datetime(df_weekly['week_start'])

# Daily Time Series to locate exact peak dates
df_daily = pd.read_sql_query("""
SELECT 
    DATE(order_purchase_timestamp) AS date,
    COUNT(order_id) AS order_volume,
    SUM(gross_order_value) AS gross_revenue,
    AVG(gross_order_value) AS aov
FROM v_sales_orders
WHERE order_status = 'delivered' AND order_purchase_timestamp >= '2017-01-09' AND order_purchase_timestamp <= '2018-08-20'
GROUP BY date
ORDER BY date;
""", conn)

df_daily['date'] = pd.to_datetime(df_daily['date'])

# --- STEP 2: Anomaly Detection Metrics ---
# 1. Rolling 8-Week Moving Average & Std Dev (Detrended Z-Score)
df_weekly['ma_8w'] = df_weekly['gross_revenue'].rolling(window=8, center=True, min_periods=4).mean()
df_weekly['std_8w'] = df_weekly['gross_revenue'].rolling(window=8, center=True, min_periods=4).std()
df_weekly['rolling_zscore'] = (df_weekly['gross_revenue'] - df_weekly['ma_8w']) / df_weekly['std_8w']

# 2. Global Z-Score on Revenue
rev_mean = df_weekly['gross_revenue'].mean()
rev_std = df_weekly['gross_revenue'].std()
df_weekly['global_zscore'] = (df_weekly['gross_revenue'] - rev_mean) / rev_std

# 3. Percentage Deviation from 8-Week Moving Average
df_weekly['pct_dev_ma'] = ((df_weekly['gross_revenue'] - df_weekly['ma_8w']) / df_weekly['ma_8w']) * 100

# 4. IQR Rule on Weekly Revenue
q1 = df_weekly['gross_revenue'].quantile(0.25)
q3 = df_weekly['gross_revenue'].quantile(0.75)
iqr = q3 - q1
upper_bound_iqr = q3 + 1.5 * iqr
lower_bound_iqr = q1 - 1.5 * iqr

# Identify Anomalies (|rolling_zscore| > 2.0 or |pct_dev_ma| > 35%)
df_weekly['is_upper_anomaly'] = (df_weekly['rolling_zscore'] > 2.0) | (df_weekly['pct_dev_ma'] > 35.0)
df_weekly['is_lower_anomaly'] = (df_weekly['rolling_zscore'] < -2.0) | (df_weekly['pct_dev_ma'] < -30.0)

# Filter Anomaly Weeks
anomalies_upper = df_weekly[df_weekly['is_upper_anomaly']].copy()
anomalies_lower = df_weekly[df_weekly['is_lower_anomaly']].copy()

print("\n--- UNUSUAL SALES PERIODS DETECTED (WEEKLY) ---")
print("\nUpper Anomalies (Positive Spikes):")
print(anomalies_upper[['week_start', 'order_volume', 'gross_revenue', 'ma_8w', 'pct_dev_ma', 'rolling_zscore']])

print("\nLower Anomalies (Negative Dips):")
print(anomalies_lower[['week_start', 'order_volume', 'gross_revenue', 'ma_8w', 'pct_dev_ma', 'rolling_zscore']])

# Daily Top Spikes and Drops
df_daily['ma_14d'] = df_daily['gross_revenue'].rolling(window=14, center=True, min_periods=7).mean()
df_daily['pct_dev_ma'] = ((df_daily['gross_revenue'] - df_daily['ma_14d']) / df_daily['ma_14d']) * 100

top_daily_spikes = df_daily.sort_values(by='gross_revenue', ascending=False).head(10)
top_daily_drops = df_daily[df_daily['date'] >= '2017-02-01'].sort_values(by='gross_revenue', ascending=True).head(10)

print("\nTop 5 Daily Revenue Spikes:")
print(top_daily_spikes[['date', 'order_volume', 'gross_revenue', 'pct_dev_ma']])

print("\nTop 5 Daily Revenue Drops (Excl. Jan 2017 startup):")
print(top_daily_drops[['date', 'order_volume', 'gross_revenue', 'pct_dev_ma']])

# --- STEP 3: Create Visualization ---
img_dir = Path("images")
img_dir.mkdir(exist_ok=True)
img_path = img_dir / "q2_unusual_sales_periods.png"

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 11), sharex=False)

# Plot 1: Weekly Revenue Time Series with Rolling Trend and Anomaly Markers
ax1.set_title("Olist Weekly Revenue ($) — Anomaly Detection & Unusual Sales Periods", fontsize=14, fontweight='bold', pad=12)
ax1.plot(df_weekly['week_start'], df_weekly['gross_revenue'] / 1e3, color='#1f77b4', linewidth=2.0, label='Weekly Gross Revenue ($k)')
ax1.plot(df_weekly['week_start'], df_weekly['ma_8w'] / 1e3, color='#ff7f0e', linewidth=2.0, linestyle='--', label='8-Week Moving Average Trend ($k)')

# Highlight Upper Anomalies (Spikes)
ax1.scatter(anomalies_upper['week_start'], anomalies_upper['gross_revenue'] / 1e3, color='red', s=100, zorder=5, label='Upper Anomaly / Spike (Z > 2.0)')

# Highlight Lower Anomalies (Dips)
ax1.scatter(anomalies_lower['week_start'], anomalies_lower['gross_revenue'] / 1e3, color='purple', s=100, zorder=5, label='Lower Anomaly / Dip (Z < -2.0)')

# Annotations for Key Events
# 1. Black Friday 2017
bf_row = df_weekly[df_weekly['week_start'] == '2017-11-20']
if not bf_row.empty:
    ax1.annotate('1. Black Friday Spike\n(2017-11-20: $474.6k, +113% vs MA)', 
                 xy=(bf_row['week_start'].values[0], bf_row['gross_revenue'].values[0] / 1e3),
                 xytext=(pd.to_datetime('2017-06-01'), 430),
                 arrowprops=dict(facecolor='red', shrink=0.05, width=1.5, headwidth=7),
                 fontweight='bold', bbox=dict(boxstyle="round,pad=0.4", fc="#ffcccc", ec="red", lw=1.5))

# 2. Brazilian Truck Drivers' Strike May 2018
strike_row = df_weekly[df_weekly['week_start'] == '2018-05-21']
if not strike_row.empty:
    ax1.annotate('2. Truckers\' Strike Dip\n(2018-05-21: $154.0k, -41.4% vs MA)', 
                 xy=(strike_row['week_start'].values[0], strike_row['gross_revenue'].values[0] / 1e3),
                 xytext=(pd.to_datetime('2018-01-01'), 90),
                 arrowprops=dict(facecolor='purple', shrink=0.05, width=1.5, headwidth=7),
                 fontweight='bold', bbox=dict(boxstyle="round,pad=0.4", fc="#e6ccff", ec="purple", lw=1.5))

# 3. Post-Black Friday / Cyber Monday Continuation
post_bf_row = df_weekly[df_weekly['week_start'] == '2017-11-27']
if not post_bf_row.empty:
    ax1.annotate('3. Cyber Monday Continuation\n(2017-11-27: $290.7k)', 
                 xy=(post_bf_row['week_start'].values[0], post_bf_row['gross_revenue'].values[0] / 1e3),
                 xytext=(pd.to_datetime('2017-08-15'), 330),
                 arrowprops=dict(facecolor='orange', shrink=0.05, width=1, headwidth=5),
                 fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="#ffe6cc", ec="orange", lw=1))

ax1.set_ylabel("Gross Revenue ($k)", fontsize=11)
ax1.legend(loc='upper left', frameon=True)
ax1.grid(True, linestyle=':', alpha=0.6)

# Plot 2: Daily Revenue Spikes (Nov 2017 Black Friday Week Detail)
df_bf_daily = df_daily[(df_daily['date'] >= '2017-11-15') & (df_daily['date'] <= '2017-12-05')].copy()

ax2.set_title("Daily Granularity Breakdown: Black Friday 2017 Week Surge (Nov 15 – Dec 05, 2017)", fontsize=13, fontweight='bold', pad=10)
bars = ax2.bar(df_bf_daily['date'].dt.strftime('%b %d'), df_bf_daily['gross_revenue'] / 1e3, color='#1f77b4', alpha=0.85)

# Highlight Black Friday Day (Nov 24, 2017)
for bar, date_str, rev in zip(bars, df_bf_daily['date'].dt.strftime('%b %d'), df_bf_daily['gross_revenue'] / 1e3):
    if date_str == 'Nov 24':
        bar.set_color('red')
        ax2.text(bar.get_x() + bar.get_width()/2, rev + 3, f'Black Friday\n${rev:.1f}k\n(1,141 orders)', 
                 ha='center', va='bottom', fontweight='bold', color='red', fontsize=9)
    elif date_str == 'Nov 23':
        bar.set_color('#ff6666')
        ax2.text(bar.get_x() + bar.get_width()/2, rev + 2, f'Eve\n${rev:.1f}k', ha='center', va='bottom', fontsize=8)
    elif date_str == 'Nov 27':
        bar.set_color('#ff9933')
        ax2.text(bar.get_x() + bar.get_width()/2, rev + 2, f'Cyber Mon\n${rev:.1f}k', ha='center', va='bottom', fontsize=8)

ax2.set_ylabel("Daily Revenue ($k)", fontsize=11)
ax2.set_xlabel("Date (Nov - Dec 2017)", fontsize=11)
ax2.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
plt.savefig(img_path, dpi=200)
plt.close()

print(f"\n[SUCCESS] Analysis complete. Chart saved to {img_path.resolve()}")
conn.close()
