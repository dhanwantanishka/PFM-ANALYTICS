"""Shared page bootstrap: filters, data loading, empty states."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st

_APP_DIR = Path(__file__).resolve().parents[1]
_SRC_DIR = _APP_DIR.parent / "src"
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from components.filters import DashboardFilters, apply_filters, render_sidebar_filters  # noqa: E402
from components.states import render_empty_state  # noqa: E402
from utils.data_loader import load_budgets, load_transactions  # noqa: E402


@dataclass
class PageContext:
    """Filtered datasets and metadata shared by dashboard pages."""

    transactions: pd.DataFrame
    budgets: pd.DataFrame
    filtered: pd.DataFrame
    filters: DashboardFilters


def load_page_context(require_data: bool = True) -> PageContext | None:
    """Load transactions, render sidebar filters, and return filtered context."""
    user_id = st.session_state.get("user_id", "user_1")
    transactions = load_transactions(user_id)
    budgets = load_budgets(user_id)
    filters = render_sidebar_filters(transactions)
    filtered = apply_filters(transactions, filters)

    if require_data and filtered.empty:
        render_empty_state(
            "No transactions match your filters",
            "Try widening the date range or selecting more categories.",
            icon=":material/filter_alt_off:",
        )
        return None

    return PageContext(
        transactions=transactions,
        budgets=budgets,
        filtered=filtered,
        filters=filters,
    )
