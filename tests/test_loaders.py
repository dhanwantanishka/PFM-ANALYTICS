"""Tests for data loaders."""

import json
from pathlib import Path

import pandas as pd
import pytest

from pfm.ingestion.loaders import load_csv, load_excel, load_json, validate_schema


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "transaction_id": ["t1", "t2"],
            "date": ["2024-06-01", "2024-06-02"],
            "description": ["Coffee", "Rent"],
            "amount": [5.50, 1200.00],
            "category": ["Dining", "Housing"],
            "account_type": ["checking", "checking"],
            "balance_after": [1000.0, 800.0],
            "is_income": [False, False],
        }
    )


def test_load_csv(tmp_path: Path, sample_df: pd.DataFrame) -> None:
    path = tmp_path / "transactions.csv"
    sample_df.to_csv(path, index=False)
    loaded = load_csv(path)
    assert len(loaded) == 2
    assert "transaction_id" in loaded.columns


def test_load_json(tmp_path: Path, sample_df: pd.DataFrame) -> None:
    path = tmp_path / "transactions.json"
    sample_df.to_json(path, orient="records")
    loaded = load_json(path)
    assert len(loaded) == 2


def test_load_excel(tmp_path: Path, sample_df: pd.DataFrame) -> None:
    path = tmp_path / "transactions.xlsx"
    sample_df.to_excel(path, index=False, engine="openpyxl")
    loaded = load_excel(path)
    assert len(loaded) == 2


def test_validate_schema_valid(sample_df: pd.DataFrame) -> None:
    issues = validate_schema(sample_df)
    assert issues["missing_columns"] == []


def test_validate_schema_missing_columns() -> None:
    df = pd.DataFrame({"amount": [10]})
    issues = validate_schema(df)
    assert "transaction_id" in issues["missing_columns"]
