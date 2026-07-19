"""Pydantic schemas for request/response validation."""

from __future__ import annotations

from datetime import date, time
from typing import Optional
from pydantic import BaseModel, Field, validator


# ── Transactions ──────────────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    amount: float = Field(..., gt=0, description="Transaction amount in INR")
    description: str = Field(..., min_length=1, max_length=500)
    transaction_type: str = Field(..., pattern="^(income|expense|transfer)$")
    category: str
    account_id: int
    date: date
    time: Optional[time] = None
    merchant: Optional[str] = Field(None, max_length=128)
    notes: Optional[str] = Field(None, max_length=1000)
    payment_method: Optional[str] = Field(None, max_length=64)
    location: Optional[str] = Field(None, max_length=128)


class TransactionUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    transaction_type: Optional[str] = Field(None, pattern="^(income|expense|transfer)$")
    category: Optional[str] = None
    merchant: Optional[str] = Field(None, max_length=128)
    notes: Optional[str] = Field(None, max_length=1000)
    payment_method: Optional[str] = Field(None, max_length=64)


class TransactionOut(BaseModel):
    id: int
    transaction_id: str
    date: date
    description: str
    amount: float
    category: str
    account_type: str
    is_income: bool
    transaction_type: str
    merchant: Optional[str]
    notes: Optional[str]
    payment_method: Optional[str]
    location: Optional[str]

    class Config:
        from_attributes = True


class PaginatedTransactions(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: list[TransactionOut]


# ── Budgets ───────────────────────────────────────────────────────────────────

class BudgetCreate(BaseModel):
    category: str
    month: str = Field(..., pattern=r"^\d{4}-\d{2}$", description="YYYY-MM format")
    amount: float = Field(..., gt=0)


class BudgetOut(BaseModel):
    id: int
    category: str
    month: str
    amount: float
    actual_spend: float = 0.0
    pct_used: float = 0.0
    remaining: float = 0.0

    class Config:
        from_attributes = True


# ── Accounts ──────────────────────────────────────────────────────────────────

class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    account_type: str = Field(..., pattern="^(Bank|Cash|Credit Card|UPI|Wallet|Investment|Loan)$")


class AccountOut(BaseModel):
    id: int
    name: str
    account_type: str
    balance: float = 0.0

    class Config:
        from_attributes = True


# ── Goals ─────────────────────────────────────────────────────────────────────

class GoalCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    target_amount: float = Field(..., gt=0)
    saved_amount: float = Field(0.0, ge=0)
    target_date: Optional[date] = None


class GoalOut(BaseModel):
    id: int
    name: str
    target_amount: float
    saved_amount: float
    target_date: Optional[date]
    pct_complete: float = 0.0

    class Config:
        from_attributes = True


# ── Bills ─────────────────────────────────────────────────────────────────────

class BillCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    amount: float = Field(..., gt=0)
    due_date: date
    is_recurring: bool = False
    reminder_days: int = Field(3, ge=1, le=30)


class BillOut(BaseModel):
    id: int
    name: str
    amount: float
    due_date: date
    is_recurring: bool
    reminder_days: int
    days_until_due: int = 0

    class Config:
        from_attributes = True


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardSummary(BaseModel):
    user_id: str
    total_balance: float
    today_income: float
    today_expenses: float
    month_income: float
    month_expenses: float
    net_savings: float
    savings_rate_pct: float
    health_score: int
    top_expense_category: Optional[str]
    largest_expense: Optional[float]
    transaction_count: int


# ── Analytics ─────────────────────────────────────────────────────────────────

class CategoryBreakdown(BaseModel):
    category: str
    amount: float
    pct_of_total: float
    transaction_count: int


class MonthlyReport(BaseModel):
    month: str
    income: float
    expenses: float
    net: float
    savings_rate_pct: float
    top_category: Optional[str]
