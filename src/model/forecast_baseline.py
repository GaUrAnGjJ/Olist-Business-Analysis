import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("forecast_baseline")

DATA_PATH = Path("data/processed/forecast/weekly_forecasting_data.csv")
OUTPUT_DIR = Path("data/processed/forecast")
IMAGES_DIR = Path("images")
DOCS_DIR = Path("Documentation")

TRAIN_WEEKS = 70
TEST_WEEKS = 15


def calculate_metrics(actual, pred):
    """Calculate MAE, RMSE, and MAPE metrics."""
    actual = np.array(actual)
    pred = np.array(pred)
    mae = np.mean(np.abs(actual - pred))
    rmse = np.sqrt(np.mean((actual - pred) ** 2))
    # Filter out zero division if any
    non_zero = actual != 0
    mape = np.mean(np.abs((actual[non_zero] - pred[non_zero]) / actual[non_zero])) * 100
    return mae, rmse, mape


def run_baseline_forecasting(data_path=DATA_PATH):
    """
    Phase 6: Step 1 & Step 2 — Chronological Split & Baseline Forecasting
    
    Responsibilities:
    - Load weekly forecasting dataset (85 rows)
    - Perform strict chronological split: 70 weeks Train, 15 weeks Test
    - Generate baseline forecasts:
      1. Naive (1-Step Ahead Persistence)
      2. Naive (Multi-Step Constant Horizon)
      3. Historical Train Mean Baseline
      4. Trailing 4-Week Moving Average Baseline
      5. Historical Drift Baseline
    - Compute out-of-sample MAE, RMSE, and MAPE
    - Save CSV and visualization
    """
    logger.info("=" * 80)
    logger.info("PHASE 6 — STEP 1 & 2: CHRONOLOGICAL TRAIN/TEST SPLIT & BASELINE FORECASTS")
    logger.info("=" * 80)

    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found at {data_path.resolve()}. Please run create_weekly_forecast_dataset.py first.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(data_path)
    df['week_start_dt'] = pd.to_datetime(df['week_start'])

    # ------------------------------------------------------------------------
    # STEP 1: CHRONOLOGICAL TRAIN / TEST SPLIT
    # ------------------------------------------------------------------------
    train_df = df.iloc[:TRAIN_WEEKS].copy()
    test_df = df.iloc[TRAIN_WEEKS:].copy()

    logger.info(f"Training Set: {len(train_df)} weeks ({train_df['week_start'].min()} to {train_df['week_start'].max()})")
    logger.info(f"Test Set:     {len(test_df)} weeks ({test_df['week_start'].min()} to {test_df['week_start'].max()})")

    actuals = test_df['gross_revenue'].values
    test_weeks = test_df['week_start'].values

    # ------------------------------------------------------------------------
    # STEP 2: GENERATE BASELINE FORECASTS
    # ------------------------------------------------------------------------
    predictions = pd.DataFrame({'week_start': test_weeks, 'actual_gross_revenue': actuals})

    # Baseline 1: Naive (1-Step Ahead Persistence) — uses previous week's actual value
    # For index i in test set, pred = value at i-1
    naive_1step = df['gross_revenue'].shift(1).iloc[TRAIN_WEEKS:].values
    predictions['naive_1step'] = naive_1step

    # Baseline 2: Naive (Multi-Step Constant Horizon) — last value of train set
    last_train_val = train_df['gross_revenue'].iloc[-1]
    predictions['naive_multistep'] = np.full(TEST_WEEKS, last_train_val)

    # Baseline 3: Historical Train Mean
    train_mean_val = train_df['gross_revenue'].mean()
    predictions['train_mean'] = np.full(TEST_WEEKS, train_mean_val)

    # Baseline 4: Trailing 4-Week Moving Average
    # Roll 4-week mean shift 1
    ma_4w = df['gross_revenue'].rolling(window=4).mean().shift(1).iloc[TRAIN_WEEKS:].values
    predictions['moving_average_4w'] = ma_4w

    # Baseline 5: Historical Drift Baseline
    first_train_val = train_df['gross_revenue'].iloc[0]
    drift_slope = (last_train_val - first_train_val) / (TRAIN_WEEKS - 1)
    drift_vals = np.array([last_train_val + (h + 1) * drift_slope for h in range(TEST_WEEKS)])
    predictions['drift'] = drift_vals

    # Save baseline predictions CSV
    csv_out_path = OUTPUT_DIR / "baseline_forecasts.csv"
    predictions.to_csv(csv_out_path, index=False)
    logger.info(f"Saved baseline predictions CSV to: {csv_out_path}")

    # ------------------------------------------------------------------------
    # COMPUTE METRICS & DISPLAY TABLE
    # ------------------------------------------------------------------------
    models = {
        'Naive (1-Step Persistence)': predictions['naive_1step'],
        'Naive (Multi-Step Constant)': predictions['naive_multistep'],
        'Train Historical Mean': predictions['train_mean'],
        'Trailing 4-Week Moving Avg': predictions['moving_average_4w'],
        'Historical Drift': predictions['drift']
    }

    metrics_list = []
    logger.info("\n--- BASELINE OUT-OF-SAMPLE EVALUATION (15 WEEKS TEST) ---")
    for name, pred in models.items():
        mae, rmse, mape = calculate_metrics(actuals, pred)
        metrics_list.append({
            'Model': name,
            'MAE ($)': mae,
            'RMSE ($)': rmse,
            'MAPE (%)': mape
        })
        logger.info(f"  {name:<30} | MAE: ${mae:10,.2f} | RMSE: ${rmse:10,.2f} | MAPE: {mape:6.2f}%")

    metrics_df = pd.DataFrame(metrics_list).sort_values('MAE ($)').reset_index(drop=True)

    # ------------------------------------------------------------------------
    # VISUALIZATION
    # ------------------------------------------------------------------------
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, ax = plt.subplots(figsize=(13, 6))

    # Plot train history (last 20 weeks of train)
    plot_train = train_df.tail(20)
    ax.plot(pd.to_datetime(plot_train['week_start']), plot_train['gross_revenue'] / 1e3, color='#555555', linewidth=2, label='Train Gross Revenue (History)')

    # Plot actual test set
    test_dt = pd.to_datetime(test_df['week_start'])
    ax.plot(test_dt, test_df['gross_revenue'] / 1e3, color='black', linewidth=2.8, marker='o', label='Actual Test Revenue')

    # Plot baseline forecasts
    ax.plot(test_dt, predictions['naive_1step'] / 1e3, color='#1f77b4', linestyle='--', linewidth=2, marker='s', label='Naive 1-Step Persistence')
    ax.plot(test_dt, predictions['naive_multistep'] / 1e3, color='#d62728', linestyle=':', linewidth=2, label='Naive Multi-Step Constant')
    ax.plot(test_dt, predictions['train_mean'] / 1e3, color='#2ca02c', linestyle='-.', linewidth=2, label='Train Historical Mean')
    ax.plot(test_dt, predictions['moving_average_4w'] / 1e3, color='#9467bd', linestyle='--', linewidth=2, label='Trailing 4-Week Moving Avg')

    # Vertical split line
    ax.axvline(test_dt.iloc[0], color='red', linestyle='--', alpha=0.7, label='Train/Test Split Boundary')

    ax.set_title('Baseline Out-of-Sample Weekly Gross Revenue Forecasts (15-Week Test Horizon)', fontsize=13, fontweight='bold')
    ax.set_xlabel('Week Start Date', fontsize=11)
    ax.set_ylabel('Gross Revenue ($ in Thousands)', fontsize=11)
    ax.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.9)
    ax.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    chart_path = IMAGES_DIR / "baseline_forecasts.png"
    plt.savefig(chart_path, dpi=300)
    plt.close()
    logger.info(f"Saved Baseline Forecast Chart to: {chart_path}")

    return train_df, test_df, predictions, metrics_df


if __name__ == "__main__":
    run_baseline_forecasting()
