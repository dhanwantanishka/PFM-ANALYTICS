"""Empty, error, and loading state components."""

from __future__ import annotations

import streamlit as st


def render_empty_state(title: str, message: str, icon: str = ":material/inbox:") -> None:
    """Render a friendly empty-state panel."""
    st.markdown(f"### {icon} {title}")
    st.caption(message)


def render_error_state(title: str, message: str, icon: str = ":material/error:") -> None:
    """Render an error panel with guidance."""
    st.error(f"{title}: {message}")


def render_loading_skeleton(label: str = "Loading data...") -> None:
    """Render a lightweight loading placeholder."""
    with st.spinner(label):
        st.markdown(
            """
            <div style="opacity:0.55">
            Loading charts and metrics…
            </div>
            """,
            unsafe_allow_html=True,
        )
