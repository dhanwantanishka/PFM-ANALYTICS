"""Reusable KPI metric card components."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def render_kpi_row(cards: list[dict]) -> None:
    """Render a row of metric cards.

    Each card dict supports keys: label, value, delta, help, delta_color.
    """
    columns = st.columns(len(cards))
    for column, card in zip(columns, cards):
        column.metric(
            label=card["label"],
            value=card["value"],
            delta=card.get("delta"),
            delta_color=card.get("delta_color", "normal"),
            help=card.get("help"),
        )


def render_metric_cards(cards: list[dict], columns: int = 4) -> None:
    """Render metric cards inside bordered containers."""
    cols = st.columns(columns)
    for idx, card in enumerate(cards):
        with cols[idx % columns]:
            with st.container(border=True):
                st.caption(card["label"])
                st.markdown(f"**{card['value']}**")
                if card.get("delta"):
                    st.caption(card["delta"])
                if card.get("help"):
                    st.caption(card["help"])


def render_alert_cards(alerts: list[dict[str, str]]) -> None:
    """Render alert cards with severity badges."""
    for alert in alerts:
        level = alert.get("level", "Low")
        color = {"High": "red", "Medium": "orange", "Low": "green", "WATCH": "blue"}.get(level, "gray")
        with st.container(border=True):
            st.markdown(f":{color}-badge[{level}] **{alert['title']}**")
            st.caption(alert["message"])


def render_insight_list(insights: list[str]) -> None:
    """Render AI-style insight bullets."""
    for insight in insights:
        st.markdown(f"- :material/lightbulb: {insight}")


def render_severity_table(
    df: pd.DataFrame,
    severity_col: str,
    severity_colors: dict[str, str],
) -> None:
    """Render a dataframe with row background colour keyed by severity."""

    def _highlight(row: pd.Series) -> list[str]:
        color = severity_colors.get(row[severity_col], "")
        return [f"background-color: {color}" if color else "" for _ in row]

    st.dataframe(df.style.apply(_highlight, axis=1), hide_index=True, width="stretch")


def render_category_cards(category_df: pd.DataFrame, top_n: int = 6) -> None:
    """Render spending category summary cards."""
    cols = st.columns(3)
    for idx, (category, row) in enumerate(category_df.head(top_n).iterrows()):
        amount = row[("amount", "sum")]
        count = int(row[("amount", "count")])
        with cols[idx % 3]:
            with st.container(border=True):
                st.markdown(f"**{category}**")
                st.markdown(f"₹{amount:,.0f}")
                st.caption(f"{count} transactions")
