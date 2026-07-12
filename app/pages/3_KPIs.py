"""Financial KPIs page — savings rate, DTI, budget variance, 50/30/20 rule."""

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

from components.charts import kpi_progress_bar  # noqa: E402
from components.filters import apply_filters, render_sidebar_filters  # noqa: E402
from components.kpi_cards import render_kpi_row  # noqa: E402
from utils.data_loader import get_user_options, load_budgets, load_transactions  # noqa: E402

from pfm.analytics.kpi_engine import (  # noqa: E402
    budget_variance,
    debt_to_income_ratio,
    emergency_fund_coverage,
    savings_rate,
    spending_50_30_20,
)
from pfm.config import NEEDS_CATEGORIES, SAVINGS_CATEGORIES, WANTS_CATEGORIES  # noqa: E402

st.set_page_config(page_title="KPIs · PFM Analytics", page_icon="📈", layout="wide")
st.title("📈 Financial KPIs")

transactions = load_transactions()
budgets = load_budgets()
filters = render_sidebar_filters(transactions, get_user_options())
filtered = apply_filters(transactions, filters)

if filtered.empty:
    st.warning("No transactions match the selected filters.")
    st.stop()

savings = savings_rate(filtered, filters.user_id)
dti = debt_to_income_ratio(filtered, filters.user_id)
emergency = emergency_fund_coverage(filtered, filters.user_id)
rule = spending_50_30_20(filtered, filters.user_id, NEEDS_CATEGORIES, WANTS_CATEGORIES, SAVINGS_CATEGORIES)
variance = budget_variance(filtered, budgets, filters.user_id)

render_kpi_row(
    [
        {"label": "Savings Rate", "value": f"{savings['rate']}%", "help": "(Income − Expenses) / Income × 100"},
        {"label": "Debt-to-Income", "value": f"{dti['dti']}%", "help": "Monthly debt / gross monthly income"},
        {
            "label": "Emergency Fund",
            "value": f"{emergency['coverage_months']} mo",
            "help": "Liquid savings ÷ average monthly expenses",
        },
        {
            "label": "Total Budget Variance",
            "value": f"₹{variance['variance'].sum():,.0f}",
            "help": "Actual spend − budgeted amount (positive = overspend)",
        },
    ]
)

st.subheader("50/30/20 Rule — Target vs Actual")
st.plotly_chart(kpi_progress_bar(rule["needs_pct"], rule["needs_target"], "Needs"), use_container_width=True)
st.plotly_chart(kpi_progress_bar(rule["wants_pct"], rule["wants_target"], "Wants"), use_container_width=True)
st.plotly_chart(
    kpi_progress_bar(100 - rule["savings_pct"], 100 - rule["savings_target"], "Savings (inverted)"),
    use_container_width=True,
)
st.caption(
    f"Needs ₹{rule['needs_amt']:,.0f} · Wants ₹{rule['wants_amt']:,.0f} · "
    f"Savings-linked ₹{rule['savings_amt']:,.0f}. Dashed line marks the target."
)

st.subheader("Budget Variance by Category")
st.dataframe(
    variance.rename(
        columns={"actual": "Actual (₹)", "budget": "Budget (₹)", "variance": "Variance (₹)", "variance_pct": "Variance (%)"}
    ),
    use_container_width=True,
    hide_index=True,
)

with st.expander("KPI formulae"):
    st.markdown(
        """
- **Savings Rate** = (Income − Expenses) / Income × 100
- **Debt-to-Income** = Avg Monthly Debt Payments / Avg Monthly Income × 100
- **Budget Variance** = Actual Spend − Budgeted Amount (positive = overspend)
- **Emergency Fund Coverage** = Liquid Savings ÷ (Avg Monthly Expenses × target months)
- **50/30/20 Rule** = Needs ≤ 50%, Wants ≤ 30%, Savings ≥ 20% of expense-side spend
        """
    )
