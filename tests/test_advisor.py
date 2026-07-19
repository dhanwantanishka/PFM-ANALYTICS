"""Tests for AI finance advisor."""

from app.services.advisor import answer_question


def test_advisor_savings_rate(sample_transactions, sample_budgets):
    answer = answer_question("What is my savings rate?", sample_transactions, sample_budgets, "user_a")
    assert "savings rate" in answer.lower()


def test_advisor_spending(sample_transactions, sample_budgets):
    answer = answer_question("Where did my money go?", sample_transactions, sample_budgets, "user_a")
    assert "category" in answer.lower() or "spend" in answer.lower()


def test_advisor_fallback(sample_transactions, sample_budgets):
    answer = answer_question("hello there", sample_transactions, sample_budgets, "user_a")
    assert "savings rate" in answer.lower() or "spending" in answer.lower()
