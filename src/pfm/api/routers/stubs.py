"""Stub routers for budgets, accounts, goals, bills, and analytics."""

from __future__ import annotations
from datetime import date

try:
    from fastapi import APIRouter, Depends, HTTPException, Query
    from sqlalchemy.orm import Session
    from sqlalchemy import func
    _A = True
except ImportError:
    _A = False

if _A:
    from pfm.api.deps import get_db
    from pfm.api.schemas import (
        BudgetCreate, BudgetOut, AccountCreate, AccountOut,
        GoalCreate, GoalOut, BillCreate, BillOut,
        CategoryBreakdown, MonthlyReport,
    )
    from pfm.db.models import Budget, Category, Account, Transaction, Goal, Bill

    # ── Budgets ───────────────────────────────────────────────────────────────
    router = APIRouter()

    budgets_router = APIRouter()

    @budgets_router.get("", response_model=list[BudgetOut])
    def list_budgets(user_id: str = Query(...), month: str = Query(None), db: Session = Depends(get_db)):
        q = db.query(Budget, Category.name).join(Category).filter(Budget.user_id == user_id)
        if month:
            q = q.filter(Budget.month == month)
        rows = q.all()
        result = []
        for b, cat_name in rows:
            # Actual spend for this month
            month_start = date(int(b.month[:4]), int(b.month[5:7]), 1)
            from calendar import monthrange
            _, last_day = monthrange(month_start.year, month_start.month)
            month_end = date(month_start.year, month_start.month, last_day)
            spent = db.query(func.coalesce(func.sum(Transaction.amount), 0)).join(Account).filter(
                Account.user_id == user_id,
                Transaction.category_id == b.category_id,
                Transaction.is_income == False,
                Transaction.date.between(month_start, month_end),
            ).scalar() or 0.0
            remaining = b.amount - spent
            pct = round(spent / b.amount * 100, 1) if b.amount > 0 else 0
            result.append(BudgetOut(id=b.id, category=cat_name, month=b.month,
                                    amount=b.amount, actual_spend=spent, pct_used=pct, remaining=remaining))
        return result

    @budgets_router.post("", response_model=BudgetOut, status_code=201)
    def create_budget(body: BudgetCreate, user_id: str = Query(...), db: Session = Depends(get_db)):
        cat = db.query(Category).filter(Category.name == body.category).first()
        if not cat:
            raise HTTPException(status_code=404, detail=f"Category '{body.category}' not found.")
        existing = db.query(Budget).filter(
            Budget.user_id == user_id, Budget.category_id == cat.id, Budget.month == body.month
        ).first()
        if existing:
            existing.amount = body.amount
            db.commit()
            db.refresh(existing)
            return BudgetOut(id=existing.id, category=body.category, month=body.month, amount=body.amount)
        b = Budget(category_id=cat.id, month=body.month, amount=body.amount, user_id=user_id)
        db.add(b)
        db.commit()
        db.refresh(b)
        return BudgetOut(id=b.id, category=body.category, month=body.month, amount=body.amount)

    # ── Accounts ──────────────────────────────────────────────────────────────
    accounts_router = APIRouter()

    @accounts_router.get("", response_model=list[AccountOut])
    def list_accounts(user_id: str = Query(...), db: Session = Depends(get_db)):
        accs = db.query(Account).filter(Account.user_id == user_id).all()
        result = []
        for acc in accs:
            inc = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
                Transaction.account_id == acc.id, Transaction.is_income == True).scalar() or 0
            exp = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
                Transaction.account_id == acc.id, Transaction.is_income == False).scalar() or 0
            result.append(AccountOut(id=acc.id, name=acc.name, account_type=acc.account_type, balance=inc - exp))
        return result

    @accounts_router.post("", response_model=AccountOut, status_code=201)
    def create_account(body: AccountCreate, user_id: str = Query(...), db: Session = Depends(get_db)):
        acc = Account(name=body.name, account_type=body.account_type, user_id=user_id)
        db.add(acc)
        db.commit()
        db.refresh(acc)
        return AccountOut(id=acc.id, name=acc.name, account_type=acc.account_type, balance=0.0)

    # ── Goals ─────────────────────────────────────────────────────────────────
    goals_router = APIRouter()

    @goals_router.get("", response_model=list[GoalOut])
    def list_goals(user_id: str = Query(...), db: Session = Depends(get_db)):
        goals = db.query(Goal).filter(Goal.user_id == user_id).all()
        return [GoalOut(
            id=g.id, name=g.name, target_amount=g.target_amount, saved_amount=g.saved_amount,
            target_date=g.target_date,
            pct_complete=round(g.saved_amount / g.target_amount * 100 if g.target_amount > 0 else 0, 1)
        ) for g in goals]

    @goals_router.post("", response_model=GoalOut, status_code=201)
    def create_goal(body: GoalCreate, user_id: str = Query(...), db: Session = Depends(get_db)):
        g = Goal(name=body.name, target_amount=body.target_amount,
                 saved_amount=body.saved_amount, target_date=body.target_date, user_id=user_id)
        db.add(g)
        db.commit()
        db.refresh(g)
        return GoalOut(id=g.id, name=g.name, target_amount=g.target_amount, saved_amount=g.saved_amount,
                       target_date=g.target_date, pct_complete=0.0)

    # ── Bills ─────────────────────────────────────────────────────────────────
    bills_router = APIRouter()

    @bills_router.get("", response_model=list[BillOut])
    def list_bills(user_id: str = Query(...), db: Session = Depends(get_db)):
        bills = db.query(Bill).filter(Bill.user_id == user_id).order_by(Bill.due_date).all()
        today = date.today()
        return [BillOut(
            id=b.id, name=b.name, amount=b.amount, due_date=b.due_date,
            is_recurring=b.is_recurring, reminder_days=b.reminder_days,
            days_until_due=(b.due_date - today).days
        ) for b in bills]

    @bills_router.post("", response_model=BillOut, status_code=201)
    def create_bill(body: BillCreate, user_id: str = Query(...), db: Session = Depends(get_db)):
        b = Bill(name=body.name, amount=body.amount, due_date=body.due_date,
                 is_recurring=body.is_recurring, reminder_days=body.reminder_days, user_id=user_id)
        db.add(b)
        db.commit()
        db.refresh(b)
        return BillOut(id=b.id, name=b.name, amount=b.amount, due_date=b.due_date,
                       is_recurring=b.is_recurring, reminder_days=b.reminder_days,
                       days_until_due=(b.due_date - date.today()).days)

    # ── Analytics ─────────────────────────────────────────────────────────────
    analytics_router = APIRouter()

    @analytics_router.get("/categories", response_model=list[CategoryBreakdown])
    def category_breakdown(user_id: str = Query(...), db: Session = Depends(get_db)):
        rows = (
            db.query(Category.name, func.sum(Transaction.amount).label("total"), func.count(Transaction.id).label("cnt"))
            .join(Transaction, Transaction.category_id == Category.id)
            .join(Account, Transaction.account_id == Account.id)
            .filter(Account.user_id == user_id, Transaction.is_income == False)
            .group_by(Category.name)
            .order_by(func.sum(Transaction.amount).desc())
            .all()
        )
        total_all = sum(r.total for r in rows)
        return [CategoryBreakdown(
            category=r.name,
            amount=r.total,
            pct_of_total=round(r.total / total_all * 100, 1) if total_all > 0 else 0,
            transaction_count=r.cnt,
        ) for r in rows]

    @analytics_router.get("/monthly", response_model=list[MonthlyReport])
    def monthly_report(user_id: str = Query(...), db: Session = Depends(get_db)):
        from sqlalchemy import extract, cast, String
        rows = (
            db.query(
                func.strftime("%Y-%m", Transaction.date).label("month"),
                func.sum(
                    func.case((Transaction.is_income == True, Transaction.amount), else_=0)
                ).label("income"),
                func.sum(
                    func.case((Transaction.is_income == False, Transaction.amount), else_=0)
                ).label("expenses"),
            )
            .join(Account, Transaction.account_id == Account.id)
            .filter(Account.user_id == user_id)
            .group_by("month")
            .order_by("month")
            .all()
        )
        result = []
        for r in rows:
            net = r.income - r.expenses
            savings_rate = round(net / r.income * 100 if r.income > 0 else 0, 1)
            result.append(MonthlyReport(
                month=r.month, income=r.income, expenses=r.expenses,
                net=net, savings_rate_pct=savings_rate, top_category=None,
            ))
        return result

    # Placeholder router for compatibility with main.py imports
    router = budgets_router

    # Export named routers
    budgets = type("Module", (), {"router": budgets_router})()
    accounts = type("Module", (), {"router": accounts_router})()
    goals = type("Module", (), {"router": goals_router})()
    bills = type("Module", (), {"router": bills_router})()
    analytics = type("Module", (), {"router": analytics_router})()
