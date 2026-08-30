import sys
import os
import time
import subprocess
from pathlib import Path

# Ensure UTF-8 output encoding for console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Root Project Directory
BASE_DIR = Path(__file__).resolve().parent

# Ensure output directories exist
(BASE_DIR / "images" / "business_analysis").mkdir(parents=True, exist_ok=True)
(BASE_DIR / "images" / "eda").mkdir(parents=True, exist_ok=True)
(BASE_DIR / "images" / "model").mkdir(parents=True, exist_ok=True)
(BASE_DIR / "data" / "processed" / "kpi").mkdir(parents=True, exist_ok=True)
(BASE_DIR / "data" / "processed" / "cleaning").mkdir(parents=True, exist_ok=True)
(BASE_DIR / "data" / "processed" / "remaining").mkdir(parents=True, exist_ok=True)
(BASE_DIR / "database").mkdir(parents=True, exist_ok=True)

# Define full pipeline execution steps grouped by stage
PIPELINE_STAGES = [
    {
        "stage_name": "STAGE 1: Database Setup & Data Quality Engineering",
        "description": "Initialize SQLite schema, load raw CSV datasets, clean timestamps, and build core analytical views.",
        "scripts": [
            ("1.1", "Create Database Schema", BASE_DIR / "src" / "Notebooks" / "create_database.py"),
            ("1.2", "Load CSV Data to SQLite", BASE_DIR / "src" / "Notebooks" / "load_database.py"),
            ("1.3", "Execute Data Cleaning & Standardization", BASE_DIR / "src" / "Notebooks" / "data_cleaning.py"),
            ("1.4", "Build Core Analytical SQL Views", BASE_DIR / "src" / "Notebooks" / "create_views.py"),
            ("1.5", "Validate View Integrity & Referential Constraints", BASE_DIR / "src" / "Notebooks" / "validate_views.py"),
        ]
    },
    {
        "stage_name": "STAGE 2: Time-Series Analysis & Revenue Forecasting Pipeline",
        "description": "Generate continuous weekly time-series, run stationarity & ACF tests, train baseline/ARIMA/ML models, and calibrate 95% conformal prediction intervals.",
        "scripts": [
            ("2.1", "Create Weekly Forecast Dataset", BASE_DIR / "src" / "model" / "create_weekly_forecast_dataset.py"),
            ("2.2", "Execute Time-Series EDA & Decomposition", BASE_DIR / "src" / "model" / "time_series_eda.py"),
            ("2.3", "Train & Evaluate Baseline Forecasting Models", BASE_DIR / "src" / "model" / "forecast_baseline.py"),
            ("2.4", "Train & Evaluate Classical ARIMA Models", BASE_DIR / "src" / "model" / "forecast_arima.py"),
            ("2.5", "Train & Evaluate Component Supervised ML Models", BASE_DIR / "src" / "model" / "forecast_components_ml.py"),
            ("2.6", "Calibrate Sequential Conformal Prediction Intervals (EnbPI)", BASE_DIR / "src" / "model" / "forecast_conformal.py"),
        ]
    },
    {
        "stage_name": "STAGE 3: Diagnostic Business Questions (Q.1 through Q.9)",
        "description": "Execute empirical analytical modules to diagnose revenue drivers, anomalies, category Pareto, freight friction, retention, regional logistics, and review drivers.",
        "scripts": [
            ("3.1", "Q1: Revenue Drivers (Order Volume vs. AOV)", BASE_DIR / "src" / "Analytics" / "q1_revenue_drivers.py"),
            ("3.2", "Q2: Anomaly Detection (Black Friday & Truckers' Strike)", BASE_DIR / "src" / "Analytics" / "q2_unusual_sales_periods.py"),
            ("3.3", "Q3: Category Concentration (Top Revenue & Volume Categories)", BASE_DIR / "src" / "Analytics" / "q3_top_categories.py"),
            ("3.4", "Q4: Freight Burden Analysis (Bulky Goods vs. Consumables)", BASE_DIR / "src" / "Analytics" / "q4_freight_burden_categories.py"),
            ("3.5", "Q5: Repeat-Purchase Behavior & Latency Peak", BASE_DIR / "src" / "Analytics" / "q5_repeat_purchase_behavior.py"),
            ("3.6", "Q6: Regional Concentration (Customer & Revenue Distribution)", BASE_DIR / "src" / "Analytics" / "q6_regional_customer_revenue.py"),
            ("3.7", "Q7: Regional Delivery Performance & Delays", BASE_DIR / "src" / "Analytics" / "q7_regional_delivery_performance.py"),
            ("3.8", "Q8: Drivers of Low Review Scores (The 3-Day Delay Cliff)", BASE_DIR / "src" / "Analytics" / "q8_low_review_score_drivers.py"),
            ("3.9", "Q9: Future Revenue Range (4-Week Out-of-Sample Forecast)", BASE_DIR / "src" / "Analytics" / "q9_future_revenue_range.py"),
        ]
    }
]

def print_banner(text, char="=", width=80):
    print("\n" + char * width)
    print(text.center(width))
    print(char * width + "\n")

def run_script(step_num, step_title, script_path):
    print(f"[{step_num}] Running {step_title}...")
    print(f"    Path: {script_path.relative_to(BASE_DIR)}")
    
    if not script_path.exists():
        print(f"    ❌ ERROR: Script file not found: {script_path}")
        return False, 0.0

    start_time = time.time()
    
    # Set environment with UTF-8 encoding
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(BASE_DIR),
            env=env,
            check=True,
            text=True,
            capture_output=True
        )
        elapsed_time = time.time() - start_time
        print(f"    ✅ Completed in {elapsed_time:.2f}s")
        return True, elapsed_time
    except subprocess.CalledProcessError as e:
        elapsed_time = time.time() - start_time
        print(f"    ❌ ERROR: Step {step_num} failed with return code {e.returncode}")
        if e.stdout:
            print("--- STDOUT ---")
            print(e.stdout[-1000:])
        if e.stderr:
            print("--- STDERR ---")
            print(e.stderr[-1000:])
        return False, elapsed_time

def main():
    start_total_time = time.time()
    print_banner("OLIST E-COMMERCE END-TO-END AUTOMATED ANALYTICS PIPELINE")
    print(f"Root Execution Path: {BASE_DIR}")
    print(f"Python Interpreter:  {sys.executable}")
    print(f"Start Time:          {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    total_steps = sum(len(stage["scripts"]) for stage in PIPELINE_STAGES)
    completed_steps = 0
    failed_steps = []
    execution_summary = []

    for stage_idx, stage in enumerate(PIPELINE_STAGES, 1):
        print_banner(stage["stage_name"], char="-")
        print(f"Description: {stage['description']}\n")
        
        stage_start_time = time.time()
        stage_passed = 0
        
        for step_num, step_title, script_path in stage["scripts"]:
            success, elapsed = run_script(step_num, step_title, script_path)
            if success:
                completed_steps += 1
                stage_passed += 1
                execution_summary.append((step_num, step_title, "PASS", elapsed))
            else:
                failed_steps.append((step_num, step_title, script_path))
                execution_summary.append((step_num, step_title, "FAIL", elapsed))
        
        stage_elapsed = time.time() - stage_start_time
        print(f"\nStage {stage_idx} Summary: {stage_passed}/{len(stage['scripts'])} steps passed ({stage_elapsed:.2f}s)")

    total_elapsed = time.time() - start_total_time
    
    print_banner("PIPELINE EXECUTION FINAL SUMMARY")
    print(f"Total Execution Time: {total_elapsed:.2f} seconds ({total_elapsed/60:.2f} minutes)")
    print(f"Steps Succeeded:      {completed_steps}/{total_steps}")
    print(f"Steps Failed:         {len(failed_steps)}/{total_steps}\n")

    print(f"{'Step':<8} {'Task Description':<60} {'Status':<8} {'Time':<8}")
    print("-" * 80)
    for step_num, title, status, elapsed in execution_summary:
        status_str = "✅ PASS" if status == "PASS" else "❌ FAIL"
        print(f"{step_num:<8} {title[:58]:<60} {status_str:<8} {elapsed:>6.2f}s")
    print("-" * 80)

    if failed_steps:
        print("\n❌ The following steps encountered failures:")
        for step_num, title, path in failed_steps:
            print(f"  - [{step_num}] {title}: {path}")
        sys.exit(1)
    else:
        print("\n🎉 SUCCESS: Entire Olist E-Commerce pipeline executed from scratch with zero errors!")
        print("All analytical datasets, database views, forecasting models, and business visualizations have been regenerated.")

if __name__ == "__main__":
    main()
