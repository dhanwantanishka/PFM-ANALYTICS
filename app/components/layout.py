"""Page layout helpers."""

from __future__ import annotations

import streamlit as st


def render_page_header(title: str, subtitle: str | None = None, icon: str | None = None) -> None:
    """Render a consistent page header."""
    heading = f"{icon} {title}" if icon else title
    st.title(heading)
    if subtitle:
        st.caption(subtitle)


def render_section(title: str, help_text: str | None = None) -> None:
    """Render a section subheader."""
    st.subheader(title)
    if help_text:
        st.caption(help_text)
