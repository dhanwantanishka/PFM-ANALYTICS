"""Feature engineering for transaction data."""

import pandas as pd


def add_temporal_features(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """Add day_of_week, is_weekend, month, and quarter features."""
    result = df.copy()
    result[date_col] = pd.to_datetime(result[date_col], errors="coerce")
    result["day_of_week"] = result[date_col].dt.dayofweek
    result["is_weekend"] = result["day_of_week"].isin([5, 6])
    result["month"] = result[date_col].dt.month
    result["quarter"] = result[date_col].dt.quarter
    return result


def add_rolling_spend(
    df: pd.DataFrame,
    date_col: str = "date",
    amount_col: str = "amount",
    window: int = 30,
) -> pd.DataFrame:
    """Compute rolling N-day spend (expenses only)."""
    result = df.copy()
    result[date_col] = pd.to_datetime(result[date_col], errors="coerce")
    result = result.sort_values(date_col).reset_index(drop=True)

    spend = result[amount_col].copy()
    if "is_income" in result.columns:
        spend = spend.where(~result["is_income"], 0)

    indexed = pd.DataFrame({amount_col: spend.values}, index=result[date_col])
    rolling = indexed[amount_col].rolling(f"{window}D").sum()
    result["rolling_30d_spend"] = rolling.fillna(0).values
    return result


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all feature engineering steps."""
    result = add_temporal_features(df)
    result = add_rolling_spend(result)
    return result
