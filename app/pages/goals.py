"""Savings Goals page — create and track financial goals with progress bars."""

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
from pfm.db.models import Goal

if "user_id" not in st.session_state:
    st.error("Please log in to manage goals.")
    st.stop()

user_id = st.session_state["user_id"]

# ─── Page header ──────────────────────────────────────────────────────────────
st.title(":material/savings: Savings Goals")
st.caption("Set financial targets, track progress, and stay motivated.")

# ─── Add new goal ─────────────────────────────────────────────────────────────
with st.expander(":material/add_circle: Create New Goal", expanded=False):
    with st.form("goal_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            goal_name = st.text_input("Goal Name *", placeholder="e.g., MacBook Pro, Emergency Fund, Goa Trip")
        with col2:
            target_amount = st.number_input("Target Amount (₹) *", min_value=1.0, value=None, step=500.0, placeholder="e.g. 220000")

        col3, col4 = st.columns(2)
        with col3:
            saved_amount = st.number_input("Already Saved (₹)", min_value=0.0, value=0.0, step=100.0)
        with col4:
            target_date = st.date_input("Target Date (optional)", value=None, min_value=date.today())

        submitted = st.form_submit_button("Create Goal", type="primary", use_container_width=True)
        if submitted:
            name_clean = goal_name.strip()
            if not name_clean:
                st.error("Please enter a goal name.")
            elif not target_amount or target_amount <= 0:
                st.error("Please enter a valid target amount.")
            else:
                session = get_session(DB_PATH)
                try:
                    session.add(Goal(
                        name=name_clean,
                        target_amount=float(target_amount),
                        saved_amount=float(saved_amount),
                        target_date=target_date,
                        user_id=user_id,
                    ))
                    session.commit()
                    st.success(f"🎯 Goal **{name_clean}** created!")
                    st.rerun()
                except Exception as e:
                    session.rollback()
                    st.error(f"Error: {e}")
                finally:
                    session.close()

# ─── Load goals ───────────────────────────────────────────────────────────────
session = get_session(DB_PATH)
try:
    goals = session.query(Goal).filter(Goal.user_id == user_id).order_by(Goal.id.desc()).all()
finally:
    session.close()

if not goals:
    st.info("No goals yet. Create one above to start saving! 🎯")
    st.stop()

st.markdown("---")

# Summary
total_target = sum(g.target_amount for g in goals)
total_saved = sum(g.saved_amount for g in goals)
m1, m2, m3 = st.columns(3)
m1.metric("Active Goals", str(len(goals)))
m2.metric("Total Saved", f"₹{total_saved:,.0f}")
m3.metric("Total Target", f"₹{total_target:,.0f}")

st.markdown("---")
st.subheader("Your Goals")

for goal in goals:
    pct = min((goal.saved_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0, 100)
    remaining = goal.target_amount - goal.saved_amount
    completed = goal.saved_amount >= goal.target_amount

    # Estimated completion
    est_text = ""
    if goal.target_date:
        days_left = (goal.target_date - date.today()).days
        if days_left > 0 and remaining > 0:
            monthly_needed = remaining / (days_left / 30)
            est_text = f"₹{monthly_needed:,.0f}/month needed · {days_left} days left"
        elif days_left <= 0:
            est_text = "⚠️ Target date has passed"
        else:
            est_text = "🎉 Goal reached!"

    with st.container(border=True):
        header_col, badge_col, actions_col = st.columns([5, 1.5, 1])

        with header_col:
            icon = "✅" if completed else "🎯"
            st.markdown(f"### {icon} {goal.name}")
            st.progress(pct / 100)

            amount_text = f"₹{goal.saved_amount:,.0f} saved of ₹{goal.target_amount:,.0f}"
            if completed:
                st.success(f"🎉 {amount_text} — **Goal achieved!**")
            else:
                st.caption(f"{amount_text} · ₹{remaining:,.0f} to go")
            if est_text:
                st.caption(est_text)

        with badge_col:
            color = "#34D399" if completed else ("#60A5FA" if pct >= 50 else "#FBBF24")
            st.markdown(
                f"<p style='font-size:2rem;font-weight:800;color:{color};text-align:center;margin:12px 0'>"
                f"{pct:.0f}%</p>",
                unsafe_allow_html=True,
            )

        with actions_col:
            # Quick add savings
            if st.button("+ Add", key=f"add_{goal.id}", help="Add savings to this goal"):
                st.session_state[f"add_mode_{goal.id}"] = True
            if st.button("🗑️", key=f"del_{goal.id}", help="Delete goal"):
                st.session_state[f"del_mode_{goal.id}"] = True

        # Add savings inline
        if st.session_state.get(f"add_mode_{goal.id}"):
            with st.form(f"add_savings_{goal.id}"):
                add_amount = st.number_input(
                    f"Add savings to **{goal.name}** (₹)",
                    min_value=1.0, value=None, step=100.0
                )
                c1, c2 = st.columns(2)
                with c1:
                    if st.form_submit_button("Save", type="primary"):
                        if add_amount and add_amount > 0:
                            upd_session = get_session(DB_PATH)
                            try:
                                g = upd_session.get(Goal, goal.id)
                                if g:
                                    g.saved_amount = min(g.saved_amount + add_amount, g.target_amount)
                                    upd_session.commit()
                                del st.session_state[f"add_mode_{goal.id}"]
                                st.rerun()
                            except Exception as e:
                                upd_session.rollback()
                                st.error(str(e))
                            finally:
                                upd_session.close()
                with c2:
                    if st.form_submit_button("Cancel"):
                        del st.session_state[f"add_mode_{goal.id}"]
                        st.rerun()

        # Delete confirmation
        if st.session_state.get(f"del_mode_{goal.id}"):
            st.warning(f"Delete **{goal.name}**? This cannot be undone.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Yes, delete", key=f"yes_del_{goal.id}", type="primary"):
                    del_session = get_session(DB_PATH)
                    try:
                        g = del_session.get(Goal, goal.id)
                        if g:
                            del_session.delete(g)
                            del_session.commit()
                        del st.session_state[f"del_mode_{goal.id}"]
                        st.rerun()
                    except Exception as e:
                        del_session.rollback()
                        st.error(str(e))
                    finally:
                        del_session.close()
            with c2:
                if st.button("Cancel", key=f"cancel_del_{goal.id}"):
                    del st.session_state[f"del_mode_{goal.id}"]
                    st.rerun()
