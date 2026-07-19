# PFM Analytics — Implementation Checklist

> **Scope:** Phase 1 analysis only. No files were modified during this review.  
> **Reviewed:** `app/`, `src/pfm/`, `tests/`, `requirements.txt`, `.streamlit/config.toml`, `README.md`  
> **Assignment:** 45-day Python internship — Inventive BizPro Technologies Pvt. Ltd.

---

## Legend
- `[x]` Completed / working  
- `[ ]` Missing / not implemented  
- `[~]` Partial / needs improvement  

---

## 1. Completed Features

### 1.1 Data Engineering (Phase 1)
- [x] CSV, Excel, JSON data loaders with automatic format detection
- [x] 11 data cleaning / validation functions
- [x] Feature engineering: `day_of_week`, `is_weekend`, `month`, `quarter`, `rolling_30d_spend`
- [x] ETL pipeline: `extract()` → `transform()` → `load()`
- [x] SQLAlchemy ORM with 5 models and relationships
- [x] Faker-based synthetic data generator (reproducible seed)
- [x] 6,000 transactions — exceeds 5,000 requirement
- [x] 4 users (Rajesh, Priya, Amit, Tanishka)
- [x] 13 months history (Jan 2024–Jan 2025)
- [x] 15 spending categories — exceeds 10 requirement
- [x] 728 budget entries (monthly per user & category)
- [x] Zero missing values in generated data
- [x] `pytest.ini`, `conftest.py`, full test suite (22 tests, 78% coverage)

### 1.2 Analytics Layer (Phase 2)
- [x] `kpi_engine.py` — savings rate, DTI, emergency fund coverage, budget variance, 50/30/20 rule
- [x] `spending_analysis.py` — by category, merchant, month, day-of-week, MoM growth, heatmap data
- [x] `statistical_tests.py` — t-tests, Pareto, correlation, category distribution
- [x] `risk_scorer.py` — 0–100 financial health score with 5 sub-components + recommendations

### 1.3 ML Models (Phase 3)
- [x] `forecaster.py` — Linear Regression, Random Forest, XGBoost with feature engineering
- [x] `anomaly_detector.py` — Isolation Forest + Z-score dual-method detection
- [x] `risk_scorer.py` — `risk_categories()` for at-risk budget categories
- [x] Feature importance export for Random Forest

### 1.4 Streamlit Dashboard (Phase 4)
- [x] Multi-page app using `st.navigation` + `st.Page` (modern API, not legacy `pages/`)
- [x] 10 pages total: Dashboard, Transactions, Spending, KPIs, Forecast, Anomaly, Upload, Reports, AI Advisor, Settings
- [x] Sidebar filters: user selector, date range picker, category multi-select
- [x] Dashboard: welcome message, 6 KPI cards, 6 charts, quick-action buttons, alerts & recommendations
- [x] Spending: treemap, pie+bar combo, merchant leaderboard, DoW heatmap, category trend, Pareto expander
- [x] KPIs: health score gauge, 6 KPI cards, 50/30/20 progress bars, budget variance table, formulae expander
- [x] Forecast: model selector (segmented_control), horizon slider, CI band slider, comparison bar charts, feature importance
- [x] Anomaly: dual-method detection, interactive scatter timeline, severity table, methodology expander
- [x] Upload: CSV/Excel uploader with schema validation, ETL pipeline integration, cache invalidation
- [x] Reports: PDF, Excel (.xlsx multi-sheet), CSV downloads; business summary markdown
- [x] AI Advisor: chat interface, rule-based engine, optional OpenAI API fallback
- [x] Settings: light/dark theme toggle, cache clear, About section, secrets snippet
- [x] Transactions: searchable ledger, type filter, sort options, summary metrics
- [x] Design tokens in `theme/tokens.py` and `theme/styles.py`
- [x] Dark theme configured in `.streamlit/config.toml` (Inter font, custom colors)
- [x] Cached data loading with `@st.cache_data`
- [x] `PageContext` dataclass to share filtered data across pages without duplicating logic

### 1.5 Reporting
- [x] `pdf_report.py` — ReportLab PDF with KPI table, category spend, and Pareto table
- [x] Excel export (multi-sheet: Transactions + Budgets)
- [x] CSV export
- [x] Business summary markdown displayed in Reports page

### 1.6 Code Quality
- [x] `from __future__ import annotations` on all `app/` modules
- [x] Type hints on all public functions
- [x] Docstrings on all public classes and functions
- [x] PEP 8 compliant (no obvious violations found in app/)
- [x] `sys.path` bootstrap kept consistent across page files via `utils/bootstrap.py`

---

## 2. Missing Features

### 2.1 Assignment Requirements Not Yet Met
- [ ] **SHAP feature importance analysis** — `shap` is in `requirements.txt` but no SHAP code exists in `src/pfm/models/`. The forecaster only exposes sklearn `feature_importances_`, not SHAP values. Required for Phase 3 deliverable.
- [ ] **Jupyter notebooks** — `notebooks/` directory is empty (`coming soon`). Phase 2 deliverable requires an EDA notebook with spending patterns, heatmaps, MoM/YoY growth.
- [ ] **Statsmodels integration** — `statsmodels` is in `requirements.txt` but never imported. No time-series decomposition or ARIMA baseline model exists.
- [ ] **XGBoost SHAP explanation** — XGBoost supports native SHAP but it is not connected to the UI.
- [ ] **Dashboard reads SQLite DB** — Streamlit loads from `data/raw/transactions.csv` (raw file), not the SQLite database. The DB schema exists but the dashboard bypasses it entirely.
- [ ] **User-level goal-setting / savings targets** — Assignment mentions financial goals; there is no goal management page or data model.
- [ ] **Statistical tests exposed in the UI** — `statistical_tests.py` has t-tests, Pareto, and correlations, but none are shown in any dashboard page.

### 2.2 Streamlit-Specific Gaps
- [ ] **No `st.fragment` usage** — Forecast and anomaly pages re-train models on every interaction. These should use `st.fragment` to avoid full-page reruns on UI-only changes.
- [ ] **No `ttl` or `max_entries` on cache** — `@st.cache_data` calls in `data_loader.py` have no TTL, causing potential stale data in long-running deployments.
- [ ] **Missing `st.secrets` for database path** — DB path is hard-coded in `src/pfm/config.py`. Should use `st.secrets` or environment variables for production deployability.
- [ ] **`st.logo` receives a Material Symbols string** — `st.logo(":material/account_balance:", text="PFM Analytics")` — Streamlit `st.logo()` expects an image path/URL, not a Material Symbols string. This will likely render incorrectly or log a warning.

---

## 3. UI Improvements

### 3.1 Visual Polish
- [~] **Dashboard welcome section** — Uses plain `st.markdown` + `st.caption`. Could be upgraded to a styled hero banner with the health score prominently displayed.
- [~] **KPI card CSS targets test IDs** — `[data-testid="stMetric"]` selectors in `styles.py` can break on Streamlit updates. Better to use `st.container(border=True)` with explicit layout.
- [~] **Sidebar filter UX** — All filters are inside a single `st.expander`. The user selector is critical and should always be visible, not collapsible.
- [~] **Forecasting page spinner scope** — All three ML models are trained before the user can interact. The heavy `compare_all_models()` trains three models synchronously even if the user only wants metrics for one.
- [ ] **No loading skeleton / progress indicator** for the dashboard's initial data load.
- [ ] **No responsive mobile layout** — Charts use fixed heights (300–460 px); sidebar always expanded on load.
- [ ] **Advisor page full rerun on submit** — `st.rerun()` is called after each message, causing a full-page rerun and scroll-to-top. Use `st.fragment` or append-only pattern.
- [ ] **Transactions page lacks pagination** — Shows up to `height=520px` of a potentially 6,000-row DataFrame with no page-size control.
- [ ] **Reports page PDF generated on every render** — `generate_summary_report()` runs unconditionally on each page load. Should be lazy (inside callback or `st.form`).
- [ ] **`components/states.py` import unverified** — Imported in `upload.py` and `anomaly.py` (`from components.states import render_empty_state`) but the file was not listed in the `app/components/` directory scan. Needs verification.
- [ ] **No breadcrumb / back navigation** — `st.switch_page()` buttons on Dashboard are one-way; no way to return without using the sidebar.

### 3.2 Navigation
- [~] **Page group naming** — "Tools" group contains Upload, Reports, AI Advisor, Settings — consider "Utilities" or splitting into "Export" (Upload + Reports) and "Tools" (Advisor + Settings) for clarity.

---

## 4. Architecture Improvements

### 4.1 Data Layer
- [~] **Dashboard bypasses SQLite** — `load_transactions()` reads `data/raw/transactions.csv` directly. After an Upload→ETL run, new data enters `pfm.db` but the dashboard still reads from the original CSV — the two storage layers are effectively disconnected.
- [~] **Redundant `sys.path` manipulation** — Every page file has its own `sys.path.insert` block in addition to importing `utils.bootstrap`. Pages should rely solely on `bootstrap.py`.
- [ ] **No `pyproject.toml` / editable install** — `src/pfm` is a package but not installed. `sys.path` hacking is required everywhere. A minimal `pyproject.toml` would eliminate this.
- [ ] **`forecasting.py` and `anomaly.py` own filters independently** — Unlike other pages that use `load_page_context()`, these two pages call `render_sidebar_filters` directly, causing filter state divergence when switching pages.
- [ ] **No environment variable management** — `src/pfm/config.py` has hard-coded paths. Production deployments cannot override `DB_PATH` or `RAW_DATA_DIR` without editing source files.

### 4.2 Performance
- [ ] **All three ML models trained on `forecasting.py` load** — `compare_all_models(X, y)` trains LR + RF + XGBoost on every interaction. Should be wrapped with `@st.cache_data` keyed by `(user_id, start_date, end_date)`.
- [ ] **`anomaly.py` runs both detectors unconditionally** — Both Isolation Forest and Z-score always run even when only the severity filter changes (a display-only operation). Use `st.fragment` for the filter controls.
- [ ] **`build_dashboard_summary()` is not cached** — Calls 5+ expensive aggregation functions on every rerun. Should be wrapped in `@st.cache_data`.

### 4.3 Code Organisation
- [~] **`app/services/__init__.py` is nearly empty** — Pattern is correct but service functions are not re-exported, requiring long import paths.
- [ ] **No `__all__` exports** in any `src/pfm` module, making the public API implicit.

---

## 5. Code Quality Improvements

### 5.1 Bugs / Issues
- [ ] **`risk_level` casing mismatch (BUG)** — `risk_categories()` returns `risk_level` values `'HIGH'`, `'MEDIUM'`, `'WATCH'` (all-caps), but `render_alert_cards()` maps color by `{"High": ..., "Medium": ..., "Low": ..., "WATCH": ...}`. `'HIGH'` and `'MEDIUM'` never match their color entries — alert badges will render without color.
- [ ] **Double model training in `forecasting.py` (BUG)** — `compare_all_models()` trains all three models; then the selected model is trained again via `trainers[model_choice](X, y)`. The selected model is trained twice per page load.
- [ ] **`== True` / `== False` comparisons (ANTI-PATTERN)** — Present throughout `src/pfm/` (`kpi_engine.py`, `risk_scorer.py`, `anomaly_detector.py`, `forecaster.py`). Generates `FutureWarning` in newer Pandas and is a PEP 8 violation.
- [ ] **`inplace=True` in `kpi_engine.py`** — `actual.rename(..., inplace=True)` should be `actual = actual.rename(...)`.
- [ ] **`pdf_report.py` HTML entity in ReportLab `Paragraph`** — `&middot;` should be the literal `·` character for robustness across ReportLab versions.
- [ ] **`dashboard.py` unused import** — `render_page_header` is imported from `components.layout` but never called (the page uses a custom `st.markdown` header). The import is dead code.

### 5.2 Testing Gaps
- [~] **No Streamlit page tests** — All existing tests cover `src/pfm/` backend. No tests for `app/` pages, components, or services. Streamlit's `AppTest` framework (`streamlit.testing.v1.AppTest`) should be used.
- [~] **`test_dashboard_metrics.py`** exists but assertions appear minimal — needs expansion.
- [ ] **No test for `pdf_report.py`** — PDF generation is untested. A smoke test verifying non-empty bytes output would suffice.
- [ ] **Coverage target** — Assignment requires ≥70% overall; current 78% excludes `app/`. Including `app/` in coverage measurement will likely drop the headline number.

### 5.3 Deprecation / Best-Practice Issues
- [ ] **`from typing import Dict, Tuple`** in `src/pfm/` modules — Should use built-in `dict` and `tuple` (lowercase) for Python 3.10+. `from __future__ import annotations` is missing from all `src/pfm/` modules.
- [ ] **`is_income == True`/`is_income == False`** comparisons — Replace with `is_income` and `~is_income`.
- [ ] **Plotly `st.plotly_chart` without explicit `key=`** — On pages with multiple identical chart calls, missing keys can cause flicker during reruns.

---

## 6. Summary Table

| Category | Total Items | Completed | Missing/Needs Work |
|---|---|---|---|
| Data Engineering (Phase 1) | 13 | 13 | 0 |
| Analytics / KPIs (Phase 2) | 4 | 4 | 0 |
| ML Models (Phase 3) | 4 | 3 | 1 (SHAP) |
| Streamlit Dashboard (Phase 4) | 17 | 15 | 2 (fragment, caching) |
| UI Polish | 11 | 0 | 11 |
| Architecture | 9 | 0 | 9 |
| Code Quality / Bugs | 12 | 0 | 12 |
| **TOTAL** | **70** | **35** | **35** |

---

## 7. Recommended Priority Order

### High — affects assignment grade / correctness
1. Fix `risk_level` casing bug — `risk_scorer.py` + `kpi_cards.py`
2. Fix double model-training in `forecasting.py`
3. Fix `st.logo` — replace Material Symbols string with image or text fallback
4. Remove unused `render_page_header` import in `dashboard.py`
5. Add SHAP analysis for forecasting models (`src/pfm/models/`) and expose in Forecasting page
6. Expose `statistical_tests.py` results in a dedicated UI section (Spending or new EDA page)

### Medium — production quality
7. Add `@st.cache_data` to `build_dashboard_summary()` and ML model trainers
8. Add `ttl` to `@st.cache_data` calls in `data_loader.py`
9. Wrap ML training and anomaly detection in `st.fragment`
10. Fix `== True`/`== False` anti-patterns in `src/pfm/` modules
11. Connect dashboard data loader to SQLite DB (not just raw CSV)
12. Unify sidebar filter usage — make `forecasting.py` and `anomaly.py` use `load_page_context()`

### Low — polish and completeness
13. Create EDA Jupyter notebook for Phase 2 deliverable
14. Add pagination / row-limit control to Transactions page
15. Make PDF generation lazy (computed only on button click)
16. Add `AppTest`-based Streamlit page tests
17. Update `README.md` project status — Phases 2–4 are substantially implemented
18. Replace `from typing import Dict, Tuple` with built-in types in `src/pfm/` modules
19. Add `pyproject.toml` to eliminate `sys.path` hacking

---

*Generated: 2026-07-19 | Analysed by: Antigravity AI (no files were modified)*
