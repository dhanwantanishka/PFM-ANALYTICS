"""Enhanced filters with quick-filter presets and advanced search."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd
import streamlit as st


@dataclass
class DashboardFilters:
    """Selected filter state shared across dashboard pages."""

    user_id: str
    user_name: str
    start_date: date
    end_date: date
    categories: list[str]
    search_query: str = ""
    income_only: bool = False
    expense_only: bool = False
    payment_methods: list[str] | None = None


QUICK_RANGES = {
    "Today": (date.today(), date.today()),
    "Yesterday": (date.today() - timedelta(days=1), date.today() - timedelta(days=1)),
    "This Week": (date.today() - timedelta(days=date.today().weekday()), date.today()),
    "Last Week": (
        date.today() - timedelta(days=date.today().weekday() + 7),
        date.today() - timedelta(days=date.today().weekday() + 1),
    ),
    "This Month": (date.today().replace(day=1), date.today()),
    "Last Month": (
        (date.today().replace(day=1) - timedelta(days=1)).replace(day=1),
        date.today().replace(day=1) - timedelta(days=1),
    ),
    "Last 3 Months": (date.today() - timedelta(days=90), date.today()),
    "This Year": (date.today().replace(month=1, day=1), date.today()),
    "All Time": None,  # Handled specially
}


def render_sidebar_filters(
    transactions: pd.DataFrame,
    override_user_id: str | None = None,
    override_user_name: str | None = None,
) -> DashboardFilters:
    """Render collapsible sidebar filter controls with quick ranges and search."""
    user_id = override_user_id if override_user_id else st.session_state.get("user_id", "user_1")
    selected_name = override_user_name if override_user_name else st.session_state.get("user_name", "Unknown User")

    income_only = False
    expense_only = False
    payment_methods = []

    with st.sidebar.expander(":material/tune: Filters", expanded=True):
        if transactions.empty:
            start_date = end_date = date.today()
            categories = []
            selected_categories = []
            payment_methods = []
            selected_payments = []
            st.info("No data available to filter.")
        else:
            # ── Quick date presets ──────────────────────────────────────────
            quick_preset = st.selectbox(
                "Quick range",
                list(QUICK_RANGES.keys()),
                index=4,  # Default: This Month
                key="filter_quick_range",
            )

            data_min = transactions["date"].min().date()
            data_max = transactions["date"].max().date()

            if QUICK_RANGES[quick_preset] is not None:
                preset_start, preset_end = QUICK_RANGES[quick_preset]
                # Ensure local variable ranges are logical
                if preset_start > preset_end:
                    preset_start, preset_end = preset_end, preset_start
                
                # Check bounds to prevent start date from exceeding max available date
                if preset_start > data_max:
                    preset_start = preset_end = data_max
                elif preset_end < data_min:
                    preset_start = preset_end = data_min
                else:
                    preset_start = max(preset_start, data_min)
                    preset_end = min(preset_end, data_max)
            else:
                preset_start, preset_end = data_min, data_max

            # Custom date override
            with st.expander("Custom date range", expanded=False):
                date_range = st.date_input(
                    "Date range",
                    value=(preset_start, preset_end),
                    min_value=transactions["date"].min().date(),
                    max_value=transactions["date"].max().date(),
                    key="filter_dates",
                )
                start_date, end_date = date_range if len(date_range) == 2 else (preset_start, preset_end)

            if "filter_dates" not in st.session_state or len(st.session_state.get("filter_dates", ())) != 2:
                start_date, end_date = preset_start, preset_end

            # ── Category filter ─────────────────────────────────────────────
            categories = sorted(transactions["category"].unique())
            selected_categories = st.multiselect(
                "Categories",
                categories,
                default=categories,
                key="filter_categories",
            )

            # ── Transaction type filter ─────────────────────────────────────
            txn_type_filter = st.radio(
                "Transaction type",
                ["All", "Income only", "Expenses only"],
                horizontal=True,
                key="filter_txn_type",
            )
            income_only = txn_type_filter == "Income only"
            expense_only = txn_type_filter == "Expenses only"

            # ── Payment method filter ───────────────────────────────────────
            if "payment_method" in transactions.columns:
                all_methods = sorted(transactions["payment_method"].dropna().unique())
                if all_methods:
                    selected_payments = st.multiselect(
                        "Payment method",
                        all_methods,
                        default=all_methods,
                        key="filter_payment",
                    )
                else:
                    selected_payments = []
            else:
                selected_payments = []

            payment_methods = selected_payments

        # ── Search bar ─────────────────────────────────────────────────────
        search_query = st.text_input(
            ":material/search: Search",
            placeholder="Merchant, notes, description…",
            key="filter_search",
        )

    st.sidebar.caption("PFM Analytics · Inventive BizPro Technologies")

    return DashboardFilters(
        user_id=user_id,
        user_name=selected_name,
        start_date=start_date,
        end_date=end_date,
        categories=selected_categories or categories,
        search_query=search_query.strip(),
        income_only=income_only,
        expense_only=expense_only,
        payment_methods=payment_methods if payment_methods else None,
    )


def apply_filters(transactions: pd.DataFrame, filters: DashboardFilters) -> pd.DataFrame:
    """Apply all sidebar filters to transactions."""
    if transactions.empty:
        return transactions.copy()

    mask = (
        (transactions["user_id"] == filters.user_id)
        & (transactions["date"].dt.date >= filters.start_date)
        & (transactions["date"].dt.date <= filters.end_date)
        & (transactions["category"].isin(filters.categories))
    )

    if filters.income_only:
        mask &= transactions["is_income"] == True  # noqa: E712
    elif filters.expense_only:
        mask &= transactions["is_income"] == False  # noqa: E712

    if filters.payment_methods is not None and "payment_method" in transactions.columns:
        mask &= transactions["payment_method"].isin(filters.payment_methods) | transactions["payment_method"].isna()

    df = transactions.loc[mask].copy()

    # Apply search across text columns
    if filters.search_query:
        q = filters.search_query.lower()
        text_cols = [c for c in ["description", "merchant", "notes", "category"] if c in df.columns]
        text_mask = df[text_cols].apply(
            lambda col: col.fillna("").str.lower().str.contains(q, regex=False)
        ).any(axis=1)
        df = df.loc[text_mask]

    return df
