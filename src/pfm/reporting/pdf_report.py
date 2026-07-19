"""PDF summary report generation using ReportLab."""

from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from pfm.analytics.kpi_engine import (
    budget_variance,
    debt_to_income_ratio,
    emergency_fund_coverage,
    savings_rate,
)
from pfm.analytics.spending_analysis import spending_by_category, top_expense_drivers


def generate_summary_report(
    transactions: pd.DataFrame,
    budgets: pd.DataFrame,
    user_id: str,
    user_name: str,
) -> io.BytesIO:
    """Generate a one-page PDF financial summary for a single user.

    Args:
        transactions: Filtered transactions for the report period.
        budgets: Monthly budget targets, used for the variance section.
        user_id: The user's internal identifier, used to scope KPI formulae.
        user_name: The user's display name, shown in the report header.

    Returns:
        An in-memory PDF file ready for a Streamlit download button.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Personal Finance Summary Report", styles["Title"]))
    story.append(
        Paragraph(
            f"{user_name} &middot; Generated {datetime.now().strftime('%d %b %Y, %H:%M')}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.6 * cm))

    expenses = transactions.loc[~transactions["is_income"]]
    income_total = float(transactions.loc[transactions["is_income"], "amount"].sum())
    expense_total = float(expenses["amount"].sum())

    savings = savings_rate(transactions, user_id)
    dti = debt_to_income_ratio(transactions, user_id)
    emergency = emergency_fund_coverage(transactions, user_id)
    variance = budget_variance(transactions, budgets, user_id)

    story.append(Paragraph("Key Financial Indicators", styles["Heading2"]))
    kpi_rows = [
        ["Metric", "Value"],
        ["Total Income", f"Rs. {income_total:,.0f}"],
        ["Total Expenses", f"Rs. {expense_total:,.0f}"],
        ["Savings Rate", f"{savings['rate']}%"],
        ["Debt-to-Income Ratio", f"{dti['dti']}%"],
        ["Emergency Fund Coverage", f"{emergency['coverage_months']} months"],
        ["Total Budget Variance", f"Rs. {variance['variance'].sum():,.0f}"],
    ]
    kpi_table = Table(kpi_rows, colWidths=[8 * cm, 6 * cm])
    kpi_table.setStyle(_default_table_style())
    story.append(kpi_table)
    story.append(Spacer(1, 0.6 * cm))

    story.append(Paragraph("Spending by Category", styles["Heading2"]))
    category_totals = spending_by_category(expenses)
    category_rows = [["Category", "Amount (Rs.)"]] + [
        [category, f"{row[('amount', 'sum')]:,.0f}"]
        for category, row in category_totals.iterrows()
    ]
    category_table = Table(category_rows, colWidths=[8 * cm, 6 * cm])
    category_table.setStyle(_default_table_style())
    story.append(category_table)
    story.append(Spacer(1, 0.6 * cm))

    story.append(Paragraph("Top Expense Drivers (Pareto)", styles["Heading2"]))
    top_drivers, top10_pct = top_expense_drivers(expenses, top_n=10)
    story.append(
        Paragraph(f"Top 10 categories account for {top10_pct:.1f}% of total spend.", styles["Normal"])
    )
    story.append(Spacer(1, 0.3 * cm))
    driver_rows = [["Category", "Total Spend (Rs.)", "% of Total"]] + [
        [category, f"{row[('amount', 'sum')]:,.0f}", f"{row[('pct_of_total', '')]:.1f}%"]
        for category, row in top_drivers.iterrows()
    ]
    driver_table = Table(driver_rows, colWidths=[6 * cm, 4 * cm, 4 * cm])
    driver_table.setStyle(_default_table_style())
    story.append(driver_table)

    doc.build(story)
    buffer.seek(0)
    return buffer


def _default_table_style() -> TableStyle:
    """Return a consistent table style used across report sections."""
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
    )
