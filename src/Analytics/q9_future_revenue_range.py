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
print(f"Executing Q.9 analysis using database: {db_path.resolve()}")

# --- STEP 1: Load Weekly Revenue Dataset ---
df_weekly = pd.read_sql_query("""
SELECT 
    DATE(purchase_timestamp, 'weekday 0', '-6 days') AS week_start,
    SUM(gross_order_value) AS gross_revenue
FROM v_customer_orders
WHERE order_status = 'delivered' AND purchase_timestamp >= '2017-01-09' AND purchase_timestamp <= '2018-08-26'
GROUP BY week_start
ORDER BY week_start ASC;
""", conn)

df_weekly['week_start'] = pd.to_datetime(df_weekly['week_start'])

# Historical metrics (Last 12 weeks baseline)
last_12_weeks = df_weekly.tail(12)
avg_last_12_weeks = last_12_weeks['gross_revenue'].mean()
min_last_12_weeks = last_12_weeks['gross_revenue'].min()
max_last_12_weeks = last_12_weeks['gross_revenue'].max()

print("\n--- RECENT 12-WEEK HISTORICAL REVENUE BASELINE ---")
print(f"Mean Weekly Revenue (Last 12W): ${avg_last_12_weeks:,.2f}")
print(f"Min Weekly Revenue (Last 12W): ${min_last_12_weeks:,.2f}")
print(f"Max Weekly Revenue (Last 12W): ${max_last_12_weeks:,.2f}")

# --- STEP 2: Defined Champion ARIMA(1,1,1) + EnbPI Conformal Forecast ---
forecast_dates = pd.to_datetime(['2018-08-27', '2018-09-03', '2018-09-10', '2018-09-17'])
point_forecasts = [190961.33, 212789.25, 223595.42, 228945.15]
lower_bounds = [118215.41, 140043.33, 150849.51, 156199.23]
upper_bounds = [263707.24, 285535.16, 296341.34, 301691.06]

df_forecast = pd.DataFrame({
    'week_start': forecast_dates,
    'point_forecast': point_forecasts,
    'lower_conformal_95': lower_bounds,
    'upper_conformal_95': upper_bounds
})

df_forecast['interval_width'] = df_forecast['upper_conformal_95'] - df_forecast['lower_conformal_95']

total_point_rev = sum(point_forecasts)
total_lower_rev = sum(lower_bounds)
total_upper_rev = sum(upper_bounds)
avg_weekly_forecast = total_point_rev / 4

print("\n--- 4-WEEK OUT-OF-SAMPLE REVENUE FORECAST SUMMARY ---")
print(df_forecast.to_string(index=False))

print("\n--- CUMULATIVE 4-WEEK FORECAST EXPECTATION ---")
print(f"Expected Cumulative Revenue (Point Estimate): ${total_point_rev:,.2f}")
print(f"Pessimistic 95% Bound (Lower Limit): ${total_lower_rev:,.2f}")
print(f"Optimistic 95% Bound (Upper Limit): ${total_upper_rev:,.2f}")
print(f"Expected Weekly Range: ${avg_weekly_forecast:,.2f}/week (95% CI: ${total_lower_rev/4:,.2f} to ${total_upper_rev/4:,.2f})")

# --- STEP 3: Create Visualization ---
img_dir = Path("images")
img_dir.mkdir(exist_ok=True)
img_path = img_dir / "q9_future_revenue_range.png"

fig, ax = plt.subplots(figsize=(13, 6))

# Plot historical actuals (Last 25 weeks)
df_plot_hist = df_weekly.tail(25)
ax.plot(df_plot_hist['week_start'], df_plot_hist['gross_revenue'] / 1e3, 
        marker='o', color='#1f77b4', linewidth=2, label='Historical Weekly Revenue (Actuals)')

# Plot 4-week forecast point line
ax.plot(df_forecast['week_start'], df_forecast['point_forecast'] / 1e3, 
        marker='s', linestyle='--', color='#d62728', linewidth=2.5, label='ARIMA(1,1,1) Point Forecast')

# Plot 95% Conformal Shaded Region
ax.fill_between(df_forecast['week_start'], 
                df_forecast['lower_conformal_95'] / 1e3, 
                df_forecast['upper_conformal_95'] / 1e3, 
                color='#d62728', alpha=0.2, label='95% Conformal Prediction Interval ($118k - $301k)')

ax.set_title("Olist 4-Week Revenue Forecast Range (ARIMA 1,1,1 + Sequential Conformal Bounds)", 
             fontsize=13, fontweight='bold', pad=12)
ax.set_ylabel("Gross Weekly Revenue ($ Thousands)", fontsize=11)
ax.set_xlabel("ISO Calendar Week Start Date", fontsize=11)

# Annotate forecast values
for idx, row in df_forecast.iterrows():
    ax.annotate(f"${row['point_forecast']/1e3:.1f}k\n[${row['lower_conformal_95']/1e3:.0f}k - ${row['upper_conformal_95']/1e3:.0f}k]", 
                (row['week_start'], row['point_forecast'] / 1e3),
                textcoords="offset points", xytext=(0,12), ha='center', fontsize=8.5, fontweight='bold', color='#d62728')

ax.legend(loc='upper left', frameon=True)
ax.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
plt.savefig(img_path, dpi=200)
plt.close()

print(f"\n[SUCCESS] Analysis complete. Chart saved to {img_path.resolve()}")
conn.close()
