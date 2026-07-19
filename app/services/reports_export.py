"""Report export helpers for PDF, Excel, and CSV."""

from __future__ import annotations

import io
from datetime import datetime

import pandas as pd

from pfm.reporting.pdf_report import generate_summary_report


def export_csv(df: pd.DataFrame) -> bytes:
    """Export a dataframe to CSV bytes."""
    return df.to_csv(index=False).encode("utf-8")


def export_excel(transactions: pd.DataFrame, budgets: pd.DataFrame) -> bytes:
    """Export transactions and budgets to a multi-sheet Excel workbook."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        transactions.to_excel(writer, sheet_name="Transactions", index=False)
        budgets.to_excel(writer, sheet_name="Budgets", index=False)
    buffer.seek(0)
    return buffer.getvalue()


def export_pdf(
    transactions: pd.DataFrame,
    budgets: pd.DataFrame,
    user_id: str,
    user_name: str,
) -> io.BytesIO:
    """Generate the PDF summary report."""
    return generate_summary_report(transactions, budgets, user_id, user_name)


def business_summary_markdown(
    transactions: pd.DataFrame,
    user_name: str,
    health_score: float,
    savings_rate_pct: float,
) -> str:
    """Build a markdown business summary for reports."""
    income = float(transactions.loc[transactions["is_income"], "amount"].sum())
    expenses = float(transactions.loc[~transactions["is_income"], "amount"].sum())
    return f"""# Financial summary — {user_name}

Generated: {datetime.now():%d %b %Y %H:%M}

| Metric | Value |
|--------|-------|
| Financial health score | {health_score}/100 |
| Total income | ₹{income:,.0f} |
| Total expenses | ₹{expenses:,.0f} |
| Net cash flow | ₹{income - expenses:,.0f} |
| Savings rate | {savings_rate_pct}% |
"""
