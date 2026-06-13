"""Application configuration."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DB_PATH = DATA_DIR / "pfm.db"

ALLOWED_CATEGORIES = [
    "Housing",
    "Utilities",
    "Groceries",
    "Dining",
    "Transportation",
    "Healthcare",
    "Insurance",
    "Entertainment",
    "Shopping",
    "Education",
    "Travel",
    "Subscriptions",
    "Income",
    "Savings",
    "Debt Payment",
    "Other",
]

NEEDS_CATEGORIES = {"Housing", "Utilities", "Groceries", "Healthcare", "Insurance", "Transportation"}
WANTS_CATEGORIES = {"Dining", "Entertainment", "Shopping", "Travel", "Subscriptions"}
SAVINGS_CATEGORIES = {"Savings", "Income"}

DATE_MIN = "2024-01-01"
DATE_MAX = "2025-12-31"

# Simulated users for synthetic dataset (assignment requires 2+ users)
USERS = [
    {"user_id": "rajesh_sharma", "user_name": "Rajesh Sharma"},
    {"user_id": "priya_singh", "user_name": "Priya Singh"},
    {"user_id": "amit_kumar", "user_name": "Amit Kumar"},
    {"user_id": "tanishka_dhanwan", "user_name": "Tanishka Dhanwan"},
]

MIN_TRANSACTIONS = 5000
MIN_MONTHS = 12
MIN_SPENDING_CATEGORIES = 10
