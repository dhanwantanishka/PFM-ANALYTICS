# tests/test_spending_analysis.py
"""Tests for spending analysis module."""

import pandas as pd
import pytest
from pfm.analytics.spending_analysis import (
    aggregate_by_category,
    aggregate_by_merchant,
    monthly_spend_trend,
    month_over_month_growth,
    day_of_week_analysis,
    top_expense_drivers,
    spending_distribution,
)


@pytest.fixture
def sample_spending_df() -> pd.DataFrame:
    return pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=10, freq="D"),
        "amount": [100, 200, 150, 300, 50, 120, 180, 90, 250, 110],
        "category": ["Dining", "Groceries", "Dining", "Housing", "Utilities",
                     "Dining", "Entertainment", "Groceries", "Housing", "Dining"],
        "merchant": ["Restaurant1", "Store1", "Restaurant2", "Landlord", "Provider",
                     "Restaurant1", "Cinema", "Store1", "Landlord", "Restaurant3"],
        "is_income": [False]*10,
        "user_name": ["User1"]*10,
    })


def test_aggregate_by_category(sample_spending_df):
    result = aggregate_by_category(sample_spending_df)
    assert len(result) > 0
    assert "category" in result.columns
    assert "total_spend" in result.columns
    assert result.iloc[0]["total_spend"] >= result.iloc[-1]["total_spend"]


def test_aggregate_by_merchant(sample_spending_df):
    result = aggregate_by_merchant(sample_spending_df, top_n=3)
    assert len(result) <= 3
    assert "merchant" in result.columns


def test_monthly_spend_trend(sample_spending_df):
    result = monthly_spend_trend(sample_spending_df)
    assert len(result) > 0
    assert "year_month" in result.columns
    assert "total_spend" in result.columns


def test_month_over_month_growth(sample_spending_df):
    result = month_over_month_growth(sample_spending_df)
    assert "mom_growth" in result.columns


def test_day_of_week_analysis(sample_spending_df):
    result = day_of_week_analysis(sample_spending_df)
    assert len(result) == 7  # 7 days
    assert "day_of_week" in result.columns


def test_top_expense_drivers(sample_spending_df):
    result = top_expense_drivers(sample_spending_df)
    assert "percentage" in result.columns
    assert result["percentage"].sum() > 0


def test_spending_distribution(sample_spending_df):
    result = spending_distribution(sample_spending_df)
    assert "total_income" in result
    assert "total_expenses" in result
    assert result["needs_pct"] + result["wants_pct"] + result["savings_pct"] <= 101