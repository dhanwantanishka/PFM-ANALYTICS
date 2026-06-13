"""Streamlit dashboard entry point (Phase 4)."""

import streamlit as st

st.set_page_config(page_title="PFM Analytics", page_icon="💰", layout="wide")

st.title("Personal Finance Management — Data Analytics")
st.info(
    "Dashboard coming in Phase 4 (Days 28–38). "
    "Run `make seed` to populate the database, then continue with Phase 2 EDA."
)

st.markdown("""
### Project Status
- **Phase 1** — Data Engineering: ETL pipeline, SQLite, synthetic data ✅
- **Phase 2** — EDA & KPIs: Jupyter notebook (next)
- **Phase 3** — ML & Anomaly Detection
- **Phase 4** — Interactive Dashboard
- **Phase 5** — Testing & Final Presentation
""")
