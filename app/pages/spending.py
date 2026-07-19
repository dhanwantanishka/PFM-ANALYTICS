"""Spending analysis — category insights, merchants, trends, and recommendations."""

from __future__ import annotations

import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parents[1]
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

import streamlit as st

import utils.bootstrap  # noqa: F401

from components.charts import (
    category_comparison_bar,
    category_pie_bar_combo,
    category_trend_line,
    dow_category_heatmap,
    merchant_leaderboard_bar,
    spending_treemap,
)
from components.kpi_cards import render_category_cards, render_kpi_row
from components.layout import render_page_header, render_section
from components.page_context import load_page_context
from pfm.analytics.spending_analysis import spending_by_category, spending_heatmap_data, top_expense_drivers

ctx = load_page_context()
if ctx is None:
    st.stop()

render_page_header(
    "Spending analysis",
    "Business insights across categories, merchants, and trends.",
    ":material/payments:",
)

expenses = ctx.filtered.loc[~ctx.filtered["is_income"]]
by_category = spending_by_category(expenses)
top_category = by_category.index[0] if not by_category.empty else "—"
top_drivers, top10_pct = top_expense_drivers(expenses, top_n=10)

render_kpi_row(
    [
        {"label": "Total spend", "value": f"₹{expenses['amount'].sum():,.0f}"},
        {"label": "Transactions", "value": f"{len(expenses):,}"},
        {"label": "Top category", "value": str(top_category)},
        {"label": "Top-10 share", "value": f"{top10_pct:.1f}%"},
    ]
)

render_section("Category overview")
render_category_cards(by_category, top_n=6)

render_section("Spending breakdown", "Interactive treemap — click to drill down")
st.plotly_chart(spending_treemap(ctx.filtered), width="stretch")

combo_left, combo_right = st.columns(2)
with combo_left:
    render_section("Category mix")
    st.plotly_chart(category_pie_bar_combo(ctx.filtered), width="stretch")
with combo_right:
    render_section("Month-over-month comparison")
    st.plotly_chart(category_comparison_bar(ctx.filtered), width="stretch")

merchant_left, merchant_right = st.columns(2)
with merchant_left:
    render_section("Top merchants")
    st.plotly_chart(merchant_leaderboard_bar(ctx.filtered, top_n=10), width="stretch")
with merchant_right:
    render_section("Day-of-week heatmap")
    st.plotly_chart(dow_category_heatmap(spending_heatmap_data(expenses)), width="stretch")

render_section("Monthly category trends")
all_categories = sorted(expenses["category"].unique())
selected = st.multiselect(
    "Focus categories",
    all_categories,
    default=all_categories[:5] if len(all_categories) > 5 else all_categories,
)
st.plotly_chart(category_trend_line(ctx.filtered, categories=selected or None), width="stretch")

with st.expander("Pareto analysis — top expense drivers"):
    st.dataframe(top_drivers, width="stretch")

render_section("Spending recommendations")
if top10_pct > 70:
    st.warning(
        f"Top 10 categories account for {top10_pct:.1f}% of spend — high concentration. "
        "Review the largest categories for negotiation or reduction opportunities."
    )
else:
    st.info("Spending is reasonably diversified across categories.")

if not by_category.empty:
    top_amt = by_category.iloc[0][("amount", "sum")]
    st.markdown(
        f"- **{by_category.index[0]}** is your largest expense at ₹{top_amt:,.0f}. "
        "Set a tighter monthly cap if this category is discretionary."
    )
