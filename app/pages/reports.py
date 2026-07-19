"""Reports — PDF, Excel, CSV export and business summary."""

from __future__ import annotations

import sys
from datetime import datetime

import streamlit as st

import utils.bootstrap  # noqa: F401

from components.layout import render_page_header, render_section
from components.page_context import load_page_context
from pfm.models.risk_scorer import financial_health_score
from services.reports_export import business_summary_markdown, export_csv, export_excel, export_pdf

ctx = load_page_context()
if ctx is None:
    st.stop()

render_page_header(
    "Reports",
    "Export financial summaries in PDF, Excel, or CSV format.",
    ":material/description:",
)

health = financial_health_score(ctx.filtered, ctx.budgets, ctx.filters.user_id)
income = float(ctx.filtered.loc[ctx.filtered["is_income"], "amount"].sum())
expenses = float(ctx.filtered.loc[~ctx.filtered["is_income"], "amount"].sum())
savings_rate_pct = round((income - expenses) / income * 100, 1) if income > 0 else 0.0

render_section("Business summary")
st.markdown(
    business_summary_markdown(
        ctx.filtered,
        ctx.filters.user_name,
        health["overall_score"],
        savings_rate_pct,
    )
)

render_section("Export options")
col1, col2, col3 = st.columns(3)

with col1:
    pdf_bytes = export_pdf(ctx.filtered, ctx.budgets, ctx.filters.user_id, ctx.filters.user_name)
    st.download_button(
        ":material/picture_as_pdf: Download PDF report",
        data=pdf_bytes.getvalue(),
        file_name=f"pfm_report_{ctx.filters.user_id}_{datetime.now():%Y%m%d}.pdf",
        mime="application/pdf",
        width="stretch",
    )

with col2:
    excel_bytes = export_excel(ctx.filtered, ctx.budgets)
    st.download_button(
        ":material/table_chart: Download Excel workbook",
        data=excel_bytes,
        file_name=f"pfm_data_{ctx.filters.user_id}_{datetime.now():%Y%m%d}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
    )

with col3:
    csv_bytes = export_csv(ctx.filtered)
    st.download_button(
        ":material/download: Download CSV",
        data=csv_bytes,
        file_name=f"transactions_{ctx.filters.user_id}_{datetime.now():%Y%m%d}.csv",
        mime="text/csv",
        width="stretch",
    )

render_section("Chart data export")
chart_export = ctx.filtered[["date", "description", "amount", "category", "is_income"]].copy()
chart_export["date"] = chart_export["date"].dt.strftime("%Y-%m-%d")
st.download_button(
    ":material/bar_chart: Export chart-ready CSV",
    data=export_csv(chart_export),
    file_name=f"chart_data_{datetime.now():%Y%m%d}.csv",
    mime="text/csv",
)
