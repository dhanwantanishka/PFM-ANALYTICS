"""Bill Reminders page — track upcoming bills and payment due dates."""

from __future__ import annotations

import sys
from datetime import date, timedelta
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
from pfm.db.models import Bill

if "user_id" not in st.session_state:
    st.error("Please log in to manage bills.")
    st.stop()

user_id = st.session_state["user_id"]
today = date.today()

REMINDER_OPTIONS = {
    "1 day before": 1,
    "3 days before": 3,
    "7 days before": 7,
    "14 days before": 14,
}

# ─── Page header ──────────────────────────────────────────────────────────────
st.title(":material/receipt: Bill Reminders")
st.caption("Never miss a payment. Track all your bills and due dates in one place.")

# ─── Add new bill ─────────────────────────────────────────────────────────────
with st.expander(":material/add_circle: Add New Bill", expanded=False):
    with st.form("bill_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            bill_name = st.text_input("Bill Name *", placeholder="e.g., Rent, Netflix, Electricity")
        with col2:
            bill_amount = st.number_input("Amount (₹) *", min_value=1.0, value=None, step=10.0)
        with col3:
            due_date = st.date_input("Due Date *", value=None, min_value=today)

        col4, col5 = st.columns(2)
        with col4:
            is_recurring = st.checkbox("Recurring bill", value=False, help="Repeats every month")
        with col5:
            reminder_label = st.selectbox("Remind me", list(REMINDER_OPTIONS.keys()), index=1)

        submitted = st.form_submit_button("Add Bill", type="primary", use_container_width=True)
        if submitted:
            name_clean = bill_name.strip()
            if not name_clean:
                st.error("Please enter a bill name.")
            elif not bill_amount or bill_amount <= 0:
                st.error("Please enter a valid amount.")
            elif not due_date:
                st.error("Please select a due date.")
            else:
                session = get_session(DB_PATH)
                try:
                    session.add(Bill(
                        name=name_clean,
                        amount=float(bill_amount),
                        due_date=due_date,
                        is_recurring=is_recurring,
                        reminder_days=REMINDER_OPTIONS[reminder_label],
                        user_id=user_id,
                    ))
                    session.commit()
                    st.success(f"✅ Bill **{name_clean}** added! You'll be reminded {reminder_label}.")
                    st.rerun()
                except Exception as e:
                    session.rollback()
                    st.error(f"Error adding bill: {e}")
                finally:
                    session.close()

# ─── Load all bills ───────────────────────────────────────────────────────────
session = get_session(DB_PATH)
try:
    bills = session.query(Bill).filter(Bill.user_id == user_id).order_by(Bill.due_date).all()
finally:
    session.close()

if not bills:
    st.info("No bills added yet. Add your first bill above!")
    st.stop()

# ─── Classify bills ───────────────────────────────────────────────────────────
overdue = [b for b in bills if b.due_date < today]
due_soon = [b for b in bills if today <= b.due_date <= today + timedelta(days=7)]
upcoming = [b for b in bills if b.due_date > today + timedelta(days=7)]

# Summary row
total_overdue_amt = sum(b.amount for b in overdue)
total_due_soon_amt = sum(b.amount for b in due_soon)
total_upcoming_amt = sum(b.amount for b in upcoming)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Bills", str(len(bills)))
m2.metric("Overdue", f"{len(overdue)} (₹{total_overdue_amt:,.0f})", delta=f"-₹{total_overdue_amt:,.0f}" if overdue else None, delta_color="inverse")
m3.metric("Due This Week", f"{len(due_soon)} (₹{total_due_soon_amt:,.0f})")
m4.metric("Upcoming", f"{len(upcoming)} (₹{total_upcoming_amt:,.0f})")

st.markdown("---")


def _render_bill_card(bill: Bill, status: str) -> None:
    days_diff = (bill.due_date - today).days
    reminder_due = today >= bill.due_date - timedelta(days=bill.reminder_days)

    with st.container(border=True):
        col_icon, col_info, col_amount, col_actions = st.columns([0.5, 4, 2, 1])

        with col_icon:
            if status == "overdue":
                st.markdown("### 🔴")
            elif reminder_due:
                st.markdown("### 🟡")
            else:
                st.markdown("### 🟢")

        with col_info:
            recurring_badge = " 🔄" if bill.is_recurring else ""
            st.markdown(f"**{bill.name}**{recurring_badge}")
            if status == "overdue":
                st.caption(f"⚠️ Overdue by {abs(days_diff)} day(s) — was due {bill.due_date.strftime('%d %b %Y')}")
            elif days_diff == 0:
                st.caption("⚡ **Due TODAY!**")
            elif days_diff == 1:
                st.caption("🔔 Due **tomorrow**")
            else:
                st.caption(f"Due on **{bill.due_date.strftime('%d %b %Y')}** ({days_diff} days away)")

        with col_amount:
            color = "#F87171" if status == "overdue" else ("#FBBF24" if reminder_due else "#94A3B8")
            st.markdown(
                f"<p style='font-size:1.3rem;font-weight:700;color:{color};text-align:right;margin:4px 0'>"
                f"₹{bill.amount:,.0f}</p>",
                unsafe_allow_html=True,
            )

        with col_actions:
            if st.button("🗑️", key=f"del_bill_{bill.id}", help="Delete this bill"):
                del_session = get_session(DB_PATH)
                try:
                    b = del_session.get(Bill, bill.id)
                    if b:
                        del_session.delete(b)
                        del_session.commit()
                    st.rerun()
                except Exception as e:
                    del_session.rollback()
                    st.error(str(e))
                finally:
                    del_session.close()


if overdue:
    st.subheader("🔴 Overdue")
    for bill in overdue:
        _render_bill_card(bill, "overdue")

if due_soon:
    st.subheader("🟡 Due This Week")
    for bill in due_soon:
        _render_bill_card(bill, "soon")

if upcoming:
    st.subheader("🟢 Upcoming")
    for bill in upcoming:
        _render_bill_card(bill, "upcoming")
