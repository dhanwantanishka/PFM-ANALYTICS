"""Dashboard metric and insight services."""

from __future__ import annotations

from datetime import date

import pandas as pd

from pfm.analytics.kpi_engine import budget_variance, savings_rate
from pfm.analytics.spending_analysis import spending_by_category, top_expense_drivers
from pfm.config import NEEDS_CATEGORIES, SAVINGS_CATEGORIES, WANTS_CATEGORIES
from pfm.models.risk_scorer import financial_health_score, risk_categories


def _monthly_totals(filtered: pd.DataFrame) -> dict[str, float]:
    """Compute income, expenses, savings, and net flow for the filtered period."""
    income = float(filtered.loc[filtered["is_income"], "amount"].sum())
    expenses = float(filtered.loc[~filtered["is_income"], "amount"].sum())
    savings = income - expenses
    return {
        "income": income,
        "expenses": expenses,
        "savings": savings,
        "net_flow": savings,
        "savings_rate": round((savings / income * 100), 1) if income > 0 else 0.0,
    }


def _current_balance(filtered: pd.DataFrame) -> float:
    """Return the latest balance_after for the selected user."""
    if "balance_after" not in filtered.columns or filtered.empty:
        return 0.0
    latest = filtered.sort_values("date").iloc[-1]
    return float(latest.get("balance_after", 0) or 0)


def _month_over_month(filtered: pd.DataFrame) -> dict[str, float | None]:
    """Compare current month totals to the previous month."""
    df = filtered.copy()
    df["month"] = df["date"].dt.to_period("M")
    months = sorted(df["month"].unique())
    if len(months) < 2:
        return {"income_delta": None, "expense_delta": None, "savings_delta": None}

    current, previous = months[-1], months[-2]
    cur = df[df["month"] == current]
    prev = df[df["month"] == previous]

    cur_income = float(cur.loc[cur["is_income"], "amount"].sum())
    prev_income = float(prev.loc[prev["is_income"], "amount"].sum())
    cur_exp = float(cur.loc[~cur["is_income"], "amount"].sum())
    prev_exp = float(prev.loc[~prev["is_income"], "amount"].sum())
    cur_savings = cur_income - cur_exp
    prev_savings = prev_income - prev_exp

    def pct_delta(current: float, previous: float) -> float | None:
        if previous == 0:
            return None
        return round(((current - previous) / abs(previous)) * 100, 1)

    return {
        "income_delta": pct_delta(cur_income, prev_income),
        "expense_delta": pct_delta(cur_exp, prev_exp),
        "savings_delta": pct_delta(cur_savings, prev_savings),
    }


def build_dashboard_summary(
    filtered: pd.DataFrame,
    budgets: pd.DataFrame,
    user_id: str,
    user_name: str,
) -> dict:
    """Build executive dashboard metrics and supporting context."""
    totals = _monthly_totals(filtered)
    mom = _month_over_month(filtered)
    health = financial_health_score(filtered, budgets, user_id)
    savings = savings_rate(filtered, user_id)
    variance = budget_variance(filtered, budgets, user_id)
    expenses = filtered.loc[~filtered["is_income"]]
    categories = spending_by_category(expenses)
    top_drivers, _ = top_expense_drivers(expenses, top_n=5)
    risk = risk_categories(filtered, budgets, user_id)

    recent = (
        filtered.sort_values("date", ascending=False)
        .head(8)[["date", "description", "amount", "category", "merchant", "is_income"]]
        .copy()
    )

    return {
        "user_name": user_name,
        "health_score": health["overall_score"],
        "health_rating": health["rating"],
        "health_breakdown": health["score_breakdown"],
        "current_balance": _current_balance(filtered),
        "monthly_income": totals["income"],
        "monthly_expenses": totals["expenses"],
        "monthly_savings": totals["savings"],
        "net_cash_flow": totals["net_flow"],
        "savings_rate": totals["savings_rate"],
        "mom": mom,
        "top_categories": categories.head(5),
        "recent_transactions": recent,
        "health_recommendations": [r for r in health["recommendations"] if r],
        "risk_alerts": risk["at_risk_details"],
        "budget_variance_total": float(variance["variance"].sum()),
        "savings_detail": savings,
    }


def generate_insights(summary: dict) -> list[str]:
    """Generate plain-language AI-style insights from dashboard summary."""
    insights: list[str] = []
    rate = summary["savings_rate"]
    if rate >= 20:
        insights.append(f"Savings rate of {rate}% meets the 20% target — strong financial discipline.")
    elif rate >= 10:
        insights.append(f"Savings rate is {rate}%, below the 20% goal. Review discretionary categories.")
    else:
        insights.append(f"Savings rate is only {rate}%. Expenses may be outpacing income.")

    if summary["budget_variance_total"] > 0:
        insights.append(
            f"You are ₹{summary['budget_variance_total']:,.0f} over budget across tracked categories."
        )
    else:
        insights.append("Spending is within or under budget across tracked categories.")

    if summary["risk_alerts"]:
        top_risk = next(iter(summary["risk_alerts"].values()))
        insights.append(
            f"Budget risk detected — a category is at {top_risk['ratio']:.0f}% of its allocated budget."
        )

    if summary["mom"]["expense_delta"] and summary["mom"]["expense_delta"] > 10:
        insights.append(
            f"Expenses rose {summary['mom']['expense_delta']}% month-over-month. Check recurring charges."
        )

    return insights[:4]


def generate_alerts(summary: dict) -> list[dict[str, str]]:
    """Build alert cards for the dashboard."""
    alerts: list[dict[str, str]] = []
    if summary["savings_rate"] < 10:
        alerts.append(
            {
                "level": "High",
                "title": "Low savings rate",
                "message": "Your savings rate is below 10%. Consider reducing wants-category spend.",
            }
        )
    if summary["budget_variance_total"] > 5000:
        alerts.append(
            {
                "level": "Medium",
                "title": "Budget overrun",
                "message": "Total budget variance is positive — you are spending above plan.",
            }
        )
    for category, detail in list(summary["risk_alerts"].items())[:2]:
        alerts.append(
            {
                "level": detail["risk_level"],
                "title": f"{category} budget watch",
                "message": f"Spent {detail['ratio']:.0f}% of budget (₹{detail['actual']:,.0f} vs ₹{detail['budget']:,.0f}).",
            }
        )
    if not alerts:
        alerts.append(
            {
                "level": "Low",
                "title": "All clear",
                "message": "No critical alerts for the selected period.",
            }
        )
    return alerts
