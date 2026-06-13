"""Synthetic personal finance data generator using Faker."""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

from pfm.config import (
    ALLOWED_CATEGORIES,
    MIN_MONTHS,
    MIN_SPENDING_CATEGORIES,
    MIN_TRANSACTIONS,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    USERS,
)

fake = Faker()
Faker.seed(42)
random.seed(42)

EXPENSE_CATEGORIES = [c for c in ALLOWED_CATEGORIES if c not in ("Income", "Savings")]
ACCOUNT_TYPES = ["checking", "savings", "credit"]

MERCHANTS = {
    "Groceries": ["Whole Foods", "Trader Joe's", "Walmart", "Costco"],
    "Dining": ["Starbucks", "McDonald's", "Chipotle", "Local Bistro"],
    "Transportation": ["Shell Gas", "Uber", "Metro Transit", "Parking Co"],
    "Housing": ["Rent Payment", "Property Mgmt", "HOA Fees"],
    "Utilities": ["Electric Co", "Water Dept", "Internet Provider"],
    "Healthcare": ["CVS Pharmacy", "City Hospital", "Dental Care"],
    "Entertainment": ["Netflix", "AMC Theaters", "Spotify"],
    "Shopping": ["Amazon", "Target", "Best Buy"],
    "Subscriptions": ["Adobe", "Gym Membership", "Cloud Storage"],
    "Education": ["Online Course", "Bookstore", "Tuition"],
    "Travel": ["Delta Airlines", "Marriott", "Expedia"],
    "Insurance": ["State Farm", "Health Ins Co"],
    "Debt Payment": ["Student Loan", "Credit Card Payment"],
    "Other": ["Misc Purchase", "ATM Withdrawal"],
}


def _random_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


def validate_dataset_requirements(transactions: pd.DataFrame) -> dict[str, bool | int]:
    """Verify the dataset meets assignment minimums."""
    expense_categories = transactions.loc[~transactions["is_income"], "category"].nunique()
    month_span = (
        transactions["date"].max().to_period("M") - transactions["date"].min().to_period("M")
    ).n + 1

    checks = {
        "rows_5000_plus": len(transactions) >= MIN_TRANSACTIONS,
        "users_2_plus": transactions["user_name"].nunique() >= 2,
        "months_12_plus": month_span >= MIN_MONTHS,
        "categories_10_plus": expense_categories >= MIN_SPENDING_CATEGORIES,
        "row_count": len(transactions),
        "user_count": int(transactions["user_name"].nunique()),
        "month_span": int(month_span),
        "spending_category_count": int(expense_categories),
    }
    return checks


def generate_transactions(
    users: list[dict[str, str]] | None = None,
    months: int = 13,
    transactions_per_user: int = 1500,
    start_date: str = "2024-01-01",
) -> pd.DataFrame:
    """Generate synthetic transaction data for named users."""
    users = users or USERS
    start = datetime.strptime(start_date, "%Y-%m-%d")
    # Use calendar months so the span is reliably 12+
    end = datetime(start.year + (start.month + months - 1) // 12, (start.month + months - 1) % 12 + 1, 1)
    end = end - timedelta(days=1)
    rows: list[dict] = []

    for user in users:
        user_id = user["user_id"]
        user_name = user["user_name"]
        accounts = [
            {"name": f"{user_id}_checking", "type": "checking", "balance": 5000.0},
            {"name": f"{user_id}_savings", "type": "savings", "balance": 15000.0},
            {"name": f"{user_id}_credit", "type": "credit", "balance": -1200.0},
        ]

        for _ in range(transactions_per_user):
            account = random.choice(accounts)
            is_income = random.random() < 0.08
            if is_income:
                category = "Income"
                amount = round(random.uniform(1500, 4500), 2)
                merchant = fake.company()
                description = f"Payroll - {merchant}"
            else:
                category = random.choices(
                    EXPENSE_CATEGORIES,
                    weights=[15, 8, 12, 10, 8, 5, 7, 10, 5, 3, 4, 5, 4, 4],
                    k=1,
                )[0]
                amount = round(random.uniform(5, 500), 2)
                if category == "Housing":
                    amount = round(random.uniform(800, 2200), 2)
                merchant = random.choice(MERCHANTS.get(category, ["Unknown"]))
                description = f"{merchant} - {fake.catch_phrase()}"

            if account["type"] == "credit" and not is_income:
                account["balance"] -= amount
            elif is_income:
                account["balance"] += amount
            else:
                account["balance"] -= amount

            rows.append(
                {
                    "transaction_id": str(uuid.uuid4())[:12],
                    "date": _random_date(start, end).strftime("%Y-%m-%d"),
                    "description": description,
                    "amount": amount,
                    "category": category,
                    "account_type": account["type"],
                    "balance_after": round(account["balance"], 2),
                    "is_income": is_income,
                    "merchant": merchant,
                    "user_id": user_id,
                    "user_name": user_name,
                }
            )

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def generate_budgets(transactions: pd.DataFrame) -> pd.DataFrame:
    """Generate monthly budget targets per category from transaction patterns."""
    expense_txns = transactions[~transactions["is_income"]]
    monthly_avg = (
        expense_txns.groupby(["user_id", "category"])
        .agg(monthly_spend=("amount", "mean"))
        .reset_index()
    )
    monthly_avg["budget_amount"] = (monthly_avg["monthly_spend"] * 1.1).round(2)

    months = pd.date_range(
        transactions["date"].min().replace(day=1),
        transactions["date"].max().replace(day=1),
        freq="MS",
    )

    budget_rows = []
    for month in months:
        for _, row in monthly_avg.iterrows():
            budget_rows.append(
                {
                    "user_id": row["user_id"],
                    "category": row["category"],
                    "month": month.strftime("%Y-%m"),
                    "amount": row["budget_amount"],
                }
            )

    return pd.DataFrame(budget_rows)


def save_datasets(
    transactions: pd.DataFrame,
    budgets: pd.DataFrame,
    raw_dir: Path | None = None,
) -> dict[str, Path]:
    """Save generated data to CSV, Excel, and JSON in the raw data directory."""
    raw_dir = raw_dir or RAW_DATA_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    paths = {
        "csv": raw_dir / "transactions.csv",
        "excel": raw_dir / "transactions.xlsx",
        "json": raw_dir / "transactions.json",
        "budgets_csv": raw_dir / "budgets.csv",
    }

    transactions.to_csv(paths["csv"], index=False)
    transactions.to_excel(paths["excel"], index=False, engine="openpyxl")
    transactions.to_json(paths["json"], orient="records", date_format="iso")
    budgets.to_csv(paths["budgets_csv"], index=False)

    return paths
