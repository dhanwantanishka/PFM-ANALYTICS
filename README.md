# Personal Finance Management — Data Analytics

A 45-day internship project building a complete Personal Finance Management (PFM) analytics system: data pipeline, EDA, ML models, and an interactive Streamlit dashboard.

**Stack:** Python 3.10+, Pandas, SQLAlchemy/SQLite, Scikit-learn, XGBoost, Streamlit, Pytest

---

## Project Plan (45 Days)

| Phase | Days | Focus | Status |
|-------|------|-------|--------|
| **1 — Data Engineering** | 1–9 | Ingestion, cleaning, ETL, SQLite storage | ✅ In progress |
| **2 — EDA & KPIs** | 10–18 | Spending analysis, financial KPIs, statistical tests | 🔲 Pending |
| **3 — ML & Anomaly Detection** | 19–27 | Forecasting, Isolation Forest, risk scoring, SHAP | 🔲 Pending |
| **4 — Dashboard** | 28–38 | Multi-page Streamlit app, upload, PDF export, AI chatbot | 🔲 Pending |
| **5 — Testing & Delivery** | 39–45 | 70%+ coverage, docs, report, presentation | 🔲 Pending |

### Deliverable Schedule

| Deliverable | Due | Format |
|-------------|-----|--------|
| GitHub repo + README | Day 3 | GitHub link |
| ETL pipeline + unit tests | Day 9 | Python files |
| EDA notebook + KPI report | Day 18 | Notebook + PDF |
| ML models + SHAP report | Day 27 | `.pkl` + PDF |
| Streamlit dashboard | Day 38 | URL / MP4 |
| Test coverage ≥ 70% | Day 41 | HTML report |
| Project report | Day 43 | PDF |
| Final presentation | Day 45 | PPTX + GitHub tag |

---

## Architecture

```
personal-finance-analytics/
├── data/
│   ├── raw/              # CSV, Excel, JSON inputs
│   ├── processed/        # Cleaned exports
│   └── pfm.db            # SQLite database
├── src/pfm/
│   ├── db/               # SQLAlchemy models
│   ├── ingestion/        # CSV/Excel/JSON loaders
│   ├── cleaning/         # Validation & quality reports
│   ├── features/         # Feature engineering
│   ├── etl/              # ETL pipeline class
│   └── data_generation/  # Faker synthetic data
├── notebooks/            # EDA & KPI analysis (Phase 2)
├── app/                  # Streamlit dashboard (Phase 4)
├── tests/                # Pytest unit tests
└── scripts/              # Seed & utility scripts
```

---

## Quick Start

```bash
# 1. Create virtual environment and install dependencies
make setup

# 2. Generate synthetic data (6,000 transactions, 4 named users, 13 months) and load into SQLite
make seed

# 3. Run tests
make test
```

### Manual Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/seed_data.py
pytest tests/ -v
```

---

## Phase 1 — What's Built

- **Data loaders** for CSV, Excel (OpenPyXL), and JSON
- **SQLite schema** with tables: `transactions`, `categories`, `accounts`, `budgets`
- **Cleaning pipeline**: missing value handling, deduplication, category normalization, business rule validation
- **Feature engineering**: `day_of_week`, `is_weekend`, `month`, `quarter`, `rolling_30d_spend`
- **ETL class** with `extract()`, `transform()`, `load()` methods
- **Synthetic data generator** using Faker — **Rajesh Sharma**, **Priya Singh**, **Amit Kumar**, **Tanishka Dhanwan** (6,000 rows, 13 months, 14 spending categories)
- **Pytest suite** covering 5+ cleaning functions with edge cases

---

## Upcoming Phases

### Phase 2 (Days 10–18)
- Jupyter notebook: spending patterns, MoM/YoY growth, heatmaps
- KPIs: savings rate, DTI, budget variance, emergency fund, 50/30/20 rule
- Correlation matrix, t-test (weekend vs weekday), Pareto analysis

### Phase 3 (Days 19–27)
- Expense forecasting: Linear Regression, Random Forest, XGBoost
- Anomaly detection: Isolation Forest + Z-score
- Financial Health Score + Logistic Regression + SHAP

### Phase 4 (Days 28–38)
- Multi-page Streamlit dashboard (Overview, Spending, KPIs, Forecasting, Anomalies)
- File upload, PDF export, optional AI finance advisor chatbot

---

## Dataset Requirements

| Field | Required |
|-------|----------|
| `transaction_id` | ✅ |
| `date` | ✅ |
| `description` | ✅ |
| `amount` | ✅ |
| `category` | ✅ |
| `account_type` | ✅ |
| `balance_after` | ✅ |
| `is_income` | ✅ |

Minimum: 5,000+ rows, 12+ months, 10+ categories, 2+ accounts.

---

## Evaluation Criteria

| Area | Weight |
|------|--------|
| Code quality & engineering | 20% |
| Data cleaning & pipeline | 15% |
| EDA depth & financial insight | 20% |
| ML model quality | 20% |
| Dashboard usability | 15% |
| Documentation & presentation | 10% |
| Bonus (AI chatbot, SHAP, deployment) | +5% |

---

## License

Confidential — Inventive BizPro Technologies Pvt. Ltd. Internship Assignment 2026.
