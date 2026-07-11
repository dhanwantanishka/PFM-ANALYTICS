"""Anomaly detection for transactions."""

import pandas as pd
import numpy as np
from typing import Dict
from sklearn.ensemble import IsolationForest


def detect_anomalies_isolation_forest(transactions: pd.DataFrame, user_id: str, 
                                      contamination: float = 0.05) -> Dict:
    """Detect anomalies using Isolation Forest."""
    user_data = transactions[
        (transactions['user_id'] == user_id) & 
        (transactions['is_income'] == False)
    ].copy()
    
    user_data['date'] = pd.to_datetime(user_data['date'])
    user_data['day_of_week'] = user_data['date'].dt.dayofweek
    user_data['month'] = user_data['date'].dt.month
    
    X = user_data[['amount', 'day_of_week', 'month']].values
    
    model = IsolationForest(contamination=contamination, random_state=42)
    anomaly_labels = model.fit_predict(X)
    
    user_data['anomaly'] = anomaly_labels == -1
    
    anomalies = user_data[user_data['anomaly']].copy()
    
    return {
        'total_transactions': len(user_data),
        'anomaly_count': len(anomalies),
        'anomaly_percentage': round(len(anomalies) / len(user_data) * 100, 2),
        'anomalies': anomalies[['date', 'amount', 'category', 'merchant']],
        'mean_anomaly_amount': round(anomalies['amount'].mean(), 2),
        'mean_normal_amount': round(user_data[~user_data['anomaly']]['amount'].mean(), 2)
    }


def detect_anomalies_zscore(transactions: pd.DataFrame, user_id: str, 
                            threshold: float = 3.0) -> Dict:
    """Detect anomalies using Z-score method."""
    user_data = transactions[
        (transactions['user_id'] == user_id) & 
        (transactions['is_income'] == False)
    ].copy()
    
    user_data['date'] = pd.to_datetime(user_data['date'])
    
    # Calculate z-scores
    mean = user_data['amount'].mean()
    std = user_data['amount'].std()
    user_data['z_score'] = np.abs((user_data['amount'] - mean) / std)
    
    # Flag anomalies
    user_data['anomaly'] = user_data['z_score'] > threshold
    
    anomalies = user_data[user_data['anomaly']].copy()
    
    return {
        'total_transactions': len(user_data),
        'anomaly_count': len(anomalies),
        'anomaly_percentage': round(len(anomalies) / len(user_data) * 100, 2),
        'anomalies': anomalies[['date', 'amount', 'category', 'merchant', 'z_score']],
        'threshold_used': threshold,
        'mean_amount': round(mean, 2),
        'std_amount': round(std, 2)
    }


def anomaly_summary_by_category(transactions: pd.DataFrame, user_id: str) -> pd.DataFrame:
    """Summarize anomalies by spending category."""
    user_data = transactions[
        (transactions['user_id'] == user_id) & 
        (transactions['is_income'] == False)
    ].copy()
    
    mean = user_data['amount'].mean()
    std = user_data['amount'].std()
    user_data['z_score'] = np.abs((user_data['amount'] - mean) / std)
    user_data['anomaly'] = user_data['z_score'] > 3.0
    
    anomaly_by_cat = user_data[user_data['anomaly']].groupby('category').agg({
        'amount': ['count', 'sum', 'mean', 'max']
    }).round(2)
    
    return anomaly_by_cat
