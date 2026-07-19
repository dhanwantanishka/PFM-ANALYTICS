"""Tests for financial health scoring."""

from pfm.models.risk_scorer import financial_health_score, risk_categories


def test_financial_health_score(sample_transactions, sample_budgets):
    result = financial_health_score(sample_transactions, sample_budgets, "user_a")
    assert 0 <= result["overall_score"] <= 100
    assert result["rating"] in {"Excellent", "Good", "Fair", "Poor"}
    assert "score_breakdown" in result


def test_risk_categories(sample_transactions, sample_budgets):
    result = risk_categories(sample_transactions, sample_budgets, "user_a")
    assert "at_risk_details" in result
