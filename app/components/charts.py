"""Reusable Plotly chart components with a consistent visual theme."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

THEME_TEMPLATE = "plotly_white"
PRIMARY_COLOR = "#2563EB"
INCOME_COLOR = "#16A34A"
EXPENSE_COLOR = "#DC2626"


def income_vs_expenses_bar(transactions: pd.DataFrame) -> go.Figure:
    """Build a monthly income-vs-expenses grouped bar chart.

    Args:
        transactions: Filtered transactions with ``date``, ``amount``,
            ``is_income`` columns.

    Returns:
        A Plotly figure.
    """
    df = transactions.copy()
    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["flow"] = df["is_income"].map({True: "Income", False: "Expenses"})
    summary = df.groupby(["month", "flow"])["amount"].sum().reset_index()

    fig = px.bar(
        summary,
        x="month",
        y="amount",
        color="flow",
        barmode="group",
        template=THEME_TEMPLATE,
        color_discrete_map={"Income": INCOME_COLOR, "Expenses": EXPENSE_COLOR},
        labels={"amount": "Amount (₹)", "month": "Month", "flow": ""},
    )
    fig.update_layout(legend_title_text="", height=380, margin=dict(t=30))
    return fig


def savings_rate_gauge(savings_rate_pct: float, target_pct: float = 20.0) -> go.Figure:
    """Build a gauge chart for savings rate against a target.

    Args:
        savings_rate_pct: Current savings rate as a percentage.
        target_pct: Target savings rate (default 20%, per the 50/30/20 rule).

    Returns:
        A Plotly figure.
    """
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=round(savings_rate_pct, 1),
            number={"suffix": "%"},
            delta={
                "reference": target_pct,
                "increasing": {"color": INCOME_COLOR},
                "decreasing": {"color": EXPENSE_COLOR},
            },
            gauge={
                "axis": {"range": [-20, 60]},
                "bar": {"color": PRIMARY_COLOR},
                "steps": [
                    {"range": [-20, 0], "color": "#FEE2E2"},
                    {"range": [0, target_pct], "color": "#FEF3C7"},
                    {"range": [target_pct, 60], "color": "#DCFCE7"},
                ],
                "threshold": {
                    "line": {"color": "black", "width": 3},
                    "thickness": 0.8,
                    "value": target_pct,
                },
            },
            title={"text": f"Savings Rate vs {target_pct:.0f}% Target"},
        )
    )
    fig.update_layout(height=320, margin=dict(t=50, b=10))
    return fig


def net_worth_trend(transactions: pd.DataFrame) -> go.Figure:
    """Build a cumulative net cash flow trend line (net-worth proxy).

    Args:
        transactions: Filtered transactions with ``date``, ``amount``,
            ``is_income`` columns.

    Returns:
        A Plotly figure.
    """
    df = transactions.sort_values("date").copy()
    df["signed_amount"] = df["amount"].where(df["is_income"], -df["amount"])
    df["cumulative"] = df["signed_amount"].cumsum()
    daily = df.groupby(df["date"].dt.date)["cumulative"].last().reset_index()

    fig = px.line(
        daily,
        x="date",
        y="cumulative",
        template=THEME_TEMPLATE,
        labels={"cumulative": "Cumulative Net Flow (₹)", "date": "Date"},
    )
    fig.update_traces(
        line_color=PRIMARY_COLOR, fill="tozeroy", fillcolor="rgba(37,99,235,0.08)"
    )
    fig.update_layout(height=380, margin=dict(t=30))
    return fig


def spending_treemap(transactions: pd.DataFrame) -> go.Figure:
    """Build a treemap of expense spend by category and merchant.

    Args:
        transactions: Filtered transactions with ``category``, ``merchant``,
            ``amount``, ``is_income`` columns.

    Returns:
        A Plotly figure.
    """
    expenses = transactions.loc[~transactions["is_income"]].copy()
    expenses["merchant"] = expenses["merchant"].fillna("Other")
    summary = (
        expenses.groupby(["category", "merchant"])["amount"].sum().reset_index()
    )
    fig = px.treemap(
        summary,
        path=[px.Constant("All Spending"), "category", "merchant"],
        values="amount",
        template=THEME_TEMPLATE,
        color="amount",
        color_continuous_scale="Blues",
    )
    fig.update_layout(height=460, margin=dict(t=30, l=0, r=0, b=0))
    return fig


def merchant_leaderboard_bar(transactions: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Build a horizontal bar chart of top merchants by expense spend.

    Args:
        transactions: Filtered transactions with ``merchant``, ``amount``,
            ``is_income`` columns.
        top_n: Number of merchants to display.

    Returns:
        A Plotly figure.
    """
    expenses = transactions.loc[~transactions["is_income"]].copy()
    expenses["merchant"] = expenses["merchant"].fillna("Other")
    top = (
        expenses.groupby("merchant")["amount"]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .reset_index()
        .sort_values("amount")
    )
    fig = px.bar(
        top,
        x="amount",
        y="merchant",
        orientation="h",
        template=THEME_TEMPLATE,
        labels={"amount": "Total Spend (₹)", "merchant": ""},
        color_discrete_sequence=[PRIMARY_COLOR],
    )
    fig.update_layout(height=380, margin=dict(t=30))
    return fig


def category_trend_line(transactions: pd.DataFrame) -> go.Figure:
    """Build a monthly spend trend line, one line per category.

    Args:
        transactions: Filtered transactions with ``date``, ``category``,
            ``amount``, ``is_income`` columns.

    Returns:
        A Plotly figure.
    """
    expenses = transactions.loc[~transactions["is_income"]].copy()
    expenses["month"] = expenses["date"].dt.to_period("M").astype(str)
    summary = expenses.groupby(["month", "category"])["amount"].sum().reset_index()
    fig = px.line(
        summary,
        x="month",
        y="amount",
        color="category",
        template=THEME_TEMPLATE,
        markers=True,
        labels={"amount": "Amount (₹)", "month": "Month", "category": "Category"},
    )
    fig.update_layout(height=420, margin=dict(t=30))
    return fig


def dow_category_heatmap(heatmap_data: pd.DataFrame) -> go.Figure:
    """Build a day-of-week × category spending heatmap.

    Args:
        heatmap_data: Pivoted spend data, e.g. from
            :func:`pfm.analytics.spending_analysis.spending_heatmap_data`.

    Returns:
        A Plotly figure.
    """
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    ordered = heatmap_data.reindex([d for d in day_order if d in heatmap_data.index])
    fig = go.Figure(
        go.Heatmap(
            z=ordered.values,
            x=ordered.columns,
            y=ordered.index,
            colorscale="Blues",
            colorbar=dict(title="₹"),
        )
    )
    fig.update_layout(template=THEME_TEMPLATE, height=380, margin=dict(t=30))
    return fig


def kpi_progress_bar(actual_pct: float, target_pct: float, label: str) -> go.Figure:
    """Build a horizontal target-vs-actual progress bar for a percentage KPI.

    Args:
        actual_pct: Actual percentage achieved.
        target_pct: Target percentage.
        label: KPI label shown as the chart title.

    Returns:
        A Plotly figure.
    """
    on_target = actual_pct <= target_pct
    bar_color = INCOME_COLOR if on_target else EXPENSE_COLOR

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=[actual_pct],
            y=[label],
            orientation="h",
            marker_color=bar_color,
            name="Actual",
            text=[f"{actual_pct:.1f}%"],
            textposition="outside",
        )
    )
    fig.add_vline(x=target_pct, line_dash="dash", line_color="black")
    fig.update_layout(
        template=THEME_TEMPLATE,
        height=110,
        margin=dict(t=10, b=10, l=10, r=60),
        showlegend=False,
        xaxis=dict(range=[0, max(actual_pct, target_pct) * 1.3 + 5]),
    )
    return fig


def forecast_chart(
    history: pd.DataFrame,
    forecast: pd.Series,
    forecast_dates: pd.DatetimeIndex,
    ci_pct: float = 0.15,
) -> go.Figure:
    """Build an actual-vs-forecast line chart with a shaded confidence band.

    Args:
        history: Historical daily spend with ``date`` and ``amount`` columns.
        forecast: Forecasted amounts, indexed 0..N-1.
        forecast_dates: Calendar dates corresponding to ``forecast``.
        ci_pct: Symmetric confidence-band width as a fraction of the forecast.

    Returns:
        A Plotly figure.
    """
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=history["date"],
            y=history["amount"],
            mode="lines",
            name="Actual",
            line=dict(color=PRIMARY_COLOR),
        )
    )

    upper = forecast * (1 + ci_pct)
    lower = forecast * (1 - ci_pct)
    fig.add_trace(
        go.Scatter(
            x=list(forecast_dates) + list(forecast_dates[::-1]),
            y=list(upper) + list(lower[::-1]),
            fill="toself",
            fillcolor="rgba(220,38,38,0.15)",
            line=dict(color="rgba(0,0,0,0)"),
            name="Confidence Band",
            showlegend=True,
        )

    )
    fig.add_trace(
        go.Scatter(
            x=forecast_dates,
            y=forecast,
            mode="lines+markers",
            name="Forecast",
            line=dict(color=EXPENSE_COLOR, dash="dash"),
        )
    )
    fig.update_layout(
        template=THEME_TEMPLATE,
        height=420,
        margin=dict(t=30),
        yaxis_title="Daily Spend (₹)",
        xaxis_title="Date",
    )
    return fig


def anomaly_timeline(transactions: pd.DataFrame, anomaly_col: str = "anomaly") -> go.Figure:
    """Build a scatter timeline highlighting flagged anomalous transactions.

    Args:
        transactions: Transactions with ``date``, ``amount``, and a boolean
            anomaly indicator column.
        anomaly_col: Name of the boolean anomaly indicator column.

    Returns:
        A Plotly figure.
    """
    df = transactions.copy()
    df["status"] = df[anomaly_col].map({True: "Anomaly", False: "Normal"})
    fig = px.scatter(
        df,
        x="date",
        y="amount",
        color="status",
        template=THEME_TEMPLATE,
        color_discrete_map={"Anomaly": EXPENSE_COLOR, "Normal": PRIMARY_COLOR},
        hover_data=["category", "merchant"] if "merchant" in df.columns else ["category"],
        labels={"amount": "Amount (₹)", "date": "Date"},
    )
    fig.update_traces(
        marker=dict(size=8),
        selector=dict(name="Anomaly"),
    )
    fig.update_layout(height=420, margin=dict(t=30), legend_title_text="")
    return fig

def spending_treemap(transactions: pd.DataFrame) -> go.Figure:
    """Build a treemap of expense spend by category and merchant.

    Args:
        transactions: Filtered transactions with `category`, `merchant`,
            `amount`, `is_income` columns.

    Returns:
        A Plotly figure.
    """
    expenses = transactions.loc[~transactions["is_income"]].copy()
    expenses["merchant"] = expenses["merchant"].fillna("Other")
    summary = expenses.groupby(["category", "merchant"])["amount"].sum().reset_index()
    fig = px.treemap(
        summary,
        path=[px.Constant("All Spending"), "category", "merchant"],
        values="amount",
        template=THEME_TEMPLATE,
        color="amount",
        color_continuous_scale="Blues",
    )
    fig.update_layout(height=460, margin=dict(t=30, l=0, r=0, b=0))
    return fig


def merchant_leaderboard_bar(transactions: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Build a horizontal bar chart of top merchants by expense spend.

    Args:
        transactions: Filtered transactions with `merchant`, `amount`,
            `is_income` columns.
        top_n: Number of merchants to display.

    Returns:
        A Plotly figure.
    """
    expenses = transactions.loc[~transactions["is_income"]].copy()
    expenses["merchant"] = expenses["merchant"].fillna("Other")
    top = (
        expenses.groupby("merchant")["amount"]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .reset_index()
        .sort_values("amount")
    )
    fig = px.bar(
        top,
        x="amount",
        y="merchant",
        orientation="h",
        template=THEME_TEMPLATE,
        labels={"amount": "Total Spend (₹)", "merchant": ""},
        color_discrete_sequence=[PRIMARY_COLOR],
    )
    fig.update_layout(height=380, margin=dict(t=30))
    return fig


def category_trend_line(transactions: pd.DataFrame) -> go.Figure:
    """Build a monthly spend trend line, one line per category.

    Args:
        transactions: Filtered transactions with `date`, `category`,
            `amount`, `is_income` columns.

    Returns:
        A Plotly figure.
    """
    expenses = transactions.loc[~transactions["is_income"]].copy()
    expenses["month"] = expenses["date"].dt.to_period("M").astype(str)
    summary = expenses.groupby(["month", "category"])["amount"].sum().reset_index()
    fig = px.line(
        summary,
        x="month",
        y="amount",
        color="category",
        template=THEME_TEMPLATE,
        markers=True,
        labels={"amount": "Amount (₹)", "month": "Month", "category": "Category"},
    )
    fig.update_layout(height=420, margin=dict(t=30))
    return fig


def dow_category_heatmap(heatmap_data: pd.DataFrame) -> go.Figure:
    """Build a day-of-week x category spending heatmap.

    Args:
        heatmap_data: Pivoted spend data, e.g. from
            `pfm.analytics.spending_analysis.spending_heatmap_data`.

    Returns:
        A Plotly figure.
    """
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    ordered = heatmap_data.reindex([d for d in day_order if d in heatmap_data.index])
    fig = go.Figure(
        go.Heatmap(
            z=ordered.values,
            x=ordered.columns,
            y=ordered.index,
            colorscale="Blues",
            colorbar=dict(title="₹"),
        )
    )
    fig.update_layout(template=THEME_TEMPLATE, height=380, margin=dict(t=30))
    return fig


def kpi_progress_bar(actual_pct: float, target_pct: float, label: str) -> go.Figure:
    """Build a horizontal target-vs-actual progress bar for a percentage KPI.

    Args:
        actual_pct: Actual percentage achieved.
        target_pct: Target percentage.
        label: KPI label shown as the chart title.

    Returns:
        A Plotly figure.
    """
    on_target = actual_pct <= target_pct
    bar_color = INCOME_COLOR if on_target else EXPENSE_COLOR

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=[actual_pct],
            y=[label],
            orientation="h",
            marker_color=bar_color,
            name="Actual",
            text=[f"{actual_pct:.1f}%"],
            textposition="outside",
        )
    )
    fig.add_vline(x=target_pct, line_dash="dash", line_color="black")
    fig.update_layout(
        template=THEME_TEMPLATE,
        height=110,
        margin=dict(t=10, b=10, l=10, r=60),
        showlegend=False,
        xaxis=dict(range=[0, max(actual_pct, target_pct) * 1.3 + 5]),
    )
    return fig


def forecast_chart(
    history: pd.DataFrame,
    forecast: pd.Series,
    forecast_dates: pd.DatetimeIndex,
    ci_pct: float = 0.15,
) -> go.Figure:
    """Build an actual-vs-forecast line chart with a shaded confidence band.

    Args:
        history: Historical daily spend with `date` and `amount` columns.
        forecast: Forecasted amounts, indexed 0..N-1.
        forecast_dates: Calendar dates corresponding to `forecast`.
        ci_pct: Symmetric confidence-band width as a fraction of the forecast.

    Returns:
        A Plotly figure.
    """
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=history["date"],
            y=history["amount"],
            mode="lines",
            name="Actual",
            line=dict(color=PRIMARY_COLOR),
        )
    )

    upper = forecast * (1 + ci_pct)
    lower = forecast * (1 - ci_pct)
    fig.add_trace(
        go.Scatter(
            x=list(forecast_dates) + list(forecast_dates[::-1]),
            y=list(upper) + list(lower[::-1]),
            fill="toself",
            fillcolor="rgba(220,38,38,0.15)",
            line=dict(color="rgba(0,0,0,0)"),
            name="Confidence Band",
            showlegend=True,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast_dates,
            y=forecast,
            mode="lines+markers",
            name="Forecast",
            line=dict(color=EXPENSE_COLOR, dash="dash"),
        )
    )
    fig.update_layout(
        template=THEME_TEMPLATE,
        height=420,
        margin=dict(t=30),
        yaxis_title="Daily Spend (₹)",
        xaxis_title="Date",
    )
    return fig


def anomaly_timeline(transactions: pd.DataFrame, anomaly_col: str = "anomaly") -> go.Figure:
    """Build a scatter timeline highlighting flagged anomalous transactions.

    Args:
        transactions: Transactions with `date`, `amount`, and a boolean
            anomaly indicator column.
        anomaly_col: Name of the boolean anomaly indicator column.

    Returns:
        A Plotly figure.
    """
    df = transactions.copy()
    df["status"] = df[anomaly_col].map({True: "Anomaly", False: "Normal"})
    fig = px.scatter(
        df,
        x="date",
        y="amount",
        color="status",
        template=THEME_TEMPLATE,
        color_discrete_map={"Anomaly": EXPENSE_COLOR, "Normal": PRIMARY_COLOR},
        hover_data=["category", "merchant"] if "merchant" in df.columns else ["category"],
        labels={"amount": "Amount (₹)", "date": "Date"},
    )
    fig.update_layout(height=420, margin=dict(t=30), legend_title_text="")
    return fig
