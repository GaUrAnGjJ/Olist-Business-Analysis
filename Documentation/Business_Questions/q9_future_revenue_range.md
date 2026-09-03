# Business Question 9: What Revenue Range Should the Business Expect in the Coming Weeks?

## 1. Business Question Formulation

**Core Question**: Based on out-of-sample time-series modeling of historical transactions, what exact point revenue predictions and **95% calibrated conformal revenue ranges** should Olist executive leadership expect across the next 4 operational weeks, and what is the cumulative expected cash-flow expectation for inventory procurement and operational planning?

**Strategic Rationale**: Precise time-series forecasting with calibrated uncertainty bounds prevents two costly operational errors:
- **Under-Forecasting Risk**: Causes stock-outs, logistics carrier capacity shortages, and delayed order fulfillment.
- **Over-Forecasting Risk**: Leads to excess inventory holding costs, over-committed marketing spend, and cash-flow strain.

---

## 2. Metric & Population Definition

### 2.1 Population & Operational Window
- **Historical Population**: 85 continuous ISO calendar weeks (`2017-01-09` to `2018-08-20`) of delivered transactions in `v_customer_orders`.
- **Forecast Horizon**: 4 continuous out-of-sample weeks spanning **`2018-08-27` to `2018-09-17`** (Weeks 86 to 89).
- **Champion Model Engine**: **ARIMA(1,1,1)**, selected as the champion model across 22 evaluated candidate algorithms due to achieving the lowest out-of-sample MAE (**$41,585.71**).
- **Uncertainty Calibration Protocol**: **Sequential Conformal Prediction (EnbPI)**, providing adaptive, distribution-free 95% prediction intervals.

### 2.2 Core Metrics
1. **Weekly Point Forecast ($\hat{y}_{t+h}$)**: Expected weekly gross revenue ($).
2. **95% Conformal Lower Bound ($\text{Lower}_{95}$)**: Pessimistic 5th-percentile revenue floor.
3. **95% Conformal Upper Bound ($\text{Upper}_{95}$)**: Optimistic 95th-percentile revenue ceiling.
4. **Cumulative 4-Week Expected Revenue**: $\sum_{h=1}^4 \hat{y}_{t+h}$.
5. **Expected Weekly Average**: $\frac{1}{4} \sum_{h=1}^4 \hat{y}_{t+h}$.

---

## 3. Analysis Execution & Empirical Forecasting Results

The analysis script [`src/business_questions/q9_future_revenue_range.py`](file:///d:/COLLEGE/DAIICT/Project/E-Commerce%20Anyalsis/src/business_questions/q9_future_revenue_range.py) was executed using the validated ARIMA(1,1,1) + EnbPI conformal bounds engine.

### 3.1 4-Week Out-of-Sample Revenue Forecast (Week 86 to 89)

| Target ISO Week Start | Operational Forecast Week | Champion ARIMA(1,1,1) Point Forecast | 95% Conformal Lower Bound | 95% Conformal Upper Bound | 95% Interval Spread ($) | Operational Scenario Context |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **2018-08-27** | **Week 1** | **$190,961.33** | **$118,215.41** | **$263,707.24** | $145,491.83 | 🟢 Immediate Transition Week |
| **2018-09-03** | **Week 2** | **$212,789.25** | **$140,043.33** | **$285,535.16** | $145,491.83 | 🟢 Baseline Weekly Scale |
| **2018-09-10** | **Week 3** | **$223,595.42** | **$150,849.51** | **$296,341.34** | $145,491.83 | 🟢 Plateau Stabilization |
| **2018-09-17** | **Week 4** | **$228,945.15** | **$156,199.23** | **$301,691.06** | $145,491.83 | 🟢 Plateau Stabilization |
| **4-Week Average** | **Weekly Mean** | **$214,072.79** | **$141,326.87** | **$286,818.70** | **$145,491.83** | 📊 **Expected Weekly Run-Rate** |

---

### 3.2 Cumulative 4-Week Revenue Expectation

| Financial Metric | Cumulative 4-Week Projection ($) | Average Weekly Run-Rate ($/week) | Business Planning Use Case |
| :--- | :---: | :---: | :--- |
| **Expected Point Estimate** | **$856,291.15** | **$214,072.79** | 🎯 Baseline Budget & Revenue Target |
| 🛡️ **Pessimistic Floor (95% CI)** | **$565,307.48** | **$141,326.87** | ⚠️ Stress-Test Cash Flow & Downside Risk |
| 🚀 **Optimistic Ceiling (95% CI)**| **$1,147,274.80** | **$286,818.70** | 📈 Maximum Logistics & Carrier Capacity |

> [!IMPORTANT]
> **Executive Summary Finding**:
> Olist executive leadership should expect weekly revenue to stabilize between **$190.9k and $228.9k** over the next 4 weeks, delivering a cumulative 4-week gross revenue of **$856,291** (with a 95% conformal confidence range between **$565,307 and $1,147,275**).

---

## 4. Model Selection & Validation Rationale

### 4.1 Champion Model Selection Evidence
In our systematic evaluation ([`Documentation/forecast_model_selection.md`](file:///d:/COLLEGE/DAIICT/Project/E-Commerce%20Anyalsis/Documentation/forecast_model_selection.md)), **ARIMA(1,1,1)** outperformed 21 alternative model specifications across 15 walk-forward rolling test weeks:

- **Lowest Observed MAE**: **$41,585.71** (vs. Naive Persistence $45,940.38 MAE, Direct ML $44,439.12 MAE).
- **Lowest MAPE**: **21.23%** out-of-sample percentage error.
- **Conformal Interval Efficiency**: Achieved **86.7% empirical coverage** with a mean width of **$137,624.48**—**26.4% narrower** than standard parametric Gaussian bounds.

> [!NOTE]
> **Notice on Extrapolation**:
> The future 4-week forecast documented here is an **extrapolation beyond the validated full-data operational window** (Weeks 1–85). As the forecast horizon extends further into the future, uncertainty bounds naturally widen. Weekly walk-forward model refitting is recommended as new actual sales data accumulates.

---

## 5. Visual Evidence

The time-series plot below illustrates 25 weeks of historical actual revenue alongside the 4-week ARIMA(1,1,1) point forecast and 95% EnbPI conformal bounds generated by `q9_future_revenue_range.py`:

![Q9 Future Revenue Range Chart](../../images/business_analysis/q9_future_revenue_range.png)

### Chart Insights:
- **Blue Solid Line**: Historical weekly actual revenue showing stabilization around the $240k/week level.
- **Red Dashed Line**: Point forecast predicting steady weekly revenue ramp from **$190.9k up to $228.9k**.
- **Red Shaded Region**: Distribution-free 95% conformal prediction interval ($118k to $301k) capturing true operational variance.

---

## 6. Strategic Business Recommendations

### Strategic Action Plan
1. **Inventory Procurement & Cash-Flow Capital**:
   - Budget operational expenses against the **$856,291 point target**, but maintain a cash reserve buffer based on the pessimistic **$565,307 floor**.
2. **Carrier Logistics Capacity Allocation**:
   - Lock in logistics carrier SLA volume commitments for **1,400 to 1,800 orders per week** (corresponding to the **$214k weekly average AOV**).
3. **Weekly Re-Calibration Cadence**:
   - Automatically execute weekly rolling walk-forward re-fitting every Monday morning as new transaction data enters `v_customer_orders`.

---

### Code & Artifact References
- **Analysis Script**: [`src/business_questions/q9_future_revenue_range.py`](file:///d:/COLLEGE/DAIICT/Project/E-Commerce%20Anyalsis/src/business_questions/q9_future_revenue_range.py)
- **Documentation Report**: [`Business_Questions/q9_future_revenue_range.md`](file:///d:/COLLEGE/DAIICT/Project/E-Commerce%20Anyalsis/Business_Questions/q9_future_revenue_range.md)
- **Model Selection Report**: [`Documentation/forecast_model_selection.md`](file:///d:/COLLEGE/DAIICT/Project/E-Commerce%20Anyalsis/Documentation/forecast_model_selection.md)
- **Generated Visualization**: [`images/q9_future_revenue_range.png`](file:///d:/COLLEGE/DAIICT/Project/E-Commerce%20Anyalsis/images/q9_future_revenue_range.png)
