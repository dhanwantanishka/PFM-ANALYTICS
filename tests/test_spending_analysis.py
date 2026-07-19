"""Tests for spending analysis module."""

import pandas as pd

from pfm.analytics.spending_analysis import (
    month_over_month_growth,
    spending_by_category,
    spending_by_merchant,
    spending_by_month,
    spending_heatmap_data,
    top_expense_drivers,
    weekend_vs_weekday_spending,
)


def test_spending_by_category(sample_spending_df):
    result = spending_by_category(sample_spending_df)
    assert len(result) > 0
    assert ("amount", "sum") in result.columns


def test_spending_by_merchant(sample_spending_df):
    result = spending_by_merchant(sample_spending_df, top_n=3)
    assert len(result) <= 3


def test_spending_by_month(sample_spending_df):
    result = spending_by_month(sample_spending_df)
    assert len(result) > 0


def test_month_over_month_growth(sample_spending_df):
    result = month_over_month_growth(sample_spending_df)
    assert len(result) >= 0


def test_weekend_vs_weekday(sample_spending_df):
    result = weekend_vs_weekday_spending(sample_spending_df)
    assert len(result) == 2


def test_top_expense_drivers(sample_spending_df):
    top, share = top_expense_drivers(sample_spending_df)
    assert "pct_of_total" in top.columns
    assert share > 0


def test_spending_heatmap_data(sample_spending_df):
    result = spending_heatmap_data(sample_spending_df)
    assert result.shape[0] > 0
