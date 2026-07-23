"""PFM Analytics — production Streamlit application entry point."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_APP_DIR = Path(__file__).resolve().parent
_SRC_DIR = _APP_DIR.parent / "src"
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from theme.styles import inject_global_styles  # noqa: E402

st.set_page_config(
    page_title="PFM Analytics",
    page_icon=":material/account_balance:",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "light_mode" not in st.session_state:
    st.session_state.light_mode = False

# Restore session from URL query parameters on browser refresh
if "user_id" not in st.session_state and "user_id" in st.query_params:
    st.session_state["user_id"] = st.query_params["user_id"]
    st.session_state["user_name"] = st.query_params.get("user_name", st.query_params["user_id"])

inject_global_styles(light_mode=st.session_state.light_mode)

st.logo(":material/account_balance:")

if "user_id" not in st.session_state:
    pages = {"Authentication": [st.Page("pages/login.py", title="Login", icon=":material/login:", default=True)]}
else:
    pages = {
        "Overview": [
            st.Page("pages/dashboard.py", title="Dashboard", icon=":material/dashboard:", default=True),
            st.Page("pages/transactions.py", title="Transactions", icon=":material/receipt_long:"),
        ],
        "Analysis": [
            st.Page("pages/spending.py", title="Spending", icon=":material/payments:"),
            st.Page("pages/kpis.py", title="KPIs", icon=":material/query_stats:"),
            st.Page("pages/forecasting.py", title="Forecast", icon=":material/trending_up:"),
            st.Page("pages/anomaly.py", title="Anomaly detection", icon=":material/warning:"),
        ],
        "Manage": [
            st.Page("pages/accounts.py", title="Accounts", icon=":material/account_balance_wallet:"),
            st.Page("pages/add_transaction.py", title="Add Transaction", icon=":material/add_circle:"),
            st.Page("pages/scanner.py", title="Receipt Scanner", icon=":material/document_scanner:"),
            st.Page("pages/budgets.py", title="Budgets", icon=":material/account_balance:"),
            st.Page("pages/goals.py", title="Savings Goals", icon=":material/savings:"),
            st.Page("pages/bills.py", title="Bill Reminders", icon=":material/receipt:"),
            st.Page("pages/recurring.py", title="Recurring Txns", icon=":material/autorenew:"),
            st.Page("pages/upload.py", title="Import / Upload", icon=":material/upload:"),
        ],
        "Tools": [
            st.Page("pages/reports.py", title="Reports", icon=":material/description:"),
            st.Page("pages/advisor.py", title="AI advisor", icon=":material/smart_toy:"),
            st.Page("pages/settings.py", title="Settings", icon=":material/settings:"),
        ],
        "Samples": [
            st.Page("pages/samples.py", title="Explore Samples", icon=":material/science:"),
        ],
    }

pg = st.navigation(pages, position="sidebar")

if "user_id" in st.session_state:
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Logged in as:** {st.session_state.user_name}")
    if st.sidebar.button("Log out"):
        del st.session_state["user_id"]
        if "user_name" in st.session_state:
            del st.session_state["user_name"]
        st.query_params.clear()
        st.rerun()

pg.run()
