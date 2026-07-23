"""Upload data — CSV/Excel import with validation, preview, and raw file management."""

from __future__ import annotations

import sys
from pathlib import Path
import tempfile

_APP_DIR = Path(__file__).resolve().parents[1]
_SRC = _APP_DIR.parent / "src"
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import pandas as pd
import streamlit as st

from components.layout import render_page_header, render_section
from components.states import render_error_state
from pfm.config import DB_PATH, RAW_DATA_DIR
from pfm.db import get_session
from pfm.db.models import Account, Transaction
from pfm.etl.pipeline import ETLPipeline
from pfm.ingestion.loaders import load_csv, load_excel, validate_schema
from utils.data_loader import load_transactions

render_page_header(
    "Import / Upload Data",
    "Upload new CSV/Excel files, preview schema validation, or manage existing data files.",
    ":material/upload:",
)

tab_upload, tab_manage = st.tabs(
    [":material/cloud_upload: Upload & Import", ":material/folder: Manage Data Files & Database"]
)

with tab_upload:
    uploaded = st.file_uploader(
        "Choose a transaction file",
        type=["csv", "xlsx", "xls"],
        help="Required columns: transaction_id, date, description, amount, category, account_type, balance_after, is_income",
    )

    if uploaded is not None:
        suffix = Path(uploaded.name).suffix.lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded.getvalue())
            tmp_path = Path(tmp.name)

        try:
            if suffix == ".csv":
                preview_df = load_csv(tmp_path)
                fmt = "csv"
            else:
                preview_df = load_excel(tmp_path)
                fmt = "excel"
        except Exception as exc:
            render_error_state("Failed to read file", str(exc))
            tmp_path.unlink(missing_ok=True)
            st.stop()

        schema = validate_schema(preview_df)
        render_section("Schema validation")
        if schema["missing_columns"]:
            st.error(f"Missing required columns: {', '.join(schema['missing_columns'])}")
        else:
            st.success("All required columns detected.")

        for warning in schema.get("warnings", []):
            st.warning(warning)

        render_section("Preview")
        st.dataframe(preview_df.head(20), hide_index=True, width="stretch")

        summary_col1, summary_col2, summary_col3 = st.columns(3)
        summary_col1.metric("Rows", len(preview_df))
        summary_col2.metric("Columns", len(preview_df.columns))
        summary_col3.metric(
            "Date range",
            f"{preview_df['date'].min():%d %b %Y} – {preview_df['date'].max():%d %b %Y}"
            if "date" in preview_df.columns
            else "—",
        )

        col_imp, col_save = st.columns([1, 1])
        with col_imp:
            if st.button(":material/cloud_upload: Import into database", type="primary", width="stretch"):
                if schema["missing_columns"]:
                    st.error("Fix schema issues before importing.")
                else:
                    with st.spinner("Running ETL pipeline..."):
                        try:
                            pipeline = ETLPipeline()
                            pipeline.extract(tmp_path, fmt=fmt)

                            # Assign to current user
                            if "user_id" in st.session_state:
                                pipeline.raw_df["user_id"] = st.session_state.user_id

                            pipeline.transform()
                            count = pipeline.load()
                            load_transactions.clear()
                            st.success(f"Successfully imported {count:,} transactions.")
                            st.json(
                                {
                                    "quality_report": pipeline.quality_report,
                                    "schema_issues": pipeline.schema_issues,
                                }
                            )
                        except Exception as exc:
                            render_error_state("Import failed", str(exc))

        with col_save:
            if st.button(":material/save: Save to data/raw/", type="secondary", width="stretch"):
                target_path = RAW_DATA_DIR / uploaded.name
                RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
                target_path.write_bytes(uploaded.getvalue())
                st.success(f"Saved file as `{uploaded.name}` in `data/raw/`.")

        tmp_path.unlink(missing_ok=True)
    else:
        st.info("Upload a transactions CSV/Excel file above to preview and import.")

with tab_manage:
    render_section("Raw Data Files in `data/raw/`")
    if RAW_DATA_DIR.exists():
        raw_files = [f for f in RAW_DATA_DIR.iterdir() if f.is_file() and not f.name.startswith(".")]
    else:
        raw_files = []

    if not raw_files:
        st.info("No raw data files found in `data/raw/`.")
    else:
        for file_path in raw_files:
            size_kb = file_path.stat().st_size / 1024.0
            size_str = f"{size_kb / 1024.0:.2f} MB" if size_kb > 1024 else f"{size_kb:.1f} KB"
            ext = file_path.suffix.lower()

            icon = "📄"
            if ext in [".csv"]:
                icon = "📊"
            elif ext in [".xlsx", ".xls"]:
                icon = "📈"
            elif ext in [".json"]:
                icon = "📋"

            with st.container(border=True):
                col1, col2, col3 = st.columns([4, 2, 2])
                with col1:
                    st.markdown(f"**{icon} {file_path.name}**")
                    st.caption(f"Path: `{file_path}`")
                with col2:
                    st.caption(f"Size: {size_str}")
                with col3:
                    if st.button("Delete CSV/File", key=f"del_file_{file_path.name}", type="secondary"):
                        st.session_state[f"confirm_del_file_{file_path.name}"] = True

                if st.session_state.get(f"confirm_del_file_{file_path.name}"):
                    st.warning(f"⚠️ Are you sure you want to delete `{file_path.name}` from disk?")
                    c_yes, c_no = st.columns(2)
                    with c_yes:
                        if st.button("Yes, delete file", key=f"yes_del_file_{file_path.name}", type="primary"):
                            try:
                                file_path.unlink(missing_ok=True)
                                del st.session_state[f"confirm_del_file_{file_path.name}"]
                                st.success(f"Deleted `{file_path.name}`.")
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Failed to delete file: {exc}")
                    with c_no:
                        if st.button("Cancel", key=f"no_del_file_{file_path.name}"):
                            del st.session_state[f"confirm_del_file_{file_path.name}"]
                            st.rerun()

    st.markdown("---")
    render_section("Database Transactions Management")
    st.caption("Purge transactions belonging to the currently logged in user.")

    cur_user = st.session_state.get("user_id", "user_1")
    if st.button(f":material/delete_forever: Purge all transactions for {cur_user}", type="secondary"):
        st.session_state["confirm_purge_txns"] = True

    if st.session_state.get("confirm_purge_txns"):
        st.warning(f"⚠️ Danger Zone: Delete ALL transactions for **{cur_user}**?")
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            if st.button("Yes, purge transactions", type="primary"):
                session = get_session(DB_PATH)
                try:
                    user_accounts = session.query(Account).filter(Account.user_id == cur_user).all()
                    acct_ids = [a.id for a in user_accounts]

                    if acct_ids:
                        session.query(Transaction).filter(Transaction.account_id.in_(acct_ids)).delete(
                            synchronize_session=False
                        )

                    session.commit()
                    load_transactions.clear()
                    del st.session_state["confirm_purge_txns"]
                    st.success("All transactions purged successfully.")
                    st.rerun()
                except Exception as exc:
                    session.rollback()
                    st.error(f"Error purging transactions: {exc}")
                finally:
                    session.close()
        with c_p2:
            if st.button("Cancel purge"):
                del st.session_state["confirm_purge_txns"]
                st.rerun()

