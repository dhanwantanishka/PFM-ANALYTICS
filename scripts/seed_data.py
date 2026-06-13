"""Seed the database with synthetic personal finance data."""

import sys
from pathlib import Path

# Add src to path for script execution
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pfm.config import DB_PATH, RAW_DATA_DIR
from pfm.config import USERS
from pfm.data_generation.synthetic import (
    generate_budgets,
    generate_transactions,
    save_datasets,
    validate_dataset_requirements,
)
from pfm.etl.pipeline import ETLPipeline


def main() -> None:
    names = ", ".join(u["user_name"] for u in USERS)
    print(f"Generating synthetic data for {len(USERS)} users ({names})...")
    transactions = generate_transactions(users=USERS, months=13, transactions_per_user=1500)
    budgets = generate_budgets(transactions)
    checks = validate_dataset_requirements(transactions)

    paths = save_datasets(transactions, budgets)
    print(f"  Transactions: {checks['row_count']:,} rows")
    print(f"  Users: {checks['user_count']} — {names}")
    print(f"  Month span: {checks['month_span']} months")
    print(f"  Spending categories: {checks['spending_category_count']}")
    print(f"  Requirements met: {all(checks[k] for k in checks if k.endswith('_plus'))}")
    print(f"  Saved to: {paths['csv']}")

    print("\nRunning ETL pipeline...")
    if DB_PATH.exists():
        DB_PATH.unlink()

    pipeline = ETLPipeline()
    result = pipeline.run(paths["csv"], fmt="csv", budgets_df=budgets)

    print(f"  Loaded {result['rows_loaded']:,} transactions to {DB_PATH}")
    print(f"  Quality report: {result['quality_report']['row_count']} rows retained")
    print(f"  Schema valid: {result['quality_report']['schema_valid']}")
    print("\nDone!")


if __name__ == "__main__":
    main()
