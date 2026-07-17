"""Anomaly Detection page — flagged transactions, colour-coded by severity."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_APP_DIR = Path(__file__).resolve().parents[1]
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from components.charts import anomaly_timeline  # noqa: E402
from components.filters import render_sidebar_filters  # noqa: E402
from components.kpi_cards import render_kpi_row, render_severity_table  # noqa: E402
from utils.data_loader import get_user_options, load_transactions  # noqa: E402

from pfm.models.anomaly_detector import (  # noqa: E402
    detect_anomalies_isolation_forest,
    detect_anomalies_zscore,
)

st.set_page_config(page_title="Anomaly Detection · PFM Analytics", page_icon="🚨", layout="wide")
st.title("🚨 Anomaly Detection")

transactions = load_transactions()
filters = render_sidebar_filters(transactions, get_user_options())

user_txns = transactions[
    (transactions["user_id"] == filters.user_id)
    & (transactions["date"].dt.date >= filters.start_date)
    & (transactions["date"].dt.date <= filters.end_date)
]

if len(user_txns.loc[~user_txns["is_income"]]) < 20:
    st.warning("Not enough expense transactions in the selected range to run anomaly detection.")
    st.stop()

col_a, col_b = st.columns(2)
with col_a:
    contamination = st.slider(
        "Isolation Forest contamination", min_value=0.01, max_value=0.15, value=0.05, step=0.01,
        help="Expected proportion of anomalous transactions.",
    )
with col_b:
    zscore_threshold = st.slider(
        "Z-score threshold", min_value=1.5, max_value=4.0, value=3.0, step=0.25,
        help="Number of standard deviations from the mean to flag as anomalous.",
    )

iso_result = detect_anomalies_isolation_forest(user_txns, filters.user_id, contamination=contamination)
z_result = detect_anomalies_zscore(user_txns, filters.user_id, threshold=zscore_threshold)

render_kpi_row(
    [
        {"label": "Isolation Forest Flags", "value": f"{iso_result['anomaly_count']}"},
        {"label": "Z-score Flags", "value": f"{z_result['anomaly_count']}"},
        {"label": "Avg Anomaly Amount (IF)", "value": f"₹{iso_result['mean_anomaly_amount']:,.0f}"},
        {"label": "Avg Normal Amount (IF)", "value": f"₹{iso_result['mean_normal_amount']:,.0f}"},
    ]
)

# Combine both methods for a severity view: flagged by both = High, one method = Medium.
iso_ids = set(iso_result["anomalies"].index)
z_ids = set(z_result["anomalies"].index)
both_ids = iso_ids & z_ids
either_ids = iso_ids | z_ids

expenses = user_txns.loc[~user_txns["is_income"]].copy()
expenses["anomaly"] = expenses.index.isin(either_ids)
expenses["severity"] = "Normal"
expenses.loc[expenses.index.isin(either_ids - both_ids), "severity"] = "Medium"
expenses.loc[expenses.index.isin(both_ids), "severity"] = "High"

st.subheader("Anomaly Timeline")
st.plotly_chart(anomaly_timeline(expenses, anomaly_col="anomaly"), use_container_width=True)

st.subheader("Flagged Transactions")
flagged = expenses.loc[expenses["severity"] != "Normal", ["date", "amount", "category", "merchant", "severity"]]
flagged = flagged.sort_values(["severity", "amount"], ascending=[True, False])
if flagged.empty:
    st.info("No anomalies flagged at the current thresholds.")
else:
    render_severity_table(
        flagged,
        severity_col="severity",
        severity_colors={"High": "#FEE2E2", "Medium": "#FEF3C7"},
    )

with st.expander("Detection methodology"):
    st.markdown(
        """
- **Isolation Forest** — unsupervised model that isolates outliers in `(amount, day_of_week, month)`
  feature space; handles non-Gaussian, arbitrary-shaped distributions. Contamination controls the
  expected outlier fraction.
- **Z-score** — flags transactions more than *k* standard deviations from the user's mean spend;
  best suited to roughly Gaussian amount distributions.
- **Severity** — transactions flagged by **both** methods are marked **High**; flagged by only one
  method are marked **Medium**.
        """
    )
