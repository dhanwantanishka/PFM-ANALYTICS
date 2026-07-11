"""Spending pattern analysis and aggregation functions."""

import pandas as pd
import numpy as np
from typing import Tuple


def spending_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate spending by category."""
    return df.groupby('category').agg({
        'amount': ['sum', 'count', 'mean']
    }).round(2).sort_values(('amount', 'sum'), ascending=False)


def spending_by_merchant(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Top N merchants by spend."""
    return df.groupby('merchant').agg({
        'amount': ['sum', 'count', 'mean']
    }).round(2).sort_values(('amount', 'sum'), ascending=False).head(top_n)


def spending_by_month(df: pd.DataFrame) -> pd.Series:
    """Monthly spending trend."""
    df['year_month'] = df['date'].dt.to_period('M')
    return df.groupby('year_month')['amount'].sum().round(2)


def spending_by_user(df: pd.DataFrame) -> pd.DataFrame:
    """Spending by user."""
    return df.groupby('user_name').agg({
        'amount': ['sum', 'count', 'mean']
    }).round(2).sort_values(('amount', 'sum'), ascending=False)


def spending_by_day_of_week(df: pd.DataFrame) -> pd.DataFrame:
    """Spending by day of week."""
    df['day_name'] = df['date'].dt.day_name()
    return df.groupby('day_name')['amount'].agg(['sum', 'count', 'mean']).round(2)


def month_over_month_growth(df: pd.DataFrame) -> pd.Series:
    """MoM growth rate (%)."""
    monthly = spending_by_month(df)
    return monthly.pct_change().mul(100).round(2)


def top_expense_drivers(df: pd.DataFrame, top_n: int = 10) -> Tuple[pd.DataFrame, float]:
    """Top N categories and their % of total spend (Pareto)."""
    by_cat = spending_by_category(df)
    by_cat['pct_of_total'] = (by_cat[('amount', 'sum')] / by_cat[('amount', 'sum')].sum() * 100).round(2)
    top = by_cat.head(top_n)
    cumsum_pct = top['pct_of_total'].sum()
    return top, cumsum_pct


def weekend_vs_weekday_spending(df: pd.DataFrame) -> pd.DataFrame:
    """Compare weekend vs weekday average spend."""
    df_copy = df.copy()
    df_copy['is_weekend'] = df_copy['date'].dt.dayofweek >= 5
    return df_copy.groupby('is_weekend').agg({
        'amount': ['sum', 'count', 'mean']
    }).round(2)


def spending_heatmap_data(df: pd.DataFrame) -> pd.DataFrame:
    """Heatmap data: day_of_week × category."""
    df_copy = df.copy()
    df_copy['day_name'] = df_copy['date'].dt.day_name()
    return df_copy.pivot_table(
        index='day_name',
        columns='category',
        values='amount',
        aggfunc='sum'
    ).round(2).fillna(0)
