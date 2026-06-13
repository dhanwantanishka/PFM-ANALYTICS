"""Data cleaning, validation, and quality reporting."""

from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd

from pfm.config import ALLOWED_CATEGORIES, DATE_MAX, DATE_MIN


def fill_missing_amounts(df: pd.DataFrame, column: str = "amount") -> pd.DataFrame:
    """Fill missing amounts with the column median."""
    result = df.copy()
    if column not in result.columns:
        return result
    median_val = result[column].median()
    result[column] = result[column].fillna(median_val)
    return result


def fill_missing_dates(df: pd.DataFrame, column: str = "date") -> pd.DataFrame:
    """Forward-fill missing dates, then back-fill any remaining."""
    result = df.copy()
    if column not in result.columns:
        return result
    result[column] = pd.to_datetime(result[column], errors="coerce")
    result[column] = result[column].ffill().bfill()
    return result


def remove_duplicates(df: pd.DataFrame, subset: list[str] | None = None) -> pd.DataFrame:
    """Remove duplicate rows based on transaction_id or full row."""
    subset = subset or ["transaction_id"]
    available = [c for c in subset if c in df.columns]
    if not available:
        return df.drop_duplicates()
    return df.drop_duplicates(subset=available, keep="first")


def normalize_category_labels(df: pd.DataFrame, column: str = "category") -> pd.DataFrame:
    """Normalize category labels: trim whitespace, fix case, map common typos."""
    result = df.copy()
    if column not in result.columns:
        return result

    typo_map = {
        "grocery": "Groceries",
        "grocerie": "Groceries",
        "dinning": "Dining",
        "restaurant": "Dining",
        "transport": "Transportation",
        "health": "Healthcare",
        "entertainment ": "Entertainment",
        "subcription": "Subscriptions",
        "debt": "Debt Payment",
        "salary": "Income",
        "paycheck": "Income",
    }

    def _normalize(value: Any) -> str:
        if pd.isna(value):
            return "Other"
        text = str(value).strip()
        if not text:
            return "Other"
        lower = text.lower()
        if lower in typo_map:
            return typo_map[lower]
        # Title-case match against allowed list
        for allowed in ALLOWED_CATEGORIES:
            if lower == allowed.lower():
                return allowed
        return text.title() if text.islower() else text

    result[column] = result[column].apply(_normalize)
    result.loc[~result[column].isin(ALLOWED_CATEGORIES), column] = "Other"
    return result


def validate_amounts(df: pd.DataFrame, column: str = "amount") -> pd.DataFrame:
    """Flag and remove rows where amount is not positive."""
    result = df.copy()
    if column not in result.columns:
        return result
    result = result[result[column] > 0]
    return result.reset_index(drop=True)


def validate_dates(
    df: pd.DataFrame,
    column: str = "date",
    min_date: str = DATE_MIN,
    max_date: str = DATE_MAX,
) -> pd.DataFrame:
    """Keep only rows with dates within the allowed range."""
    result = df.copy()
    if column not in result.columns:
        return result
    result[column] = pd.to_datetime(result[column], errors="coerce")
    min_dt = pd.Timestamp(min_date)
    max_dt = pd.Timestamp(max_date)
    mask = (result[column] >= min_dt) & (result[column] <= max_dt)
    return result[mask].reset_index(drop=True)


def validate_categories(
    df: pd.DataFrame,
    column: str = "category",
    allowed: list[str] | None = None,
) -> pd.DataFrame:
    """Keep only rows with categories in the allowed list."""
    allowed = allowed or ALLOWED_CATEGORIES
    result = df.copy()
    if column not in result.columns:
        return result
    return result[result[column].isin(allowed)].reset_index(drop=True)


def clean_description(df: pd.DataFrame, column: str = "description") -> pd.DataFrame:
    """Normalize transaction descriptions."""
    result = df.copy()
    if column not in result.columns:
        return result
    result[column] = (
        result[column]
        .astype(str)
        .str.strip()
        .apply(lambda x: re.sub(r"\s+", " ", x))
    )
    return result


def generate_quality_report(df: pd.DataFrame, original_count: int) -> dict[str, Any]:
    """Generate a data quality summary report."""
    completeness = {}
    for col in df.columns:
        null_pct = float(df[col].isna().mean() * 100)
        completeness[col] = round(100 - null_pct, 2)

    anomalies = []
    if "amount" in df.columns and (df["amount"] <= 0).any():
        anomalies.append("Non-positive amounts detected before validation")
    if "date" in df.columns and df["date"].isna().any():
        anomalies.append("Null dates remain after cleaning")

    return {
        "row_count": len(df),
        "rows_removed": original_count - len(df),
        "completeness_pct": completeness,
        "duplicate_count": int(df.duplicated(subset=["transaction_id"]).sum())
        if "transaction_id" in df.columns
        else 0,
        "anomaly_flags": anomalies,
        "schema_valid": all(
            c in df.columns
            for c in [
                "transaction_id",
                "date",
                "description",
                "amount",
                "category",
                "account_type",
                "balance_after",
                "is_income",
            ]
        ),
    }


def run_cleaning_pipeline(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Apply the full cleaning pipeline and return cleaned data + quality report."""
    original_count = len(df)
    cleaned = df.copy()
    cleaned = fill_missing_dates(cleaned)
    cleaned = fill_missing_amounts(cleaned)
    cleaned = remove_duplicates(cleaned)
    cleaned = normalize_category_labels(cleaned)
    cleaned = clean_description(cleaned)
    cleaned = validate_amounts(cleaned)
    cleaned = validate_dates(cleaned)
    cleaned = validate_categories(cleaned)
    report = generate_quality_report(cleaned, original_count)
    return cleaned, report
