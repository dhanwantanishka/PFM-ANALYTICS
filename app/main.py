"""PFM Analytics — Streamlit dashboard entry point."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_APP_DIR = Path(__file__).resolve().parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

from utils.data_loader import load_budgets, load_transactions  # noqa: E402

st.set_page_config(
    page_title="PFM Analytics",
    page_icon="\U0001F4B0",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("\U0001F4B0 Personal Finance Management — Analytics")
st.caption("Inventive BizPro Technologies Pvt. Ltd. · Python Internship 2026")

transactions = load_transactions()
budgets = load_budgets()

st.success(
    f"Loaded {len(transactions):,} transactions for "
    f"{transactions['user_id'].nunique()} users, "
    f"{transactions['date'].dt.to_period('M').nunique()} months."
)

st.markdown(
    """
Use the sidebar to navigate between pages:

- **Overview** — income vs. expenses, savings rate, net cash flow
- **Spending Analysis** — category treemap, merchant leaderboard, trends
- **KPIs** — savings rate, DTI, budget variance, 50/30/20 breakdown
- **Forecasting** — expense forecast with model comparison
- **Anomaly Detection** — flagged transactions by severity
- **Settings** — data, model, and display preferences
"""
)
