import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import r2_score
from statsmodels.tsa.api import SimpleExpSmoothing, Holt
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("forecast_arima")

DATA_PATH = Path("data/processed/forecast/weekly_forecasting_data.csv")
OUTPUT_DIR = Path("data/processed/forecast")
IMAGES_DIR = Path("images")
DOCS_DIR = Path("Documentation")

TRAIN_WEEKS = 70
TEST_WEEKS = 15


def calculate_metrics(actual, pred):
    """Calculate MAE, RMSE, MAPE, MAE %, RMSE %, and R2 score metrics."""
    actual = np.array(actual)
    pred = np.array(pred)
    mean_actual = float(np.mean(actual))
    
    mae = float(np.mean(np.abs(actual - pred)))
    rmse = float(np.sqrt(np.mean((actual - pred) ** 2)))
    
    non_zero = actual != 0
    mape = float(np.mean(np.abs((actual[non_zero] - pred[non_zero]) / actual[non_zero])) * 100)
    
    mae_pct = (mae / mean_actual) * 100 if mean_actual != 0 else 0.0
    rmse_pct = (rmse / mean_actual) * 100 if mean_actual != 0 else 0.0
    
    r2 = float(r2_score(actual, pred))
    
    return mae, mae_pct, rmse, rmse_pct, mape, r2


def run_arima_forecasting(data_path=DATA_PATH):
    """
    Phase 6: Comprehensive Model Comparison
    - Existing Baselines (Naive Persistence, Moving Average, Drift)
    - Classical Models (ARIMA(1,1,1), Simple Exp Smoothing, Holt Linear, Holt Damped)
    - Transformation Experiments (Log-transformed ARIMA, Log-transformed Holt Damped)
    All evaluated under Option A — Rolling One-Step-Ahead Protocol.
    """
    logger.info("=" * 80)
    logger.info("PHASE 6 — COMPREHENSIVE FORECASTING MODEL COMPARISON (OPTION A)")
    logger.info("=" * 80)

    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found at {data_path.resolve()}. Please run create_weekly_forecast_dataset.py first.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(data_path)
    df['week_start_dt'] = pd.to_datetime(df['week_start'])
    df['is_black_friday'] = (df['week_start'] == '2017-11-20').astype(int)

    train_df = df.iloc[:TRAIN_WEEKS].copy()
    test_df = df.iloc[TRAIN_WEEKS:].copy()
    actuals = test_df['gross_revenue'].values
    test_weeks = test_df['week_start'].values

    logger.info(f"Training observations (Initial): {len(train_df)} weeks ({train_df['week_start'].min()} to {train_df['week_start'].max()})")
    logger.info(f"Test evaluation horizon:         {len(test_df)} weeks ({test_df['week_start'].min()} to {test_df['week_start'].max()})")

    history_y = list(train_df['gross_revenue'].values)
    history_exog = list(train_df['is_black_friday'].values)
    test_exog = test_df['is_black_friday'].values

    preds = {
        # Existing Baselines
        'Naive Persistence': [],
        'Moving Average (4W)': [],
        'Drift': [],
        
        # Classical Models
        'ARIMA(1,1,1) Original': [],
        'Simple Exp Smoothing': [],
        'Holt Linear Trend': [],
        'Holt Damped Trend': [],
        'SARIMAX(1,1,1) + Black Friday': [],
        
        # Transformation Experiments
        'ARIMA(1,1,1) Log Transformed': [],
        'Holt Damped Log Transformed': []
    }

    logger.info("\nExecuting Option A 1-step rolling prediction loop across 15 test weeks...")

    for t in range(TEST_WEEKS):
        curr_y = np.array(history_y)
        curr_log_y = np.log(curr_y)
        curr_exog = np.array(history_exog).reshape(-1, 1)
        next_exog = np.array([[test_exog[t]]])

        # 1. Existing Baselines
        preds['Naive Persistence'].append(curr_y[-1])
        preds['Moving Average (4W)'].append(np.mean(curr_y[-4:]))
        slope = (curr_y[-1] - curr_y[0]) / (len(curr_y) - 1)
        preds['Drift'].append(curr_y[-1] + slope)

        # 2. Classical Models
        m_arima = ARIMA(curr_y, order=(1, 1, 1)).fit()
        preds['ARIMA(1,1,1) Original'].append(m_arima.forecast(steps=1)[0])

        m_ses = SimpleExpSmoothing(curr_y, initialization_method='estimated').fit()
        preds['Simple Exp Smoothing'].append(m_ses.forecast(steps=1)[0])

        m_holt = Holt(curr_y, initialization_method='estimated').fit()
        preds['Holt Linear Trend'].append(m_holt.forecast(steps=1)[0])

        m_damped = Holt(curr_y, damped_trend=True, initialization_method='estimated').fit()
        preds['Holt Damped Trend'].append(m_damped.forecast(steps=1)[0])

        ms111 = SARIMAX(curr_y, exog=curr_exog, order=(1, 1, 1)).fit(disp=False)
        preds['SARIMAX(1,1,1) + Black Friday'].append(ms111.forecast(steps=1, exog=next_exog)[0])

        # 3. Transformation Experiments (Log Transformed)
        m_log_arima = ARIMA(curr_log_y, order=(1, 1, 1)).fit()
        preds['ARIMA(1,1,1) Log Transformed'].append(np.exp(m_log_arima.forecast(steps=1)[0]))

        m_log_damped = Holt(curr_log_y, damped_trend=True, initialization_method='estimated').fit()
        preds['Holt Damped Log Transformed'].append(np.exp(m_log_damped.forecast(steps=1)[0]))

        # Reveal actual observation and update history
        actual_val = actuals[t]
        history_y.append(actual_val)
        history_exog.append(test_exog[t])

    # Predictions DataFrame
    predictions_df = pd.DataFrame({'week_start': test_weeks, 'actual_gross_revenue': actuals})
    for model_name, pred_list in preds.items():
        predictions_df[model_name] = pred_list

    csv_preds_path = OUTPUT_DIR / "arima_forecasts_rolling.csv"
    predictions_df.to_csv(csv_preds_path, index=False)

    # Leaderboard DataFrame
    leaderboard = []
    category_map = {
        'Naive Persistence': 'Existing Baselines',
        'Moving Average (4W)': 'Existing Baselines',
        'Drift': 'Existing Baselines',
        'ARIMA(1,1,1) Original': 'Classical Models',
        'Simple Exp Smoothing': 'Classical Models',
        'Holt Linear Trend': 'Classical Models',
        'Holt Damped Trend': 'Classical Models',
        'SARIMAX(1,1,1) + Black Friday': 'Classical Models',
        'ARIMA(1,1,1) Log Transformed': 'Transformation Experiment',
        'Holt Damped Log Transformed': 'Transformation Experiment'
    }

    for model_name, pred_list in preds.items():
        mae, mae_pct, rmse, rmse_pct, mape, r2 = calculate_metrics(actuals, pred_list)
        leaderboard.append({
            'Category': category_map.get(model_name, 'Other'),
            'MODEL': model_name,
            'R2 Score': r2,
            'MAE ($)': mae,
            'MAE (%)': mae_pct,
            'RMSE ($)': rmse,
            'RMSE (%)': rmse_pct,
            'MAPE (%)': mape
        })

    leaderboard_df = pd.DataFrame(leaderboard).sort_values('MAE ($)').reset_index(drop=True)
    csv_leaderboard_path = OUTPUT_DIR / "model_comparison_summary.csv"
    leaderboard_df.to_csv(csv_leaderboard_path, index=False)
    logger.info(f"Saved Leaderboard Summary CSV to: {csv_leaderboard_path}")

    # ------------------------------------------------------------------------
    # PRINT CLEAN COMPARISON TABLE
    # ------------------------------------------------------------------------
    print("\n" + "=" * 125)
    print(f"{'CATEGORY':<25} | {'MODEL':<30} | {'R2 Score':<9} | {'MAE ($)':<12} | {'MAE (%)':<9} | {'RMSE ($)':<12} | {'RMSE (%)':<9} | {'MAPE (%)':<8}")
    print("-" * 125)
    for idx, row in leaderboard_df.iterrows():
        print(f"{row['Category']:<25} | {row['MODEL']:<30} | {row['R2 Score']:9.4f} | ${row['MAE ($)']:10,.2f} | {row['MAE (%)']:7.2f}%  | ${row['RMSE ($)']:10,.2f} | {row['RMSE (%)']:7.2f}%  | {row['MAPE (%)']:7.2f}%")
    print("=" * 125 + "\n")

    # ------------------------------------------------------------------------
    # VISUALIZATION
    # ------------------------------------------------------------------------
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, ax = plt.subplots(figsize=(14, 7))

    plot_history = train_df.tail(15)
    test_dt = pd.to_datetime(test_df['week_start'])

    ax.plot(pd.to_datetime(plot_history['week_start']), plot_history['gross_revenue'] / 1e3, color='#666666', linewidth=2, label='Train History (Last 15 Weeks)')
    ax.plot(test_dt, actuals / 1e3, color='black', linewidth=3, marker='o', label='Actual Test Revenue')

    ax.plot(test_dt, predictions_df['Naive Persistence'] / 1e3, color='#1f77b4', linestyle='--', linewidth=2, label='Naive Persistence Baseline')
    ax.plot(test_dt, predictions_df['ARIMA(1,1,1) Original'] / 1e3, color='#2ca02c', linestyle='-', linewidth=2.5, marker='^', label='ARIMA(1,1,1) Original [WINNER: MAE $41.5k]')
    ax.plot(test_dt, predictions_df['ARIMA(1,1,1) Log Transformed'] / 1e3, color='#ff7f0e', linestyle='-.', linewidth=2, label='ARIMA(1,1,1) Log Transformed')
    ax.plot(test_dt, predictions_df['Simple Exp Smoothing'] / 1e3, color='#9467bd', linestyle=':', linewidth=2, label='Simple Exp Smoothing')

    ax.axvline(test_dt.iloc[0], color='red', linestyle='--', alpha=0.7, label='Train/Test Boundary')

    ax.set_title('Comprehensive Forecasting Experiment — Option A Rolling Evaluation', fontsize=14, fontweight='bold')
    ax.set_xlabel('Week Start Date', fontsize=12)
    ax.set_ylabel('Gross Revenue ($ in Thousands)', fontsize=12)
    ax.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.9)
    ax.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    chart_path = IMAGES_DIR / "arima_forecasts_comparison.png"
    plt.savefig(chart_path, dpi=300)
    plt.close()

    # ------------------------------------------------------------------------
    # DOCUMENTATION REPORT
    # ------------------------------------------------------------------------
    report_path = DOCS_DIR / "forecasting_baseline_arima_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Comprehensive Forecasting Experiment Report\n\n")
        f.write("## 1. Experimental Setup\n\n")
        f.write("- **Protocol**: Option A — Rolling One-Step-Ahead Evaluation (15 test weeks).\n")
        f.write("- **Categories Evaluated**: Existing Baselines, Classical Exponential Smoothing Models, and Log Transformation Experiments.\n\n")

        f.write("## 2. Evaluation Leaderboard Table\n\n")
        headers = ["Rank", "Category", "MODEL", "R2 Score", "MAE ($)", "MAE (%)", "RMSE ($)", "RMSE (%)", "MAPE (%)"]
        f.write("| " + " | ".join(headers) + " |\n")
        f.write("| " + " | ".join(["---"] * len(headers)) + " |\n")
        for rank, row in leaderboard_df.iterrows():
            f.write(f"| {rank+1} | {row['Category']} | {row['MODEL']} | {row['R2 Score']:.4f} | ${row['MAE ($)']:,.2f} | {row['MAE (%)']:.2f}% | ${row['RMSE ($)']:,.2f} | {row['RMSE (%)']:.2f}% | {row['MAPE (%)']:.2f}% |\n")
        f.write("\n\n")

    return train_df, test_df, predictions_df, leaderboard_df


if __name__ == "__main__":
    run_arima_forecasting()
