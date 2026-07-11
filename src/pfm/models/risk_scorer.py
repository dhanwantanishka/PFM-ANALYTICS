"""Financial risk scoring and health metrics."""

import pandas as pd
from typing import Dict


def financial_health_score(transactions: pd.DataFrame, budgets: pd.DataFrame, user_id: str) -> Dict:
    """Calculate 0-100 Financial Health Score."""
    user_txn = transactions[transactions['user_id'] == user_id]
    user_budget = budgets[budgets['user_id'] == user_id]
    
    # Score components (each 0-20)
    scores = {}
    
    # 1. Savings Rate (0-20)
    income = user_txn[user_txn['is_income'] == True]['amount'].sum()
    expenses = user_txn[user_txn['is_income'] == False]['amount'].sum()
    savings_rate = (income - expenses) / income * 100 if income > 0 else 0
    scores['savings'] = min(20, max(0, savings_rate))
    
    # 2. Budget Compliance (0-20)
    actual_spend = user_txn[user_txn['is_income'] == False]['amount'].sum()
    budgeted_spend = user_budget['amount'].sum()
    budget_ratio = actual_spend / budgeted_spend if budgeted_spend > 0 else 1
    budget_compliance = max(0, 20 * (1 - abs(budget_ratio - 1)))
    scores['budget'] = budget_compliance
    
    # 3. Debt Management (0-20)
    debt_payments = user_txn[user_txn['category'] == 'Debt Payment']['amount'].sum()
    debt_score = 20 if debt_payments > 0 else 10
    scores['debt'] = debt_score
    
    # 4. Spending Consistency (0-20)
    monthly_spend = user_txn[user_txn['is_income'] == False].groupby(
        user_txn['date'].dt.to_period('M')
    )['amount'].sum()
    if len(monthly_spend) > 1:
        spend_std = monthly_spend.std() / monthly_spend.mean() * 100 if monthly_spend.mean() > 0 else 0
        consistency_score = max(0, 20 * (1 - min(1, spend_std / 100)))
    else:
        consistency_score = 10
    scores['consistency'] = consistency_score
    
    # 5. Transaction Frequency (0-20)
    txn_count = len(user_txn[user_txn['is_income'] == False])
    frequency_score = min(20, txn_count / 30)  # Normalize to ~180 txns
    scores['frequency'] = frequency_score
    
    total_score = sum(scores.values())
    
    return {
        'overall_score': round(total_score, 1),
        'score_breakdown': {k: round(v, 1) for k, v in scores.items()},
        'rating': 'Excellent' if total_score >= 80 else 'Good' if total_score >= 60 else 'Fair' if total_score >= 40 else 'Poor',
        'recommendations': [
            'Increase savings rate' if scores['savings'] < 10 else None,
            'Better budget adherence' if scores['budget'] < 10 else None,
            'Focus on debt reduction' if scores['debt'] < 15 else None,
            'Stabilize spending patterns' if scores['consistency'] < 10 else None
        ]
    }


def risk_categories(transactions: pd.DataFrame, budgets: pd.DataFrame, user_id: str) -> Dict:
    """Identify spending categories at risk of overbudget."""
    user_txn = transactions[
        (transactions['user_id'] == user_id) & 
        (transactions['is_income'] == False)
    ].copy()
    user_budget = budgets[budgets['user_id'] == user_id].copy()
    
    user_txn['month'] = user_txn['date'].dt.to_period('M').astype(str)
    
    actual_by_cat = user_txn.groupby('category')['amount'].sum()
    budgeted_by_cat = user_budget.groupby('category')['amount'].sum()
    
    at_risk = {}
    for cat in actual_by_cat.index:
        if cat in budgeted_by_cat.index:
            actual = actual_by_cat[cat]
            budgeted = budgeted_by_cat[cat]
            ratio = actual / budgeted if budgeted > 0 else 0
            
            if ratio > 0.8:
                at_risk[cat] = {
                    'actual': round(actual, 2),
                    'budget': round(budgeted, 2),
                    'ratio': round(ratio * 100, 1),
                    'risk_level': 'HIGH' if ratio > 1.2 else 'MEDIUM' if ratio > 0.9 else 'WATCH'
                }
    
    return {
        'total_at_risk_categories': len(at_risk),
        'at_risk_details': at_risk
    }
