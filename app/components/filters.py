"""Reusable sidebar filter widgets for the dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

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


def render_sidebar_filters(
    transactions: pd.DataFrame, users: list[dict[str, str]]
) -> DashboardFilters:
    """Render the sidebar filter controls.

    Args:
        transactions: Full transactions dataset, used to derive filter ranges.
        users: Configured users to populate the user selector.

    Returns:
        The filter selections made by the user.
    """
    st.sidebar.header("Filters")

    user_names = [u["user_name"] for u in users]
    selected_name = st.sidebar.selectbox("User", user_names)
    user_id = next(u["user_id"] for u in users if u["user_name"] == selected_name)

    min_date = transactions["date"].min().date()
    max_date = transactions["date"].max().date()
    date_range = st.sidebar.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    start_date, end_date = date_range if len(date_range) == 2 else (min_date, max_date)

    categories = sorted(transactions["category"].unique())
    selected_categories = st.sidebar.multiselect(
        "Categories", categories, default=categories
    )

    st.sidebar.divider()
    st.sidebar.caption("PFM Analytics · Inventive BizPro Technologies")

    return DashboardFilters(
        user_id=user_id,
        user_name=selected_name,
        start_date=start_date,
        end_date=end_date,
        categories=selected_categories or categories,
    )


def apply_filters(transactions: pd.DataFrame, filters: DashboardFilters) -> pd.DataFrame:
    """Apply the selected sidebar filters to the transactions dataframe.

    Args:
        transactions: Full transactions dataset.
        filters: Filter selections from :func:`render_sidebar_filters`.

    Returns:
        The filtered subset of transactions.
    """
    mask = (
        (transactions["user_id"] == filters.user_id)
        & (transactions["date"].dt.date >= filters.start_date)
        & (transactions["date"].dt.date <= filters.end_date)
        & (transactions["category"].isin(filters.categories))
    )
    return transactions.loc[mask].copy()
