import sys
import os
sys.path.insert(0, '.')
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
import json

db_path = Path("database/olist_ecommerce.db")
if not db_path.exists():
    db_path = Path("data/olist_ecommerce.db")

print(f"Connecting to database: {db_path.resolve()}")
conn = sqlite3.connect(db_path)

# Ensure views exist
views = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='view';", conn)['name'].tolist()
print(f"Available views: {views}")

if 'v_sales_orders' not in views:
    from src.Notebooks.create_views import create_all_views
    create_all_views(db_path)

results = {}

# --- 1. SALES & REVENUE PERFORMANCE ---
print("\n--- 1. Sales & Revenue ---")

# Overall Totals
df_totals = pd.read_sql_query("""
SELECT 
    COUNT(order_id) AS total_orders,
    SUM(CASE WHEN order_status = 'delivered' THEN 1 ELSE 0 END) AS delivered_orders,
    SUM(product_sales_revenue) AS total_product_sales,
    SUM(freight_charges) AS total_freight,
    SUM(gross_order_value) AS total_gross_revenue,
    AVG(gross_order_value) AS overall_aov,
    AVG(total_items_count) AS avg_items_per_order
FROM v_sales_orders;
""", conn)
print("Overall Totals:")
print(df_totals)
results['overall_totals'] = df_totals.to_dict(orient='records')[0]

# Monthly Revenue & Order Growth
df_monthly = pd.read_sql_query("""
SELECT 
    strftime('%Y-%m', order_purchase_timestamp) AS year_month,
    COUNT(order_id) AS order_count,
    SUM(gross_order_value) AS monthly_gross_revenue,
    SUM(product_sales_revenue) AS monthly_product_sales,
    SUM(freight_charges) AS monthly_freight,
    AVG(gross_order_value) AS monthly_aov
FROM v_sales_orders
WHERE order_status = 'delivered' AND strftime('%Y-%m', order_purchase_timestamp) IS NOT NULL
GROUP BY year_month
ORDER BY year_month;
""", conn)

df_monthly['mom_revenue_growth_%'] = df_monthly['monthly_gross_revenue'].pct_change() * 100
df_monthly['mom_order_growth_%'] = df_monthly['order_count'].pct_change() * 100
print("\nMonthly Trend (First 5 & Last 5):")
print(df_monthly.head(5))
print(df_monthly.tail(5))
results['monthly_trend'] = df_monthly.to_dict(orient='records')

# Category Performance (Top 10 & Bottom 10)
df_cat = pd.read_sql_query("""
SELECT 
    product_category_name_english AS category,
    COUNT(DISTINCT order_id) AS total_orders,
    COUNT(order_item_id) AS total_items_sold,
    SUM(price) AS category_product_sales,
    SUM(freight_value) AS category_freight,
    SUM(item_total_value) AS category_gross_revenue,
    AVG(price) AS avg_item_price
FROM v_sales_order_items
WHERE order_status = 'delivered'
GROUP BY product_category_name_english
ORDER BY category_gross_revenue DESC;
""", conn)

tot_rev = df_cat['category_gross_revenue'].sum()
df_cat['revenue_share_%'] = (df_cat['category_gross_revenue'] / tot_rev) * 100
print("\nTop 10 Product Categories by Revenue:")
print(df_cat.head(10)[['category', 'total_orders', 'category_gross_revenue', 'revenue_share_%', 'avg_item_price']])
results['top_categories'] = df_cat.head(15).to_dict(orient='records')
results['bottom_categories'] = df_cat.tail(10).to_dict(orient='records')


# --- 2. GEOGRAPHIC PERFORMANCE ---
print("\n--- 2. Geographic Performance ---")

df_state = pd.read_sql_query("""
SELECT 
    customer_state AS state,
    COUNT(order_id) AS total_orders,
    SUM(gross_order_value) AS total_gross_revenue,
    SUM(freight_charges) AS total_freight,
    AVG(gross_order_value) AS state_aov,
    AVG(freight_charges) AS avg_freight_per_order,
    AVG(freight_charges / NULLIF(gross_order_value, 0)) * 100 AS freight_ratio_pct
FROM v_customer_orders
WHERE order_status = 'delivered'
GROUP BY customer_state
ORDER BY total_gross_revenue DESC;
""", conn)

tot_state_rev = df_state['total_gross_revenue'].sum()
df_state['revenue_share_pct'] = (df_state['total_gross_revenue'] / tot_state_rev) * 100
print("\nTop 10 States by Revenue:")
print(df_state.head(10)[['state', 'total_orders', 'total_gross_revenue', 'revenue_share_pct', 'avg_freight_per_order']])
results['state_performance'] = df_state.to_dict(orient='records')

df_city = pd.read_sql_query("""
SELECT 
    customer_city AS city,
    customer_state AS state,
    COUNT(order_id) AS total_orders,
    SUM(gross_order_value) AS total_gross_revenue,
    AVG(gross_order_value) AS city_aov
FROM v_customer_orders
WHERE order_status = 'delivered'
GROUP BY customer_city, customer_state
ORDER BY total_gross_revenue DESC;
""", conn)
print("\nTop 10 Cities by Revenue:")
print(df_city.head(10))
results['top_cities'] = df_city.head(15).to_dict(orient='records')


# --- 3. CUSTOMER ANALYSIS ---
print("\n--- 3. Customer Analysis ---")

# Customer Repeat Behavior
df_cust_freq = pd.read_sql_query("""
SELECT 
    customer_unique_id,
    COUNT(order_id) AS order_count,
    SUM(gross_order_value) AS total_customer_spend
FROM v_customer_orders
WHERE order_status = 'delivered'
GROUP BY customer_unique_id;
""", conn)

total_unique_customers = len(df_cust_freq)
repeat_customers = len(df_cust_freq[df_cust_freq['order_count'] > 1])
single_order_customers = len(df_cust_freq[df_cust_freq['order_count'] == 1])
repeat_rate = (repeat_customers / total_unique_customers) * 100

print(f"Total Unique Customers: {total_unique_customers:,}")
print(f"Single-Order Customers: {single_order_customers:,} ({(single_order_customers/total_unique_customers)*100:.2f}%)")
print(f"Repeat Customers: {repeat_customers:,} ({repeat_rate:.2f}%)")

cust_distribution = df_cust_freq['order_count'].value_counts().reset_index()
cust_distribution.columns = ['order_count', 'customer_count']
cust_distribution['customer_pct'] = (cust_distribution['customer_count'] / total_unique_customers) * 100
print("\nCustomer Order Frequency Distribution:")
print(cust_distribution.head(5))

# Customer Spend Concentration (Pareto Analysis)
df_cust_sorted = df_cust_freq.sort_values(by='total_customer_spend', ascending=False)
total_spend = df_cust_sorted['total_customer_spend'].sum()
df_cust_sorted['cum_spend'] = df_cust_sorted['total_customer_spend'].cumsum()
df_cust_sorted['cum_spend_pct'] = (df_cust_sorted['cum_spend'] / total_spend) * 100
df_cust_sorted['cum_cust_pct'] = (np.arange(1, len(df_cust_sorted) + 1) / total_unique_customers) * 100

top_1_pct_spend = df_cust_sorted[df_cust_sorted['cum_cust_pct'] <= 1.0]['cum_spend_pct'].max()
top_5_pct_spend = df_cust_sorted[df_cust_sorted['cum_cust_pct'] <= 5.0]['cum_spend_pct'].max()
top_10_pct_spend = df_cust_sorted[df_cust_sorted['cum_cust_pct'] <= 10.0]['cum_spend_pct'].max()
top_20_pct_spend = df_cust_sorted[df_cust_sorted['cum_cust_pct'] <= 20.0]['cum_spend_pct'].max()

print(f"Top 1% Customers Spend Share: {top_1_pct_spend:.2f}%")
print(f"Top 5% Customers Spend Share: {top_5_pct_spend:.2f}%")
print(f"Top 10% Customers Spend Share: {top_10_pct_spend:.2f}%")
print(f"Top 20% Customers Spend Share: {top_20_pct_spend:.2f}%")

results['customer_metrics'] = {
    'total_unique_customers': total_unique_customers,
    'single_order_customers': single_order_customers,
    'repeat_customers': repeat_customers,
    'repeat_rate_pct': round(repeat_rate, 2),
    'top_1_pct_spend_pct': round(top_1_pct_spend, 2),
    'top_5_pct_spend_pct': round(top_5_pct_spend, 2),
    'top_10_pct_spend_pct': round(top_10_pct_spend, 2),
    'top_20_pct_spend_pct': round(top_20_pct_spend, 2),
    'order_frequency_distribution': cust_distribution.head(5).to_dict(orient='records')
}


# --- 4. DELIVERY PERFORMANCE ---
print("\n--- 4. Delivery Performance ---")

df_delivery = pd.read_sql_query("""
SELECT 
    COUNT(order_id) AS total_delivered_orders,
    AVG(delivery_days) AS avg_actual_delivery_days,
    AVG(JULIANDAY(estimated_delivery_date) - JULIANDAY(purchase_timestamp)) AS avg_estimated_delivery_days,
    AVG(delivery_delay_days) AS avg_delivery_delay_days,
    SUM(is_late) AS late_order_count,
    AVG(is_late) * 100 AS late_delivery_rate_pct,
    AVG(CASE WHEN is_late = 1 THEN delivery_delay_days ELSE NULL END) AS avg_days_late_for_late_orders
FROM v_delivery_satisfaction
WHERE order_status = 'delivered';
""", conn)

print("Overall Delivery Stats:")
print(df_delivery)
results['delivery_totals'] = df_delivery.to_dict(orient='records')[0]

# State-wise Delivery Performance
df_delivery_state = pd.read_sql_query("""
SELECT 
    customer_state AS state,
    COUNT(order_id) AS total_orders,
    AVG(delivery_days) AS avg_actual_days,
    AVG(JULIANDAY(estimated_delivery_date) - JULIANDAY(purchase_timestamp)) AS avg_estimated_days,
    AVG(is_late) * 100 AS late_rate_pct,
    AVG(CASE WHEN is_late = 1 THEN delivery_delay_days ELSE NULL END) AS avg_delay_when_late,
    AVG(review_score) AS avg_review_score
FROM v_delivery_satisfaction
WHERE order_status = 'delivered'
GROUP BY customer_state
HAVING total_orders >= 100
ORDER BY late_rate_pct DESC;
""", conn)

print("\nTop 5 Worst Delivery States (Highest Late Rate):")
print(df_delivery_state.head(5))
print("\nTop 5 Best Delivery States (Lowest Late Rate):")
print(df_delivery_state.tail(5))
results['state_delivery_worst'] = df_delivery_state.head(10).to_dict(orient='records')
results['state_delivery_best'] = df_delivery_state.tail(10).to_dict(orient='records')


# --- 5. SATISFACTION & REVIEWS ---
print("\n--- 5. Satisfaction & Reviews ---")

# Review Score Distribution
df_review_dist = pd.read_sql_query("""
SELECT 
    review_score,
    COUNT(order_id) AS order_count,
    (COUNT(order_id) * 100.0 / (SELECT COUNT(*) FROM v_delivery_satisfaction WHERE review_score IS NOT NULL)) AS share_pct
FROM v_delivery_satisfaction
WHERE review_score IS NOT NULL
GROUP BY review_score
ORDER BY review_score DESC;
""", conn)

print("Review Score Distribution:")
print(df_review_dist)
results['review_score_distribution'] = df_review_dist.to_dict(orient='records')

# Review Score vs On-time vs Late
df_review_delay = pd.read_sql_query("""
SELECT 
    CASE 
        WHEN is_late = 0 THEN 'On-Time / Early'
        WHEN delivery_delay_days BETWEEN 0.01 AND 3.00 THEN '1-3 Days Late'
        WHEN delivery_delay_days BETWEEN 3.01 AND 7.00 THEN '4-7 Days Late'
        WHEN delivery_delay_days > 7.00 THEN '>7 Days Late'
        ELSE 'Undelivered/Other'
    END AS delay_category,
    COUNT(order_id) AS total_orders,
    AVG(review_score) AS avg_review_score,
    SUM(CASE WHEN review_score <= 2 THEN 1 ELSE 0 END) * 100.0 / COUNT(order_id) AS detractor_rate_pct,
    SUM(CASE WHEN review_score = 5 THEN 1 ELSE 0 END) * 100.0 / COUNT(order_id) AS promoter_rate_pct
FROM v_delivery_satisfaction
WHERE order_status = 'delivered' AND review_score IS NOT NULL
GROUP BY delay_category
ORDER BY avg_review_score DESC;
""", conn)

print("\nReview Score by Delay Category:")
print(df_review_delay)
results['review_by_delay'] = df_review_delay.to_dict(orient='records')

# Category Satisfaction & Late Rate
df_cat_sat = pd.read_sql_query("""
SELECT 
    soi.product_category_name_english AS category,
    COUNT(DISTINCT ds.order_id) AS total_orders,
    AVG(ds.review_score) AS avg_review_score,
    AVG(ds.is_late) * 100 AS late_rate_pct,
    SUM(CASE WHEN ds.review_score <= 2 THEN 1 ELSE 0 END) * 100.0 / COUNT(DISTINCT ds.order_id) AS detractor_rate_pct
FROM v_delivery_satisfaction ds
JOIN v_sales_order_items soi ON ds.order_id = soi.order_id
WHERE ds.order_status = 'delivered' AND ds.review_score IS NOT NULL
GROUP BY category
HAVING total_orders >= 200
ORDER BY avg_review_score ASC;
""", conn)

print("\nBottom 10 Categories by Customer Satisfaction:")
print(df_cat_sat.head(10))
print("\nTop 10 Categories by Customer Satisfaction:")
print(df_cat_sat.tail(10))
results['worst_satisfaction_categories'] = df_cat_sat.head(10).to_dict(orient='records')
results['best_satisfaction_categories'] = df_cat_sat.tail(10).to_dict(orient='records')

with open("data/business_eda_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\n[SUCCESS] Business EDA analysis script completed. Saved to data/business_eda_results.json")
conn.close()
