"""Expense forecasting — model comparison, confidence intervals, recommendations."""

from __future__ import annotations

import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parents[1]
_SRC_DIR = _APP_DIR.parent / "src"
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

import pandas as pd
import streamlit as st

import utils.bootstrap  # noqa: F401

from components.charts import forecast_chart, model_comparison_bar
from components.filters import apply_filters, render_sidebar_filters
from components.kpi_cards import render_kpi_row
from components.layout import render_page_header, render_section
from components.states import render_empty_state
from pfm.models.forecaster import (
    compare_all_models,
    forecast_next_days,
    forecast_recommendation,
    prepare_forecast_data,
    train_linear_regression,
    train_random_forest,
    train_xgboost,
)
from utils.data_loader import load_transactions

render_page_header(
    "Expense forecasting",
    "Compare Linear Regression, Random Forest, and XGBoost on your spending history.",
    ":material/trending_up:",
)

user_id = st.session_state.get("user_id", "user_1")
transactions = load_transactions(user_id)
filters = render_sidebar_filters(transactions)
filtered = apply_filters(transactions, filters)

user_txns = filtered
if len(user_txns.loc[~user_txns["is_income"]]) < 40:
    render_empty_state(
        "Insufficient history",
        "Select a date range with at least 40 days of expense transactions.",
        ":material/history:",
    )
    st.stop()

col_a, col_b, col_c = st.columns([2, 1, 1])
with col_a:
    model_choice = st.segmented_control(
        "Forecasting model",
        ["Linear Regression", "Random Forest", "XGBoost"],
        default="XGBoost",
    )
with col_b:
    horizon = st.slider("Forecast horizon (days)", min_value=3, max_value=30, value=7)
with col_c:
    ci_pct = st.slider("Confidence band (±%)", min_value=5, max_value=30, value=15) / 100

with st.spinner("Training models and generating forecast..."):
    X, y = prepare_forecast_data(transactions, filters.user_id)
    comparison = compare_all_models(X, y)
    trainers = {
        "Linear Regression": train_linear_regression,
        "Random Forest": train_random_forest,
        "XGBoost": train_xgboost,
    }
    result = trainers[model_choice](X, y)
    forecast_values = forecast_next_days(result["model"], X, days=horizon)

render_kpi_row(
    [
        {"label": "Selected model", "value": result["type"]},
        {"label": "MAE", "value": f"₹{result['mae']:,.2f}"},
        {"label": "RMSE", "value": f"₹{result['rmse']:,.2f}"},
        {"label": "R²", "value": f"{result['r2']:.3f}"},
        {"label": f"{horizon}-day total", "value": f"₹{forecast_values.sum():,.0f}"},
    ]
)

expenses = user_txns.loc[~user_txns["is_income"]]
history = expenses.groupby("date")["amount"].sum().reset_index().sort_values("date")
last_date = history["date"].max()
forecast_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=horizon, freq="D")

render_section(f"{horizon}-day forecast vs history")
st.plotly_chart(
    forecast_chart(history.tail(90), forecast_values, forecast_dates, ci_pct=ci_pct),
    width="stretch",
)

compare_left, compare_right = st.columns(2)
with compare_left:
    render_section("Model comparison — MAE")
    st.plotly_chart(model_comparison_bar(comparison, metric="mae"), width="stretch")
with compare_right:
    render_section("Model comparison — R²")
    st.plotly_chart(model_comparison_bar(comparison, metric="r2"), width="stretch")

st.dataframe(comparison, hide_index=True, width="stretch")

if "feature_importance" in result:
    with st.expander("Prediction explanation — feature importance"):
        st.dataframe(result["feature_importance"], hide_index=True, width="stretch")

render_section("Business recommendation")
st.info(forecast_recommendation(comparison, horizon))

with st.expander("Methodology notes"):
    st.markdown(
        """
- **Linear Regression** — fast baseline; assumes linear relationships between lag/rolling features and spend.
- **Random Forest** — captures non-linear patterns and provides feature importance.
- **XGBoost** — gradient boosting; typically strongest on tabular financial data.
- Models use lag (t-1, t-7) and rolling (7d, 30d) features on daily aggregated spend with an 80/20 split.
- Confidence bands are illustrative (±% of forecast); not formal prediction intervals.
        """
    )
