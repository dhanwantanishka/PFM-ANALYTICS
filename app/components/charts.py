"""Reusable Plotly chart components with a consistent visual theme."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from theme.tokens import CHART_COLORS, EXPENSE, INCOME, PLOTLY_TEMPLATE, PRIMARY

_TEMPLATE = PLOTLY_TEMPLATE
_LAYOUT = dict(template=_TEMPLATE, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")


def _apply_layout(fig: go.Figure, height: int = 380, margin: dict | None = None, **kwargs) -> go.Figure:
    m = margin if margin is not None else dict(t=30, l=10, r=10, b=10)
    fig.update_layout(height=height, margin=m, autosize=True, **_LAYOUT, **kwargs)
    return fig


def income_vs_expenses_bar(transactions: pd.DataFrame) -> go.Figure:
    """Monthly income vs expenses grouped bar chart."""
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
        color_discrete_map={"Income": INCOME, "Expenses": EXPENSE},
        labels={"amount": "Amount (₹)", "month": "Month", "flow": ""},
    )
    return _apply_layout(fig, legend=dict(orientation="h", y=1.12))


def savings_rate_gauge(savings_rate_pct: float, target_pct: float = 20.0) -> go.Figure:
    """Gauge chart for savings rate against target."""
    # Clamp to a readable range centred around 0–100
    lo, hi = -30, 70
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=round(savings_rate_pct, 1),
            number={"suffix": "%", "font": {"size": 36}},
            delta={
                "reference": target_pct,
                "increasing": {"color": INCOME},
                "decreasing": {"color": EXPENSE},
                "relative": False,
            },
            gauge={
                "axis": {
                    "range": [lo, hi],
                    "tickwidth": 1,
                    "tickcolor": "#94A3B8",
                    "tickfont": {"size": 11},
                    "nticks": 6,
                },
                "bar": {"color": PRIMARY, "thickness": 0.3},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": [
                    {"range": [lo, 0], "color": "#7F1D1D"},
                    {"range": [0, target_pct], "color": "#713F12"},
                    {"range": [target_pct, hi], "color": "#14532D"},
                ],
                "threshold": {
                    "line": {"color": "#F1F5F9", "width": 3},
                    "thickness": 0.8,
                    "value": target_pct,
                },
            },
            title={"text": f"Savings rate vs {target_pct:.0f}% target", "font": {"size": 13}},
            domain={"x": [0.05, 0.95], "y": [0, 1]},
        )
    )
    return _apply_layout(fig, height=300, margin=dict(t=50, l=10, r=10, b=10))


def net_worth_trend(transactions: pd.DataFrame) -> go.Figure:
    """Cumulative net cash flow trend."""
    df = transactions.sort_values("date").copy()
    df["signed_amount"] = df["amount"].where(df["is_income"], -df["amount"])
    df["cumulative"] = df["signed_amount"].cumsum()
    daily = df.groupby(df["date"].dt.date)["cumulative"].last().reset_index()
    fig = px.line(daily, x="date", y="cumulative", labels={"cumulative": "Cumulative net flow (₹)", "date": "Date"})
    fig.update_traces(line_color=PRIMARY, fill="tozeroy", fillcolor="rgba(96,165,250,0.12)")
    return _apply_layout(fig)


def cash_flow_area(transactions: pd.DataFrame) -> go.Figure:
    """Monthly net cash flow area chart."""
    df = transactions.copy()
    df["month"] = df["date"].dt.to_period("M").astype(str)
    income = df.loc[df["is_income"]].groupby("month")["amount"].sum()
    expenses = df.loc[~df["is_income"]].groupby("month")["amount"].sum()
    net = (income.reindex(income.index.union(expenses.index), fill_value=0) -
           expenses.reindex(income.index.union(expenses.index), fill_value=0))
    plot_df = net.reset_index()
    plot_df.columns = ["month", "net_flow"]
    fig = px.area(plot_df, x="month", y="net_flow", labels={"net_flow": "Net cash flow (₹)", "month": "Month"})
    fig.update_traces(line_color=PRIMARY, fillcolor="rgba(96,165,250,0.2)")
    return _apply_layout(fig, height=340)


def savings_trend_line(transactions: pd.DataFrame) -> go.Figure:
    """Monthly savings trend."""
    df = transactions.copy()
    df["month"] = df["date"].dt.to_period("M").astype(str)
    monthly = df.groupby("month").apply(
        lambda g: g.loc[g["is_income"], "amount"].sum() - g.loc[~g["is_income"], "amount"].sum(),
        include_groups=False,
    )
    plot_df = monthly.reset_index()
    plot_df.columns = ["month", "savings"]
    fig = px.line(plot_df, x="month", y="savings", markers=True, labels={"savings": "Savings (₹)", "month": "Month"})
    fig.update_traces(line_color=INCOME)
    return _apply_layout(fig, height=340)


def budget_progress_chart(variance_df: pd.DataFrame, top_n: int = 8) -> go.Figure:
    """Horizontal bar chart of budget utilization by category."""
    agg = variance_df.groupby("category").agg(actual=("actual", "sum"), budget=("budget", "sum")).reset_index()
    agg = agg[agg["budget"] > 0].copy()
    agg["pct_used"] = (agg["actual"] / agg["budget"] * 100).round(1)
    agg = agg.sort_values("pct_used", ascending=False).head(top_n)
    fig = px.bar(
        agg,
        x="pct_used",
        y="category",
        orientation="h",
        color="pct_used",
        color_continuous_scale=["#34D399", "#FBBF24", "#F87171"],
        labels={"pct_used": "% of budget used", "category": ""},
    )
    fig.add_vline(x=100, line_dash="dash", line_color="#94A3B8")
    return _apply_layout(fig, height=360, showlegend=False)


def spending_treemap(transactions: pd.DataFrame) -> go.Figure:
    """Treemap of expense spend by category and merchant."""
    expenses = transactions.loc[~transactions["is_income"]].copy()
    expenses["merchant"] = expenses["merchant"].fillna("Other")
    summary = expenses.groupby(["category", "merchant"])["amount"].sum().reset_index()
    fig = px.treemap(
        summary,
        path=[px.Constant("All spending"), "category", "merchant"],
        values="amount",
        color="amount",
        color_continuous_scale="Blues",
    )
    return _apply_layout(fig, height=460)


def category_pie_bar_combo(transactions: pd.DataFrame, top_n: int = 8) -> go.Figure:
    """Combined pie and bar for category spend."""
    expenses = transactions.loc[~transactions["is_income"]].copy()
    summary = expenses.groupby("category")["amount"].sum().sort_values(ascending=False).head(top_n).reset_index()
    fig = go.Figure()
    fig.add_trace(
        go.Pie(
            labels=summary["category"],
            values=summary["amount"],
            hole=0.45,
            marker=dict(colors=CHART_COLORS),
            domain=dict(x=[0, 0.45]),
        )
    )
    fig.add_trace(
        go.Bar(
            x=summary["amount"],
            y=summary["category"],
            orientation="h",
            marker_color=PRIMARY,
            xaxis="x2",
            yaxis="y2",
        )
    )
    fig.update_layout(
        xaxis2=dict(domain=[0.55, 1], anchor="y2"),
        yaxis2=dict(domain=[0, 1], anchor="x2"),
        showlegend=False,
        **_LAYOUT,
        height=420,
    )
    return fig


def merchant_leaderboard_bar(transactions: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Horizontal bar chart of top merchants."""
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
    fig = px.bar(top, x="amount", y="merchant", orientation="h", labels={"amount": "Total spend (₹)", "merchant": ""})
    fig.update_traces(marker_color=PRIMARY)
    return _apply_layout(fig)


def category_trend_line(transactions: pd.DataFrame, categories: list[str] | None = None) -> go.Figure:
    """Monthly spend trend by category."""
    expenses = transactions.loc[~transactions["is_income"]].copy()
    if categories:
        expenses = expenses[expenses["category"].isin(categories)]
    expenses["month"] = expenses["date"].dt.to_period("M").astype(str)
    summary = expenses.groupby(["month", "category"])["amount"].sum().reset_index()
    fig = px.line(
        summary,
        x="month",
        y="amount",
        color="category",
        markers=True,
        color_discrete_sequence=CHART_COLORS,
        labels={"amount": "Amount (₹)", "month": "Month", "category": "Category"},
    )
    return _apply_layout(fig, height=420)


def category_comparison_bar(transactions: pd.DataFrame) -> go.Figure:
    """Compare current vs previous month by category."""
    expenses = transactions.loc[~transactions["is_income"]].copy()
    expenses["month"] = expenses["date"].dt.to_period("M")
    months = sorted(expenses["month"].unique())
    if len(months) < 2:
        fig = go.Figure()
        fig.add_annotation(text="Need at least two months of data", showarrow=False)
        return _apply_layout(fig, height=300)
    current, previous = months[-1], months[-2]
    cur = expenses[expenses["month"] == current].groupby("category")["amount"].sum()
    prev = expenses[expenses["month"] == previous].groupby("category")["amount"].sum()
    plot_df = pd.DataFrame({"current": cur, "previous": prev}).fillna(0).reset_index()
    plot_df = plot_df.melt(id_vars="category", var_name="period", value_name="amount")
    fig = px.bar(
        plot_df,
        x="category",
        y="amount",
        color="period",
        barmode="group",
        color_discrete_map={"current": PRIMARY, "previous": "#64748B"},
        labels={"amount": "Spend (₹)", "category": "Category", "period": "Period"},
    )
    return _apply_layout(fig, height=400)


def dow_category_heatmap(heatmap_data: pd.DataFrame) -> go.Figure:
    """Day-of-week × category heatmap."""
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
    return _apply_layout(fig)


def kpi_progress_bar(actual_pct: float, target_pct: float, label: str) -> go.Figure:
    """Horizontal target vs actual progress bar."""
    on_target = actual_pct <= target_pct
    bar_color = INCOME if on_target else EXPENSE
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=[actual_pct],
            y=[label],
            orientation="h",
            marker_color=bar_color,
            text=[f"{actual_pct:.1f}%"],
            textposition="outside",
        )
    )
    fig.add_vline(x=target_pct, line_dash="dash", line_color="#94A3B8")
    fig.update_layout(
        height=110,
        margin=dict(t=10, b=10, l=10, r=60),
        showlegend=False,
        xaxis=dict(range=[0, max(actual_pct, target_pct) * 1.3 + 5]),
        **_LAYOUT,
    )
    return fig


def health_score_gauge(score: float) -> go.Figure:
    """Financial health score gauge (0-100)."""
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "/100"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": PRIMARY},
                "steps": [
                    {"range": [0, 40], "color": "#7F1D1D"},
                    {"range": [40, 60], "color": "#713F12"},
                    {"range": [60, 80], "color": "#1E3A5F"},
                    {"range": [80, 100], "color": "#14532D"},
                ],
            },
            title={"text": "Financial health score"},
        )
    )
    return _apply_layout(fig, height=300)


def forecast_chart(
    history: pd.DataFrame,
    forecast: pd.Series,
    forecast_dates: pd.DatetimeIndex,
    ci_pct: float = 0.15,
) -> go.Figure:
    """Actual vs forecast with confidence band."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=history["date"],
            y=history["amount"],
            mode="lines",
            name="Actual",
            line=dict(color=PRIMARY),
        )
    )
    upper = forecast * (1 + ci_pct)
    lower = forecast * (1 - ci_pct)
    fig.add_trace(
        go.Scatter(
            x=list(forecast_dates) + list(forecast_dates[::-1]),
            y=list(upper) + list(lower[::-1]),
            fill="toself",
            fillcolor="rgba(248,113,113,0.15)",
            line=dict(color="rgba(0,0,0,0)"),
            name="Confidence band",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast_dates,
            y=forecast,
            mode="lines+markers",
            name="Forecast",
            line=dict(color=EXPENSE, dash="dash"),
        )
    )
    fig.update_layout(yaxis_title="Daily spend (₹)", xaxis_title="Date", **_LAYOUT, height=420)
    return fig


def model_comparison_bar(comparison_df: pd.DataFrame, metric: str = "mae") -> go.Figure:
    """Bar chart comparing model performance metrics."""
    fig = px.bar(
        comparison_df,
        x="model",
        y=metric,
        color="model",
        color_discrete_sequence=CHART_COLORS,
        labels={metric: metric.upper(), "model": "Model"},
    )
    return _apply_layout(fig, height=320, showlegend=False)


def anomaly_timeline(transactions: pd.DataFrame, anomaly_col: str = "anomaly") -> go.Figure:
    """Scatter timeline highlighting anomalies."""
    df = transactions.copy()
    df["status"] = df[anomaly_col].map({True: "Anomaly", False: "Normal"})
    fig = px.scatter(
        df,
        x="date",
        y="amount",
        color="status",
        color_discrete_map={"Anomaly": EXPENSE, "Normal": PRIMARY},
        hover_data=["category", "merchant"] if "merchant" in df.columns else ["category"],
        labels={"amount": "Amount (₹)", "date": "Date"},
    )
    fig.update_traces(marker=dict(size=8), selector=dict(name="Anomaly"))
    return _apply_layout(fig, height=420, legend_title_text="")
