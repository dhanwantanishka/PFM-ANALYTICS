"""Cached data loading utilities for the PFM Streamlit dashboard."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from pfm.config import DB_PATH
from pfm.db import get_session
from pfm.db.models import Transaction, Category, Account, Budget

@st.cache_data(show_spinner="Loading transactions...")
def load_transactions(user_id: str) -> pd.DataFrame:
    """Load and cache the raw transactions dataset from the database.

    Returns:
        Transactions with parsed dates, ready for filtering.
    """
    session = get_session(DB_PATH)
    try:
        query = session.query(
            Transaction.transaction_id,
            Transaction.date,
            Transaction.description,
            Transaction.amount,
            Category.name.label("category"),
            Account.account_type,
            Account.user_id,
            Transaction.balance_after,
            Transaction.is_income,
            Transaction.transaction_type,
            Transaction.merchant,
            Transaction.time,
            Transaction.notes,
            Transaction.payment_method,
            Transaction.location,
            Transaction.day_of_week,
            Transaction.is_weekend,
            Transaction.month,
            Transaction.quarter,
            Transaction.rolling_30d_spend
        ).join(Category, Transaction.category_id == Category.id) \
         .join(Account, Transaction.account_id == Account.id) \
         .filter(Account.user_id == user_id)
         
        df = pd.read_sql(query.statement, session.bind)
        if df.empty:
            df = pd.DataFrame(columns=[
                "transaction_id", "date", "description", "amount", "category",
                "account_type", "user_id", "balance_after", "is_income", "transaction_type",
                "merchant", "time", "notes", "payment_method", "location",
                "day_of_week", "is_weekend", "month", "quarter", "rolling_30d_spend"
            ])
        df["date"] = pd.to_datetime(df["date"])
        return df
    finally:
        session.close()


@st.cache_data(show_spinner="Loading budgets...")
def load_budgets(user_id: str) -> pd.DataFrame:
    """Load and cache the monthly budgets dataset from the database.

    Returns:
        Budget targets per user, category, and month.
    """
    session = get_session(DB_PATH)
    try:
        query = session.query(
            Category.name.label("category"),
            Budget.month,
            Budget.amount,
            Budget.user_id
        ).join(Category, Budget.category_id == Category.id) \
         .filter(Budget.user_id == user_id)
        df = pd.read_sql(query.statement, session.bind)
        if df.empty:
            df = pd.DataFrame(columns=["category", "month", "amount", "user_id"])
        return df
    finally:
        session.close()
