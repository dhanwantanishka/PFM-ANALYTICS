"""Dashboard API router — GET /dashboard."""
from __future__ import annotations
from datetime import date

try:
    from fastapi import APIRouter, Depends, Query
    from sqlalchemy.orm import Session
    from sqlalchemy import func
    _A = True
except ImportError:
    _A = False

if _A:
    from pfm.api.deps import get_db
    from pfm.api.schemas import DashboardSummary
    from pfm.db.models import Transaction, Account, Category

    router = APIRouter()

    @router.get("", response_model=DashboardSummary)
    def get_dashboard(
        user_id: str = Query(...),
        db: Session = Depends(get_db),
    ):
        """Live dashboard metrics from real DB data."""
        today = date.today()
        month_start = today.replace(day=1)

        base = (
            db.query(Transaction, Account)
            .join(Account, Transaction.account_id == Account.id)
            .filter(Account.user_id == user_id)
        )

        all_txn = base.all()
        today_txn = [(t, a) for t, a in all_txn if t.date == today]
        month_txn = [(t, a) for t, a in all_txn if t.date >= month_start]

        def sums(rows, income_flag):
            return sum(t.amount for t, a in rows if t.is_income == income_flag)

        total_income = sums(all_txn, True)
        total_expenses = sums(all_txn, False)
        net_savings = total_income - total_expenses
        savings_rate = round(net_savings / total_income * 100 if total_income > 0 else 0, 1)

        month_inc = sums(month_txn, True)
        month_exp = sums(month_txn, False)

        today_inc = sums(today_txn, True)
        today_exp = sums(today_txn, False)

        # Top expense category (all time)
        expense_txn = [(t, a) for t, a in all_txn if not t.is_income]
        cat_spend: dict[int, float] = {}
        for t, _ in expense_txn:
            cat_spend[t.category_id] = cat_spend.get(t.category_id, 0) + t.amount
        top_cat_id = max(cat_spend, key=cat_spend.get) if cat_spend else None
        top_cat = None
        if top_cat_id:
            cat_obj = db.query(Category).filter(Category.id == top_cat_id).first()
            top_cat = cat_obj.name if cat_obj else None

        largest_expense = max((t.amount for t, _ in expense_txn), default=None)

        from pfm.models.risk_scorer import financial_health_score
        import pandas as pd
        rows_data = [{
            "user_id": user_id, "date": t.date, "amount": t.amount,
            "is_income": t.is_income, "category_id": t.category_id,
        } for t, _ in all_txn]
        txn_df = pd.DataFrame(rows_data)
        if not txn_df.empty:
            txn_df["date"] = pd.to_datetime(txn_df["date"])
        import numpy as np
        health_score = 50
        if not txn_df.empty:
            try:
                h = financial_health_score(txn_df, pd.DataFrame(), user_id)
                health_score = h.get("overall_score", 50)
            except Exception:
                pass

        return DashboardSummary(
            user_id=user_id,
            total_balance=net_savings,
            today_income=today_inc,
            today_expenses=today_exp,
            month_income=month_inc,
            month_expenses=month_exp,
            net_savings=net_savings,
            savings_rate_pct=savings_rate,
            health_score=int(health_score),
            top_expense_category=top_cat,
            largest_expense=largest_expense,
            transaction_count=len(all_txn),
        )
