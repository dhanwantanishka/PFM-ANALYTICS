"""Tests for synthetic data generation requirements."""

from pfm.config import USERS
from pfm.data_generation.synthetic import generate_transactions, validate_dataset_requirements


def test_named_users_in_dataset() -> None:
    transactions = generate_transactions(users=USERS, months=13, transactions_per_user=1500)
    names = set(transactions["user_name"].unique())
    assert "Rajesh Sharma" in names
    assert "Priya Singh" in names
    assert "Amit Kumar" in names
    assert "Tanishka Dhanwan" in names


def test_dataset_meets_assignment_minimums() -> None:
    transactions = generate_transactions(users=USERS, months=13, transactions_per_user=1500)
    checks = validate_dataset_requirements(transactions)

    assert checks["rows_5000_plus"] is True
    assert checks["users_2_plus"] is True
    assert checks["months_12_plus"] is True
    assert checks["categories_10_plus"] is True
    assert checks["row_count"] >= 5000
    assert checks["user_count"] == 4
    assert checks["month_span"] >= 12
    assert checks["spending_category_count"] >= 10
