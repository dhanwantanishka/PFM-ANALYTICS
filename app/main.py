"""PFM Analytics — Streamlit dashboard entry point (landing overview)."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_APP_DIR = Path(__file__).resolve().parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

from components.charts import income_vs_expenses_bar, net_worth_trend, savings_rate_gauge  # noqa: E402
from components.filters import apply_filters, render_sidebar_filters  # noqa: E402
from components.kpi_cards import render_kpi_row  # noqa: E402
from utils.data_loader import get_user_options, load_transactions  # noqa: E402

st.set_page_config(
    page_title="PFM Analytics",
    page_icon="\U0001F4B0",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("\U0001F4B0 Personal Finance Management — Analytics")
st.caption("Inventive BizPro Technologies Pvt. Ltd. · Python Internship 2026")

transactions = load_transactions()
filters = render_sidebar_filters(transactions, get_user_options())
filtered = apply_filters(transactions, filters)

if filtered.empty:
    st.warning("No transactions match the selected filters.")
    st.stop()

income = float(filtered.loc[filtered["is_income"], "amount"].sum())
expenses = float(filtered.loc[~filtered["is_income"], "amount"].sum())
net_flow = income - expenses
savings_rate_pct = round((income - expenses) / income * 100, 1) if income > 0 else 0.0

render_kpi_row(
    [
        {"label": "Total Income", "value": f"₹{income:,.0f}"},
        {"label": "Total Expenses", "value": f"₹{expenses:,.0f}"},
        {"label": "Net Cash Flow", "value": f"₹{net_flow:,.0f}"},
        {"label": "Savings Rate", "value": f"{savings_rate_pct}%"},
    ]
)

col_left, col_right = st.columns([3, 2])
with col_left:
    st.plotly_chart(income_vs_expenses_bar(filtered), use_container_width=True)
with col_right:
    st.plotly_chart(savings_rate_gauge(savings_rate_pct), use_container_width=True)

st.plotly_chart(net_worth_trend(filtered), use_container_width=True)