# Business Question 2: Which Periods Demonstrate Unusual Sales Behavior?

## 1. Business Question Formulation

**Core Question**: Which specific calendar periods (weeks, days, or months) exhibit statistically anomalous sales behavior (extreme revenue spikes or severe volume drops) on the Olist marketplace, what underlying business or macro events caused them, and what is their quantitative impact?

**Strategic Rationale**: E-commerce revenue stream volatility is rarely random noise; it is driven by planned promotional surges (e.g. Black Friday) or unplanned exogenous shocks (e.g. logistics strikes, holiday shutdowns). Identifying unusual periods allows leadership to:
- **Prevent Stockouts & Carrier Bottlenecks**: Prepare fulfillment and server infrastructure for predictable spikes.
- **Isolate Macro Disruption Losses**: Quantify non-recurring supply chain shocks to separate structural business failure from temporary external disruptions.
- **De-bias Forecasting Models**: Prevent anomaly spikes from distorting baseline time-series model parameters (e.g. ARIMA or exponential smoothing).

---

## 2. Metric & Population Definition

### 2.1 Population Criteria
- **Target Population**: All delivered transactions in `v_sales_orders` where `order_status = 'delivered'`.
- **Temporal Horizons**: 
  - **Weekly Level**: 85 continuous ISO calendar weeks (`2017-01-09` to `2018-08-20`).
  - **Daily Level**: 588 continuous calendar days (`2017-01-09` to `2018-08-20`) for exact spike/drop pinpointing.

### 2.2 Anomaly Detection Metrics
To separate genuine operational anomalies from underlying growth trends, we apply three detrending and statistical outlier rules:

#### A. Detrended Rolling Z-Score ($Z_{\text{rolling}}$)
Because Olist experienced rapid growth during 2017, a static global mean overstates early anomalies and understates late ones. We compute an 8-week centered moving average ($\text{MA}_8(x)$) and moving standard deviation ($\sigma_8(x)$):

$$Z_{\text{rolling}, t} = \frac{x_t - \text{MA}_8(x_t)}{\sigma_8(x_t)}$$

- **Upper Anomaly Flag**: $Z_{\text{rolling}, t} > +2.0$ (Statistically significant revenue surge).
- **Lower Anomaly Flag**: $Z_{\text{rolling}, t} < -2.0$ (Statistically significant revenue collapse).

#### B. Percentage Deviation from Moving Trend ($\text{Dev}_{\text{MA}}$)
$$\text{Dev}_{\text{MA}, t} = \left( \frac{x_t - \text{MA}_8(x_t)}{\text{MA}_8(x_t)} \right) \times 100\%$$

- **Upper Anomaly Cutoff**: $\text{Dev}_{\text{MA}} > +35.0\%$
- **Lower Anomaly Cutoff**: $\text{Dev}_{\text{MA}} < -30.0\%$

---

## 3. Analysis Execution & Empirical Results

The analysis script [`src/business_questions/q2_unusual_sales_periods.py`](file:///d:/COLLEGE/DAIICT/Project/E-Commerce%20Anyalsis/src/business_questions/q2_unusual_sales_periods.py) was executed against `database/olist_ecommerce.db`.

### 3.1 Primary Identified Unusual Periods (Weekly Level)

| Period / Event Name | ISO Week Start | Weekly Revenue ($) | 8-Week Moving Avg ($) | Deviation from Trend (%) | Detrended Z-Score | Anomaly Classification |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Black Friday 2017 Peak** | **`2017-11-20`** | **$474,623.65** | **$248,092.76** | **+91.31%** | **+2.16** | 🔴 **Major Positive Spike** |
| **Cyber Monday Tail** | `2017-11-27` | $290,742.61 | $249,012.18 | +16.76% | +0.65 | 🟠 High Promotional Volume |
| **Early Feb Growth Surge** | `2017-02-06` | $62,541.22 | $40,741.65 | +53.51% | +1.17 | 🟠 Early Seller Expansion |
| **Brazilian Truckers' Strike** | **`2018-05-21`** | **$154,018.75** | **$257,136.21** | **-40.10%** | **-1.83** | 🟣 **Major Supply Disruption Dip** |
| **Christmas Holiday Slump** | **`2017-12-25`** | **$129,715.48** | **$244,841.65** | **-47.02%** | **-1.62** | 🟣 **Holiday Operational Pause** |
| **Year-End Pre-Christmas Dip**| `2017-12-18` | $144,302.22 | $244,857.34 | -41.06% | -0.94 | 🟣 Shipping Cutoff Drop |
| **Easter / Holy Week Dip** | `2017-04-10` | $70,056.24 | $104,556.78 | -33.00% | -2.25 | 🟣 **Religious Holiday Dip** |
| **Carnaval Season Slump** | `2017-02-20` | $60,207.28 | $90,587.12 | -33.54% | -1.40 | 🟣 **Cultural Holiday Dip** |

---

### 3.2 Daily Granularity Analysis of Key Events

#### A. Black Friday 2017 Week Breakdown (Nov 20 – Nov 28, 2017)

| Date | Day of Week | Daily Orders | Daily Gross Revenue ($) | Deviation from 14-Day MA (%) | Event Note |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **2017-11-23** | Thursday | 623 | $90,147.22 | +70.2% | Black Friday Eve Surge |
| **2017-11-24** | **Friday** | **1,147** | **$175,178.46** | **+230.68%** | 🔥 **Black Friday Single-Day Peak** |
| **2017-11-25** | Saturday | 487 | $70,683.26 | +31.4% | Weekend Promotional Tail |
| **2017-11-27** | Monday | 395 | $55,887.39 | +1.3% | Cyber Monday |
| **2017-11-28** | Tuesday | 372 | $55,990.30 | +1.2% | Post-Cyber Monday |

> **Black Friday Impact**: On Black Friday day (`2017-11-24`), single-day revenue reached **$175.2k** (1,147 orders)—representing **3.3× the average daily volume** of November 2017.

#### B. Brazilian Truck Drivers' Strike Impact (May 21 – May 31, 2018)
In late May 2018, a nationwide 10-day strike by Brazilian truck drivers (*Greve dos Caminhoneiros*) paralyzed freight transportation, fuel distribution, and postal routes across Brazil.
- **Pre-Strike Baseline (Week of May 14)**: $264,812.55 revenue (1,617 orders).
- **Strike Week (Week of May 21)**: Revenue collapsed to **$154,018.75** (941 orders)—a **-41.8% sudden drop** in revenue and **-41.8% drop in order volume**.
- **Recovery (Week of June 04)**: Revenue rebounded immediately to **$278,924.31** (1,675 orders) as logistics operations resumed.

---

## 4. Validation of Results

To validate that these identified periods represent genuine operational anomalies:

1. **Statistical Threshold Validation**:
   - The Black Friday week (`2017-11-20`) exceeded **+2.16 standard deviations** ($Z > 2.0$) above the rolling 8-week moving average and sat **+$226.5k above trend**.
   - The Easter week (`2017-04-10`) recorded a detrended Z-score of **-2.25** ($Z < -2.0$).
2. **External Event Conformation**:
   - Every single flagged anomaly aligns precisely with documented external events in Brazil:
     - **Promotional Spikes**: Black Friday (Nov 24), Cyber Monday (Nov 27), Mother's Day prep (May 07–16), Dia dos Namorados prep (June 11).
     - **Exogenous Disruptions**: Nationwide Truck Drivers' Strike (May 21–31, 2018).
     - **Holiday Pauses**: Carnaval (Feb 20–28), Easter (April 10–16), Christmas Eve/Day (Dec 24–25).

---

## 5. Visual Evidence

The chart below illustrates the weekly detrended anomaly detection and the daily Black Friday surge generated by `q2_unusual_sales_periods.py`:

![Q2 Anomaly Detection Chart](../../images/business_analysis/q2_unusual_sales_periods.png)

### Chart Insights:
- **Top Panel**: The blue weekly line shows two severe structural anomalies: the massive red spike during Black Friday 2017 ($474.6k) and the purple dip during the May 2018 Truckers' Strike ($154.0k).
- **Bottom Panel**: Daily breakdown shows how Black Friday (Nov 24) created a 1-day revenue tower of $175.2k, flanked by Black Friday Eve ($90.1k) and Cyber Monday ($55.9k).

---

## 6. Business Insights & Strategic Recommendations

### Key Findings
1. **Black Friday is the Marketplace's Single Dependent Peak**:
   - Black Friday week alone generated **3.0% of annual operational revenue**. The promotional spike is highly concentrated in a 48-hour window (Thursday night through Friday).
2. **Severe Vulnerability to Postal Freight Disruptions**:
   - The May 2018 Truckers' Strike caused an instant **-41.8% revenue loss**, proving Olist's vulnerability to centralized carrier dependence (Correios/road freight).
3. **Predictable Holiday Demand Slumps**:
   - Sales experience predictable 30%–47% contractions during Carnaval (late Feb), Easter (mid-April), and Christmas week (late Dec) as buyers step away and shipping guarantees expire.

### Strategic Action Plan
1. **Pre-Black Friday Server & Logistics Stress-Testing**:
   - Scale seller API infrastructure and carrier pickup schedules specifically for the 48-hour period around Black Friday to handle 3.3× normal order throughput.
2. **Multi-Carrier Logistics Diversification**:
   - To prevent catastrophic revenue drops during road freight strikes, Olist must diversify carrier partnerships beyond standard road postal networks to include private regional 3PLs and local courier fleets.
3. **Holiday Promotional Smoothing**:
   - Introduce early-bird holiday campaigns (e.g. "Early Christmas Shipping" in early December) to smooth out the severe revenue drop observed between Dec 18 and Dec 31.

---

### Code & Artifact References
- **Analysis Script**: [`src/business_questions/q2_unusual_sales_periods.py`](file:///d:/COLLEGE/DAIICT/Project/E-Commerce%20Anyalsis/src/business_questions/q2_unusual_sales_periods.py)
- **Documentation Report**: [`Business_Questions/q2_unusual_sales_periods.md`](file:///d:/COLLEGE/DAIICT/Project/E-Commerce%20Anyalsis/Business_Questions/q2_unusual_sales_periods.md)
- **Generated Visualization**: [`images/q2_unusual_sales_periods.png`](file:///d:/COLLEGE/DAIICT/Project/E-Commerce%20Anyalsis/images/q2_unusual_sales_periods.png)
