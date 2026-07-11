"""Statistical analysis and hypothesis testing functions."""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from scipy import stats


def correlation_matrix(transactions: pd.DataFrame) -> pd.DataFrame:
    """Compute correlation matrix for financial metrics."""
    df = transactions.copy()
    
    user_metrics = []
    for user_id in df['user_id'].unique():
        user_data = df[df['user_id'] == user_id]
        
        income = user_data[user_data['is_income'] == True]['amount'].sum()
        expenses = user_data[user_data['is_income'] == False]['amount'].sum()
        savings = user_data[user_data['category'].isin(['Savings'])]['amount'].sum()
        debt = user_data[user_data['category'] == 'Debt Payment']['amount'].sum()
        discretionary = user_data[user_data['category'].isin(['Dining', 'Entertainment', 'Shopping'])]['amount'].sum()
        
        user_metrics.append({
            'user_id': user_id,
            'income': income,
            'expenses': expenses,
            'savings': savings,
            'debt_payment': debt,
            'discretionary_spend': discretionary
        })
    
    metrics_df = pd.DataFrame(user_metrics)
    return metrics_df.corr().round(3)


def weekday_vs_weekend_ttest(transactions: pd.DataFrame) -> Dict:
    """T-test: Is weekend spending significantly different from weekday?"""
    df = transactions.copy()
    df['is_weekend'] = df['date'].dt.dayofweek >= 5
    
    weekday_spend = df[df['is_weekend'] == False]['amount'].values
    weekend_spend = df[df['is_weekend'] == True]['amount'].values
    
    t_stat, p_value = stats.ttest_ind(weekend_spend, weekday_spend)
    
    return {
        't_statistic': round(t_stat, 4),
        'p_value': round(p_value, 4),
        'significant': p_value < 0.05,
        'weekday_mean': round(weekday_spend.mean(), 2),
        'weekend_mean': round(weekend_spend.mean(), 2),
        'interpretation': 'Weekend spending is SIGNIFICANTLY different' if p_value < 0.05 else 'No significant difference'
    }


def pareto_analysis(transactions: pd.DataFrame, top_n: int = 10) -> Dict:
    """Pareto analysis: Do top N categories drive 80% of spend?"""
    df = transactions[transactions['is_income'] == False].copy()
    
    cat_spend = df.groupby('category')['amount'].sum().sort_values(ascending=False)
    total_spend = cat_spend.sum()
    
    top_categories = cat_spend.head(top_n)
    top_spend = top_categories.sum()
    top_pct = (top_spend / total_spend * 100)
    
    cumsum = cat_spend.cumsum()
    cumsum_pct = (cumsum / total_spend * 100)
    categories_for_80 = (cumsum_pct <= 80).sum() + 1
    
    return {
        'top_n': top_n,
        'top_n_percentage': round(top_pct, 2),
        'follows_80_20': top_pct >= 80,
        'categories_for_80_percent': categories_for_80,
        'total_categories': len(cat_spend),
        'top_categories': dict(top_categories),
        'interpretation': f'Top {categories_for_80} of {len(cat_spend)} categories drive 80% of spending'
    }


def income_vs_spending_correlation(transactions: pd.DataFrame) -> Dict:
    """Correlation between income and spending across users."""
    df = transactions.copy()
    
    user_summary = []
    for user_id in df['user_id'].unique():
        user_data = df[df['user_id'] == user_id]
        
        income = user_data[user_data['is_income'] == True]['amount'].sum()
        spending = user_data[user_data['is_income'] == False]['amount'].sum()
        
        user_summary.append({'user_id': user_id, 'income': income, 'spending': spending})
    
    summary_df = pd.DataFrame(user_summary)
    correlation = summary_df['income'].corr(summary_df['spending'])
    
    return {
        'correlation': round(correlation, 3),
        'interpretation': 'Strong positive' if correlation > 0.7 else 'Moderate' if correlation > 0.4 else 'Weak',
        'meaning': 'Higher income users tend to spend more' if correlation > 0.3 else 'Income and spending are independent'
    }


def category_spending_distribution(transactions: pd.DataFrame) -> pd.DataFrame:
    """Statistical summary of spending by category."""
    df = transactions[transactions['is_income'] == False].copy()
    
    stats_by_cat = df.groupby('category')['amount'].agg([
        ('count', 'count'),
        ('mean', 'mean'),
        ('std', 'std'),
        ('min', 'min'),
        ('max', 'max'),
        ('sum', 'sum')
    ]).round(2).sort_values('sum', ascending=False)
    
    return stats_by_cat


def budget_vs_actual_pvalue(transactions: pd.DataFrame, budgets: pd.DataFrame) -> Dict:
    """T-test: Is actual spending significantly different from budgeted amount?"""
    df = transactions[transactions['is_income'] == False].copy()
    df['month'] = df['date'].dt.to_period('M').astype(str)
    
    actual_by_month = df.groupby('month')['amount'].sum().values
    budgeted_by_month = budgets.groupby('month')['amount'].sum().values
    
    min_len = min(len(actual_by_month), len(budgeted_by_month))
    actual = actual_by_month[:min_len]
    budgeted = budgeted_by_month[:min_len]
    
    t_stat, p_value = stats.ttest_rel(actual, budgeted)
    
    return {
        't_statistic': round(t_stat, 4),
        'p_value': round(p_value, 4),
        'significant': p_value < 0.05,
        'actual_mean': round(actual.mean(), 2),
        'budgeted_mean': round(budgeted.mean(), 2),
        'interpretation': 'Actual spending SIGNIFICANTLY exceeds budget' if t_stat > 0 and p_value < 0.05 else 'Within budget expectations'
    }
