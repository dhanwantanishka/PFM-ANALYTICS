"""Budget tracking page — set monthly category budgets and track spending."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parents[1]
_SRC_DIR = _APP_DIR.parent / "src"
for _p in [str(_APP_DIR), str(_SRC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

import utils.bootstrap  # noqa: F401

from pfm.config import DB_PATH
from pfm.db import get_session
from pfm.db.models import Budget, Category, Transaction, Account
from sqlalchemy import func

from theme.tokens import EXPENSE, INCOME, PRIMARY

if "user_id" not in st.session_state:
    st.error("Please log in to manage budgets.")
    st.stop()

user_id = st.session_state["user_id"]
current_month = date.today().strftime("%Y-%m")
display_month = date.today().strftime("%B %Y")

# ─── Page header ──────────────────────────────────────────────────────────────
st.title(":material/account_balance: Budgets")
st.caption(f"Set and track your monthly spending limits for **{display_month}**.")

# ─── Set / Update a budget ────────────────────────────────────────────────────
session = get_session(DB_PATH)
try:
    all_categories = session.query(Category).order_by(Category.name).all()
    expense_categories = [c for c in all_categories if c.budget_type != "income"]
    cat_names = [c.name for c in expense_categories]
    cat_map = {c.name: c.id for c in expense_categories}
finally:
    session.close()

with st.expander(":material/add_circle: Add / Update Budget", expanded=False):
    with st.form("budget_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            budget_category = st.selectbox("Category", cat_names)
        with col2:
            budget_amount = st.number_input("Monthly Limit (₹)", min_value=1.0, value=None, step=100.0, placeholder="e.g. 8000")
        with col3:
            budget_month = st.text_input("Month (YYYY-MM)", value=current_month, max_chars=7)

        submitted = st.form_submit_button("Save Budget", type="primary", use_container_width=True)
        if submitted:
            if not budget_amount or budget_amount <= 0:
                st.error("Please enter a valid budget amount.")
            else:
                session = get_session(DB_PATH)
                try:
                    cat_id = cat_map[budget_category]
                    existing = session.query(Budget).filter(
                        Budget.user_id == user_id,
                        Budget.category_id == cat_id,
                        Budget.month == budget_month,
                    ).first()
                    if existing:
                        existing.amount = budget_amount
                    else:
                        session.add(Budget(
                            category_id=cat_id,
                            month=budget_month,
                            amount=budget_amount,
                            user_id=user_id,
                        ))
                    session.commit()
                    st.success(f"✅ Budget for **{budget_category}** set to ₹{budget_amount:,.0f}/month.")
                    st.rerun()
                except Exception as e:
                    session.rollback()
                    st.error(f"Error saving budget: {e}")
                finally:
                    session.close()

# ─── Load budgets & actual spend for current month ───────────────────────────
session = get_session(DB_PATH)
try:
    budgets_rows = (
        session.query(Budget, Category.name)
        .join(Category, Budget.category_id == Category.id)
        .filter(Budget.user_id == user_id, Budget.month == current_month)
        .all()
    )

    # Actual spend this month per category
    month_start = date(date.today().year, date.today().month, 1)
    spend_rows = (
        session.query(Category.name, func.sum(Transaction.amount).label("spent"))
        .join(Transaction, Transaction.category_id == Category.id)
        .join(Account, Transaction.account_id == Account.id)
        .filter(
            Account.user_id == user_id,
            Transaction.is_income == False,  # noqa: E712
            Transaction.date >= month_start,
        )
        .group_by(Category.name)
        .all()
    )
finally:
    session.close()

spend_map = {row.name: float(row.spent) for row in spend_rows}

if not budgets_rows:
    st.info(f"No budgets set for {display_month}. Use the form above to add one!")
    st.stop()

st.markdown(f"### {display_month} Budget Tracker")
st.markdown("---")

# Summary metrics
total_budget = sum(b.amount for b, _ in budgets_rows)
total_spent = sum(spend_map.get(name, 0.0) for _, name in budgets_rows)
total_remaining = total_budget - total_spent
overall_pct = (total_spent / total_budget * 100) if total_budget > 0 else 0

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Budget", f"₹{total_budget:,.0f}")
m2.metric("Total Spent", f"₹{total_spent:,.0f}", delta=f"{overall_pct:.1f}% used", delta_color="inverse")
m3.metric("Remaining", f"₹{total_remaining:,.0f}", delta_color="normal")
m4.metric("Categories", str(len(budgets_rows)))

st.markdown("---")

# ─── Per-category progress bars ───────────────────────────────────────────────
for budget, cat_name in sorted(budgets_rows, key=lambda x: x[1]):
    spent = spend_map.get(cat_name, 0.0)
    limit = budget.amount
    pct = min((spent / limit * 100) if limit > 0 else 0, 100)
    remaining = limit - spent
    over_budget = spent > limit

    with st.container(border=True):
        col_info, col_pct, col_actions = st.columns([4, 1, 1])
        with col_info:
            # Status icon
            if over_budget:
                icon = "🔴"
            elif pct >= 80:
                icon = "🟡"
            else:
                icon = "🟢"

            st.markdown(f"**{icon} {cat_name}**")

            # Progress bar using Streamlit's native progress
            bar_val = min(pct / 100, 1.0)
            st.progress(bar_val)

            spend_label = f"₹{spent:,.0f} of ₹{limit:,.0f}"
            if over_budget:
                st.caption(f"⚠️ {spend_label} — **over by ₹{abs(remaining):,.0f}**")
            elif pct >= 80:
                st.caption(f"⚠️ {spend_label} — only ₹{remaining:,.0f} remaining (warning!)")
            else:
                st.caption(f"{spend_label} — ₹{remaining:,.0f} remaining")

        with col_pct:
            color = "#F87171" if over_budget else ("#FBBF24" if pct >= 80 else "#34D399")
            st.markdown(
                f"<p style='font-size:1.6rem;font-weight:700;color:{color};text-align:center;margin:8px 0'>"
                f"{pct:.0f}%</p>",
                unsafe_allow_html=True,
            )

        with col_actions:
            if st.button("🗑️", key=f"del_budget_{budget.id}", help="Delete this budget"):
                del_session = get_session(DB_PATH)
                try:
                    b = del_session.get(Budget, budget.id)
                    if b:
                        del_session.delete(b)
                        del_session.commit()
                    st.rerun()
                except Exception as e:
                    del_session.rollback()
                    st.error(str(e))
                finally:
                    del_session.close()

# ─── Alerts ───────────────────────────────────────────────────────────────────
over = [(name, spend_map.get(name, 0), b.amount) for b, name in budgets_rows if spend_map.get(name, 0) > b.amount]
warn = [(name, spend_map.get(name, 0), b.amount) for b, name in budgets_rows
        if b.amount > 0 and spend_map.get(name, 0) / b.amount >= 0.8 and spend_map.get(name, 0) <= b.amount]

if over or warn:
    st.markdown("---")
    st.subheader("🔔 Alerts")
    for name, spent_v, limit_v in over:
        st.error(f"**{name}** exceeded budget by ₹{spent_v - limit_v:,.0f}! (spent ₹{spent_v:,.0f} of ₹{limit_v:,.0f})")
    for name, spent_v, limit_v in warn:
        st.warning(f"**{name}** is at {spent_v/limit_v*100:.0f}% of budget — only ₹{limit_v - spent_v:,.0f} left.")
