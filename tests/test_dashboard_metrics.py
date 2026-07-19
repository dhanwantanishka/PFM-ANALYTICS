"""Tests for dashboard metrics service."""

import pandas as pd

from app.services.dashboard_metrics import build_dashboard_summary, generate_alerts, generate_insights


def test_build_dashboard_summary(sample_transactions, sample_budgets):
    filtered = sample_transactions[sample_transactions["user_id"] == "user_a"]
    summary = build_dashboard_summary(filtered, sample_budgets, "user_a", "Alice")
    assert "health_score" in summary
    assert summary["monthly_income"] >= 0
    assert summary["monthly_expenses"] >= 0


def test_generate_insights_returns_list(sample_transactions, sample_budgets):
    filtered = sample_transactions[sample_transactions["user_id"] == "user_a"]
    summary = build_dashboard_summary(filtered, sample_budgets, "user_a", "Alice")
    insights = generate_insights(summary)
    assert isinstance(insights, list)
    assert len(insights) >= 1


def test_generate_alerts_returns_list(sample_transactions, sample_budgets):
    filtered = sample_transactions[sample_transactions["user_id"] == "user_a"]
    summary = build_dashboard_summary(filtered, sample_budgets, "user_a", "Alice")
    alerts = generate_alerts(summary)
    assert isinstance(alerts, list)
    assert "title" in alerts[0]
