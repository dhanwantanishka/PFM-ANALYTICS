"""Pytest configuration and shared fixtures."""

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "app"))


@pytest.fixture
def sample_transactions() -> pd.DataFrame:
    """Minimal transaction dataset for analytics tests."""
    dates = pd.date_range("2024-01-01", periods=90, freq="D")
    rows = []
    for i, date in enumerate(dates):
        rows.append(
            {
                "transaction_id": f"txn_{i}",
                "date": date,
                "description": "Salary" if i % 30 == 0 else "Groceries",
                "amount": 50000.0 if i % 30 == 0 else 500.0 + (i % 7) * 50,
                "category": "Income" if i % 30 == 0 else "Groceries",
                "account_type": "checking",
                "balance_after": 100000 - i * 100,
                "is_income": i % 30 == 0,
                "merchant": "Employer" if i % 30 == 0 else "Store",
                "user_id": "user_a",
                "user_name": "Alice",
            }
        )
    return pd.DataFrame(rows)


@pytest.fixture
def sample_budgets() -> pd.DataFrame:
    """Minimal budget dataset for KPI tests."""
    return pd.DataFrame(
        [
            {"user_id": "user_a", "month": "2024-01", "category": "Groceries", "amount": 5000},
            {"user_id": "user_a", "month": "2024-02", "category": "Groceries", "amount": 5000},
            {"user_id": "user_a", "month": "2024-03", "category": "Groceries", "amount": 5000},
        ]
    )


@pytest.fixture
def sample_spending_df() -> pd.DataFrame:
    """Expense-only sample for spending analysis tests."""
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=10, freq="D"),
            "amount": [100, 200, 150, 300, 50, 120, 180, 90, 250, 110],
            "category": [
                "Dining",
                "Groceries",
                "Dining",
                "Housing",
                "Utilities",
                "Dining",
                "Entertainment",
                "Groceries",
                "Housing",
                "Dining",
            ],
            "merchant": [
                "Restaurant1",
                "Store1",
                "Restaurant2",
                "Landlord",
                "Provider",
                "Restaurant1",
                "Cinema",
                "Store1",
                "Landlord",
                "Restaurant3",
            ],
            "is_income": [False] * 10,
            "user_name": ["User1"] * 10,
        }
    )
