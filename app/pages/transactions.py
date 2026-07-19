"""Transactions — fully paginated, searchable, filterable transaction ledger."""

from __future__ import annotations

import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parents[1]
_SRC_DIR = _APP_DIR.parent / "src"
for _p in [str(_APP_DIR), str(_SRC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st
import pandas as pd

import utils.bootstrap  # noqa: F401

from components.layout import render_page_header, render_section
from components.page_context import load_page_context
from pfm.config import DB_PATH
from pfm.db import get_session
from pfm.db.models import Transaction, Account, Category

ctx = load_page_context(require_data=False)
if ctx is None:
    st.stop()

render_page_header(
    "Transactions",
    "Full transaction ledger with search, filters, and pagination.",
    ":material/receipt_long:",
)

df = ctx.filtered.copy()

# ─── Inline search & controls ─────────────────────────────────────────────────
ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([3, 1, 1, 1])
with ctrl1:
    inline_search = st.text_input(
        "Search", placeholder="Description, merchant, category, notes…", label_visibility="collapsed"
    )
with ctrl2:
    sort_order = st.selectbox(
        "Sort", ["Newest first", "Oldest first", "Amount ↑", "Amount ↓"],
        label_visibility="collapsed"
    )
with ctrl3:
    page_size = st.selectbox("Per page", [25, 50, 100, 200], index=1, label_visibility="collapsed")
with ctrl4:
    export_btn = st.button(":material/download: Export CSV", use_container_width=True)

# Apply inline search on top of sidebar filters
if inline_search:
    s = inline_search.lower()
    text_cols = [c for c in ["description", "merchant", "notes", "category"] if c in df.columns]
    mask = df[text_cols].apply(lambda col: col.fillna("").str.lower().str.contains(s, regex=False)).any(axis=1)
    df = df[mask]

# Sort
if sort_order == "Newest first":
    df = df.sort_values("date", ascending=False)
elif sort_order == "Oldest first":
    df = df.sort_values("date", ascending=True)
elif sort_order == "Amount ↑":
    df = df.sort_values("amount", ascending=True)
else:
    df = df.sort_values("amount", ascending=False)

# ─── Summary metrics ──────────────────────────────────────────────────────────
income_total = float(df.loc[df["is_income"], "amount"].sum()) if not df.empty else 0.0
expense_total = float(df.loc[~df["is_income"], "amount"].sum()) if not df.empty else 0.0
net = income_total - expense_total

m1, m2, m3, m4 = st.columns(4)
m1.metric("Transactions", f"{len(df):,}")
m2.metric("Income", f"₹{income_total:,.0f}")
m3.metric("Expenses", f"₹{expense_total:,.0f}")
m4.metric("Net", f"₹{net:,.0f}", delta_color="normal")

# ─── Pagination ───────────────────────────────────────────────────────────────
total_rows = len(df)
total_pages = max(1, (total_rows + page_size - 1) // page_size)

if "txn_page" not in st.session_state:
    st.session_state.txn_page = 1

# Reset page when filters change
if st.session_state.txn_page > total_pages:
    st.session_state.txn_page = 1

page = st.session_state.txn_page
start_idx = (page - 1) * page_size
end_idx = min(start_idx + page_size, total_rows)
page_df = df.iloc[start_idx:end_idx].copy()

# ─── Display ──────────────────────────────────────────────────────────────────
render_section(f"Showing {start_idx + 1}–{end_idx} of {total_rows:,} transactions")

# Format for display
display_cols = ["date", "description", "merchant", "amount", "category", "account_type", "payment_method", "notes"]
display_cols = [c for c in display_cols if c in page_df.columns]
show = page_df[display_cols].copy()
show["date"] = show["date"].dt.strftime("%d %b %Y")
show["amount"] = page_df.apply(
    lambda r: f"{'+ ' if r['is_income'] else '- '}₹{r['amount']:,.2f}", axis=1
)

st.dataframe(
    show.rename(columns={
        "date": "Date", "description": "Description", "merchant": "Merchant",
        "amount": "Amount", "category": "Category", "account_type": "Account",
        "payment_method": "Payment", "notes": "Notes"
    }),
    hide_index=True,
    use_container_width=True,
    height=min(max(len(show) * 38 + 40, 200), 560),
)

# ─── Pagination controls ──────────────────────────────────────────────────────
if total_pages > 1:
    pg_cols = st.columns([1, 1, 3, 1, 1])
    with pg_cols[0]:
        if st.button("⏮ First", disabled=(page == 1), use_container_width=True):
            st.session_state.txn_page = 1
            st.rerun()
    with pg_cols[1]:
        if st.button("◀ Prev", disabled=(page == 1), use_container_width=True):
            st.session_state.txn_page = page - 1
            st.rerun()
    with pg_cols[2]:
        st.markdown(
            f"<p style='text-align:center;margin-top:8px;color:#94A3B8'>"
            f"Page <strong>{page}</strong> of <strong>{total_pages}</strong> "
            f"({total_rows:,} total)</p>",
            unsafe_allow_html=True
        )
    with pg_cols[3]:
        if st.button("Next ▶", disabled=(page == total_pages), use_container_width=True):
            st.session_state.txn_page = page + 1
            st.rerun()
    with pg_cols[4]:
        if st.button("Last ⏭", disabled=(page == total_pages), use_container_width=True):
            st.session_state.txn_page = total_pages
            st.rerun()

# ─── CSV Export ──────────────────────────────────────────────────────────────
if export_btn and not df.empty:
    export_df = df.copy()
    export_df["date"] = export_df["date"].dt.strftime("%Y-%m-%d")
    csv = export_df.to_csv(index=False)
    st.download_button(
        label=":material/download: Download CSV",
        data=csv,
        file_name=f"transactions_{ctx.filters.user_id}.csv",
        mime="text/csv",
        use_container_width=True,
    )
