"""ETL pipeline: extract, transform, load."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from pfm.cleaning.validators import run_cleaning_pipeline
from pfm.config import DB_PATH, NEEDS_CATEGORIES, SAVINGS_CATEGORIES, WANTS_CATEGORIES
from pfm.db import get_session, init_db
from pfm.db.models import Account, Budget, Category, Transaction, User
from pfm.features.engineering import engineer_features
from pfm.ingestion.loaders import load_csv, load_excel, load_json, validate_schema


class ETLPipeline:
    """Reusable ETL pipeline for personal finance data."""

    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or DB_PATH
        self.raw_df: pd.DataFrame | None = None
        self.cleaned_df: pd.DataFrame | None = None
        self.quality_report: dict[str, Any] = {}
        self.schema_issues: dict[str, list[str]] = {}

    def extract(self, source: str | Path, fmt: str = "csv") -> pd.DataFrame:
        """Load data from CSV, Excel, or JSON."""
        source = Path(source)
        loaders = {"csv": load_csv, "excel": load_excel, "json": load_json}
        if fmt not in loaders:
            raise ValueError(f"Unsupported format: {fmt}. Use csv, excel, or json.")
        self.raw_df = loaders[fmt](source)
        self.schema_issues = validate_schema(self.raw_df)
        return self.raw_df

    def transform(self, df: pd.DataFrame | None = None) -> pd.DataFrame:
        """Clean, validate, and engineer features."""
        data = df if df is not None else self.raw_df
        if data is None:
            raise ValueError("No data to transform. Call extract() first.")
        cleaned, report = run_cleaning_pipeline(data)
        self.cleaned_df = engineer_features(cleaned)
        self.quality_report = report
        return self.cleaned_df

    def load(
        self,
        df: pd.DataFrame | None = None,
        budgets_df: pd.DataFrame | None = None,
        session: Session | None = None,
    ) -> int:
        """Persist cleaned data to SQLite."""
        data = df if df is not None else self.cleaned_df
        if data is None:
            raise ValueError("No data to load. Call transform() first.")

        init_db(self.db_path)
        own_session = session is None
        session = session or get_session(self.db_path)

        try:
            self._seed_categories(session)
            self._seed_users(session, data, budgets_df)
            account_map = self._seed_accounts(session, data)
            category_map = {c.name: c.id for c in session.query(Category).all()}
            count = self._load_transactions(session, data, account_map, category_map)

            if budgets_df is not None:
                self._load_budgets(session, budgets_df, category_map)

            session.commit()
            return count
        except Exception:
            session.rollback()
            raise
        finally:
            if own_session:
                session.close()

    def run(
        self,
        source: str | Path,
        fmt: str = "csv",
        budgets_df: pd.DataFrame | None = None,
    ) -> dict[str, Any]:
        """Execute the full ETL pipeline."""
        self.extract(source, fmt)
        self.transform()
        rows_loaded = self.load(budgets_df=budgets_df)
        return {
            "rows_loaded": rows_loaded,
            "quality_report": self.quality_report,
            "schema_issues": self.schema_issues,
        }

    def _seed_users(
        self,
        session: Session,
        df: pd.DataFrame,
        budgets_df: pd.DataFrame | None,
    ) -> None:
        """Seed default/synthetic users if they do not exist."""
        from pfm.auth import hash_password
        from pfm.config import USERS

        # Extract unique users from df or default to "user_1"
        user_ids = set()
        user_col = "user_id" if "user_id" in df.columns else None
        if user_col:
            user_ids.update(df[user_col].dropna().astype(str).unique())
        else:
            user_ids.add("user_1")

        if budgets_df is not None and "user_id" in budgets_df.columns:
            user_ids.update(budgets_df["user_id"].dropna().astype(str).unique())

        config_user_map = {u["user_id"]: u["user_name"] for u in USERS}

        existing_user_ids = {u.user_id for u in session.query(User).all()}

        for uid in user_ids:
            if uid not in existing_user_ids:
                name = config_user_map.get(uid, uid.replace("_", " ").title())
                # Default password for seeded users is "password123"
                p_hash = hash_password("password123")
                session.add(User(user_id=uid, user_name=name, password_hash=p_hash))
        session.flush()

    def _seed_categories(self, session: Session) -> None:
        budget_type_map = {}
        for cat in NEEDS_CATEGORIES:
            budget_type_map[cat] = "needs"
        for cat in WANTS_CATEGORIES:
            budget_type_map[cat] = "wants"
        for cat in SAVINGS_CATEGORIES:
            budget_type_map[cat] = "savings"

        existing = {c.name for c in session.query(Category).all()}
        from pfm.config import ALLOWED_CATEGORIES

        for name in ALLOWED_CATEGORIES:
            if name not in existing:
                session.add(
                    Category(name=name, budget_type=budget_type_map.get(name, "expense"))
                )
        session.flush()

    def _seed_accounts(self, session: Session, df: pd.DataFrame) -> dict[str, int]:
        account_map: dict[str, int] = {}
        user_col = "user_id" if "user_id" in df.columns else None

        for _, row in df[["account_type"] + ([user_col] if user_col else [])].drop_duplicates().iterrows():
            user_id = row[user_col] if user_col else "user_1"
            key = f"{user_id}_{row['account_type']}"
            existing = (
                session.query(Account)
                .filter_by(name=key, account_type=row["account_type"], user_id=user_id)
                .first()
            )
            if existing:
                account_map[key] = existing.id
            else:
                acct = Account(name=key, account_type=row["account_type"], user_id=user_id)
                session.add(acct)
                session.flush()
                account_map[key] = acct.id

        return account_map

    def _load_transactions(
        self,
        session: Session,
        df: pd.DataFrame,
        account_map: dict[str, int],
        category_map: dict[str, int],
    ) -> int:
        count = 0
        for _, row in df.iterrows():
            user_id = row.get("user_id", "user_1")
            acct_key = f"{user_id}_{row['account_type']}"
            txn = Transaction(
                transaction_id=str(row["transaction_id"]),
                date=pd.Timestamp(row["date"]).date(),
                description=str(row["description"]),
                amount=float(row["amount"]),
                category_id=category_map[row["category"]],
                account_id=account_map[acct_key],
                balance_after=float(row["balance_after"]) if pd.notna(row.get("balance_after")) else None,
                is_income=bool(row["is_income"]),
                merchant=row.get("merchant"),
                day_of_week=int(row["day_of_week"]) if pd.notna(row.get("day_of_week")) else None,
                is_weekend=bool(row["is_weekend"]) if pd.notna(row.get("is_weekend")) else None,
                month=int(row["month"]) if pd.notna(row.get("month")) else None,
                quarter=int(row["quarter"]) if pd.notna(row.get("quarter")) else None,
                rolling_30d_spend=float(row["rolling_30d_spend"])
                if pd.notna(row.get("rolling_30d_spend"))
                else None,
            )
            session.merge(txn)
            count += 1
        return count

    def _load_budgets(
        self,
        session: Session,
        budgets_df: pd.DataFrame,
        category_map: dict[str, int],
    ) -> None:
        for _, row in budgets_df.iterrows():
            budget = Budget(
                category_id=category_map[row["category"]],
                month=str(row["month"]),
                amount=float(row["amount"]),
                user_id=str(row.get("user_id", "user_1")),
            )
            session.add(budget)
        session.flush()
