"""Financial KPIs — business metrics, health score, and recommendations."""

from __future__ import annotations

import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parents[1]
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

import streamlit as st

import utils.bootstrap  # noqa: F401

from components.charts import health_score_gauge, kpi_progress_bar
from components.kpi_cards import render_kpi_row
from components.layout import render_page_header, render_section
from components.page_context import load_page_context
from pfm.analytics.kpi_engine import (
    budget_variance,
    debt_to_income_ratio,
    emergency_fund_coverage,
    savings_rate,
    spending_50_30_20,
)
from pfm.config import NEEDS_CATEGORIES, SAVINGS_CATEGORIES, WANTS_CATEGORIES
from pfm.models.risk_scorer import financial_health_score

ctx = load_page_context()
if ctx is None:
    st.stop()

render_page_header(
    "Financial KPIs",
    "Business metrics that matter — not just technical stats.",
    ":material/query_stats:",
)

savings = savings_rate(ctx.filtered, ctx.filters.user_id)
dti = debt_to_income_ratio(ctx.filtered, ctx.filters.user_id)
emergency = emergency_fund_coverage(ctx.filtered, ctx.filters.user_id)
rule = spending_50_30_20(
    ctx.filtered,
    ctx.filters.user_id,
    NEEDS_CATEGORIES,
    WANTS_CATEGORIES,
    SAVINGS_CATEGORIES,
)
variance = budget_variance(ctx.filtered, ctx.budgets, ctx.filters.user_id)
health = financial_health_score(ctx.filtered, ctx.budgets, ctx.filters.user_id)
budget_score = health["score_breakdown"]["budget"]
goal_progress = min(100, round(emergency["coverage_months"] / 3 * 100, 1))

score_col, metrics_col = st.columns([1, 2])
with score_col:
    st.plotly_chart(health_score_gauge(health["overall_score"]), width="stretch")
    st.markdown(f"**Rating:** {health['rating']}")
with metrics_col:
    render_kpi_row(
        [
            {"label": "Savings rate", "value": f"{savings['rate']}%", "help": "Target: 20%+"},
            {"label": "Debt ratio (DTI)", "value": f"{dti['dti']}%", "help": "Lower is better"},
            {"label": "Emergency fund", "value": f"{emergency['coverage_months']:.1f} mo", "help": "Target: 3+ months"},
            {"label": "Budget score", "value": f"{budget_score:.0f}/20", "help": "Adherence to budget"},
            {"label": "Needs / wants / savings", "value": f"{rule['needs_pct']}/{rule['wants_pct']}/{rule['savings_pct']}%"},
            {"label": "Goal progress", "value": f"{goal_progress}%", "help": "Emergency fund vs 3-month target"},
        ]
    )

render_section("50/30/20 rule — target vs actual")
st.plotly_chart(kpi_progress_bar(rule["needs_pct"], rule["needs_target"], "Needs"), width="stretch")
st.plotly_chart(kpi_progress_bar(rule["wants_pct"], rule["wants_target"], "Wants"), width="stretch")
st.plotly_chart(
    kpi_progress_bar(100 - rule["savings_pct"], 100 - rule["savings_target"], "Savings (inverted)"),
    width="stretch",
)

render_section("Budget variance by category")
st.dataframe(
    variance.rename(
        columns={
            "actual": "Actual (₹)",
            "budget": "Budget (₹)",
            "variance": "Variance (₹)",
            "variance_pct": "Variance (%)",
        }
    ),
    hide_index=True,
    width="stretch",
)

render_section("Recommendations")
recs = [r for r in health["recommendations"] if r]
if recs:
    for rec in recs:
        st.warning(rec)
else:
    st.success("All KPIs are within healthy ranges for this period.")

with st.expander("KPI formulae"):
    st.markdown(
        """
- **Savings rate** = (Income − Expenses) / Income × 100
- **Debt-to-income** = Avg monthly debt payments / avg monthly income × 100
- **Budget variance** = Actual spend − budgeted amount (positive = overspend)
- **Emergency fund** = Liquid savings ÷ (avg monthly expenses × target months)
- **50/30/20 rule** = Needs ≤ 50%, Wants ≤ 30%, Savings ≥ 20%
- **Financial health score** = Composite 0–100 from savings, budget, debt, consistency, frequency
        """
    )
