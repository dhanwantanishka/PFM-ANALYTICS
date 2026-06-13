"""SQLAlchemy ORM models for personal finance data."""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class Category(Base):
    """Spending/income category lookup."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    budget_type: Mapped[str] = mapped_column(String(16), default="expense")  # needs/wants/savings/income

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="category")
    budgets: Mapped[list["Budget"]] = relationship(back_populates="category")


class Account(Base):
    """Bank or credit account."""

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    account_type: Mapped[str] = mapped_column(String(32), nullable=False)  # checking, savings, credit
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, default="user_1")

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="account")


class Transaction(Base):
    """Individual financial transaction."""

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    balance_after: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_income: Mapped[bool] = mapped_column(Boolean, default=False)
    merchant: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # Engineered features
    day_of_week: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_weekend: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    month: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quarter: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rolling_30d_spend: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    category: Mapped["Category"] = relationship(back_populates="transactions")
    account: Mapped["Account"] = relationship(back_populates="transactions")


class Budget(Base):
    """Monthly budget target per category."""

    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    month: Mapped[str] = mapped_column(String(7), nullable=False)  # YYYY-MM
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, default="user_1")

    category: Mapped["Category"] = relationship(back_populates="budgets")
