"""Spending Analysis page — category treemap, merchant leaderboard, trends."""

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

from components.charts import (  # noqa: E402
    category_trend_line,
    dow_category_heatmap,
    merchant_leaderboard_bar,
    spending_treemap,
)
from components.filters import apply_filters, render_sidebar_filters  # noqa: E402
from components.kpi_cards import render_kpi_row  # noqa: E402
from utils.data_loader import get_user_options, load_transactions  # noqa: E402

from pfm.analytics.spending_analysis import (  # noqa: E402
    spending_by_category,
    spending_heatmap_data,
    top_expense_drivers,
)

st.set_page_config(page_title="Spending Analysis · PFM Analytics", page_icon="🛍️", layout="wide")
st.title("🛍️ Spending Analysis")

transactions = load_transactions()
filters = render_sidebar_filters(transactions, get_user_options())
filtered = apply_filters(transactions, filters)

if filtered.empty:
    st.warning("No transactions match the selected filters.")
    st.stop()

expenses = filtered.loc[~filtered["is_income"]]
top_category = spending_by_category(expenses).index[0] if not expenses.empty else "—"
top_drivers, top10_pct = top_expense_drivers(expenses, top_n=10)

render_kpi_row(
    [
        {"label": "Total Spend", "value": f"₹{expenses['amount'].sum():,.0f}"},
        {"label": "Transactions", "value": f"{len(expenses):,}"},
        {"label": "Top Category", "value": str(top_category)},
        {"label": "Top-10 Categories Share", "value": f"{top10_pct:.1f}%"},
    ]
)

st.subheader("Spending Breakdown")
st.plotly_chart(spending_treemap(filtered), use_container_width=True)

col_left, col_right = st.columns(2)
with col_left:
    st.subheader("Top Merchants")
    st.plotly_chart(merchant_leaderboard_bar(filtered, top_n=10), use_container_width=True)
with col_right:
    st.subheader("Day-of-Week × Category Heatmap")
    st.plotly_chart(dow_category_heatmap(spending_heatmap_data(expenses)), use_container_width=True)

st.subheader("Monthly Category Trends")
st.plotly_chart(category_trend_line(filtered), use_container_width=True)

with st.expander("Pareto detail — top expense drivers"):
    st.caption("The 80/20 rule: which categories drive most of the spend.")
    st.dataframe(top_drivers, use_container_width=True)
