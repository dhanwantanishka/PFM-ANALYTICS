"""Upload data — CSV/Excel import with validation and preview."""

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
from pfm.etl.pipeline import ETLPipeline
from pfm.ingestion.loaders import load_csv, load_excel, validate_schema
from utils.data_loader import load_transactions

render_page_header(
    "Upload data",
    "Import CSV or Excel files with automatic schema detection and validation.",
    ":material/upload:",
)

uploaded = st.file_uploader(
    "Choose a file",
    type=["csv", "xlsx", "xls"],
    help="Required columns: transaction_id, date, description, amount, category, account_type, balance_after, is_income",
)

if uploaded is None:
    st.info("Upload a transactions file to preview and import.")
    st.stop()

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
summary_col3.metric("Date range", f"{preview_df['date'].min():%d %b %Y} – {preview_df['date'].max():%d %b %Y}" if "date" in preview_df.columns else "—")

if st.button(":material/cloud_upload: Import into database", type="primary"):
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
                st.json({"quality_report": pipeline.quality_report, "schema_issues": pipeline.schema_issues})
            except Exception as exc:
                render_error_state("Import failed", str(exc))
tmp_path.unlink(missing_ok=True)
