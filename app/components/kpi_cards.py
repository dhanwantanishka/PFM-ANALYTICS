"""Reusable KPI metric card components."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def render_kpi_row(cards: list[dict[str, str]]) -> None:
    """Render a row of Streamlit metric cards.

    Args:
        cards: Each dict supports keys ``label``, ``value``, and optionally
            ``delta`` and ``help``.
    """
    columns = st.columns(len(cards))
    for column, card in zip(columns, cards):
        column.metric(
            label=card["label"],
            value=card["value"],
            delta=card.get("delta"),
            help=card.get("help"),
        )


def render_severity_table(
    df: pd.DataFrame, severity_col: str, severity_colors: dict[str, str]
) -> None:
    """Render a dataframe with row background colour keyed by a severity column.

    Args:
        df: Table to display.
        severity_col: Column whose values map to background colours.
        severity_colors: Mapping of severity value to a CSS colour string.
    """

    def _highlight(row: pd.Series) -> list[str]:
        color = severity_colors.get(row[severity_col], "")
        return [f"background-color: {color}" if color else "" for _ in row]

    st.dataframe(
        df.style.apply(_highlight, axis=1),
        use_container_width=True,
        hide_index=True,
    )