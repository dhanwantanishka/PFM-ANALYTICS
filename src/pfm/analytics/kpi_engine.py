"""Financial KPI calculations and personal finance health metrics."""

import pandas as pd
import numpy as np
from typing import Dict


def savings_rate(transactions: pd.DataFrame, user_id: str) -> Dict[str, float]:
    """Savings Rate = (Income - Expenses) / Income × 100"""
    user_income = transactions[
        (transactions['user_id'] == user_id) & 
        (transactions['is_income'] == True)
    ]['amount'].sum()
    
    if user_income == 0:
        return {'rate': 0.0, 'income': 0.0, 'expenses': 0.0, 'savings': 0.0}
    
    user_exp = transactions[
        (transactions['user_id'] == user_id) & 
        (transactions['is_income'] == False)
    ]['amount'].sum()
    
    savings = user_income - user_exp
    rate = round((savings / user_income * 100), 2) if user_income > 0 else 0.0
    
    return {
        'rate': rate,
        'income': round(user_income, 2),
        'expenses': round(user_exp, 2),
        'savings': round(savings, 2)
    }


def debt_to_income_ratio(transactions: pd.DataFrame, user_id: str) -> Dict[str, float]:
    """DTI = Monthly Debt Payments / Gross Monthly Income × 100"""
    user_income = transactions[
        (transactions['user_id'] == user_id) & 
        (transactions['is_income'] == True)
    ]['amount'].sum()
    
    debt_payments = transactions[
        (transactions['user_id'] == user_id) & 
        (transactions['category'] == 'Debt Payment')
    ]['amount'].sum()
    
    months = max(1, (transactions['date'].max() - transactions['date'].min()).days // 30)
    avg_monthly_income = user_income / max(1, months)
    avg_monthly_debt = debt_payments / max(1, months)
    
    dti = round((avg_monthly_debt / avg_monthly_income * 100), 2) if avg_monthly_income > 0 else 0.0
    
    return {
        'dti': dti,
        'monthly_debt': round(avg_monthly_debt, 2),
        'monthly_income': round(avg_monthly_income, 2)
    }


def budget_variance(transactions: pd.DataFrame, budgets: pd.DataFrame, user_id: str) -> pd.DataFrame:
    """Budget Variance = Actual Spend - Budgeted Amount"""
    txn_user = transactions[
        (transactions['user_id'] == user_id) & 
        (transactions['is_income'] == False)
    ].copy()
    txn_user['month'] = txn_user['date'].dt.to_period('M').astype(str)
    
    actual = txn_user.groupby(['month', 'category'])['amount'].sum().reset_index()
    actual.rename(columns={'amount': 'actual'}, inplace=True)
    
    budget_user = budgets[budgets['user_id'] == user_id].copy()
    budget_user['month'] = budget_user['month']
    
    merged = actual.merge(
        budget_user[['month', 'category', 'amount']].rename(columns={'amount': 'budget'}),
        on=['month', 'category'],
        how='left'
    )
    merged['budget'] = merged['budget'].fillna(0)
    merged['variance'] = (merged['actual'] - merged['budget']).round(2)
    merged['variance_pct'] = (
        (merged['variance'] / merged['budget'] * 100).fillna(0).round(2)
    )
    
    return merged.sort_values(['month', 'variance'], ascending=[True, False])


def emergency_fund_coverage(transactions: pd.DataFrame, user_id: str, months: int = 3) -> Dict[str, float]:
    """Emergency Fund Coverage = Liquid Savings / (Avg Monthly Expenses × months)"""
    liquid = transactions[
        (transactions['user_id'] == user_id) & 
        (transactions['account_type'] == 'savings') &
        (transactions['is_income'] == True)
    ]['balance_after'].max()
    liquid = max(0, liquid) if not pd.isna(liquid) else 0
    
    expenses = transactions[
        (transactions['user_id'] == user_id) & 
        (transactions['is_income'] == False)
    ]['amount'].sum()
    
    num_months = max(1, (transactions['date'].max() - transactions['date'].min()).days // 30)
    avg_monthly = expenses / num_months if num_months > 0 else 0
    
    required = avg_monthly * months
    coverage = round(liquid / required, 2) if required > 0 else 0.0
    
    return {
        'coverage_months': coverage,
        'liquid_savings': round(liquid, 2),
        'avg_monthly_expense': round(avg_monthly, 2),
        'target_emergency_fund': round(required, 2)
    }


def spending_50_30_20(transactions: pd.DataFrame, user_id: str, 
                     needs: set, wants: set, savings: set) -> Dict[str, float]:
    """50/30/20 Rule: Needs (50%), Wants (30%), Savings (20%)"""
    user_txn = transactions[
        (transactions['user_id'] == user_id) & 
        (transactions['is_income'] == False)
    ].copy()
    
    total = user_txn['amount'].sum()
    
    if total == 0:
        return {
            'needs_pct': 0.0, 'wants_pct': 0.0, 'savings_pct': 0.0,
            'needs_amt': 0.0, 'wants_amt': 0.0, 'savings_amt': 0.0,
            'needs_target': 50.0, 'wants_target': 30.0, 'savings_target': 20.0
        }
    
    needs_amt = user_txn[user_txn['category'].isin(needs)]['amount'].sum()
    wants_amt = user_txn[user_txn['category'].isin(wants)]['amount'].sum()
    savings_amt = user_txn[user_txn['category'].isin(savings)]['amount'].sum()
    
    return {
        'needs_pct': round(needs_amt / total * 100, 2),
        'wants_pct': round(wants_amt / total * 100, 2),
        'savings_pct': round(savings_amt / total * 100, 2),
        'needs_amt': round(needs_amt, 2),
        'wants_amt': round(wants_amt, 2),
        'savings_amt': round(savings_amt, 2),
        'needs_target': 50.0,
        'wants_target': 30.0,
        'savings_target': 20.0
    }
