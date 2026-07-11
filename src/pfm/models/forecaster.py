"""Expense forecasting models."""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb


def prepare_forecast_data(transactions: pd.DataFrame, user_id: str, 
                          target_days: int = 7) -> Tuple[pd.DataFrame, pd.Series]:
    """Prepare data for forecasting: X (features), y (target)."""
    user_data = transactions[
        (transactions['user_id'] == user_id) & 
        (transactions['is_income'] == False)
    ].copy().sort_values('date')
    
    user_data['date'] = pd.to_datetime(user_data['date'])
    user_data['day_of_week'] = user_data['date'].dt.dayofweek
    user_data['month'] = user_data['date'].dt.month
    user_data['is_weekend'] = user_data['day_of_week'] >= 5
    
    # Aggregate daily spending
    daily_spend = user_data.groupby('date').agg({
        'amount': 'sum',
        'day_of_week': 'first',
        'month': 'first',
        'is_weekend': 'first',
        'category': lambda x: len(x)  # transaction count
    }).reset_index()
    daily_spend.columns = ['date', 'amount', 'day_of_week', 'month', 'is_weekend', 'txn_count']
    
    # Create rolling features
    daily_spend['rolling_7d'] = daily_spend['amount'].rolling(7, min_periods=1).mean()
    daily_spend['rolling_30d'] = daily_spend['amount'].rolling(30, min_periods=1).mean()
    daily_spend['lag_1'] = daily_spend['amount'].shift(1)
    daily_spend['lag_7'] = daily_spend['amount'].shift(7)
    
    daily_spend = daily_spend.dropna()
    
    X = daily_spend[['day_of_week', 'month', 'is_weekend', 'txn_count', 'rolling_7d', 'rolling_30d', 'lag_1', 'lag_7']]
    y = daily_spend['amount']
    
    return X, y


def train_linear_regression(X: pd.DataFrame, y: pd.Series) -> Dict:
    """Train linear regression model."""
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    return {
        'model': model,
        'mae': round(mae, 2),
        'rmse': round(rmse, 2),
        'r2': round(r2, 3),
        'type': 'Linear Regression'
    }


def train_random_forest(X: pd.DataFrame, y: pd.Series) -> Dict:
    """Train random forest model."""
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    return {
        'model': model,
        'mae': round(mae, 2),
        'rmse': round(rmse, 2),
        'r2': round(r2, 3),
        'type': 'Random Forest',
        'feature_importance': feature_importance
    }


def train_xgboost(X: pd.DataFrame, y: pd.Series) -> Dict:
    """Train XGBoost model."""
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = xgb.XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    return {
        'model': model,
        'mae': round(mae, 2),
        'rmse': round(rmse, 2),
        'r2': round(r2, 3),
        'type': 'XGBoost'
    }


def forecast_next_days(model, X_recent: pd.DataFrame, days: int = 7) -> pd.Series:
    """Forecast spending for next N days using trained model."""
    forecasts = []
    X_current = X_recent.iloc[-1:].copy()
    
    for _ in range(days):
        forecast = model.predict(X_current)[0]
        forecasts.append(forecast)
        
        # Update features for next day (simplified)
        X_current['day_of_week'] = (X_current['day_of_week'].values[0] + 1) % 7
    
    return pd.Series(forecasts, index=range(days))
