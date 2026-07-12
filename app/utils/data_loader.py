"""Cached data loading utilities for the PFM Streamlit dashboard."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from pfm.config import RAW_DATA_DIR, USERS  # noqa: E402
from pfm.ingestion.loaders import load_csv  # noqa: E402


@st.cache_data(show_spinner="Loading transactions...")
def load_transactions() -> pd.DataFrame:
    """Load and cache the raw transactions dataset.

    Returns:
        Transactions with parsed dates, ready for filtering.
    """
    df = load_csv(RAW_DATA_DIR / "transactions.csv")
    df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data(show_spinner="Loading budgets...")
def load_budgets() -> pd.DataFrame:
    """Load and cache the monthly budgets dataset.

    Returns:
        Budget targets per user, category, and month.
    """
    return pd.read_csv(RAW_DATA_DIR / "budgets.csv")


def get_user_options() -> list[dict[str, str]]:
    """Return the configured users for the user selector.

    Returns:
        List of ``{"user_id": ..., "user_name": ...}`` dicts.
    """
    return USERS
