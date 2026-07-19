"""Settings — theme, cache, and application preferences."""

from __future__ import annotations

import sys

import streamlit as st

import utils.bootstrap  # noqa: F401

from components.layout import render_page_header, render_section
from theme.styles import inject_global_styles
from utils.data_loader import load_budgets, load_transactions

render_page_header(
    "Settings",
    "Customize appearance and manage application data.",
    ":material/settings:",
)

render_section("Appearance")
light_mode = st.toggle("Light theme preview", value=st.session_state.get("light_mode", False))
st.session_state.light_mode = light_mode
inject_global_styles(light_mode=light_mode)
st.caption(
    "Primary theme is configured in `.streamlit/config.toml`. "
    "The toggle applies a preview overlay; restart the app after editing config for full light mode."
)

render_section("Data & cache")
if st.button(":material/refresh: Clear data cache"):
    load_transactions.clear()
    load_budgets.clear()
    st.success("Cache cleared. Data will reload on the next page refresh.")

render_section("About")
st.markdown(
    """
**PFM Analytics** — Personal Finance Management platform  
**Organization:** Inventive BizPro Technologies Pvt. Ltd.  
**Stack:** Python, Pandas, SQLAlchemy, SQLite, Scikit-learn, XGBoost, Streamlit  

**Pages:** Dashboard · Spending · KPIs · Forecast · Anomaly · Upload · Transactions · Reports · AI Advisor
    """
)

render_section("Configuration")
st.code(
    """
# .streamlit/secrets.toml (optional — for AI advisor API)
[openai]
api_key = "sk-..."
    """,
    language="toml",
)
