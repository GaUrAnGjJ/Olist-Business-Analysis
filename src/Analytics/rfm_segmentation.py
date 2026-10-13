"""
RFM Segmentation Analysis — Olist E-Commerce Platform
======================================================
Computes Recency, Frequency, and Monetary scores for every unique customer,
assigns segment labels, and answers the core business question:

    "What percentage of customers generate the large portion of total revenue?"

Outputs:
  - data/processed/rfm/rfm_scores.csv         : Full RFM table per customer
  - data/processed/rfm/rfm_segment_summary.csv: Segment-level aggregated stats
  - images/business_analysis/rfm_segmentation.png : 4-panel dashboard
"""

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from pathlib import Path

# ── Style ──────────────────────────────────────────────────────────────────────
sns.set_theme(style="whitegrid")
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['figure.dpi'] = 150

# ── Database path ──────────────────────────────────────────────────────────────
db_path = Path("database/olist_ecommerce.db")
if not db_path.exists():
    db_path = Path("data/olist_ecommerce.db")

conn = sqlite3.connect(db_path)
print(f"[INFO] Connected to database: {db_path.resolve()}")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Pull raw customer-level data from v_customer_orders
# ══════════════════════════════════════════════════════════════════════════════
print("\n[STEP 1] Querying customer order data from v_customer_orders ...")

df_raw = pd.read_sql_query("""
SELECT
    customer_unique_id,
    order_id,
    purchase_timestamp,
    gross_order_value
FROM v_customer_orders
WHERE order_status = 'delivered'
  AND gross_order_value > 0
""", conn)

conn.close()

df_raw['purchase_timestamp'] = pd.to_datetime(df_raw['purchase_timestamp'])
print(f"  Rows fetched  : {len(df_raw):,}")
print(f"  Unique customers: {df_raw['customer_unique_id'].nunique():,}")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Compute R, F, M values per customer
# ══════════════════════════════════════════════════════════════════════════════
print("\n[STEP 2] Computing Recency, Frequency, Monetary per customer ...")

# Snapshot date = day after the latest order in the dataset (analysis reference point)
snapshot_date = df_raw['purchase_timestamp'].max() + pd.Timedelta(days=1)
print(f"  Snapshot date (analysis reference): {snapshot_date.date()}")

df_rfm = (
    df_raw
    .groupby('customer_unique_id')
    .agg(
        last_purchase=('purchase_timestamp', 'max'),
        frequency=('order_id',            'nunique'),
        monetary=('gross_order_value',    'sum')
    )
    .reset_index()
)

df_rfm['recency_days'] = (snapshot_date - df_rfm['last_purchase']).dt.days
df_rfm.drop(columns='last_purchase', inplace=True)

print(f"  Customers with RFM computed: {len(df_rfm):,}")
print(df_rfm[['recency_days', 'frequency', 'monetary']].describe().round(2))

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Score each dimension into quintiles (1–5)
#   Recency  : lower days = more recent = BETTER → score 5
#   Frequency: higher orders = more active  = BETTER → score 5
#   Monetary : higher spend  = more value   = BETTER → score 5
# ══════════════════════════════════════════════════════════════════════════════
print("\n[STEP 3] Assigning quintile scores (1–5) ...")

def quintile_score(series, ascending=True):
    """Score a series into 5 quintile buckets. ascending=True means higher value → higher score."""
    labels = [1, 2, 3, 4, 5] if ascending else [5, 4, 3, 2, 1]
    try:
        return pd.qcut(series, q=5, labels=labels, duplicates='drop').astype(int)
    except ValueError:
        # Fallback for very low cardinality
        return pd.cut(series, bins=5, labels=labels, duplicates='drop').astype(int)

df_rfm['R_score'] = quintile_score(df_rfm['recency_days'],  ascending=False)  # lower days → better
df_rfm['F_score'] = quintile_score(df_rfm['frequency'],     ascending=True)
df_rfm['M_score'] = quintile_score(df_rfm['monetary'],      ascending=True)

df_rfm['RFM_score'] = df_rfm['R_score'] + df_rfm['F_score'] + df_rfm['M_score']

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Assign segment labels based on RFM composite & individual scores
# ══════════════════════════════════════════════════════════════════════════════
print("\n[STEP 4] Assigning segment labels ...")

def assign_segment(row):
    r, f, m, rfm = row['R_score'], row['F_score'], row['M_score'], row['RFM_score']

    if rfm >= 13:
        return 'Champions'           # High across all three
    elif r >= 4 and f >= 3:
        return 'Loyal Customers'     # Recent AND frequent
    elif r >= 4 and f <= 2:
        return 'Promising'           # Recent but low frequency
    elif r >= 3 and rfm >= 9:
        return 'Potential Loyalists' # Mid recency, decent overall score
    elif r <= 2 and f >= 4:
        return 'At Risk'             # Used to buy often but not recent
    elif r <= 2 and f >= 2:
        return 'Need Attention'      # Lapsing moderate buyers
    elif r == 1 and f == 1 and m >= 3:
        return 'Hibernating High-Value' # One-time big spender, gone cold
    elif r == 1 and f == 1:
        return 'Lost'                # One-time buyers, long gone
    else:
        return 'Occasional'          # Catch-all mid-tier

df_rfm['segment'] = df_rfm.apply(assign_segment, axis=1)

seg_order = [
    'Champions',
    'Loyal Customers',
    'Potential Loyalists',
    'Promising',
    'At Risk',
    'Need Attention',
    'Occasional',
    'Hibernating High-Value',
    'Lost',
]

print("\n--- SEGMENT DISTRIBUTION ---")
seg_counts = df_rfm['segment'].value_counts()
for seg in seg_order:
    n = seg_counts.get(seg, 0)
    pct = n / len(df_rfm) * 100
    print(f"  {seg:<26}: {n:>6,} customers ({pct:5.2f}%)")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — Pareto / Revenue Concentration Analysis
# ══════════════════════════════════════════════════════════════════════════════
print("\n[STEP 5] Pareto Revenue Concentration Analysis ...")

total_revenue = df_rfm['monetary'].sum()

# Sort customers by monetary desc, compute cumulative revenue share
df_sorted = df_rfm.sort_values('monetary', ascending=False).reset_index(drop=True)
df_sorted['cum_revenue']     = df_sorted['monetary'].cumsum()
df_sorted['cum_rev_pct']     = df_sorted['cum_revenue'] / total_revenue * 100
df_sorted['cum_cust_pct']    = (df_sorted.index + 1) / len(df_sorted) * 100

# Find thresholds
def pct_customers_for_rev_share(target_pct):
    idx = df_sorted[df_sorted['cum_rev_pct'] >= target_pct].index[0]
    return ((idx + 1) / len(df_sorted) * 100), idx + 1

pct_cust_50, n_50   = pct_customers_for_rev_share(50)
pct_cust_80, n_80   = pct_customers_for_rev_share(80)

print(f"\n  Total Revenue        : ${total_revenue:,.2f}")
print(f"  Total Customers      : {len(df_rfm):,}")
print(f"\n  >> Top {pct_cust_50:.1f}% of customers ({n_50:,} people) generate 50% of revenue")
print(f"  >> Top {pct_cust_80:.1f}% of customers ({n_80:,} people) generate 80% of revenue")


# Segment-level summary
df_seg_summary = (
    df_rfm
    .groupby('segment')
    .agg(
        customer_count=('customer_unique_id', 'count'),
        avg_recency_days=('recency_days',      'mean'),
        avg_frequency=('frequency',            'mean'),
        total_revenue=('monetary',             'sum'),
        avg_monetary=('monetary',              'mean'),
        avg_rfm_score=('RFM_score',            'mean'),
    )
    .reset_index()
)
df_seg_summary['customer_pct'] = df_seg_summary['customer_count'] / len(df_rfm) * 100
df_seg_summary['revenue_pct']  = df_seg_summary['total_revenue']  / total_revenue * 100
df_seg_summary = df_seg_summary.set_index('segment').loc[
    [s for s in seg_order if s in df_seg_summary['segment'].values]
].reset_index()

print("\n--- SEGMENT REVENUE CONCENTRATION ---")
print(f"{'Segment':<26} {'Customers':>10} {'Cust%':>7} {'Revenue ($)':>14} {'Rev%':>7} {'Avg LTV ($)':>12}")
print("-" * 82)
for _, row in df_seg_summary.iterrows():
    print(f"  {row['segment']:<24} {int(row['customer_count']):>10,} {row['customer_pct']:>7.2f}% "
          f"${row['total_revenue']:>13,.2f} {row['revenue_pct']:>7.2f}% ${row['avg_monetary']:>11,.2f}")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 6 — Save outputs
# ══════════════════════════════════════════════════════════════════════════════
print("\n[STEP 6] Saving CSV outputs ...")

rfm_dir = Path("data/processed/rfm")
rfm_dir.mkdir(parents=True, exist_ok=True)

rfm_out = rfm_dir / "rfm_scores.csv"
seg_out  = rfm_dir / "rfm_segment_summary.csv"

df_rfm.to_csv(rfm_out, index=False)
df_seg_summary.to_csv(seg_out, index=False)

print(f"  Saved: {rfm_out.resolve()}")
print(f"  Saved: {seg_out.resolve()}")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 7 — 4-Panel Visualization
# ══════════════════════════════════════════════════════════════════════════════
print("\n[STEP 7] Generating 4-panel RFM dashboard ...")

# Colour palette per segment
SEG_COLORS = {
    'Champions':              '#1a9641',
    'Loyal Customers':        '#52b788',
    'Potential Loyalists':    '#b7e4c7',
    'Promising':              '#fee08b',
    'At Risk':                '#f4a261',
    'Need Attention':         '#e76f51',
    'Occasional':             '#adb5bd',
    'Hibernating High-Value': '#9b5de5',
    'Lost':                   '#d62828',
}

fig = plt.figure(figsize=(20, 16))
fig.suptitle("RFM Customer Segmentation — Olist E-Commerce Platform",
             fontsize=18, fontweight='bold', y=0.98)

# ── Panel 1 (top-left): Pareto Curve — Cumulative Revenue vs Customers ───────
ax1 = fig.add_subplot(2, 2, 1)

ax1.plot(df_sorted['cum_cust_pct'], df_sorted['cum_rev_pct'],
         color='#1f77b4', linewidth=2.5, label='Cumulative Revenue')

# Reference line: perfect equality
ax1.plot([0, 100], [0, 100], 'k--', linewidth=1, alpha=0.4, label='Perfect Equality')

# Annotate 50% and 80% thresholds
for rev_target, color, label_txt in [(50, '#e76f51', '50%'), (80, '#d62828', '80%')]:
    pct_c, _ = pct_customers_for_rev_share(rev_target)
    ax1.axhline(rev_target, color=color, linestyle=':', linewidth=1.5, alpha=0.7)
    ax1.axvline(pct_c,      color=color, linestyle=':', linewidth=1.5, alpha=0.7)
    ax1.annotate(
        f"Top {pct_c:.1f}% customers\n→ {rev_target}% revenue",
        xy=(pct_c, rev_target),
        xytext=(pct_c + 8, rev_target - 12),
        fontsize=8.5, color=color,
        arrowprops=dict(arrowstyle='->', color=color, lw=1.2),
    )

ax1.fill_between(df_sorted['cum_cust_pct'], df_sorted['cum_rev_pct'],
                 df_sorted['cum_cust_pct'], alpha=0.08, color='#1f77b4')

ax1.set_xlabel("Cumulative % of Customers (sorted by spend)", fontsize=10)
ax1.set_ylabel("Cumulative % of Total Revenue", fontsize=10)
ax1.set_title("Pareto Curve — Revenue Concentration", fontsize=12, fontweight='bold')
ax1.legend(fontsize=9)
ax1.set_xlim(0, 100)
ax1.set_ylim(0, 100)
ax1.grid(True, linestyle=':', alpha=0.6)

# ── Panel 2 (top-right): Segment Customer Count & Revenue % (grouped bar) ────
ax2 = fig.add_subplot(2, 2, 2)

segs        = df_seg_summary['segment'].tolist()
cust_pcts   = df_seg_summary['customer_pct'].tolist()
rev_pcts    = df_seg_summary['revenue_pct'].tolist()
x           = np.arange(len(segs))
bar_w       = 0.38

colors_list = [SEG_COLORS.get(s, '#888') for s in segs]

bars_c = ax2.bar(x - bar_w/2, cust_pcts, bar_w, color=colors_list, alpha=0.75, label='Customer %')
bars_r = ax2.bar(x + bar_w/2, rev_pcts,  bar_w, color=colors_list, alpha=1.0,  label='Revenue %', edgecolor='black', linewidth=0.5)

ax2.set_xticks(x)
ax2.set_xticklabels(segs, rotation=35, ha='right', fontsize=8)
ax2.set_ylabel("Percentage (%)", fontsize=10)
ax2.set_title("Customer Share vs Revenue Share per Segment", fontsize=12, fontweight='bold')
ax2.legend(fontsize=9)
ax2.grid(True, axis='y', linestyle=':', alpha=0.6)

for bar, val in zip(bars_r, rev_pcts):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
             f"{val:.1f}%", ha='center', va='bottom', fontsize=7.5, fontweight='bold')

# ── Panel 3 (bottom-left): Monetary Distribution per Segment (box plot) ──────
ax3 = fig.add_subplot(2, 2, 3)

seg_data     = [df_rfm[df_rfm['segment'] == s]['monetary'].values for s in segs]
bp = ax3.boxplot(seg_data, patch_artist=True, vert=True,
                 medianprops=dict(color='black', linewidth=2),
                 flierprops=dict(marker='o', markersize=2, alpha=0.3))

for patch, s in zip(bp['boxes'], segs):
    patch.set_facecolor(SEG_COLORS.get(s, '#888'))
    patch.set_alpha(0.75)

ax3.set_xticks(range(1, len(segs) + 1))
ax3.set_xticklabels(segs, rotation=35, ha='right', fontsize=8)
ax3.set_ylabel("Customer Lifetime Spend (\$)", fontsize=10)
ax3.set_title("Monetary Value Distribution per Segment", fontsize=12, fontweight='bold')
ax3.set_yscale('log')
ax3.grid(True, axis='y', linestyle=':', alpha=0.6)

# ── Panel 4 (bottom-right): RFM Score Distribution heatmap (F vs R) ──────────
ax4 = fig.add_subplot(2, 2, 4)

heatmap_data = (
    df_rfm
    .groupby(['R_score', 'F_score'])['monetary']
    .sum()
    .unstack(fill_value=0)
)

sns.heatmap(
    heatmap_data,
    annot=True,
    fmt='.0f',
    cmap='YlOrRd',
    ax=ax4,
    linewidths=0.5,
    linecolor='white',
    cbar_kws={'label': 'Total Revenue ($)'},
)
ax4.set_xlabel("Frequency Score (1=Low -> 5=High)", fontsize=10)
ax4.set_ylabel("Recency Score (1=Old -> 5=Recent)", fontsize=10)
ax4.set_title("Revenue Heatmap: Recency x Frequency Score", fontsize=12, fontweight='bold')

plt.tight_layout(rect=[0, 0, 1, 0.96])

img_dir = Path("images/business_analysis")
img_dir.mkdir(parents=True, exist_ok=True)
img_path = img_dir / "rfm_segmentation.png"
plt.savefig(img_path, dpi=200, bbox_inches='tight')
plt.close()

print(f"  Chart saved: {img_path.resolve()}")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 8 — Final Pareto Summary Print
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 65)
print("  PARETO REVENUE CONCENTRATION — FINAL SUMMARY")
print("=" * 65)
print(f"  Total Customers  : {len(df_rfm):,}")
print(f"  Total Revenue    : ${total_revenue:,.2f}")
print()

for target in [10, 20, 30, 50, 80]:
    pct_c, n_c = pct_customers_for_rev_share(target)
    rev_these  = df_sorted.iloc[:n_c]['monetary'].sum()
    print(f"  Top {pct_c:5.1f}% customers ({n_c:>6,} people) "
          f"-> ${rev_these:>12,.2f}  ({target}% of revenue)")

print()
print("  Segment breakdown (sorted by revenue %  desc):")
for _, row in df_seg_summary.sort_values('revenue_pct', ascending=False).iterrows():
    print(f"    {row['segment']:<26}  {row['customer_pct']:5.1f}% customers "
          f"-> {row['revenue_pct']:5.1f}% revenue   (avg LTV ${row['avg_monetary']:,.2f})")

print("\n[SUCCESS] RFM Segmentation complete.")
