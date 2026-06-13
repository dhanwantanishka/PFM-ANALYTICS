"""Data loaders for CSV, Excel, and JSON formats."""

from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_COLUMNS = [
    "transaction_id",
    "date",
    "description",
    "amount",
    "category",
    "account_type",
    "balance_after",
    "is_income",
]


def load_csv(path: str | Path, **kwargs: Any) -> pd.DataFrame:
    """Load transactions from a CSV file."""
    df = pd.read_csv(path, **kwargs)
    return _normalize_loaded_df(df)


def load_excel(path: str | Path, sheet_name: str | int = 0, **kwargs: Any) -> pd.DataFrame:
    """Load transactions from an Excel file using OpenPyXL."""
    df = pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl", **kwargs)
    return _normalize_loaded_df(df)


def load_json(path: str | Path, **kwargs: Any) -> pd.DataFrame:
    """Load transactions from a JSON file (records orientation)."""
    df = pd.read_json(path, **kwargs)
    return _normalize_loaded_df(df)


def _normalize_loaded_df(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names and parse common types after load."""
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    if "amount" in df.columns:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    if "balance_after" in df.columns:
        df["balance_after"] = pd.to_numeric(df["balance_after"], errors="coerce")

    if "is_income" in df.columns:
        df["is_income"] = df["is_income"].astype(str).str.lower().isin(
            ["true", "1", "yes", "t"]
        )

    return df


def validate_schema(df: pd.DataFrame) -> dict[str, list[str]]:
    """Validate that required columns exist and report issues."""
    issues: dict[str, list[str]] = {"missing_columns": [], "empty": [], "warnings": []}

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        issues["missing_columns"] = missing

    if df.empty:
        issues["empty"].append("Dataset contains zero rows")

    if "merchant" not in df.columns:
        issues["warnings"].append("Optional column 'merchant' not present")

    return issues
