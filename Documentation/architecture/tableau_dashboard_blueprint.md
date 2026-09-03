# Tableau Dashboard Suite Strategy & Implementation Blueprint
## Olist E-Commerce Diagnostic Analytics & Conformal Revenue Engine

---

## Executive Overview

This document provides the complete end-to-end strategy, specification, and implementation blueprint for building an enterprise-grade Tableau Dashboard Suite for the **Olist E-Commerce Diagnostic Analytics Platform**.

The suite transforms **100,000+ raw marketplace transactions**, diagnostic insights across 9 core business pillars, and advanced **Conformal Revenue Forecasting** into five (5) interactive, decision-centric dashboards tailored for executive leadership, operational managers, logistics heads, and financial planners.

```
       +-------------------------------------------------------------------------+
       |                  Olist Tableau Enterprise Architecture                 |
       +-------------------------------------------------------------------------+
                                           |
    +-------------------+------------------+-------------------+------------------+
    |                   |                  |                   |                  |
+---v-------------+ +---v------------+ +---v-------------+ +---v------------+ +---v-------------+
| 1. Executive    | | 2. Catalog &   | | 3. Logistics &  | | 4. Customer    | | 5. Forecast &   |
|    Revenue      | |    Category    | |    Regional SLA | |    Experience  | |    Conformal    |
|    Command      | |    Analytics   | |    Operations   | |    & Retention | |    Risk Engine  |
+-----------------+ +----------------+ +-----------------+ +----------------+ +-----------------+
```

---

## Dashboard Suite Summary Matrix

| # | Dashboard Name | Primary Target Persona | Core Analytical Focus | Key Business Impact Enabled |
|---|---|---|---|---|
| **1** | **Executive Revenue Command Center** | CEO, COO, VP Commercial | Top-line revenue drivers, order volume vs. AOV dynamics, macro anomaly tracking. | Reallocates 80% marketing budget to volume acquisition; establishes anomaly response protocols. |
| **2** | **Catalog & Category Analytics** | Chief Merchandising Officer, Category Managers | Pareto catalog concentration risk, freight-to-price tax burden per category. | Protects Top 10 revenue-generating categories (62.1% sales); optimizes freight subsidy policies. |
| **3** | **Logistics & Regional SLA Operations** | Chief Logistics Officer, Supply Chain Leads | State-level delivery duration, 3PL SLA bottlenecks, geographic revenue density. | Reduces 2.6x regional delivery speed gap; guides Salvador (BA) regional fulfillment hub setup. |
| **4** | **Customer Experience & Retention** | Head of CX, Customer Support, Marketing | Review score drivers, post-delivery delay cliff, repeat purchase latency & churn. | Mitigates 1-star review spikes past Day 3 delay; triggers 21-day retention campaigns (1.92x LTV). |
| **5** | **Forecasting & Conformal Risk Engine** | CFO, VP FP&A, Treasury | 4-Week out-of-sample revenue forecast, ARIMA(1,1,1) predictions, 95% Conformal EnbPI bounds. | Replaces static budgeting with distribution-free risk bounds ($856.3k target, $565.3k reserve floor). |

---

## Detailed Specifications per Dashboard

---

### Dashboard 1: Executive Revenue Command Center

#### 1. Why We Need It
- **Business Problem**: Leadership requires a single source of truth to monitor macro revenue trajectory, evaluate whether basket size (AOV) or order volume drives top-line growth, and detect revenue spikes/dips caused by external events.
- **Analytical Basis**: Addresses **Q1 (Revenue Drivers)** and **Q2 (Macro Anomalies)**.

#### 2. Business Impact & Decisions Enabled
- **Marketing Capital Allocation**: Proves that order volume drives **98.3% of revenue variation** ($r = +0.983$), while AOV is static ($140–$170, $r = +0.063$). Shift focus from upselling to top-of-funnel acquisition.
- **Operational Risk Mitigation**: Identifies operational bottlenecks from Black Friday surge (+224% revenue spike) and the May 2018 Truckers' Strike (-41.5% drop), establishing pre-promotional capacity planning.

#### 3. Data Sources Required
- **SQL View**: `v_sales_orders` (SQLite database: `data/olist_ecommerce.db`)
- **Processed CSV**: `data/processed/kpi/kpi_monthly_sales_trend_clean.csv`
- **Granularity**: Monthly & Weekly Aggregation.

#### 4. Tableau Visual Layout & Chart Breakdown

| Section / Tile | Chart Type | Dimension / Metric | Business Insight |
|---|---|---|---|
| **Header Scorecard** | KPI Cards | Total Gross Revenue, Total Orders, Gross AOV, Late Delivery Rate | Four decision-critical KPIs provide immediate top-line and service-health context. |
| **Main Visual** | Two Aligned Line Charts (Small Multiples) | Shared X-Axis: Order Month/Week<br>View 1: Order Volume<br>View 2: Gross Revenue | Preserves the temporal trend of both measures without the perceptual ambiguity of a dual-axis chart. |
| **Driver Matrix** | Scatter Plot | X-Axis: Monthly Order Count<br>Y-Axis: Monthly Revenue ($)<br>Color: AOV ($) | Uses position on common scales to expose the strong volume–revenue relationship ($r=0.983$). |
| **Anomaly Tracker** | Time-Series Line Chart with Annotations | X-Axis: Weekly Date<br>Line: Revenue<br>Annotations: Nov 2017 (Black Friday), May 2018 (Strike) | Makes temporal trends and exceptional shocks easy to identify without adding a separate encoding layer. |

#### 5. Tableau Calculated Fields
```sql
-- Monthly AOV
[AOV] = SUM([gross_revenue]) / COUNTD([order_id])

-- Volume Growth MoM
[MoM_Volume_Growth] = (COUNTD([order_id]) - LOOKUP(COUNTD([order_id]), -1)) / LOOKUP(COUNTD([order_id]), -1)

-- Anomaly Flag
[Anomaly_Period_Flag] = IF [order_purchase_timestamp] >= #2017-11-20# AND [order_purchase_timestamp] <= #2017-11-27# THEN "Black Friday"
ELSEIF [order_purchase_timestamp] >= #2018-05-20# AND [order_purchase_timestamp] <= #2018-05-31# THEN "Truckers' Strike"
ELSE "Normal Operations" END
```

---

### Dashboard 2: Catalog & Category Analytics

#### 1. Why We Need It
- **Business Problem**: Product performance skew can create hidden revenue vulnerabilities. Low-priced heavy products suffer from excessive freight costs relative to item price, causing cart abandonment.
- **Analytical Basis**: Addresses **Q3 (Category Pareto Concentration)** and **Q4 (Freight Burden Tax)**.

#### 2. Business Impact & Decisions Enabled
- **Catalog Risk Management**: Reveals heavy Pareto concentration—**14.1% of categories** (10 out of 71) produce **62.1% of revenue** ($9.58M). Enables targeted seller SLAs and inventory protection for core categories (Health & Beauty, Watches, Bed & Bath).
- **Shipping Policy Optimization**: Uncovers low-value categories with high freight tax (e.g., Telephony faces 31.7% freight-to-price ratio). Justifies flat-rate shipping subsidies ($5 flat rate for items < $30) and mandatory flat-pack packaging.

#### 3. Data Sources Required
- **SQL Views**: `v_sales_order_items`, `v_sales_orders`
- **Processed CSV**: `data/processed/kpi/kpi_category_performance.csv`
- **Granularity**: Product Category & Order Item level.

#### 4. Tableau Visual Layout & Chart Breakdown

| Section / Tile | Chart Type | Dimension / Metric | Business Insight |
|---|---|---|---|
| **Top Pareto Visual** | Sorted Bar Chart + Cumulative-Share Line (Coordinated Views) | View 1: Category Revenue ($), sorted descending<br>View 2: Cumulative Revenue % by category rank | Preserves the Pareto story while avoiding a mixed-unit dual-axis chart; the two views can share category selection/highlighting. |
| **Freight Burden Matrix** | Scatter Plot (4 Quadrants) | X-Axis: Avg Item Price ($)<br>Y-Axis: Freight-to-Price Ratio (%)<br>Size: Order Volume | Uses quantitative position and size to pinpoint high-burden categories versus premium categories. |
| **Category Table** | Highlight Table | Metrics: Revenue, Units Sold, Avg Price, Avg Freight, Freight Tax %, 1-Star Review Rate | Supports precise lookup after the overview charts identify categories requiring investigation. |

#### 5. Tableau Calculated Fields
```sql
-- Freight Burden Ratio
[Freight_Tax_Ratio] = SUM([freight_value]) / SUM([price])

-- Top 10 Pareto Classification
[Pareto_Category_Tier] = IF RUNNING_SUM(SUM([price])) / SUM(TOTAL(SUM([price]))) <= 0.621 THEN "Top 10 High Contribution (62.1%)"
ELSE "Long Tail Categories" END
```

---

### Dashboard 3: Logistics & Regional SLA Operations

#### 1. Why We Need It
- **Business Problem**: Logistics in Brazil varies severely by region due to geography and 3PL inefficiencies, creating wide delivery SLA discrepancies and localized customer dissatisfaction.
- **Analytical Basis**: Addresses **Q6 (Regional Customer Revenue)** and **Q7 (Regional Delivery Performance)**.

#### 2. Business Impact & Decisions Enabled
- **Fulfillment Network Expansion**: Documents **2.6x delivery speed disparity** between Southeast (10.8 days) and North (22.6 days). Guides placement of a new regional fulfillment hub in **Salvador (Bahia)** to serve the Northeast market.
- **3PL SLA Enforcement**: Targets state-level bottleneck areas (e.g., Alagoas with 23.9% late delivery rate and Maranhão with 21.4% late rate) for postal carrier re-negotiation or termination.

#### 3. Data Sources Required
- **SQL View**: `v_delivery_satisfaction`, `v_customer_orders`
- **Processed CSV**: `data/processed/cleaning/olist_customers_cleaned.csv`
- **Granularity**: Brazilian State (UF) & Regional level.

#### 4. Tableau Visual Layout & Chart Breakdown

| Section / Tile | Chart Type | Dimension / Metric | Business Insight |
|---|---|---|---|
| **Geographic SLA View** | Filled Map / Choropleth Map | Location: Brazilian States (UF)<br>Color Metric: Late Delivery Rate (%) | Uses spatial position for location and color for an ordered quantitative SLA measure, making regional bottlenecks immediately visible. |
| **Regional Performance** | Small-Multiple Horizontal Bar Charts | Panel 1: Avg Actual Delivery Days vs Estimated Days<br>Panel 2: Late Delivery Rate (%) | Keeps like-with-like quantitative comparisons on aligned axes and avoids combining days and percentages in one grouped chart. |
| **State SLA Matrix** | Scatter Plot | X-Axis: Avg Delivery Distance (km)<br>Y-Axis: Late Delivery Rate (%)<br>Size: Total Orders | Uses common-scale position to investigate whether geographic distance is associated with delivery failures. |

#### 5. Tableau Calculated Fields
```sql
-- Is Delivery Late
[Is_Late_Delivery] = IF [actual_delivery_date] > [estimated_delivery_date] THEN 1 ELSE 0 END

-- Late Delivery Rate %
[Late_Delivery_Rate] = SUM([Is_Late_Delivery]) / COUNT([order_id])

-- Delivery Duration Days
[Delivery_Duration_Days] = DATEDIFF('day', [order_purchase_timestamp], [actual_delivery_date])
```

---

### Dashboard 4: Customer Experience & Retention

#### 1. Why We Need It
- **Business Problem**: Customer acquisition without retention creates a leaking bucket. Delivery delays severely impact customer satisfaction, causing spikes in negative 1-star reviews.
- **Analytical Basis**: Addresses **Q5 (Customer Repeat Retention)** and **Q8 (Low Review Score Drivers & Delay Cliff)**.

#### 2. Business Impact & Decisions Enabled
- **Proactive SLA Interventions**: Discovers the non-linear **3-Day Delay Cliff**—shipping delays past 3 days triple detractor rates from 20.6% to 62.2%. Enables automated trigger of **SMS apologies + $15 discount vouchers on Day 3** of delay before negative reviews are logged.
- **LTV Expansion**: Capitalizes on repeat buyer behavior—repeat buyers yield **1.92x higher LTV** ($308.53 vs $160.73). Guides automated **21-day post-delivery re-engagement campaigns** matching the median repeat purchase latency (29 days).

#### 3. Data Sources Required
- **SQL View**: `v_delivery_satisfaction`, `v_customer_orders`
- **Processed CSV**: `data/processed/cleaning/olist_order_reviews_cleaned.csv`
- **Granularity**: Order Review level & Customer ID level.

#### 4. Tableau Visual Layout & Chart Breakdown

| Section / Tile | Chart Type | Dimension / Metric | Business Insight |
|---|---|---|---|
| **Delay Cliff Visual** | Line Chart | X-Axis: Ordered Delivery Delay Buckets<br>Y-Axis: Detractor Rate (1–2 Star Reviews, %)<br>Optional point labels: sample size | Directly emphasizes the ordered change in detractor rate and makes the Day-3 threshold easy to detect. |
| **Repeat Purchase Latency** | Histogram / Distribution Chart | X-Axis: Days Between Purchases (0-120 days)<br>Y-Axis: Count of Repeat Customers | Appropriate for the distribution task; the bin size should remain explicit and adjustable. |
| **LTV Comparison** | Two Aligned Bar Charts | Panel 1: Average Order Value by Buyer Type<br>Panel 2: Total LTV by Buyer Type | Uses aligned position/length for straightforward comparison and avoids using a bullet chart for a simple categorical comparison. |

#### 5. Tableau Calculated Fields
```sql
-- Delay Bucket
[Delay_Severity_Bucket] = 
IF DATEDIFF('day', [estimated_delivery_date], [actual_delivery_date]) <= 0 THEN "0. On-Time / Early"
ELSEIF DATEDIFF('day', [estimated_delivery_date], [actual_delivery_date]) <= 3 THEN "1. Minor Delay (1-3 Days)"
ELSEIF DATEDIFF('day', [estimated_delivery_date], [actual_delivery_date]) <= 7 THEN "2. Moderate Delay (4-7 Days)"
ELSE "3. Severe Delay (8+ Days)" END

-- Review Detractor Flag (1-2 Stars)
[Is_Detractor] = IF [review_score] <= 2 THEN 1 ELSE 0 END
```

---

### Dashboard 5: Financial Forecasting & Conformal Risk Engine

#### 1. Why We Need It
- **Business Problem**: Financial and inventory planning requires accurate forward-looking revenue estimates along with reliable, distribution-free uncertainty intervals to manage downside risk.
- **Analytical Basis**: Addresses **Q9 (Future Revenue Range & Conformal Forecasting)**.

#### 2. Business Impact & Decisions Enabled
- **Calibrated Financial Planning**: Integrates **ARIMA(1,1,1)** point forecasts with **Sequential Conformal Prediction (EnbPI)** bounds. Establishes a 4-week cumulative revenue expectation of **$856.3k** while enforcing financial liquidity reserves for the pessimistic **$565.3k floor**.
- **Model Transparency**: Compares out-of-sample performance across baseline, classical time-series, and ML models, demonstrating why ARIMA(1,1,1) was selected (lowest MAE of $41.5k).

#### 3. Data Sources Required
- **Processed CSVs**:
  - `data/processed/forecast/future_4week_conformal_forecast.csv`
  - `data/processed/forecast/weekly_forecasting_data.csv`
  - `data/processed/forecast/model_comparison_summary.csv`
- **Granularity**: Weekly Time Series (85 historical weeks + 4 forecast weeks).

#### 4. Tableau Visual Layout & Chart Breakdown

| Section / Tile | Chart Type | Dimension / Metric | Business Insight |
|---|---|---|---|
| **Main Forecast Visual** | Time-Series Line + Prediction Band | X-Axis: ISO Week<br>Line: Historical Revenue + Point Forecast<br>Shaded Area: 95% Conformal Lower/Upper Bounds | Preserves temporal ordering while showing the forecast distribution directly around the point prediction. |
| **Model Leaderboard** | Horizontal Bar Chart | X-Axis: Out-of-Sample MAE ($) or MAPE (%)<br>Y-Axis: Model, sorted best-to-worst<br>Use separate views for materially different metrics | Uses position/length on a common scale for accurate model ranking instead of encoding multiple metrics in one crowded chart. |
| **Conformal Efficiency** | Side-by-Side Bar Chart | X-Axis: Interval Method<br>Y-Axis: Mean Interval Width ($)<br>Bars: Parametric Gaussian vs EnbPI Conformal | Directly compares interval width and makes the 26.4% reduction easy to quantify. |

#### 5. Tableau Calculated Fields
```sql
-- Forecast Target Type
[Data_Segment] = IF [week_date] <= #2018-08-20# THEN "Historical Actuals"
ELSE "4-Week Conformal Forecast" END

-- Upper Conformal Band Gap
[Conformal_Band_Width] = [conformal_upper_95] - [conformal_lower_95]
```

---

## Visualization Design Principles Applied

The chart choices above follow the task-first and perceptual principles from Tamara Munzner's *Visualization Analysis & Design* teaching slides. Quantitative comparisons favor aligned spatial position and length; temporal trends use line charts; correlation uses scatterplots; spatial questions use maps; distributions use histograms; and complex views are simplified with filtering, aggregation, faceting, or coordinated views. The design also avoids unnecessary dual-axis charts because they can be easy to misread, and avoids radar-style displays for non-cyclic data. fileciteturn27file2L374-L395 fileciteturn27file6L1138-L1153 fileciteturn27file0L98-L105 fileciteturn27file8L1361-L1366

The dashboard should therefore prioritize **comparison, trend detection, lookup, and geographic localization** over decorative chart variety. Small multiples and coordinated views are used where measures have incompatible units or where separating views improves comparison accuracy. fileciteturn27file4L760-L797

---

## Data Architecture & Schema Mapping in Tableau

```
+-----------------------------------------------------------------------------------+
|                            TABLEAU DATA ARCHITECTURE                               |
+-----------------------------------------------------------------------------------+
                                          |
          +-------------------------------+-------------------------------+
          |                                                               |
+---------v-----------------------+                     +-----------------v-----------------+
| SQLite Live/Extract Data Source |                     | Processed CSV Data Extracts       |
| (olist_ecommerce.db)            |                     | (data/processed/forecast & kpi)   |
+---------------------------------+                     +-----------------------------------+
  | Views:                                                | Files:
  |  - v_sales_orders (Order KPIs)                        |  - future_4week_conformal_forecast
  |  - v_sales_order_items (Category KPIs)                |  - weekly_forecasting_data
  |  - v_customer_orders (RFM & LTV)                      |  - kpi_category_performance
  |  - v_delivery_satisfaction (SLA/Reviews)              |  - kpi_monthly_sales_trend_clean
```

### Data Modeling Guidelines in Tableau
1. **Use Logical Relationships (Tableau Data Model)**: Avoid physical SQL joins between order-level and item-level views to prevent **data fan-out** and duplicate revenue counting. Relate `v_sales_orders` to `v_sales_order_items` on `order_id`.
2. **Data Extract Strategy**: Create `.hyper` extracts for maximum performance. Schedule daily automated extract refreshes via Tableau Server / Tableau Cloud bridge.

---

## Visual Design System & Styling Guidelines

### Color Palette Architecture
- **Primary Dark Theme Accent**: Deep Navy (`#1E293B`) for cards and headers.
- **Revenue & Positive Growth**: Emerald Green (`#059669`).
- **Logistics Bottleneck / Late SLA**: Coral Crimson (`#DC2626`).
- **Conformal Interval Uncertainty Shading**: Soft Ice Blue (`#93C5FD`) with 30% opacity.
- **Top 10 Pareto Categories**: Indigo Blue (`#4F46E5`).

### Typography & Grid Layout
- **Font Family**: Inter, Roboto, or Arial (Clean Sans-Serif).
- **Dashboard Size**: Fixed Desktop Width (`1440px x 900px`) for optimal executive display.
- **Containers**: Use tiled layout containers with 8px inner padding and soft shadow borders for a polished SaaS dashboard aesthetic.

---

## Expected Business ROI & Summary

By deploying this Tableau Dashboard Suite, Olist executive and operational teams gain:
1. **Top-line Focus**: Clear evidence to align marketing spend with order acquisition.
2. **Logistics Optimization**: Precise regional SLA visibility to guide the Salvador fulfillment center expansion and 3PL carrier remediation.
3. **Retention Uplift**: Automated delivery delay triggers to prevent 1-star reviews and structured retention campaigns targeting a 1.92x LTV boost.
4. **Calibrated Financial Risk Control**: Probabilistic forecast bounds for confident capital allocation and inventory management.
