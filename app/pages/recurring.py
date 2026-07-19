"""Recurring transactions page — schedule and track recurring expenses/income."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parents[1]
_SRC_DIR = _APP_DIR.parent / "src"
for _p in [str(_APP_DIR), str(_SRC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st
import utils.bootstrap  # noqa: F401

from pfm.config import DB_PATH
from pfm.db import get_session
from pfm.db.models import RecurringTransaction, Category, Account

if "user_id" not in st.session_state:
    st.error("Please log in to manage recurring transactions.")
    st.stop()

user_id = st.session_state["user_id"]

# ─── Page header ──────────────────────────────────────────────────────────────
st.title(":material/autorenew: Recurring Transactions")
st.caption("Schedule and manage your automatic expenses and income.")

session = get_session(DB_PATH)
try:
    all_categories = session.query(Category).order_by(Category.name).all()
    user_accounts = session.query(Account).filter(Account.user_id == user_id).all()
finally:
    session.close()

cat_names = [c.name for c in all_categories]
cat_map = {c.name: c.id for c in all_categories}
acc_names = [a.name for a in user_accounts]
acc_map = {a.name: a.id for a in user_accounts}

# ─── Add New Recurring Transaction ────────────────────────────────────────────
with st.expander(":material/add_circle: Add New Schedule", expanded=False):
    if not user_accounts:
        st.warning("You need at least one account to create a recurring transaction.")
    else:
        with st.form("recurring_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                rec_name = st.text_input("Name *", placeholder="e.g. Netflix Subscription, Rent")
                rec_amount = st.number_input("Amount (₹) *", min_value=1.0, value=None, step=100.0)
                rec_type = st.selectbox("Type", ["Expense", "Income"])
            with col2:
                rec_freq = st.selectbox("Frequency", ["Monthly", "Weekly", "Yearly", "Daily"])
                rec_date = st.date_input("Next Date *", min_value=date.today())
                rec_cat = st.selectbox("Category", cat_names)
                rec_acc = st.selectbox("Account", acc_names)

            submitted = st.form_submit_button("Save Schedule", type="primary", use_container_width=True)
            if submitted:
                if not rec_name.strip():
                    st.error("Please enter a name.")
                elif not rec_amount or rec_amount <= 0:
                    st.error("Please enter a valid amount.")
                else:
                    session = get_session(DB_PATH)
                    try:
                        rt = RecurringTransaction(
                            name=rec_name.strip(),
                            amount=float(rec_amount),
                            frequency=rec_freq.lower(),
                            next_date=rec_date,
                            transaction_type=rec_type.lower(),
                            category_id=cat_map[rec_cat],
                            account_id=acc_map[rec_acc],
                            user_id=user_id
                        )
                        session.add(rt)
                        session.commit()
                        st.success(f"✅ Recurring transaction '{rec_name}' scheduled!")
                        st.rerun()
                    except Exception as e:
                        session.rollback()
                        st.error(f"Error saving schedule: {e}")
                    finally:
                        session.close()

# ─── Load Existing Schedules ──────────────────────────────────────────────────
session = get_session(DB_PATH)
try:
    schedules = (
        session.query(RecurringTransaction, Category.name, Account.name)
        .join(Category, RecurringTransaction.category_id == Category.id)
        .join(Account, RecurringTransaction.account_id == Account.id)
        .filter(RecurringTransaction.user_id == user_id)
        .order_by(RecurringTransaction.next_date)
        .all()
    )
finally:
    session.close()

if not schedules:
    st.info("No recurring transactions scheduled. Add one above!")
    st.stop()

st.markdown("---")
st.subheader("Your Schedules")

# Display as cards
for rt, cat_name, acc_name in schedules:
    days_left = (rt.next_date - date.today()).days
    
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
        with c1:
            st.markdown(f"**{rt.name}**")
            st.caption(f"{cat_name} • {acc_name}")
        with c2:
            st.markdown(f"**₹{rt.amount:,.0f}**")
            color = "green" if rt.transaction_type == "income" else "red"
            st.markdown(f"<span style='color:{color};'>{rt.transaction_type.title()} ({rt.frequency.title()})</span>", unsafe_allow_html=True)
        with c3:
            if days_left < 0:
                st.error(f"Overdue: {rt.next_date.strftime('%d %b %Y')}")
            elif days_left == 0:
                st.warning("Due Today!")
            else:
                st.success(f"Next: {rt.next_date.strftime('%d %b %Y')}")
        with c4:
            if st.button("🗑️", key=f"del_rt_{rt.id}", help="Delete this schedule"):
                del_session = get_session(DB_PATH)
                try:
                    obj = del_session.get(RecurringTransaction, rt.id)
                    if obj:
                        del_session.delete(obj)
                        del_session.commit()
                    st.rerun()
                except Exception as e:
                    del_session.rollback()
                    st.error(f"Error: {e}")
                finally:
                    del_session.close()
