"""Tests for data cleaning and validation functions."""

import pandas as pd
import pytest

from pfm.cleaning.validators import (
    clean_description,
    fill_missing_amounts,
    fill_missing_dates,
    generate_quality_report,
    normalize_category_labels,
    remove_duplicates,
    run_cleaning_pipeline,
    validate_amounts,
    validate_categories,
    validate_dates,
)


@pytest.fixture
def dirty_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "transaction_id": ["t1", "t1", "t2", "t3", "t4", "t5"],
            "date": ["2024-01-01", "2024-01-01", None, "2023-01-01", "2024-06-01", "2024-06-02"],
            "description": ["  Coffee  ", "Coffee", "Rent", "Old", "Free", "Grocery"],
            "amount": [5.0, 5.0, 1200.0, 50.0, -10.0, None],
            "category": ["dinning", "dinning", "housing", "Groceries", "Dining", "grocery"],
            "account_type": ["checking"] * 6,
            "balance_after": [100.0] * 6,
            "is_income": [False] * 6,
        }
    )


def test_fill_missing_amounts_median() -> None:
    df = pd.DataFrame({"amount": [10.0, None, 30.0]})
    result = fill_missing_amounts(df)
    assert result["amount"].isna().sum() == 0
    assert result.loc[1, "amount"] == 20.0


def test_fill_missing_amounts_empty_column() -> None:
    df = pd.DataFrame({"other": [1, 2]})
    result = fill_missing_amounts(df)
    assert "amount" not in result.columns


def test_fill_missing_dates_forward_fill() -> None:
    df = pd.DataFrame({"date": ["2024-01-01", None, None]})
    result = fill_missing_dates(df)
    assert result["date"].isna().sum() == 0
    assert str(result.loc[1, "date"].date()) == "2024-01-01"


def test_fill_missing_dates_null_input() -> None:
    df = pd.DataFrame({"amount": [1.0]})
    result = fill_missing_dates(df)
    assert "date" not in result.columns


def test_remove_duplicates() -> None:
    df = pd.DataFrame({"transaction_id": ["a", "a", "b"], "amount": [1, 1, 2]})
    result = remove_duplicates(df)
    assert len(result) == 2


def test_normalize_category_labels_typos() -> None:
    df = pd.DataFrame({"category": ["dinning", "grocery", "SALARY", "Unknown Cat"]})
    result = normalize_category_labels(df)
    assert result.loc[0, "category"] == "Dining"
    assert result.loc[1, "category"] == "Groceries"
    assert result.loc[2, "category"] == "Income"
    assert result.loc[3, "category"] == "Other"


def test_validate_amounts_removes_non_positive() -> None:
    df = pd.DataFrame({"amount": [10.0, 0.0, -5.0, 3.0]})
    result = validate_amounts(df)
    assert len(result) == 2


def test_validate_dates_range() -> None:
    df = pd.DataFrame({"date": ["2024-06-01", "2020-01-01", "2024-12-31"]})
    result = validate_dates(df)
    assert len(result) == 2


def test_validate_categories() -> None:
    df = pd.DataFrame({"category": ["Dining", "InvalidCat", "Groceries"]})
    result = validate_categories(df)
    assert len(result) == 2


def test_clean_description() -> None:
    df = pd.DataFrame({"description": ["  hello   world  ", "normal"]})
    result = clean_description(df)
    assert result.loc[0, "description"] == "hello world"


def test_generate_quality_report() -> None:
    df = pd.DataFrame(
        {
            "transaction_id": ["t1"],
            "date": pd.to_datetime(["2024-01-01"]),
            "description": ["Test"],
            "amount": [10.0],
            "category": ["Dining"],
            "account_type": ["checking"],
            "balance_after": [100.0],
            "is_income": [False],
        }
    )
    report = generate_quality_report(df, original_count=5)
    assert report["row_count"] == 1
    assert report["rows_removed"] == 4
    assert report["schema_valid"] is True


def test_run_cleaning_pipeline(dirty_df: pd.DataFrame) -> None:
    cleaned, report = run_cleaning_pipeline(dirty_df)
    assert len(cleaned) < len(dirty_df)
    assert report["schema_valid"] is True
    assert "Dining" in cleaned["category"].values
