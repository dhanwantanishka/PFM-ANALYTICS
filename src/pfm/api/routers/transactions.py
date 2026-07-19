"""Transactions API router — GET, POST, PUT, DELETE /transactions."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

try:
    from fastapi import APIRouter, Depends, HTTPException, Query
    from sqlalchemy.orm import Session
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False

if _AVAILABLE:
    from pfm.api.deps import get_db
    from pfm.api.schemas import TransactionCreate, TransactionOut, TransactionUpdate, PaginatedTransactions
    from pfm.db.models import Account, Category, Transaction

    router = APIRouter()

    def _get_user_id(x_user_id: str = Query(..., description="Authenticated user ID")) -> str:
        return x_user_id

    @router.get("", response_model=PaginatedTransactions)
    def list_transactions(
        user_id: str = Depends(_get_user_id),
        page: int = Query(1, ge=1),
        page_size: int = Query(50, ge=1, le=500),
        category: Optional[str] = Query(None),
        start_date: Optional[date] = Query(None),
        end_date: Optional[date] = Query(None),
        transaction_type: Optional[str] = Query(None),
        search: Optional[str] = Query(None),
        db: Session = Depends(get_db),
    ):
        """Paginated transaction list with filters."""
        q = (
            db.query(Transaction, Category.name.label("cat_name"), Account.account_type)
            .join(Category, Transaction.category_id == Category.id)
            .join(Account, Transaction.account_id == Account.id)
            .filter(Account.user_id == user_id)
        )
        if category:
            q = q.filter(Category.name == category)
        if start_date:
            q = q.filter(Transaction.date >= start_date)
        if end_date:
            q = q.filter(Transaction.date <= end_date)
        if transaction_type:
            q = q.filter(Transaction.transaction_type == transaction_type.lower())
        if search:
            s = f"%{search}%"
            q = q.filter(
                Transaction.description.ilike(s)
                | Transaction.merchant.ilike(s)
                | Transaction.notes.ilike(s)
            )

        total = q.count()
        rows = q.order_by(Transaction.date.desc()).offset((page - 1) * page_size).limit(page_size).all()

        items = []
        for txn, cat_name, acc_type in rows:
            items.append(TransactionOut(
                id=txn.id,
                transaction_id=txn.transaction_id,
                date=txn.date,
                description=txn.description,
                amount=txn.amount,
                category=cat_name,
                account_type=acc_type,
                is_income=txn.is_income,
                transaction_type=txn.transaction_type or "expense",
                merchant=txn.merchant,
                notes=txn.notes,
                payment_method=txn.payment_method,
                location=txn.location,
            ))

        return PaginatedTransactions(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
            items=items,
        )

    @router.post("", response_model=TransactionOut, status_code=201)
    def create_transaction(
        body: TransactionCreate,
        user_id: str = Depends(_get_user_id),
        db: Session = Depends(get_db),
    ):
        """Create a new transaction."""
        # Validate account belongs to user
        account = db.query(Account).filter(Account.id == body.account_id, Account.user_id == user_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found or does not belong to user.")
        category = db.query(Category).filter(Category.name == body.category).first()
        if not category:
            raise HTTPException(status_code=404, detail=f"Category '{body.category}' not found.")

        txn = Transaction(
            transaction_id=str(uuid.uuid4()),
            date=body.date,
            time=body.time,
            description=body.description,
            amount=body.amount,
            category_id=category.id,
            account_id=body.account_id,
            is_income=body.transaction_type == "income",
            transaction_type=body.transaction_type,
            merchant=body.merchant,
            notes=body.notes,
            payment_method=body.payment_method,
            location=body.location,
            day_of_week=body.date.weekday(),
            is_weekend=body.date.weekday() >= 5,
            month=body.date.month,
            quarter=(body.date.month - 1) // 3 + 1,
        )
        db.add(txn)
        db.commit()
        db.refresh(txn)

        return TransactionOut(
            id=txn.id, transaction_id=txn.transaction_id, date=txn.date,
            description=txn.description, amount=txn.amount, category=body.category,
            account_type=account.account_type, is_income=txn.is_income,
            transaction_type=txn.transaction_type, merchant=txn.merchant,
            notes=txn.notes, payment_method=txn.payment_method, location=txn.location,
        )

    @router.put("/{transaction_id}", response_model=TransactionOut)
    def update_transaction(
        transaction_id: str,
        body: TransactionUpdate,
        user_id: str = Depends(_get_user_id),
        db: Session = Depends(get_db),
    ):
        """Update an existing transaction."""
        txn = (
            db.query(Transaction)
            .join(Account, Transaction.account_id == Account.id)
            .filter(Transaction.transaction_id == transaction_id, Account.user_id == user_id)
            .first()
        )
        if not txn:
            raise HTTPException(status_code=404, detail="Transaction not found.")

        if body.amount is not None:
            txn.amount = body.amount
        if body.description is not None:
            txn.description = body.description
        if body.transaction_type is not None:
            txn.transaction_type = body.transaction_type
            txn.is_income = body.transaction_type == "income"
        if body.merchant is not None:
            txn.merchant = body.merchant
        if body.notes is not None:
            txn.notes = body.notes
        if body.payment_method is not None:
            txn.payment_method = body.payment_method
        if body.category is not None:
            cat = db.query(Category).filter(Category.name == body.category).first()
            if cat:
                txn.category_id = cat.id

        db.commit()
        db.refresh(txn)

        cat = db.query(Category).filter(Category.id == txn.category_id).first()
        acc = db.query(Account).filter(Account.id == txn.account_id).first()
        return TransactionOut(
            id=txn.id, transaction_id=txn.transaction_id, date=txn.date,
            description=txn.description, amount=txn.amount,
            category=cat.name if cat else "Unknown", account_type=acc.account_type if acc else "Unknown",
            is_income=txn.is_income, transaction_type=txn.transaction_type or "expense",
            merchant=txn.merchant, notes=txn.notes, payment_method=txn.payment_method, location=txn.location,
        )

    @router.delete("/{transaction_id}", status_code=204)
    def delete_transaction(
        transaction_id: str,
        user_id: str = Depends(_get_user_id),
        db: Session = Depends(get_db),
    ):
        """Delete a transaction."""
        txn = (
            db.query(Transaction)
            .join(Account, Transaction.account_id == Account.id)
            .filter(Transaction.transaction_id == transaction_id, Account.user_id == user_id)
            .first()
        )
        if not txn:
            raise HTTPException(status_code=404, detail="Transaction not found.")
        db.delete(txn)
        db.commit()
