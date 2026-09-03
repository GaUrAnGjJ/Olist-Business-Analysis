# Executive Business EDA & Diagnostic Master Summary

## Executive Overview

This master summary synthesizes the empirical diagnostic insights, statistical validation, dataset lineage, and operational recommendations across all **9 Business Questions (Q.1 through Q.9)** conducted on the Olist e-commerce database. The analyses follow the rigorous **Question $\to$ Definition $\to$ Metric $\to$ Analysis $\to$ Validation $\to$ Visualization** protocol, bridging baseline data diagnostics with strategic executive decision-making.

---

## Comprehensive 9-Question Executive Matrix

| # | Business Question | Key Empirical Finding | Empirical Evidence (Metrics & Trends) | Dataset Evidence (SQL Views & Sample Counts) | Strategic Business Action Required |
| :-: | :--- | :--- | :--- | :--- | :--- |
| **Q.1** | **What drives changes in revenue: order volume or AOV?** | **Order volume is the primary revenue engine ($r = +0.983$)**, while Average Order Value (AOV) remains static ($r = +0.063$). | Order volume correlation: **$r = 0.983$ ($p < 0.001$)** vs. AOV correlation: **$r = 0.063$**. Order volume grew +500% while AOV stayed flat ($140–$170). | **`v_customer_orders`** (99,441 delivered orders over 85 ISO weeks). Order volume expanded from 200 to 1,842 orders/week. | **Focus top-of-funnel marketing on acquiring transaction volume** and new buyer traffic rather than forcing cart upsells. |
| **Q.2** | **Which periods demonstrate unusual sales behavior?** | **Two major macro anomalies**: Black Friday 2017 (+224% revenue spike) and the May 2018 Truck Drivers' Strike (-41.5% revenue drop). | Black Friday week (`2017-11-20`): **$474.6k revenue** (vs $146k baseline). Truckers' strike week (`2018-05-21`): **$154.0k revenue** (vs $263k baseline). | **`v_customer_orders`** filtered by timestamp. Black Friday week = 7,333 orders ($474,623.65); Strike week = 2,431 orders ($154,018.75). | **Implement pre-holiday promotional smoothing** to prevent server/logistics crashes, and establish multi-modal air/3PL redundancy. |
| **Q.3** | **Which categories generate the most revenue and orders?** | **Pareto Concentration**: **14.1% of product categories** (10 out of 71) generate **62.1% of total revenue ($9.58M)**. | Top 3 categories (`health_beauty` $1.26M, `watches_gifts` $1.21M, `bed_bath_table` $1.04M) produce **22.7% of total revenue**. | **`v_sales_order_items`** (112,650 items across 71 categories). `health_beauty` = 9,670 items; `watches_gifts` = 5,991 items; `bed_bath_table` = 11,115 items. | **Protect Top 10 category inventory** via priority seller onboarding incentives and strict SLA enforcement for top sellers. |
| **Q.4** | **Which categories have the highest freight burden?** | **Dual Freight Friction**: Bulky goods have high dollar freight ($40.42), while low-price consumables carry a **31.7% freight-to-price tax**. | Freight ranges from $10.50 (`telephony`) to **$40.42 (`office_furniture`)**. Low-cost categories face **31.7%–34.2% relative freight burden**. | **`v_sales_order_items`** joined with `olist_order_items_dataset`. `office_furniture` = 1,654 items ($40.42 freight); `telephony` = 4,545 items ($10.50 freight / $33.12 price). | **Implement flat-rate shipping subsidies** for items < $30 and mandate flat-pack packaging standards for bulky furniture. |
| **Q.5** | **What does repeat-purchase behavior look like?** | **Structural Customer Churn**: **97.00% single-order buyers**. However, repeat buyers yield a **1.92× LTV multiplier** ($308.53 vs $160.73). | **90,557 out of 93,358 customers bought only once**. Median repurchase latency is **29.0 days**. 52.4% repeat in the same category. | **`v_customer_orders`** aggregated over 93,358 `customer_unique_id` records. Single-order = 90,557 buyers; Repeat (2+ orders) = 2,801 buyers (5,801 total orders). | **Deploy automated 21-day post-purchase re-engagement campaigns** with a $10 coupon to capture buyers at the 29-day latency peak. |
| **Q.6** | **Which regions contribute the most customers and revenue?** | **Geographic Core vs. Perimeter**: Southeast generates **64.6% of revenue ($9.96M)**. Remote buyers pay 2× freight and place 48% higher AOV. | Top 3 states (SP, RJ, MG) represent **62.54% of revenue**. North/NE freight is **$36–$41** (vs $19.84 SE), driving **$223 AOV** in North vs $150 SE. | **`v_customer_orders`** joined with `olist_customers_dataset`. SP state = 41,746 buyers ($5.77M); RJ state = 12,852 buyers ($2.06M); MG state = 11,635 buyers ($1.82M). | **Build primary fulfillment centers (FBA)** in SP/RJ for core demand, and offer tiered freight discounts for high-basket NE/North orders. |
| **Q.7** | **How does delivery performance vary across regions?** | **Logistics Asymmetry & Northeast Delay**: 2.6× duration gap between SE (10.8d) and North (22.6d). Northeast has **14.3% late delivery rate**. | Delivery duration: SE 10.75d vs North 22.59d. State extremes: SP (8.76d, 5.89% late) vs AL (**23.93% late rate**, 3.85 ★ score). | **`v_delivery_satisfaction`** (96,478 delivered orders). SE region = 65,920 orders (10.75d avg); North region = 1,845 orders (22.59d avg); AL state = 413 orders (23.93% late). | **Audit and replace failing 3PL postal carriers** in Northeast (AL, MA, PI, CE) and establish a regional distribution hub in Salvador (BA). |
| **Q.8** | **What characteristics are associated with low review scores?** | **Late delivery multiplies detractor risk by 4.8×**. Dissatisfaction hits a non-linear **3-Day Delay Cliff** (tripling 1-star reviews). | On-time detractor rate: 11.36% vs **Late: 54.60%**. 1–3 days late = 20.6% detractors $\to$ **4–7 days late = 62.2% detractors** (2.28 ★). | **`v_delivery_satisfaction`** joined with `olist_order_reviews_dataset` (109,370 item reviews). On-time = 100,843 items; 4–7d late = 1,973 items; 8–14d late = 1,925 items. | **Automate "Day 3 Delay Interventions"**: Send proactive SMS apologies + $15 gift vouchers on Day 3 of delay before reviews are posted. |
| **Q.9** | **What revenue range should the business expect in the coming weeks?** | **Stabilized Revenue Run-Rate**: Champion ARIMA(1,1,1) projects **$856.3k cumulative 4-week revenue** ($214.1k/week avg). | 95% Conformal Prediction Range: **[$565.3k to $1.15M cumulative]** (Weekly bounds: **$141.3k to $286.8k/week**). MAE = $41,585.71. | **`v_customer_orders`** aggregated over 85 historical weeks (`2017-01-09` to `2018-08-20`). 4-week forecast window (Weeks 86–89: `2018-08-27` to `2018-09-17`). | **Budget operational expenses against the $856.3k target**, while maintaining a cash reserve buffer matching the **$565.3k floor**. |

---

## Detailed Question-by-Question Deep Dive

### Q.1: Revenue Drivers — Order Volume vs. AOV
- **Business Question**: What drives changes in revenue: order volume or Average Order Value (AOV)?
- **Key Finding**: Revenue growth is overwhelmingly driven by **order volume expansion** ($r = +0.983$), while AOV remains remarkably stable ($r = +0.063$). E-commerce top-line scaling is a customer transaction volume game.
- **Empirical Evidence**:
  - Pearson Correlation: $\text{Volume vs. Revenue } r = +0.983$ ($p = 1.42 \times 10^{-62}$); $\text{AOV vs. Revenue } r = +0.063$ ($p = 0.567$).
  - Weekly order volume expanded from 200 orders/week (Jan 2017) to > 1,800 orders/week (mid-2018), while AOV stayed flat within the $140–$170 band.
- **Dataset Evidence**:
  - View queried: `v_customer_orders` over 99,441 delivered orders aggregated into 85 continuous ISO calendar weeks (`2017-01-09` to `2018-08-20`).
- **Business Action Required**:
  - Direct 80% of marketing acquisition budget toward top-of-funnel user acquisition rather than complex basket-building cross-sell incentives.

---

### Q.2: Anomaly Detection — Black Friday & Truckers' Strike
- **Business Question**: Which periods demonstrate unusual sales behavior?
- **Key Finding**: Identified two macro anomaly events that created severe revenue spikes and structural supply chain collapses.
- **Empirical Evidence**:
  - **Black Friday Surge (`2017-11-20`)**: Gross revenue spiked to **$474,623.65** (+224.2% above pre-holiday baseline of $146.4k/week), causing order processing backlogs.
  - **Brazilian Truck Drivers' Strike (`2018-05-21`)**: Gross revenue collapsed to **$154,018.75** (-41.5% below prior week baseline of $263.2k), causing nationwide fulfillment halts.
- **Dataset Evidence**:
  - Table/View queried: `v_customer_orders` filtered by `order_purchase_timestamp`. Black Friday week (`2017-11-20`) recorded 7,333 delivered orders ($474,623.65 revenue); Strike week (`2018-05-21`) dropped to 2,431 delivered orders ($154,018.75 revenue).
- **Business Action Required**:
  - **Black Friday Preparation**: Implement pre-holiday deal smoothing (e.g. "Black November") to spread order processing loads across 3 weeks.
  - **Logistics Resilience**: Establish contracts with secondary regional air-freight couriers to maintain operations during highway blockades.

---

### Q.3: Catalog Concentration — Top Revenue & Volume Categories
- **Business Question**: Which categories generate the most revenue and orders?
- **Key Finding**: Olist exhibits heavy Pareto concentration: **14.1% of categories (10 out of 71) account for 62.1% of gross revenue** ($9.58M) and 58.7% of order volume.
- **Empirical Evidence**:
  - Top 3 Categories: `health_beauty` ($1.26M, 8.16% share), `watches_gifts` ($1.21M, 7.82% share), `bed_bath_table` ($1.04M, 6.72% share).
  - Bottom 35 categories combined generate less than 5% of gross revenue.
- **Dataset Evidence**:
  - View queried: `v_sales_order_items` comprising 112,650 items across 71 categories. `health_beauty` (9,670 items), `watches_gifts` (5,991 items), `bed_bath_table` (11,115 items).
- **Business Action Required**:
  - **Catalog Protection**: Implement strict seller SLA monitoring for the Top 10 categories to ensure zero stock-outs.
  - **Long-Tail Rationalization**: Offboard non-performing sellers in long-tail categories with high return rates.

---

### Q.4: Freight Friction — High-Burden Categories
- **Business Question**: Which categories have the highest freight burden?
- **Key Finding**: Freight burden exhibits a duality between **Bulky Freight Goods** (high absolute dollar cost) and **Low-Price Consumables** (high relative price ratio).
- **Empirical Evidence**:
  - **Bulky Category Leader**: `office_furniture` averages **$40.42 freight per order** (27.2% of product price).
  - **Low-Price Consumable Leaders**: `telephony` (31.7% freight ratio), `stationery` (28.5% freight ratio), `baby` (24.8% freight ratio). Shipping costs over 25% act as a "checkout tax" driving cart abandonment.
- **Dataset Evidence**:
  - View/Table queried: `v_sales_order_items` joined with `olist_order_items_dataset`. `office_furniture` (1,654 items, average product price $148.60 vs average freight $40.42); `telephony` (4,545 items, average product price $33.12 vs average freight $10.50).
- **Business Action Required**:
  - **Consumable Subsidies**: Introduce flat-rate $5 shipping subsidies for items under $30.
  - **Packaging Optimization**: Mandate flat-pack packaging standards for bulky furniture sellers to cut volumetric freight weight by 20%.

---

### Q.5: Customer Retention — Repeat-Purchase Behavior
- **Business Question**: What does repeat-purchase behavior look like?
- **Key Finding**: Extreme customer retention failure: **97.00% of customers purchase only once**. However, repeat buyers generate nearly **double the lifetime value** ($308.53 LTV vs $160.73 single-order LTV).
- **Empirical Evidence**:
  - Single-order buyers: **90,557 (97.00%)**, generating $14.56M (94.4% of revenue).
  - Repeat buyers (2+ orders): **2,801 (3.00%)**, generating $864.2k (5.6% of revenue).
  - Median repurchase latency ($\Delta t_{1 \to 2}$): **29.0 days**. 52.41% of repeat buyers purchase in the exact same category.
- **Dataset Evidence**:
  - View queried: `v_customer_orders` aggregated across 93,358 unique `customer_unique_id` entries. Single-order cohort = 90,557 customers; repeat cohort (2+ orders) = 2,801 customers accounting for 5,801 total orders.
- **Business Action Required**:
  - **30-Day Trigger Campaign**: Launch automated email/SMS re-engagement flows at Day 21 post-delivery offering a $10 second-order coupon to capture buyers at the 29-day latency peak.

---

### Q.6: Regional Distribution — Geographic Customer & Revenue Share
- **Business Question**: Which regions contribute the most customers and revenue?
- **Key Finding**: Severe geographic concentration in the **Southeast region (64.6% of revenue, 68.5% of customers)**. Remote buyers in the North & Northeast pay 2× freight fees ($36–$41) and compensate by placing 48% larger basket sizes ($223 AOV vs $150 SE).
- **Empirical Evidence**:
  - **Southeast (SE)**: 64,002 customers (68.5%), **$9.96M revenue (64.6%)**, $150.48 AOV, $19.84 avg freight.
  - **Top 3 States**: SP ($5.77M, 37.4%), RJ ($2.06M, 13.3%), MG ($1.82M, 11.8%) = **62.54% of platform revenue**.
  - **North (N)**: $223.46 AOV, $41.35 avg freight (+108% higher freight than SE).
- **Dataset Evidence**:
  - View/Table queried: `v_customer_orders` joined with `olist_customers_dataset` across 27 Brazilian state codes. SP state = 41,746 customers ($5,770,248.16); RJ state = 12,852 customers ($2,055,876.31); MG state = 11,635 customers ($1,822,176.45).
- **Business Action Required**:
  - **Fulfillment Expansion**: Establish regional fulfillment hubs (FBA model) in São Paulo and Rio de Janeiro.
  - **Remote Freight Thresholds**: Offer free shipping on orders over $200 in the North/Northeast to unlock high-AOV demand.

---

### Q.7: Logistics Performance — Regional Delivery Speeds & Delay Rates
- **Business Question**: How does delivery performance vary across regions?
- **Key Finding**: Massive 2.6× regional delivery duration gap between Southeast (10.8 days avg) and North (22.6 days avg). The Northeast region suffers from a severe **14.33% late delivery rate** (peaking at 23.9% in Alagoas), driving down customer satisfaction.
- **Empirical Evidence**:
  - Delivery duration: SE (10.75d), S (14.03d), MW (15.02d), NE (20.01d), N (22.59d).
  - State extremes: SP (8.76d, 5.89% late) vs Alagoas (AL: 24.54d, **23.93% late rate**, 3.85 ★ avg score).
  - Correlation: State Late Delivery Rate % vs. Detractor Rate %: **$r = +0.8098$**.
- **Dataset Evidence**:
  - View queried: `v_delivery_satisfaction` comprising 96,478 delivered orders with valid delivery dates. Southeast = 65,920 orders (10.75d avg duration); North = 1,845 orders (22.59d avg duration); Alagoas (AL) = 413 orders (23.93% late delivery rate).
- **Business Action Required**:
  - **Carrier Overhaul**: Terminate underperforming postal carrier contracts in Northeast states (AL, MA, PI, CE).
  - **Regional Hub**: Open a distribution node in Salvador (BA) to cut Northeast delivery times below 10 days.

---

### Q.8: Customer Satisfaction — Drivers of Low Review Scores
- **Business Question**: What characteristics are associated with low review scores?
- **Key Finding**: Late delivery is the single biggest driver of customer 1-star reviews, increasing detractor risk by **4.8×** (54.6% late vs 11.4% on-time). Dissatisfaction exhibits a non-linear **3-Day Delay Cliff**—tripling detractor rates past Day 3 of delay.
- **Empirical Evidence**:
  - Review score distribution: Promoters (76.86%), Passives (8.41%), Detractors (14.73%).
  - **The 3-Day Delay Cliff**: On-Time = 11.36% detractors $\to$ 1–3 Days Late = 20.60% $\to$ **4–7 Days Late = 62.19% detractors (2.28 ★)** $\to$ 8–14 Days Late = 78.39% (1.74 ★).
  - High-detractor categories: `office_furniture` (**25.45% detractors**), `fashion_male_clothing` (**25.00% detractors**).
- **Dataset Evidence**:
  - View/Table queried: `v_delivery_satisfaction` joined with `olist_order_reviews_dataset` (109,370 reviewed order items). On-time cohort = 100,843 items (11.36% detractor rate); 4–7 days late cohort = 1,973 items (62.19% detractor rate); 8–14 days late cohort = 1,925 items (78.39% detractor rate).
- **Business Action Required**:
  - **Automated Day 3 Delay Intervention**: Trigger automated SMS alerts on Day 2 of delay offering a **$15 platform voucher + proactive apology** on Day 3 before negative reviews are posted.

---

### Q.9: Revenue Forecasting — Out-of-Sample Expected Run-Rate
- **Business Question**: What revenue range should the business expect in the coming weeks?
- **Key Finding**: Time-series out-of-sample forecasting projects weekly gross revenue stabilizing between **$190.9k and $228.9k** over the next 4 weeks, with an expected cumulative 4-week gross revenue of **$856,291** (95% conformal confidence interval between **$565,307 and $1,147,275**).
- **Empirical Evidence**:
  - Validated champion model **ARIMA(1,1,1)** achieved lowest out-of-sample MAE (**$41,585.71**) and 21.23% MAPE.
  - **Sequential Conformal Bounds (EnbPI)**: Week 1 [$118.2k – $263.7k], Week 2 [$140.0k – $285.5k], Week 3 [$150.8k – $296.3k], Week 4 [$156.2k – $301.7k].
  - 4-Week expected cumulative revenue: **$856,291** (Weekly average: **$214,073/week**).
- **Dataset Evidence**:
  - View queried: `v_customer_orders` aggregated across 85 continuous historical weeks (`2017-01-09` to `2018-08-20`). Extrapolated 4-step out-of-sample forecast window (Weeks 86–89: `2018-08-27` to `2018-09-17`) using ARIMA(1,1,1) + EnbPI conformal bounds.
- **Business Action Required**:
  - **Capital & Operations Alignment**: Budget procurement capital against the **$856.3k point target**, while holding cash reserves matching the **$565.3k floor**.

---

### Artifact & Document References
- **Master Executive Summary**: [`Documentation/Business_Questions/executive_business_eda_summary.md`](file:///d:/COLLEGE/DAIICT/Project/E-Commerce%20Anyalsis/Documentation/Business_Questions/executive_business_eda_summary.md)
- **Question Reports (Q1 - Q9)**: [`Documentation/Business_Questions/`](file:///d:/COLLEGE/DAIICT/Project/E-Commerce%20Anyalsis/Documentation/Business_Questions/)
- **Analysis Scripts (Q1 - Q9)**: [`src/business_questions/`](file:///d:/COLLEGE/DAIICT/Project/E-Commerce%20Anyalsis/src/business_questions/)
- **Visualizations (Q1 - Q9)**: [`images/business_analysis/`](file:///d:/COLLEGE/DAIICT/Project/E-Commerce%20Anyalsis/images/business_analysis/)
