"""Anomaly detection — risk level, flagged transactions, and suggested actions."""

from __future__ import annotations

import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parents[1]
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

import streamlit as st

import utils.bootstrap  # noqa: F401

from components.charts import anomaly_timeline
from components.filters import render_sidebar_filters
from components.kpi_cards import render_kpi_row, render_severity_table
from components.layout import render_page_header, render_section
from components.states import render_empty_state
from pfm.models.anomaly_detector import detect_anomalies_isolation_forest, detect_anomalies_zscore
from utils.data_loader import load_transactions

render_page_header(
    "Anomaly detection",
    "Identify suspicious transactions with severity scoring and recommended actions.",
    ":material/warning:",
)

user_id = st.session_state.get("user_id", "user_1")
transactions = load_transactions(user_id)
filters = render_sidebar_filters(transactions)

user_txns = transactions[
    (transactions["date"].dt.date >= filters.start_date)
    & (transactions["date"].dt.date <= filters.end_date)
]

if len(user_txns.loc[~user_txns["is_income"]]) < 20:
    render_empty_state(
        "Not enough data",
        "Need at least 20 expense transactions in the selected range.",
        ":material/data_threshold:",
    )
    st.stop()

filter_col1, filter_col2, filter_col3 = st.columns(3)
with filter_col1:
    contamination = st.slider("Isolation Forest contamination", 0.01, 0.15, 0.05, 0.01)
with filter_col2:
    zscore_threshold = st.slider("Z-score threshold", 1.5, 4.0, 3.0, 0.25)
with filter_col3:
    severity_filter = st.multiselect("Severity filter", ["High", "Medium"], default=["High", "Medium"])

iso_result = detect_anomalies_isolation_forest(user_txns, filters.user_id, contamination=contamination)
z_result = detect_anomalies_zscore(user_txns, filters.user_id, threshold=zscore_threshold)

iso_ids = set(iso_result["anomalies"].index)
z_ids = set(z_result["anomalies"].index)
both_ids = iso_ids & z_ids
either_ids = iso_ids | z_ids

expenses = user_txns.loc[~user_txns["is_income"]].copy()
expenses["anomaly"] = expenses.index.isin(either_ids)
expenses["severity"] = "Normal"
expenses.loc[expenses.index.isin(either_ids - both_ids), "severity"] = "Medium"
expenses.loc[expenses.index.isin(both_ids), "severity"] = "High"

risk_level = "Low"
if len(both_ids) >= 5:
    risk_level = "High"
elif len(either_ids) >= 3:
    risk_level = "Medium"

render_kpi_row(
    [
        {"label": "Risk level", "value": risk_level},
        {"label": "IF flags", "value": str(iso_result["anomaly_count"])},
        {"label": "Z-score flags", "value": str(z_result["anomaly_count"])},
        {"label": "High severity", "value": str(len(both_ids))},
    ]
)

render_section("Interactive timeline")
st.plotly_chart(anomaly_timeline(expenses, anomaly_col="anomaly"), width="stretch")

render_section("Suspicious transactions")
flagged = expenses.loc[expenses["severity"] != "Normal"].copy()
flagged["reason"] = flagged["severity"].map(
    {
        "High": "Flagged by Isolation Forest AND Z-score",
        "Medium": "Flagged by one detection method",
    }
)
flagged["suggested_action"] = flagged["severity"].map(
    {
        "High": "Review immediately — verify merchant and amount",
        "Medium": "Monitor — confirm this transaction is expected",
    }
)
flagged = flagged[flagged["severity"].isin(severity_filter)]
display = flagged[
    ["date", "amount", "category", "merchant", "severity", "reason", "suggested_action"]
].sort_values(["severity", "amount"], ascending=[True, False])

if display.empty:
    st.info("No anomalies match the current filters.")
else:
    render_severity_table(
        display,
        severity_col="severity",
        severity_colors={"High": "#7F1D1D", "Medium": "#713F12"},
    )

with st.expander("Detection methodology"):
    st.markdown(
        """
- **Isolation Forest** — unsupervised outlier detection in `(amount, day_of_week, month)` space.
- **Z-score** — flags transactions beyond *k* standard deviations from the user's mean spend.
- **Severity** — both methods = **High**; one method = **Medium**.
        """
    )
