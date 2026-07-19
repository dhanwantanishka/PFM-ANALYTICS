"""Add / manage transactions page — manually record income, expenses, and transfers."""

from __future__ import annotations

import sys
import uuid
from datetime import date, datetime, time
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parents[1]
_SRC_DIR = _APP_DIR.parent / "src"
for _p in [str(_APP_DIR), str(_SRC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st
import pandas as pd

import utils.bootstrap  # noqa: F401

from pfm.config import DB_PATH
from pfm.db import get_session
from pfm.db.models import Account, Category, Transaction
from utils.data_loader import load_transactions

# ─── Auth guard ───────────────────────────────────────────────────────────────
if "user_id" not in st.session_state:
    st.error("Please log in to manage your transactions.")
    st.stop()

user_id = st.session_state["user_id"]

PAYMENT_METHODS = ["UPI", "Cash", "Debit Card", "Credit Card", "Net Banking", "Cheque", "Other"]
TRANSACTION_TYPES = ["Expense", "Income", "Transfer"]

# ─── Auto-categorization rules ────────────────────────────────────────────────
AUTO_CATEGORY_RULES = {
    "swiggy": "Dining", "zomato": "Dining", "dominos": "Dining", "mcdonald": "Dining",
    "kfc": "Dining", "subway": "Dining", "restaurant": "Dining", "cafe": "Dining",
    "uber": "Transportation", "ola": "Transportation", "rapido": "Transportation",
    "petrol": "Transportation", "diesel": "Transportation", "metro": "Transportation",
    "amazon": "Shopping", "flipkart": "Shopping", "myntra": "Shopping",
    "nykaa": "Shopping", "meesho": "Shopping", "ajio": "Shopping",
    "netflix": "Subscriptions", "hotstar": "Subscriptions", "spotify": "Subscriptions",
    "prime": "Subscriptions", "youtube": "Subscriptions", "zee5": "Subscriptions",
    "gym": "Healthcare", "pharmacy": "Healthcare", "hospital": "Healthcare",
    "doctor": "Healthcare", "medical": "Healthcare", "apollo": "Healthcare",
    "rent": "Housing", "maintenance": "Housing", "electricity": "Utilities",
    "water": "Utilities", "gas": "Utilities", "internet": "Utilities",
    "airtel": "Utilities", "jio": "Utilities", "bsnl": "Utilities",
    "salary": "Income", "freelance": "Income", "dividend": "Income",
    "interest": "Income", "bonus": "Income", "refund": "Income",
    "school": "Education", "college": "Education", "course": "Education",
    "udemy": "Education", "coursera": "Education", "books": "Education",
    "hotel": "Travel", "flight": "Travel", "makemytrip": "Travel",
    "irctc": "Travel", "goibibo": "Travel",
}


def auto_suggest_category(merchant: str, description: str) -> str | None:
    """Suggest a category based on merchant/description keywords."""
    text = (merchant + " " + description).lower()
    for keyword, category in AUTO_CATEGORY_RULES.items():
        if keyword in text:
            return category
    return None


# ─── Load user's accounts and categories ──────────────────────────────────────
session = get_session(DB_PATH)
try:
    user_accounts = session.query(Account).filter(Account.user_id == user_id).all()
    all_categories = session.query(Category).order_by(Category.name).all()
finally:
    session.close()

category_names = [c.name for c in all_categories]
account_options = {f"{a.name} ({a.account_type})": a.id for a in user_accounts}

# ─── Page header ──────────────────────────────────────────────────────────────
st.title(":material/add_circle: Add Transaction")
st.caption("Record a new income, expense, or transfer. Nothing is pre-filled.")

if not user_accounts:
    st.warning(
        "⚠️ You have no accounts yet. Please create one first before adding transactions."
    )
    if st.button(":material/account_balance_wallet: Go to Accounts"):
        st.switch_page("pages/accounts.py")
    st.stop()

# ─── Pre-fill data (from receipt scanner) ─────────────────────────────────────
prefill = st.session_state.pop("prefill_txn", {})

# ─── Transaction form ─────────────────────────────────────────────────────────
with st.form("add_transaction_form", clear_on_submit=True):
    st.subheader("Transaction Details")

    # Row 1: Type, Amount, Date, Time
    c1, c2, c3, c4 = st.columns([1.5, 1.5, 1.5, 1.5])
    with c1:
        txn_type = st.selectbox("Transaction Type *", TRANSACTION_TYPES)
    with c2:
        amount = st.number_input(
            "Amount (₹) *", min_value=0.01, 
            value=float(prefill.get("amount")) if prefill.get("amount") else None, 
            step=1.0, placeholder="0.00"
        )
    with c3:
        try:
            prefill_date = date.fromisoformat(prefill["date"]) if prefill.get("date") else None
        except (ValueError, TypeError):
            prefill_date = None
        txn_date = st.date_input("Date *", value=prefill_date, max_value=date.today())
    with c4:
        txn_time = st.time_input("Time *", value=None, step=60)

    # Row 2: Description, Merchant
    c5, c6 = st.columns(2)
    with c5:
        description = st.text_input("Description *", value=prefill.get("description", ""), placeholder="e.g., Grocery shopping at DMart")
    with c6:
        merchant = st.text_input("Merchant / Payee", value=prefill.get("merchant", ""), placeholder="e.g., DMart, Swiggy, HDFC Bank")

    # Auto-suggest category based on merchant/description
    suggested_cat = None
    if merchant or description:
        suggested_cat = auto_suggest_category(merchant or "", description or "")

    # Row 3: Category, Account, Payment Method
    c7, c8, c9 = st.columns(3)
    with c7:
        default_idx = category_names.index(suggested_cat) if suggested_cat and suggested_cat in category_names else 0
        category = st.selectbox(
            "Category *",
            category_names,
            index=default_idx,
            help=f"Auto-suggested: {suggested_cat}" if suggested_cat else "Select a category",
        )
    with c8:
        account_label = st.selectbox("Account *", list(account_options.keys()))
    with c9:
        payment_method = st.selectbox("Payment Method", PAYMENT_METHODS)

    # Row 4: Notes, Location
    c10, c11 = st.columns(2)
    with c10:
        notes = st.text_area("Notes", placeholder="Optional: add any extra details here", height=80)
    with c11:
        location = st.text_input("Location (optional)", placeholder="e.g., Bengaluru, MG Road")

    # Row 5: Receipt upload
    receipt_file = st.file_uploader(
        "Receipt Upload (optional)",
        type=["jpg", "jpeg", "png", "pdf"],
        help="Upload a photo or scan of your receipt."
    )

    st.divider()
    submitted = st.form_submit_button("💾 Save Transaction", type="primary", width="stretch")

# ─── Handle submission ────────────────────────────────────────────────────────
if submitted:
    errors = []
    if not amount or amount <= 0:
        errors.append("Amount must be greater than 0.")
    if not txn_date:
        errors.append("Please select a date.")
    if not txn_time:
        errors.append("Please select a time.")
    if not description.strip():
        errors.append("Description is required.")
    if not account_label:
        errors.append("Please select an account.")

    if errors:
        for e in errors:
            st.error(f"❌ {e}")
    else:
        # Get category_id
        session = get_session(DB_PATH)
        try:
            cat_obj = session.query(Category).filter(Category.name == category).first()
            account_id = account_options[account_label]
            is_income = txn_type == "Income"

            # Handle receipt upload
            receipt_path = None
            if receipt_file is not None:
                receipts_dir = Path(_APP_DIR).parent / "data" / "receipts"
                receipts_dir.mkdir(parents=True, exist_ok=True)
                receipt_filename = f"{user_id}_{uuid.uuid4().hex[:8]}_{receipt_file.name}"
                receipt_path = str(receipts_dir / receipt_filename)
                with open(receipt_path, "wb") as f:
                    f.write(receipt_file.read())

            new_txn = Transaction(
                transaction_id=str(uuid.uuid4()),
                date=txn_date,
                time=txn_time,
                description=description.strip(),
                amount=float(amount),
                category_id=cat_obj.id,
                account_id=account_id,
                is_income=is_income,
                transaction_type=txn_type.lower(),
                merchant=merchant.strip() if merchant else None,
                notes=notes.strip() if notes else None,
                payment_method=payment_method,
                location=location.strip() if location else None,
                receipt_path=receipt_path,
                # Engineered features
                day_of_week=txn_date.weekday(),
                is_weekend=txn_date.weekday() >= 5,
                month=txn_date.month,
                quarter=(txn_date.month - 1) // 3 + 1,
            )
            session.add(new_txn)
            session.commit()

            # Clear cache so dashboard updates instantly
            load_transactions.clear()

            st.success(
                f"✅ Transaction saved! **₹{amount:,.2f}** — {description.strip()} "
                f"on {txn_date.strftime('%d %b %Y')}"
            )
            if suggested_cat:
                st.info(f"💡 Auto-categorized as **{suggested_cat}** based on merchant name.")

        except Exception as exc:
            session.rollback()
            st.error(f"❌ Failed to save transaction: {exc}")
        finally:
            session.close()

# ─── Recent transactions list ─────────────────────────────────────────────────
st.divider()
st.subheader("Your Recent Transactions")

try:
    df = load_transactions(user_id)
    if df.empty:
        st.info("No transactions yet. Add one above!")
    else:
        display = df.sort_values("date", ascending=False).head(50).copy()
        display["date"] = display["date"].dt.strftime("%d %b %Y")
        display["amount"] = display.apply(
            lambda r: f"{'+ ' if r['is_income'] else '- '}₹{r['amount']:,.2f}", axis=1
        )
        cols_to_show = ["date", "description", "merchant", "category", "amount", "account_type", "payment_method"]
        cols_available = [c for c in cols_to_show if c in display.columns]
        st.dataframe(
            display[cols_available].rename(columns={
                "date": "Date", "description": "Description", "merchant": "Merchant",
                "category": "Category", "amount": "Amount", "account_type": "Account",
                "payment_method": "Payment"
            }),
            hide_index=True,
            width="stretch",
        )
except Exception as e:
    st.warning(f"Could not load recent transactions: {e}")
