# Generate notebook (save as: create_notebook.py in project root)
import json
from pathlib import Path

notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["# Phase 2: Spending Pattern Analysis (EDA)\n", "\n", "**Days 10-12**: Exploratory Data Analysis\n", "\n", "- Aggregate spending by category, merchant, month\n", "- Identify top-10 expense drivers\n", "- Analyze time-series trends\n", "- Day-of-week patterns\n", "- Budget vs actual comparison"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["import pandas as pd\n", "import numpy as np\n", "import matplotlib.pyplot as plt\n", "import seaborn as sns\n", "import plotly.graph_objects as go\n", "import plotly.express as px\n", "from datetime import datetime\n", "from sqlalchemy import create_engine\n", "from sqlalchemy.orm import sessionmaker\n", "\n", "import sys\n", "sys.path.insert(0, '../src')\n", "\n", "from pfm.analytics.spending_analysis import (\n", "    get_transactions_df, spending_by_category, spending_by_merchant,\n", "    spending_by_month, spending_by_user_category, spending_by_day_of_week,\n", "    month_over_month_growth, top_expense_drivers, weekend_vs_weekday_spending,\n", "    spending_heatmap_data, budget_vs_actual\n", ")\n", "from pfm.config import DB_PATH, USERS\n", "\n", "# Setup\n", "engine = create_engine(f'sqlite:///{DB_PATH}')\n", "Session = sessionmaker(bind=engine)\n", "session = Session()\n", "\n", "print('✅ Environment loaded')\n", "print(f'Database: {DB_PATH}')\n", "print(f'Users: {len(USERS)}')"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## 1. Dataset Overview"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["# Load data\n", "df = get_transactions_df(session)\n", "budgets = pd.read_sql('SELECT * FROM budgets', engine)\n", "\n", "print(f'Total transactions: {len(df):,}')\n", "print(f'Date range: {df[\"date\"].min().date()} to {df[\"date\"].max().date()}')\n", "print(f'Users: {df[\"user_name\"].nunique()}')\n", "print(f'Categories: {df[\"category\"].nunique()}')\n", "print(f'Missing values: {df.isnull().sum().sum()}')\n", "print(f'\\nExpenses only: {(~df[\"is_income\"]).sum():,}')\n", "print(f'Income only: {df[\"is_income\"].sum():,}')\n", "print(f'\\nTotal spend: Rs. {(~df[\"is_income\"]).sum():,.0f}')\n", "print(f'Total income: Rs. {df[\"is_income\"].sum():,.0f}')"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## 2. Spending by Category"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["cat_spend = spending_by_category(df)\n", "print(cat_spend)\n", "\n", "# Pie chart\n", "fig = px.pie(\n", "    names=cat_spend.index,\n", "    values=cat_spend[('amount', 'sum')],\n", "    title='Spending Distribution by Category',\n", "    hole=0.3\n", ")\n", "fig.show()"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## 3. Top 10 Merchants"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["merch = spending_by_merchant(df, top_n=10)\n", "print(merch)\n", "\n", "# Bar chart\n", "fig = px.bar(\n", "    x=merch[('amount', 'sum')],\n", "    y=merch.index,\n", "    orientation='h',\n", "    title='Top 10 Merchants by Spend',\n", "    labels={'x': 'Amount (Rs.)', 'y': 'Merchant'}\n", ")\n", "fig.update_layout(height=500)\n", "fig.show()"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## 4. Monthly Spending Trend"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["monthly = spending_by_month(df)\n", "print(monthly)\n", "\n", "fig = px.line(\n", "    x=monthly.index.astype(str),\n", "    y=monthly.values,\n", "    title='Monthly Spending Trend',\n", "    markers=True,\n", "    labels={'x': 'Month', 'y': 'Spending (Rs.)'}\n", ")\n", "fig.update_layout(height=400)\n", "fig.show()"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## 5. Month-over-Month Growth Rate"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["mom = month_over_month_growth(df)\n", "print('\\nMonth-over-Month Growth (%)')\n", "print(mom)\n", "\n", "fig = px.bar(\n", "    x=mom.index.astype(str),\n", "    y=mom.values,\n", "    title='Monthly Growth Rate (%)',\n", "    color=mom.values,\n", "    color_continuous_scale='RdYlGn',\n", "    labels={'x': 'Month', 'y': 'Growth %'}\n", ")\n", "fig.show()"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## 6. Day-of-Week Heatmap"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["heatmap_data = spending_heatmap_data(df)\n", "print(heatmap_data)\n", "\n", "fig = px.imshow(\n", "    heatmap_data,\n", "    title='Spending Heatmap: Day of Week × Category',\n", "    labels={'x': 'Category', 'y': 'Day', 'color': 'Amount (Rs.)'},\n", "    color_continuous_scale='YlOrRd'\n", ")\n", "fig.update_layout(height=400)\n", "fig.show()"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## 7. Weekend vs Weekday Spending"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["wknd = weekend_vs_weekday_spending(df)\n", "print(wknd)\n", "\n", "day_type = ['Weekday', 'Weekend']\n", "avg_spend = [wknd[('amount', 'mean')][False], wknd[('amount', 'mean')][True]]\n", "\n", "fig = px.bar(\n", "    x=day_type,\n", "    y=avg_spend,\n", "    title='Average Spending: Weekday vs Weekend',\n", "    labels={'y': 'Average Spend (Rs.)'}\n", ")\n", "fig.show()"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## 8. Top Expense Drivers (Pareto Analysis)"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["top_cat, cum_pct = top_expense_drivers(df, top_n=10)\n", "print(f'Top 10 categories account for {cum_pct:.1f}% of total spend')\n", "print(top_cat)\n", "\n", "fig = px.bar(\n", "    x=top_cat[('amount', 'sum')],\n", "    y=top_cat.index,\n", "    orientation='h',\n", "    title=f'Top 10 Expense Drivers ({cum_pct:.0f}% of spend)',\n", "    labels={'x': 'Amount (Rs.)'}\n", ")\n", "fig.show()"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## 9. Spending by User"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["user_spend = df[~df['is_income']].groupby('user_name')['amount'].agg(['sum', 'count', 'mean']).round(2)\n", "print(user_spend)\n", "\n", "fig = px.bar(\n", "    user_spend.reset_index(),\n", "    x='user_name',\n", "    y='sum',\n", "    title='Total Spending by User',\n", "    labels={'sum': 'Total Spend (Rs.)', 'user_name': 'User'}\n", ")\n", "fig.show()"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## 10. Spending by User & Category"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["user_cat = spending_by_user_category(df)\n", "print(user_cat)\n", "\n", "fig = px.imshow(\n", "    user_cat,\n", "    title='Spending Matrix: Users × Categories',\n", "    labels={'color': 'Amount (Rs.)'},\n", "    color_continuous_scale='Blues'\n", ")\n", "fig.update_layout(height=400)\n", "fig.show()"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## 11. Budget vs Actual"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["bv = budget_vs_actual(df, budgets)\n", "print(bv.head(15))\n", "\n", "# Summary by category\n", "bv_summary = bv.groupby('category').agg({'variance': 'mean'}).round(2).sort_values('variance', ascending=False)\n", "print('\\nAverage Budget Variance by Category')\n", "print(bv_summary)\n", "\n", "fig = px.bar(\n", "    bv_summary.reset_index().head(15),\n", "    x='variance',\n", "    y='category',\n", "    orientation='h',\n", "    title='Avg Budget Variance by Category (Over Budget = Positive)',\n", "    color='variance',\n", "    color_continuous_scale='RdYlGn_r',\n", "    labels={'variance': 'Variance (Rs.)', 'category': ''}\n", ")\n", "fig.show()"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Key Findings"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["print('📊 KEY FINDINGS - SPENDING PATTERN ANALYSIS\\n')\n", "\n", "# Finding 1: Top category\n", "top_cat_name = cat_spend.index[0]\n", "top_cat_pct = (cat_spend[('amount', 'sum')][0] / cat_spend[('amount', 'sum')].sum() * 100)\n", "print(f'1️⃣ Top Spending Category: {top_cat_name} ({top_cat_pct:.1f}% of spend)')\n", "\n", "# Finding 2: Pareto\n", "print(f'\\n2️⃣ Pareto Rule (80/20): Top 10 categories = {cum_pct:.1f}% of total spend')\n", "\n", "# Finding 3: MoM trend\n", "mom_avg = mom[1:].mean()\n", "print(f'\\n3️⃣ Average MoM Growth: {mom_avg:+.2f}% (trend: {\"📈 Increasing\" if mom_avg > 0 else \"📉 Decreasing\"})')\n", "\n", "# Finding 4: Weekday vs Weekend\n", "wkday_avg = wknd[('amount', 'mean')][False]\n", "wknd_avg = wknd[('amount', 'mean')][True]\n", "diff_pct = ((wknd_avg - wkday_avg) / wkday_avg * 100)\n", "print(f'\\n4️⃣ Weekend vs Weekday: Weekend avg {abs(diff_pct):.1f}% {\"higher\" if diff_pct > 0 else \"lower\"} than weekday')\n", "\n", "# Finding 5: Budget overruns\n", "overruns = (bv['variance'] > 0).sum()\n", "overrun_pct = (overruns / len(bv) * 100)\n", "print(f'\\n5️⃣ Budget Compliance: {overrun_pct:.1f}% of categories over budget')\n", "\n", "# Finding 6: Top merchant\n", "top_merch = merch.index[0]\n", "top_merch_amt = merch[('amount', 'sum')][0]\n", "print(f'\\n6️⃣ Top Merchant: {top_merch} (Rs. {top_merch_amt:,.0f})')\n", "\n", "# Finding 7: User variation\n", "user_spend_range = user_spend['sum'].max() - user_spend['sum'].min()\n", "print(f'\\n7️⃣ User Spend Variation: Rs. {user_spend_range:,.0f} (high variation = different lifestyles)')\n", "\n", "print('\\n' + '='*60)"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Insights & Recommendations"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["insights = f\"\"\"\n💡 ACTIONABLE INSIGHTS\n\n1. SPENDING CONCENTRATION\n   - {cum_pct:.0f}% of spending is concentrated in just 10 categories\n   - Focus on controlling top 3 categories to reduce overall expenses\n   \n2. BUDGET MANAGEMENT\n   - {overrun_pct:.0f}% of tracked categories are exceeding budgets\n   - Review spending limits for categories with frequent overruns\n   \n3. TEMPORAL PATTERNS\n   - Weekend spending is {abs(diff_pct):.0f}% {\"higher\" if diff_pct > 0 else \"lower\"} than weekdays\n   - Consider stricter controls on discretionary spending on weekends\n   \n4. MERCHANT CONCENTRATION\n   - Top merchant ({top_merch}) accounts for Rs. {top_merch_amt:,.0f}\n   - Negotiate bulk discounts or find alternative providers\n   \n5. GROWTH TRAJECTORY\n   - Average MoM growth: {mom_avg:+.2f}%\n   - {'Monitor increasing trend' if mom_avg > 0 else 'Leverage decreasing trend'}\n   \n6. USER PATTERNS\n   - Spending varies significantly across users (Rs. {user_spend_range:,.0f})\n   - Personalized budgets recommended\n\"\"\"\n\nprint(insights)"]
        }
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.10.0"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

# Write notebook
nb_path = Path("notebooks/01_eda_spending_patterns.ipynb")
nb_path.parent.mkdir(exist_ok=True)

with open(nb_path, 'w') as f:
    json.dump(notebook, f, indent=2)

print(f"✅ Notebook created: {nb_path}")