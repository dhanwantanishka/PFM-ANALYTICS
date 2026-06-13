"""Tests for ETL pipeline and feature engineering."""

from pathlib import Path

import pandas as pd
import pytest

from pfm.etl.pipeline import ETLPipeline
from pfm.features.engineering import add_temporal_features, engineer_features


@pytest.fixture
def clean_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "transaction_id": [f"t{i}" for i in range(5)],
            "date": pd.date_range("2024-06-01", periods=5, freq="D"),
            "description": ["Item"] * 5,
            "amount": [10.0, 20.0, 15.0, 30.0, 5.0],
            "category": ["Dining"] * 5,
            "account_type": ["checking"] * 5,
            "balance_after": [100.0] * 5,
            "is_income": [False] * 5,
            "user_id": ["user_1"] * 5,
        }
    )


def test_add_temporal_features(clean_df: pd.DataFrame) -> None:
    result = add_temporal_features(clean_df)
    assert "day_of_week" in result.columns
    assert "is_weekend" in result.columns
    assert "month" in result.columns
    assert "quarter" in result.columns


def test_engineer_features(clean_df: pd.DataFrame) -> None:
    result = engineer_features(clean_df)
    assert "rolling_30d_spend" in result.columns


def test_etl_pipeline_end_to_end(tmp_path: Path, clean_df: pd.DataFrame) -> None:
    csv_path = tmp_path / "transactions.csv"
    db_path = tmp_path / "test.db"
    clean_df.to_csv(csv_path, index=False)

    pipeline = ETLPipeline(db_path=db_path)
    result = pipeline.run(csv_path, fmt="csv")

    assert result["rows_loaded"] == 5
    assert result["quality_report"]["schema_valid"] is True
    assert db_path.exists()
