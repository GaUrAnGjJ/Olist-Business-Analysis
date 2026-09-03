# Comprehensive Forecasting Experiment Report

## 1. Experimental Setup

- **Protocol**: Option A — Rolling One-Step-Ahead Evaluation (15 test weeks).
- **Categories Evaluated**: Existing Baselines, Classical Exponential Smoothing Models, and Log Transformation Experiments.

## 2. Evaluation Leaderboard Table

| Rank | Category | MODEL | R2 Score | MAE ($) | MAE (%) | RMSE ($) | RMSE (%) | MAPE (%) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Classical Models | ARIMA(1,1,1) Original | -0.0808 | $41,585.71 | 17.15% | $57,970.39 | 23.91% | 21.23% |
| 2 | Existing Baselines | Naive Persistence | -0.2565 | $45,940.38 | 18.94% | $62,504.91 | 25.78% | 23.45% |
| 3 | Transformation Experiment | ARIMA(1,1,1) Log Transformed | -0.2524 | $45,962.89 | 18.95% | $62,403.66 | 25.73% | 23.44% |
| 4 | Classical Models | SARIMAX(1,1,1) + Black Friday | -0.2355 | $46,060.38 | 18.99% | $61,981.06 | 25.56% | 23.54% |
| 5 | Existing Baselines | Drift | -0.3021 | $46,216.35 | 19.06% | $63,630.40 | 26.24% | 23.71% |
| 6 | Classical Models | Simple Exp Smoothing | -0.3453 | $46,882.40 | 19.33% | $64,675.69 | 26.67% | 23.75% |
| 7 | Transformation Experiment | Holt Damped Log Transformed | -0.3083 | $47,357.68 | 19.53% | $63,780.44 | 26.30% | 24.02% |
| 8 | Existing Baselines | Moving Average (4W) | -0.6401 | $54,340.85 | 22.41% | $71,412.90 | 29.45% | 26.86% |
| 9 | Classical Models | Holt Linear Trend | -0.6448 | $55,655.87 | 22.95% | $71,515.66 | 29.49% | 28.12% |
| 10 | Classical Models | Holt Damped Trend | -0.8357 | $62,818.39 | 25.90% | $75,551.16 | 31.16% | 31.47% |


