"""Samples page — Explore fully populated synthetic data."""

from __future__ import annotations

import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parents[1]
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

import streamlit as st

from components.charts import (
    budget_progress_chart,
    cash_flow_area,
    income_vs_expenses_bar,
    net_worth_trend,
    savings_rate_gauge,
    savings_trend_line,
)
from components.kpi_cards import render_alert_cards, render_insight_list, render_kpi_row
from components.layout import render_section
from components.filters import render_sidebar_filters, apply_filters
from components.states import render_empty_state
from utils.data_loader import load_transactions, load_budgets
from pfm.analytics.kpi_engine import budget_variance
from services.dashboard_metrics import build_dashboard_summary, generate_alerts, generate_insights
from utils.formatting import format_currency

st.title("Explore Sample Data")
st.markdown("Here you can explore our fully populated synthetic datasets. This data is completely isolated from your personal account.")

# Hardcoded synthetic users from seed_data.py
SAMPLE_USERS = {
    "Rajesh Sharma": "rajesh_sharma",
    "Priya Singh": "priya_singh",
    "Amit Kumar": "amit_kumar",
    "Tanishka Dhanwan": "tanishka_dhanwan"
}

selected_name = st.selectbox("Select a Sample User Profile to view:", list(SAMPLE_USERS.keys()))
selected_id = SAMPLE_USERS[selected_name]

transactions = load_transactions(selected_id)
budgets = load_budgets(selected_id)

filters = render_sidebar_filters(
    transactions,
    override_user_id=selected_id,
    override_user_name=selected_name
)
filtered = apply_filters(transactions, filters)

if filtered.empty:
    render_empty_state(
        "No transactions match your filters",
        "Try widening the date range or selecting more categories.",
        icon=":material/filter_alt_off:",
    )
    st.stop()

summary = build_dashboard_summary(
    filtered,
    budgets,
    filters.user_id,
    filters.user_name,
)
mom = summary["mom"]

st.markdown(f"### Viewing sample data for **{filters.user_name}** :material/science:")
st.caption("All financial data displayed below is synthetic and generated for demonstration purposes.")

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

st.space("small")
render_section("Income vs expense", "Monthly comparison for the filtered period")
chart_left, chart_right = st.columns([3, 2])
with chart_left:
    st.plotly_chart(income_vs_expenses_bar(filtered), width="stretch")
with chart_right:
    st.plotly_chart(savings_rate_gauge(summary["savings_rate"]), width="stretch")

mid_left, mid_right = st.columns(2)
with mid_left:
    render_section("Cash flow")
    st.plotly_chart(cash_flow_area(filtered), width="stretch")
with mid_right:
    render_section("Savings trend")
    st.plotly_chart(savings_trend_line(filtered), width="stretch")

variance = budget_variance(filtered, budgets, filters.user_id)
render_section("Budget progress", "Categories closest to or over budget")
st.plotly_chart(budget_progress_chart(variance), width="stretch")

render_section("Net worth trend", "Cumulative net cash flow proxy")
st.plotly_chart(net_worth_trend(filtered), width="stretch")

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
