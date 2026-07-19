"""Tests for forecaster model comparison."""

import pandas as pd

from pfm.models.forecaster import compare_all_models, forecast_recommendation, prepare_forecast_data


def test_compare_all_models(sample_transactions):
    X, y = prepare_forecast_data(sample_transactions, "user_a")
    if len(X) < 10:
        return
    comparison = compare_all_models(X, y)
    assert len(comparison) == 3
    assert "mae" in comparison.columns
    assert comparison.iloc[0]["mae"] <= comparison["mae"].max()


def test_forecast_recommendation():
    comparison = pd.DataFrame(
        [
            {"model": "XGBoost", "mae": 100.0, "rmse": 150.0, "r2": 0.5},
            {"model": "Linear Regression", "mae": 120.0, "rmse": 160.0, "r2": 0.4},
        ]
    )
    text = forecast_recommendation(comparison, horizon=7)
    assert "XGBoost" in text
