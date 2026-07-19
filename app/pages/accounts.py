"""Accounts management page — create and manage financial accounts."""

from __future__ import annotations

import sys
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
from pfm.db.models import Account

# ─── Auth guard ───────────────────────────────────────────────────────────────
if "user_id" not in st.session_state:
    st.error("Please log in to manage your accounts.")
    st.stop()

user_id = st.session_state["user_id"]

ACCOUNT_TYPES = ["Bank", "Cash", "Credit Card", "UPI", "Wallet", "Investment", "Loan"]

# ─── Page header ──────────────────────────────────────────────────────────────
st.title(":material/account_balance_wallet: Accounts")
st.caption("Manage your financial accounts. All balances reflect real transactions.")

# ─── Add new account ──────────────────────────────────────────────────────────
with st.expander(":material/add_circle: Add New Account", expanded=False):
    with st.form("add_account_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            acc_name = st.text_input("Account Name", placeholder="e.g., HDFC Savings, Paytm Wallet")
        with col2:
            acc_type = st.selectbox("Account Type", ACCOUNT_TYPES)
        opening_balance = st.number_input(
            "Opening Balance (₹)", min_value=0.0, value=0.0, step=100.0,
            help="Enter your current balance in this account."
        )
        submitted = st.form_submit_button("Add Account", type="primary", width="stretch")

        if submitted:
            name_clean = acc_name.strip()
            if not name_clean:
                st.error("Please enter an account name.")
            else:
                session = get_session(DB_PATH)
                try:
                    # Check for duplicate name
                    exists = session.query(Account).filter(
                        Account.user_id == user_id,
                        Account.name == name_clean
                    ).first()
                    if exists:
                        st.error(f"An account named '{name_clean}' already exists.")
                    else:
                        new_account = Account(
                            name=name_clean,
                            account_type=acc_type,
                            user_id=user_id,
                        )
                        session.add(new_account)
                        session.commit()
                        st.success(f"✅ Account **{name_clean}** added successfully!")
                        st.rerun()
                except Exception as exc:
                    session.rollback()
                    st.error(f"Error adding account: {exc}")
                finally:
                    session.close()

# ─── List accounts with balances ──────────────────────────────────────────────
session = get_session(DB_PATH)
try:
    accounts = session.query(Account).filter(Account.user_id == user_id).all()
finally:
    session.close()

if not accounts:
    st.info("You have no accounts yet. Add one above to get started!")
    st.stop()

st.markdown("---")
st.subheader("Your Accounts")

# Calculate actual balance from transactions
from sqlalchemy import func, case
from pfm.db.models import Transaction as Txn

session = get_session(DB_PATH)
try:
    for account in accounts:
        # Sum income - expenses for this account
        income_sum = session.query(func.coalesce(func.sum(Txn.amount), 0)).filter(
            Txn.account_id == account.id, Txn.is_income == True  # noqa: E712
        ).scalar() or 0.0
        expense_sum = session.query(func.coalesce(func.sum(Txn.amount), 0)).filter(
            Txn.account_id == account.id, Txn.is_income == False  # noqa: E712
        ).scalar() or 0.0
        balance = income_sum - expense_sum
        txn_count = session.query(func.count(Txn.id)).filter(Txn.account_id == account.id).scalar() or 0

        with st.container(border=True):
            col_icon, col_info, col_balance, col_actions = st.columns([0.5, 3, 2, 1])
            with col_icon:
                icons = {
                    "Bank": "🏦", "Cash": "💵", "Credit Card": "💳",
                    "UPI": "📱", "Wallet": "👛", "Investment": "📈", "Loan": "📋"
                }
                st.markdown(f"### {icons.get(account.account_type, '💰')}")
            with col_info:
                st.markdown(f"**{account.name}**")
                st.caption(f"{account.account_type} · {txn_count} transactions")
            with col_balance:
                color = "#34D399" if balance >= 0 else "#F87171"
                st.markdown(
                    f"<p style='font-size:1.4rem;font-weight:700;color:{color};margin:0'>₹{balance:,.2f}</p>",
                    unsafe_allow_html=True
                )
            with col_actions:
                if st.button("Delete", key=f"del_{account.id}", type="secondary"):
                    st.session_state[f"confirm_del_{account.id}"] = True

            # Confirm delete
            if st.session_state.get(f"confirm_del_{account.id}"):
                st.warning(
                    f"⚠️ Delete **{account.name}**? This will not delete your transactions, "
                    "but they will be unlinked."
                )
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Yes, delete", key=f"yes_del_{account.id}", type="primary"):
                        del_session = get_session(DB_PATH)
                        try:
                            acc_to_del = del_session.get(Account, account.id)
                            if acc_to_del:
                                del_session.delete(acc_to_del)
                                del_session.commit()
                            st.success("Account deleted.")
                            st.rerun()
                        except Exception as e:
                            del_session.rollback()
                            st.error(f"Could not delete: {e}")
                        finally:
                            del_session.close()
                with c2:
                    if st.button("Cancel", key=f"cancel_del_{account.id}"):
                        del st.session_state[f"confirm_del_{account.id}"]
                        st.rerun()
finally:
    session.close()
