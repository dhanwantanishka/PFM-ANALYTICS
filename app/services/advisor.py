"""Rule-based + optional LLM finance advisor using real transaction data."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

import pandas as pd

from pfm.analytics.kpi_engine import budget_variance, savings_rate, spending_50_30_20
from pfm.analytics.spending_analysis import spending_by_category, top_expense_drivers
from pfm.config import NEEDS_CATEGORIES, SAVINGS_CATEGORIES, WANTS_CATEGORIES
from pfm.models.risk_scorer import financial_health_score


def _match_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _build_rich_context(transactions: pd.DataFrame, budgets: pd.DataFrame, user_id: str) -> dict:
    """Build a rich, data-driven context dict from real transactions."""
    user_txn = transactions[transactions["user_id"] == user_id].copy()
    expenses = user_txn.loc[~user_txn["is_income"]]
    income_txn = user_txn.loc[user_txn["is_income"]]

    ctx: dict[str, Any] = {}

    if user_txn.empty:
        return {"no_data": True}

    # Date range
    ctx["date_min"] = str(user_txn["date"].min().date())
    ctx["date_max"] = str(user_txn["date"].max().date())
    ctx["total_transactions"] = len(user_txn)

    # Income & expense totals
    ctx["total_income"] = float(income_txn["amount"].sum())
    ctx["total_expenses"] = float(expenses["amount"].sum())
    ctx["net_savings"] = ctx["total_income"] - ctx["total_expenses"]
    ctx["savings_rate_pct"] = round(
        ctx["net_savings"] / ctx["total_income"] * 100 if ctx["total_income"] > 0 else 0, 1
    )

    # This month
    this_month = date.today().strftime("%Y-%m")
    month_txn = user_txn[user_txn["date"].dt.strftime("%Y-%m") == this_month]
    month_exp = month_txn.loc[~month_txn["is_income"]]
    month_inc = month_txn.loc[month_txn["is_income"]]
    ctx["this_month"] = this_month
    ctx["month_income"] = float(month_inc["amount"].sum())
    ctx["month_expenses"] = float(month_exp["amount"].sum())
    ctx["month_savings"] = ctx["month_income"] - ctx["month_expenses"]

    # Top categories
    if not expenses.empty:
        top_cats = (
            expenses.groupby("category")["amount"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
        )
        ctx["top_categories"] = {cat: round(amt, 0) for cat, amt in top_cats.items()}
        ctx["largest_expense_category"] = top_cats.index[0]
        ctx["largest_expense_amount"] = float(top_cats.iloc[0])

    # Top merchants
    if "merchant" in expenses.columns:
        top_merch = (
            expenses.dropna(subset=["merchant"])
            .groupby("merchant")["amount"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
        )
        ctx["top_merchants"] = {m: round(a, 0) for m, a in top_merch.items()}

    # Budget variance
    if not budgets.empty:
        variance_df = budget_variance(user_txn, budgets, user_id)
        over = variance_df[variance_df["variance"] > 0]
        ctx["over_budget_categories"] = over[["category", "actual", "budget", "variance"]].to_dict("records")

    # Financial health
    health = financial_health_score(user_txn, budgets, user_id)
    ctx["health_score"] = health["overall_score"]
    ctx["health_rating"] = health["rating"]
    ctx["health_recommendations"] = health.get("recommendations", [])

    # 50/30/20 rule
    rule = spending_50_30_20(user_txn, user_id, NEEDS_CATEGORIES, WANTS_CATEGORIES, SAVINGS_CATEGORIES)
    ctx["needs_pct"] = rule["needs_pct"]
    ctx["wants_pct"] = rule["wants_pct"]
    ctx["savings_pct"] = rule["savings_pct"]

    # Day of week spend pattern
    if "day_of_week" in expenses.columns:
        dow_map = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
        dow_spend = expenses.groupby("day_of_week")["amount"].sum()
        if not dow_spend.empty:
            peak_day = dow_map.get(int(dow_spend.idxmax()), "Unknown")
            ctx["peak_spending_day"] = peak_day

    return ctx


def answer_question(
    question: str,
    transactions: pd.DataFrame,
    budgets: pd.DataFrame,
    user_id: str,
) -> str:
    """Answer a natural-language finance question using real transaction analytics."""
    q = question.strip().lower()
    if not q:
        return "Ask me about spending, savings, budgeting, forecasting, or anomalies."

    ctx = _build_rich_context(transactions, budgets, user_id)

    if ctx.get("no_data"):
        return (
            "You don't have any transactions yet. Go to **Manage → Add Transaction** to record your "
            "first transaction, or **Manage → Import / Upload** to import from CSV."
        )

    # ── Savings rate ──────────────────────────────────────────────────────────
    if _match_any(q, ("savings", "save", "saving rate", "how much do i save")):
        rate = ctx["savings_rate_pct"]
        rec = "Great job — you're meeting the 20% savings target! 🎉" if rate >= 20 else \
              "Aim for at least 20% savings rate. Try reducing your top expense category."
        return (
            f"Your overall savings rate is **{rate}%** across all recorded transactions.\n\n"
            f"- Total income: ₹{ctx['total_income']:,.0f}\n"
            f"- Total expenses: ₹{ctx['total_expenses']:,.0f}\n"
            f"- Net savings: ₹{ctx['net_savings']:,.0f}\n\n"
            f"{rec}"
        )

    # ── This month ────────────────────────────────────────────────────────────
    if _match_any(q, ("this month", "current month", "monthly")):
        return (
            f"**{ctx['this_month']} Summary:**\n\n"
            f"- Income: ₹{ctx['month_income']:,.0f}\n"
            f"- Expenses: ₹{ctx['month_expenses']:,.0f}\n"
            f"- Net: ₹{ctx['month_savings']:,.0f} {'💚' if ctx['month_savings'] >= 0 else '🔴'}\n"
        )

    # ── Spending / expenses ───────────────────────────────────────────────────
    if _match_any(q, ("spend", "spending", "expense", "expenses", "where did my money", "where is my money")):
        cats = ctx.get("top_categories", {})
        if not cats:
            return "No expense transactions found in your data."
        cat_lines = "\n".join([f"- **{cat}**: ₹{amt:,.0f}" for cat, amt in cats.items()])
        return (
            f"Your top spending categories:\n\n{cat_lines}\n\n"
            f"**{ctx.get('largest_expense_category', 'Unknown')}** is your biggest expense at "
            f"₹{ctx.get('largest_expense_amount', 0):,.0f}."
        )

    # ── Budget ────────────────────────────────────────────────────────────────
    if _match_any(q, ("budget", "over budget", "variance", "budget left")):
        over = ctx.get("over_budget_categories", [])
        if not over:
            return "✅ You are within budget across all tracked categories. Well done!"
        lines = [f"- **{r['category']}**: spent ₹{r['actual']:,.0f} vs budget ₹{r['budget']:,.0f} (over by ₹{r['variance']:,.0f})" for r in over[:5]]
        return f"Categories over budget:\n\n" + "\n".join(lines)

    # ── 50/30/20 ──────────────────────────────────────────────────────────────
    if _match_any(q, ("50/30/20", "needs", "wants", "rule")):
        needs_status = "✅" if ctx["needs_pct"] <= 50 else "⚠️"
        wants_status = "✅" if ctx["wants_pct"] <= 30 else "⚠️"
        save_status = "✅" if ctx["savings_pct"] >= 20 else "⚠️"
        return (
            f"**50/30/20 Rule Breakdown:**\n\n"
            f"{needs_status} Needs: **{ctx['needs_pct']}%** (target ≤50%)\n"
            f"{wants_status} Wants: **{ctx['wants_pct']}%** (target ≤30%)\n"
            f"{save_status} Savings: **{ctx['savings_pct']}%** (target ≥20%)"
        )

    # ── Health score ──────────────────────────────────────────────────────────
    if _match_any(q, ("health", "score", "rating", "how am i doing")):
        recs = [r for r in ctx.get("health_recommendations", []) if r]
        rec_text = "\n".join([f"- {r}" for r in recs[:3]]) if recs else "Keep up the great work!"
        return (
            f"**Financial Health Score: {ctx['health_score']}/100 — {ctx['health_rating']}**\n\n"
            f"Recommendations:\n{rec_text}"
        )

    # ── Top merchants ─────────────────────────────────────────────────────────
    if _match_any(q, ("merchant", "shop", "store", "top merchant", "where am i shopping")):
        merch = ctx.get("top_merchants", {})
        if not merch:
            return "No merchant data available. Add merchant names when recording transactions."
        lines = "\n".join([f"- **{m}**: ₹{a:,.0f}" for m, a in merch.items()])
        return f"Your top merchants by spend:\n\n{lines}"

    # ── Peak spending day ─────────────────────────────────────────────────────
    if _match_any(q, ("day", "weekend", "weekday", "when do i spend")):
        peak = ctx.get("peak_spending_day", "Unknown")
        return f"You spend the most on **{peak}**. Consider reviewing your spending habits on that day."

    # ── Reduce / save tips ────────────────────────────────────────────────────
    if _match_any(q, ("reduce", "cut", "save more", "tip", "advice", "suggest")):
        cats = ctx.get("top_categories", {})
        top_cat = list(cats.keys())[0] if cats else "expenses"
        top_amt = list(cats.values())[0] if cats else 0
        rate = ctx["savings_rate_pct"]
        return (
            f"**Personalised Tips Based on Your Data:**\n\n"
            f"1. Your biggest expense is **{top_cat}** at ₹{top_amt:,.0f}. A 10% cut saves ₹{top_amt*0.1:,.0f}.\n"
            f"2. Your savings rate is **{rate}%**. {'Increase it to 20%+ for financial security.' if rate < 20 else 'Maintain this rate!'}\n"
            f"3. Review subscriptions and recurring bills in **Manage → Bill Reminders**.\n"
            f"4. Set monthly category budgets in **Manage → Budgets** to stay on track."
        )

    # ── Forecast ──────────────────────────────────────────────────────────────
    if _match_any(q, ("forecast", "predict", "future", "next month")):
        return (
            "Open the **Analysis → Forecast** page to compare Linear Regression, Random Forest, and XGBoost "
            "models trained on your actual transaction history. Use a longer date range (40+ days) for better predictions."
        )

    # ── Anomaly ───────────────────────────────────────────────────────────────
    if _match_any(q, ("anomaly", "anomalies", "fraud", "suspicious", "unusual", "flagged")):
        return (
            "Open the **Analysis → Anomaly detection** page to review flagged transactions from your data. "
            "High severity means both Isolation Forest and Z-score algorithms identified the same transaction."
        )

    # ── Fallback ──────────────────────────────────────────────────────────────
    return (
        "I can answer questions about your **real financial data**. Try:\n\n"
        "- *What is my savings rate?*\n"
        "- *Where am I spending the most?*\n"
        "- *Which categories are over budget?*\n"
        "- *How is my 50/30/20 breakdown?*\n"
        "- *What is my financial health score?*\n"
        "- *Show me my top merchants*\n"
        "- *Give me tips to save more*"
    )


def try_api_answer(question: str, data_context: dict[str, Any]) -> str | None:
    """Optional LLM answer — injects real transaction data into the prompt."""
    try:
        import streamlit as st
        api_key = st.secrets.get("openai", {}).get("api_key")
        if not api_key:
            return None
    except Exception:
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        # Build a rich system prompt from real data
        system_prompt = (
            "You are a professional personal finance advisor. You ONLY use the real financial data "
            "provided below to answer questions. Do NOT make up numbers. Be concise and helpful.\n\n"
            f"USER'S FINANCIAL SUMMARY:\n{data_context}"
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            max_tokens=400,
        )
        return response.choices[0].message.content
    except Exception:
        return None
