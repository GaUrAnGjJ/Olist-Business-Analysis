# Executive Business EDA & KPI Analysis Report: Olist E-Commerce Performance

## 1. Executive Summary

While forecasting models project *future revenue trajectories*, this **Business EDA & KPI Report** investigates **what happened, why it happened, and where the critical operational opportunities and threats reside**.

Utilizing clean SQL analytical views (`v_sales_orders`, `v_sales_order_items`, `v_customer_orders`, and `v_delivery_satisfaction`) built upon 99,441 orders spanning 2016–2018, this report presents empirical evidence across five core operational pillars:
1. **Sales & Revenue Dynamics**: Macro revenue trajectories, AOV stability, and category revenue concentration.
2. **Geographic Performance**: Multi-state regional dominance vs. remote frontier freight burdens.
3. **Customer Retention & Concentration**: Empirical evidence of a high-churn, acquisition-dependent customer model.
4. **Delivery & Logistics Execution**: Lead time accuracy, regional delivery bottlenecks, and carrier buffers.
5. **Customer Satisfaction & Review Root-Causes**: The quantitative relationship between delivery delay thresholds and customer churn/detraction.

---

## 2. Pillar 1 — Sales & Revenue Performance

### 2.1 Macro Revenue & Order Metrics
Between September 2016 and August 2018, the Olist platform generated **$15.84M in Gross Revenue** across **99,441 orders** (96,478 successfully delivered).

| Metric | Total Value | Share (%) | Operational Note |
| :--- | :---: | :---: | :--- |
| **Gross Revenue** | **$15,843,514.92** | **100.0%** | Total customer payments (Products + Freight) |
| **Product Sales Revenue** | **$13,591,643.70** | **85.79%** | Net merchandise value sold by marketplace sellers |
| **Freight Revenue** | **$2,251,871.22** | **14.21%** | Logistics and shipping fees collected from customers |
| **Total Delivered Orders** | **96,478** | **97.02%** | Orders successfully fulfilled |
| **Average Order Value (AOV)** | **$159.33** | - | Average gross basket size |
| **Average Items per Order** | **1.13** | - | Low cross-selling / bundling per transaction |

### 2.2 Revenue & Order Trajectory Analysis
E-commerce operational growth occurred in two distinct phases:
- **Phase 1: Hyper-Growth (Jan 2017 – Nov 2017)**: Monthly revenue expanded from **$137.7k** (750 orders) in Jan 2017 to **$1.18M** (7,544 orders) in Nov 2017, capped by an extreme Black Friday spike (`2017-11-20`) generating $474.6k in a single week.
- **Phase 2: Operational Plateau (Dec 2017 – Aug 2018)**: Monthly order volume and revenue stabilized into a plateau ranging between **$1.00M and $1.15M** (~6,100 to 6,800 orders per month). 

> [!IMPORTANT]
> **Business Insight**: Revenue growth was driven by order volume expansion rather than price inflation. AOV remained tight around **$150–$168** throughout 2017–2018, indicating that growth stagnated in 2018 because new customer acquisition hit a ceiling.

### 2.3 Product Category Concentration
Olist offers products across 70+ categories, but revenue generation is heavily concentrated in a small core of categories:

| Rank | Product Category (English) | Orders | Gross Revenue ($) | Revenue Share (%) | Avg Item Price ($) |
| :---: | :--- | :---: | :---: | :---: | :---: |
| **1** | `health_beauty` | 8,647 | $1,241,189.65 | **9.16%** | $130.28 |
| **2** | `watches_gifts` | 5,495 | $1,111,304.70 | **8.20%** | $199.04 |
| **3** | `bed_bath_table` | 9,272 | $1,076,897.45 | **7.95%** | $93.44 |
| **4** | `sports_leisure` | 7,530 | $982,887.89 | **7.25%** | $113.25 |
| **5** | `computers_accessories` | 6,530 | $907,725.68 | **6.70%** | $116.26 |
| 6 | `furniture_decor` | 6,307 | $773,782.72 | 5.71% | $87.25 |
| 7 | `housewares` | 5,743 | $666,590.22 | 4.92% | $90.60 |
| 8 | `cool_stuff` | 3,559 | $607,967.66 | 4.49% | $164.12 |
| 9 | `auto` | 3,810 | $588,432.55 | 4.34% | $139.85 |
| 10 | `garden_tools` | 3,448 | $498,515.65 | 3.68% | $110.24 |

- **Top 5 Category Share**: The top 5 categories generate **39.26%** ($6.32M) of total revenue.
- **Top 10 Category Share**: The top 10 categories account for **62.40%** ($9.46M) of total revenue.

---

## 3. Pillar 2 — Geographic Performance & Regional Disparities

### 3.1 State-Level Revenue & Order Distribution
Olist's customer base displays extreme geographical skew towards the Southeastern region of Brazil:

| State | Region | Orders | Gross Revenue ($) | Revenue Share (%) | Avg Freight / Order ($) | Freight % of Order |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **SP** | Southeast | 40,501 | $5,762,600.08 | **37.42%** | **$17.33** | 13.5% |
| **RJ** | Southeast | 12,350 | $2,052,845.54 | **13.33%** | **$23.95** | 15.6% |
| **MG** | Southeast | 11,354 | $1,816,609.91 | **11.80%** | **$23.46** | 16.7% |
| **RS** | South | 5,345 | $860,401.76 | 5.59% | $24.80 | 16.7% |
| **PR** | South | 4,923 | $780,724.87 | 5.07% | $23.49 | 15.8% |
| **SC** | South | 3,546 | $594,389.92 | 3.86% | $24.85 | 16.0% |
| **BA** | Northeast | 3,256 | $590,422.37 | 3.83% | **$29.96** | 18.7% |
| **DF** | Midwest | 2,080 | $345,690.66 | 2.24% | $23.86 | 15.5% |
| **GO** | Midwest | 1,957 | $333,799.30 | 2.17% | $26.25 | 16.7% |
| **ES** | Southeast | 1,995 | $317,261.08 | 2.06% | $24.57 | 16.7% |

> [!NOTE]
> **Southeastern Hegemony**: São Paulo (SP), Rio de Janeiro (RJ), and Minas Gerais (MG) alone account for **62.55% of all orders ($9.63M)**.

### 3.2 City-Level Concentration
The top 5 metro areas (São Paulo, Rio de Janeiro, Belo Horizonte, Brasília, Curitiba) contribute **$4.21M (27.3%)** of gross revenue. São Paulo city alone generates 15,045 orders ($2.11M), benefiting from proximity to major fulfillment centers and low shipping costs ($17.33 avg freight).

### 3.3 The Remote Freight Penalty
Customers in Northern and Northeastern states suffer severe freight cost surcharges:
- **Maranhão (MA)**: Avg freight **$38.26** per order (23.4% of basket value).
- **Pará (PA)**: Avg freight **$35.84** per order (22.1% of basket value).
- **Piauí (PI)**: Avg freight **$34.90** per order (21.8% of basket value).
- **Rondônia (RO)**: Avg freight **$41.08** per order (25.1% of basket value).

*Business Impact*: High freight friction suppresses conversion rates in Northern/Northeastern states, limiting marketplace expansion beyond the Southeast corridor.

---

## 4. Pillar 3 — Customer Behaviour, Retention & Concentration

### 4.1 New vs. Returning Customers (Retention Audit)
Analysis of unique customer identifiers (`customer_unique_id`) reveals a startling structural vulnerability in the Olist business model:

| Customer Group | Unique Customers | Customer Share (%) | Total Orders Placed | Total Revenue Generated ($) |
| :--- | :---: | :---: | :---: | :---: |
| **Single-Order Customers (1 Order)** | **90,557** | **97.00%** | 90,557 | $14,402,118.42 |
| **Repeat Customers (2+ Orders)** | **2,801** | **3.00%** | 5,921 | $998,421.50 |
| **Total Platform Customers** | **93,358** | **100.0%** | **96,478** | **$15,400,539.92** |

#### Order Frequency Breakdown:
- **1 Order**: 90,557 customers (**97.00%**)
- **2 Orders**: 2,573 customers (**2.76%**)
- **3 Orders**: 181 customers (**0.19%**)
- **4 Orders**: 28 customers (**0.03%**)
- **5+ Orders**: 19 customers (**0.02%**)

> [!WARNING]
> **Critical Strategic Finding — Near-Zero Retention**:
> Olist's repeat customer rate is **only 3.00%**. 97 out of 100 customers purchase exactly once and never return. Olist operates as a "one-and-done" transactional marketplace. Revenue growth has relied 100% on continuous top-of-funnel customer acquisition rather than building Customer Lifetime Value (LTV).

### 4.2 Customer Spend Concentration (Pareto Analysis)
Although repeat purchases are low, customer spend distribution shows moderate Pareto concentration due to varying order monetary values:

| Customer Tier | Cumulative Customer Share (%) | Cumulative Revenue Share (%) | Total Spend Contribution ($) |
| :--- | :---: | :---: | :---: |
| **Top 1% Customers** | 1.00% | **10.34%** | $1,592,415.82 |
| **Top 5% Customers** | 5.00% | **26.79%** | $4,125,804.64 |
| **Top 10% Customers** | 10.00% | **38.25%** | $5,890,706.52 |
| **Top 20% Customers** | 20.00% | **53.52%** | $8,242,368.95 |

The top 20% of customers account for **53.52%** of gross revenue, driven primarily by high-value single transactions (e.g. expensive electronics, watches, or bulk purchases).

---

## 5. Pillar 4 — Delivery Performance & Logistics Execution

### 5.1 Delivery Duration & Lead Time Accuracy
Fulfillment execution was evaluated across 96,478 delivered orders:

| Delivery Performance Metric | Value | Operational Context |
| :--- | :---: | :--- |
| **Average Actual Delivery Duration** | **12.50 Days** | Purchase timestamp to customer receipt |
| **Average Estimated Delivery Duration** | **23.90 Days** | Estimated promised date at checkout |
| **Average Delivery Buffer (Over-Estimate)** | **+11.40 Days** | Olist pads estimated delivery dates by ~11.4 days |
| **Overall Late Delivery Rate** | **8.12%** | 7,834 orders delivered after estimated date |
| **Average Days Late (For Late Orders)** | **+9.55 Days** | Average delay duration when a package misses target |

### 5.2 Regional Delivery Friction (Best vs. Worst States)
Delivery performance varies dramatically across Brazilian states, reflecting regional postal infrastructure bottlenecks:

#### Top 5 Best Performing States (Lowest Late Rate):
1. **São Paulo (SP)**: 5.41% Late Rate | 8.28 Actual Days | 4.25 Avg Review
2. **Paraná (PR)**: 5.22% Late Rate | 11.53 Actual Days | 4.24 Avg Review
3. **Minas Gerais (MG)**: 5.78% Late Rate | 11.54 Actual Days | 4.19 Avg Review
4. **Santa Catarina (SC)**: 6.21% Late Rate | 14.47 Actual Days | 4.21 Avg Review
5. **Distrito Federal (DF)**: 6.35% Late Rate | 12.51 Actual Days | 4.18 Avg Review

#### Top 5 Worst Performing States (Severe Logistics Bottlenecks):
1. **Alagoas (AL)**: **20.91% Late Rate** | 24.04 Actual Days | Avg Delay when late: **+9.25 Days** | 3.85 Avg Review
2. **Maranhão (MA)**: **19.80% Late Rate** | 21.08 Actual Days | Avg Delay when late: **+9.97 Days** | 3.83 Avg Review
3. **Sergipe (SE)**: **19.10% Late Rate** | 21.03 Actual Days | Avg Delay when late: **+16.89 Days** | 3.91 Avg Review
4. **Ceará (CE)**: **15.40% Late Rate** | 20.61 Actual Days | Avg Delay when late: **+14.33 Days** | 3.94 Avg Review
5. **Piauí (PI)**: **14.71% Late Rate** | 18.98 Actual Days | Avg Delay when late: **+12.30 Days** | 3.99 Avg Review

---

## 6. Pillar 5 — Customer Satisfaction & Review Score Analysis

### 6.1 Review Score Distribution
Out of 98,673 submitted customer reviews:

| Review Score | Star Rating | Order Count | Share (%) | Customer Sentiment |
| :---: | :---: | :---: | :---: | :--- |
| **5.0** | ⭐⭐⭐⭐⭐ | 56,955 | **57.72%** | Promoters (Highly Satisfied) |
| **4.0** | ⭐⭐⭐⭐ | 19,018 | **19.27%** | Satisfied |
| **3.0** | ⭐⭐⭐ | 8,136 | 8.25% | Neutral |
| **2.0** | ⭐⭐ | 3,125 | 3.17% | Dissatisfied |
| **1.0** | ⭐ | 11,316 | **11.47%** | Detractors (Severely Unhappy) |

- **Net Promoter View**: **76.99%** of reviews are positive (4 or 5 stars). However, **14.64%** (14,441 orders) are explicit Detractors (1 or 2 stars).

### 6.2 The Smoking Gun: Delivery Delays vs. Customer Detraction
By joining review scores directly with delivery delay thresholds (`v_delivery_satisfaction`), we uncover the **#1 driver of negative customer reviews**:

| Delivery Delay Category | Total Orders | Average Review Score | 5-Star Promoter Rate (%) | 1-2 Star Detractor Rate (%) |
| :--- | :---: | :---: | :---: | :---: |
| **On-Time / Early Delivery** | 88,163 | **4.30 / 5.0** | **62.38%** | **9.19%** |
| **1–3 Days Late** | 2,634 | **3.56 / 5.0** | 43.13% | **19.17%** |
| **4–7 Days Late** | 1,773 | **2.24 / 5.0** | 18.05% | **61.25%** |
| **> 7 Days Late** | 3,248 | **1.62 / 5.0** | 7.45% | **78.36%** |

> [!CAUTION]
> **Key Finding — The 3-Day Delay Cliff**:
> - When an order is delivered on-time, detractor rate is **only 9.19%** and average rating is **4.30**.
> - Delaying an order by just 1–3 days **doubles detractor rate to 19.17%**.
> - Delaying an order by 4–7 days causes detractor rate to **skyrocket to 61.25%** (Score collapses to **2.24**).
> - Delays beyond 7 days destroy satisfaction: **78.36% leave 1-star or 2-star reviews** (Score drops to **1.62**).

### 6.3 Product Categories Associated with Low Satisfaction

| Product Category | Orders | Avg Review Score | Late Delivery Rate (%) | Detractor Rate (1-2 Stars) | Primary Friction Cause |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `office_furniture` | 1,244 | **3.49** | 8.83% | **33.84%** | Shipping damage, assembly issues, carrier delays |
| `fixed_telephony` | 209 | **3.67** | 3.97% | **27.75%** | Product defect / compatibility issues |
| `furniture_decor` | 6,260 | **3.90** | 8.33% | **23.19%** | Bulky freight delays, missing parts |
| `bed_bath_table` | 9,177 | **3.89** | 8.24% | **21.34%** | Material quality mismatches |
| `computers_accessories` | 6,499 | **3.92** | 7.65% | **19.90%** | Technical defects, wrong specifications |

*Bulky Goods Penalty*: Heavy items (`office_furniture`, `furniture_decor`, `bed_bath_table`) suffer from high detractor rates due to freight damage, complex delivery logistics, and higher carrier delay sensitivity.

---

## 7. Strategic Business Recommendations

Based on these empirical findings, Olist leadership should execute four targeted operational initiatives:

### 1. Shift Strategy from Acquisition to Retention (LTV Playbook)
- **Problem**: 97.0% single-order customer rate is draining marketing margins.
- **Action**: Implement post-purchase automated re-engagement campaigns, loyalty reward points, and personalized category cross-selling (e.g. recommending refill items in `health_beauty` or accessories for `computers_accessories`).

### 2. Overhaul Northeast & North Regional Logistics
- **Problem**: States like Alagoas (20.9% late rate) and Maranhão (19.8% late rate) suffer severe shipping delays and high detractor rates.
- **Action**: Partner with regional Northeastern fulfillment hubs or regional 3PL carriers to establish micro-fulfillment centers in Salvador (BA) and Recife (PE), reducing transit times by 8–10 days.

### 3. Implement Automated Carrier Escalation at Day 3 of Delay
- **Problem**: Customer detractor rate jumps from 9.2% to 61.3% once delays pass 3 days.
- **Action**: Build an automated logistics alert system: when a shipment exceeds its estimated carrier milestone by 48 hours, automatically trigger proactive SMS notifications and issue a small customer credit ($10 freight voucher) to preserve goodwill before the review is submitted.

### 4. Seller Quality Control & Packaging Audits for Bulky Categories
- **Problem**: `office_furniture` has a 33.8% detractor rate despite normal late delivery rates.
- **Action**: Institute mandatory packaging standards and partner with specialized heavy-goods carriers for furniture products to prevent transit damage.

---

## 8. Summary Table of Key Business KPIs

| Pillar | Key Performance Indicator (KPI) | Empirical Benchmark Value |
| :--- | :--- | :---: |
| **Sales** | Gross Operational Revenue | **$15,843,514.92** |
| **Sales** | Average Order Value (AOV) | **$159.33** |
| **Sales** | Top 5 Category Revenue Share | **39.26%** |
| **Geography** | Southeast Order Share (SP, RJ, MG) | **62.55%** |
| **Geography** | Remote State Freight Surcharge (MA/PA/RO) | **22.0% – 25.1% of order value** |
| **Customers** | Single-Order Customer Rate | **97.00%** |
| **Customers** | Top 20% Customer Spend Share | **53.52%** |
| **Delivery** | Average Actual Delivery Duration | **12.50 Days** |
| **Delivery** | Overall Late Delivery Rate | **8.12%** |
| **Satisfaction** | Overall 5-Star Promoter Rate | **57.72%** |
| **Satisfaction** | Detractor Rate on On-Time Orders | **9.19%** |
| **Satisfaction** | Detractor Rate on 4-7 Day Late Orders | **61.25%** |

---
*Report compiled from SQL analytical views in `database/olist_ecommerce.db`.*
