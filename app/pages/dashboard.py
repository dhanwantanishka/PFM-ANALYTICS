"""Executive dashboard — financial health, trends, insights, and alerts."""

from __future__ import annotations

import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parents[1]
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

import streamlit as st

import utils.bootstrap  # noqa: F401

from components.charts import (
    budget_progress_chart,
    cash_flow_area,
    income_vs_expenses_bar,
    net_worth_trend,
    savings_rate_gauge,
    savings_trend_line,
)
from components.kpi_cards import render_alert_cards, render_insight_list, render_kpi_row
from components.layout import render_page_header, render_section
from components.page_context import load_page_context
from pfm.analytics.kpi_engine import budget_variance
from services.dashboard_metrics import build_dashboard_summary, generate_alerts, generate_insights
from utils.formatting import format_currency

ctx = load_page_context()
if ctx is None:
    st.stop()

summary = build_dashboard_summary(
    ctx.filtered,
    ctx.budgets,
    ctx.filters.user_id,
    ctx.filters.user_name,
)
mom = summary["mom"]

st.markdown(f"### Welcome back, **{ctx.filters.user_name}** :material/waving_hand:")
st.caption("Your executive financial overview for the selected period.")

render_kpi_row(
    [
        {
            "label": "Financial health",
            "value": f"{summary['health_score']}/100",
            "help": summary["health_rating"],
        },
        {
            "label": "Current balance",
            "value": format_currency(summary["current_balance"]),
        },
        {
            "label": "Monthly savings",
            "value": format_currency(summary["monthly_savings"]),
            "delta": f"{mom['savings_delta']}%" if mom["savings_delta"] is not None else None,
        },
        {
            "label": "Monthly expenses",
            "value": format_currency(summary["monthly_expenses"]),
            "delta": f"{mom['expense_delta']}%" if mom["expense_delta"] is not None else None,
            "delta_color": "inverse",
        },
        {
            "label": "Monthly income",
            "value": format_currency(summary["monthly_income"]),
            "delta": f"{mom['income_delta']}%" if mom["income_delta"] is not None else None,
        },
        {
            "label": "Net cash flow",
            "value": format_currency(summary["net_cash_flow"]),
        },
    ]
)

quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)
with quick_col1:
    if st.button(":material/upload: Upload data", width="stretch"):
        st.switch_page("pages/upload.py")
with quick_col2:
    if st.button(":material/description: Generate report", width="stretch"):
        st.switch_page("pages/reports.py")
with quick_col3:
    if st.button(":material/smart_toy: Ask AI advisor", width="stretch"):
        st.switch_page("pages/advisor.py")
with quick_col4:
    if st.button(":material/receipt_long: View transactions", width="stretch"):
        st.switch_page("pages/transactions.py")

st.space("small")
render_section("Income vs expense", "Monthly comparison for the filtered period")
chart_left, chart_right = st.columns([3, 2])
with chart_left:
    st.plotly_chart(income_vs_expenses_bar(ctx.filtered), width="stretch")
with chart_right:
    st.plotly_chart(savings_rate_gauge(summary["savings_rate"]), width="stretch")

mid_left, mid_right = st.columns(2)
with mid_left:
    render_section("Cash flow")
    st.plotly_chart(cash_flow_area(ctx.filtered), width="stretch")
with mid_right:
    render_section("Savings trend")
    st.plotly_chart(savings_trend_line(ctx.filtered), width="stretch")

variance = budget_variance(ctx.filtered, ctx.budgets, ctx.filters.user_id)
render_section("Budget progress", "Categories closest to or over budget")
st.plotly_chart(budget_progress_chart(variance), width="stretch")

render_section("Net worth trend", "Cumulative net cash flow proxy")
st.plotly_chart(net_worth_trend(ctx.filtered), width="stretch")

bottom_left, bottom_mid, bottom_right = st.columns([1, 1, 1])
with bottom_left:
    render_section("Top categories")
    top_df = summary["top_categories"].reset_index()
    top_df.columns = ["Category", "Total", "Count", "Average"]
    st.dataframe(
        top_df[["Category", "Total"]].assign(Total=lambda d: d["Total"].map(lambda x: f"₹{x:,.0f}")),
        hide_index=True,
        width="stretch",
    )
with bottom_mid:
    render_section("Recent transactions")
    recent = summary["recent_transactions"].copy()
    recent["date"] = recent["date"].dt.strftime("%d %b %Y")
    recent["amount"] = recent["amount"].map(lambda x: f"₹{x:,.0f}")
    st.dataframe(recent[["date", "description", "amount", "category"]], hide_index=True, width="stretch")
with bottom_right:
    render_section("AI insights")
    render_insight_list(generate_insights(summary))

render_section("Alerts & recommendations")
alert_col, rec_col = st.columns(2)
with alert_col:
    render_alert_cards(generate_alerts(summary))
with rec_col:
    if summary["health_recommendations"]:
        for rec in summary["health_recommendations"]:
            st.info(rec)
    else:
        st.success("Your finances look healthy for this period. Keep monitoring monthly trends.")
