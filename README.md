# Personal Finance Management — Data Analytics

[![Status](https://img.shields.io/badge/status-complete-brightgreen)]() 
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]() 
[![FastAPI](https://img.shields.io/badge/FastAPI-0.139.2-teal)]()
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-red)]() 
[![SQLite](https://img.shields.io/badge/database-SQLite-lightblue)]() 

> A **45-day Python internship project** building a complete Personal Finance Management (PFM) analytics system: data pipeline, EDA, ML models, REST API, and an interactive dashboard.

**Organization:** Inventive BizPro Technologies Pvt. Ltd. | **Duration:** 45 Days  
**Stack:** Python 3.10+, Pandas, SQLAlchemy, SQLite, Scikit-learn, XGBoost, Streamlit, Pytest

---

## 📋 Table of Contents

- [Overview](#overview)
- [Project Status](#project-status)
- [Architecture](#architecture)
- [Directory Structure](#directory-structure)
- [Quick Start](#quick-start)
- [Phase 1 Deliverables](#phase-1-deliverables)
- [Dataset Overview](#dataset-overview)
- [Testing](#testing)
- [Development Roadmap](#development-roadmap)
- [Tech Stack](#tech-stack)
- [Git Workflow](#git-workflow)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

A comprehensive data analytics platform for personal finance management featuring:

- 💾 **Multi-format data ingestion** — CSV, Excel, JSON with automatic type detection
- 🧹 **Smart data cleaning** — Missing value handling, deduplication, normalization
- 🔄 **ETL pipeline** — Structured extract → transform → load workflow
- 📊 **Feature engineering** — Temporal features, rolling statistics
- 🗄️ **SQLite database** — Persistent storage with SQLAlchemy ORM
- 🧪 **Comprehensive testing** — 97 tests (40 standard + 57 advanced), 80%+ code coverage
- 🎯 **Production-ready code** — Type hints, docstrings, PEP8 compliant

---

## 📈 Project Status

| Phase | Focus | Status | Deliverable |
|-------|-------|--------|-------------|
| **1 — Data Engineering** | Ingestion, cleaning, ETL, SQLite | ✅ COMPLETE | GitHub repo, Database |
| **2 — Core Features** | Real Transactions, Budgets, Goals, Bills | ✅ COMPLETE | Interactive pages |
| **3 — AI & Analytics** | Filters, AI Advisor, Receipt Scanner | ✅ COMPLETE | GenAI Integration |
| **4 — Performance & API**| DB Indexes, FastAPI REST Layer | ✅ COMPLETE | API Endpoints |
| **5 — Testing & Delivery**| UI/UX Polish, Recurring Txns | ✅ COMPLETE | Final Application |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA SOURCES                               │
│   CSV / Excel / JSON / User Input (Forms & Receipt Scanner)     │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                 SQLite Database (pfm.db)                        │
│  Tables: transactions, accounts, categories, budgets,           │
│          goals, bills, recurring_transactions                   │
└────────┬─────────────────────────────┬──────────────────────────┘
         │                             │
         ▼                             ▼
┌──────────────────┐        ┌────────────────────────────────┐
│  API Layer       │        │   ML Pipeline & GenAI          │
│ (FastAPI)        │        │  Forecasting | Anomaly         │
│ /transactions    │        │  OpenAI Vision OCR             │
│ /budgets /goals  │        │  Data-driven LLM Advisor       │
└────────┬─────────┘        └────────────┬───────────────────┘
         │                               │
         └──────────────┬────────────────┘
                        ▼
        ┌──────────────────────────────────────────┐
        │   Streamlit Dashboard (Frontend)         │
        │   Dashboard | Add Transaction | Goals    │
        │   Budgets | Bills | AI Advisor | Scanner │
        └──────────────────────────────────────────┘
```

---

## 📂 Directory Structure

```
personal-finance-analytics/
│
├── 📄 README.md                          # This file
├── 📄 .gitignore                         # Git exclusions
├── 📄 .env.example                       # Environment template
├── 📄 requirements.txt                   # Python dependencies
├── 📄 Makefile                           # Build automation (setup, seed, test)
├── 📄 pytest.ini                         # Pytest configuration
│
├── 📁 data/
│   ├── raw/                              # CSV, Excel, JSON inputs
│   │   ├── transactions.csv              # 6,000 rows, 11 columns
│   │   ├── transactions.xlsx             # Excel format
│   │   ├── transactions.json             # JSON format
│   │   └── budgets.csv                   # 728 budget entries
│   ├── processed/                        # Cleaned datasets
│   ├── synthetic/                        # Generated data
│   └── pfm.db                            # SQLite database (auto-created)
│
├── 📁 src/pfm/                           # Main package
│   ├── __init__.py
│   ├── config.py                         # Configuration, constants, user list
│   │
│   ├── ingestion/                        # Data loading
│   │   ├── loaders.py                    # CSV, Excel, JSON loaders
│   │   └── __init__.py
│   │
│   ├── cleaning/                         # Data validation & cleaning
│   │   ├── validators.py                 # 11 cleaning functions
│   │   └── __init__.py
│   │
│   ├── features/                         # Feature engineering
│   │   ├── engineering.py                # Temporal + rolling features
│   │   └── __init__.py
│   │
│   ├── db/                               # Database layer
│   │   ├── models.py                     # SQLAlchemy ORM (5 classes)
│   │   ├── __init__.py                   # Engine, session factory
│   │   └── __pycache__/
│   │
│   ├── etl/                              # ETL orchestration
│   │   ├── pipeline.py                   # Main ETL class
│   │   └── __init__.py
│   │
│   ├── analytics/                        # (Phase 2) KPI & EDA
│   │   └── __init__.py
│   │
│   ├── models/                           # (Phase 3) ML models
│   │   └── __init__.py
│   │
│   └── _pycache__/
│
├── 📁 notebooks/                         # Jupyter notebooks (Phase 2+)
│   └── (coming soon)
│
├── 📁 tests/                             # Pytest suite
│   ├── test_cleaning.py                  # 11 cleaning function tests
│   ├── test_loaders.py                   # Loader tests
│   ├── test_etl.py                       # ETL pipeline tests
│   ├── test_synthetic.py                 # Synthetic data validation
│   ├── conftest.py                       # Pytest fixtures
│   ├── _pycache__/
│   └── __pycache__/
│
├── 📁 scripts/
│   └── seed_data.py                      # Generate + load synthetic data
│
├── 📁 models/                            # (Phase 3+) Serialized .pkl files
│
├── 📁 reports/                           # (Phase 4+) PDF exports, coverage
│   └── htmlcov/                          # Coverage report (auto-generated)
│
└── 📁 .venv/                             # Virtual environment (git-ignored)
```

---

## 🚀 Quick Start

### Prerequisites
```bash
✓ Python 3.10+
✓ Git
✓ Terminal/Command line
```

### Installation (3 steps)

```bash
# 1️⃣  Navigate to project
cd personal-finance-analytics

# 2️⃣  Create virtual environment & install dependencies
make setup
# Equivalent: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

# 3️⃣  Generate synthetic data + load into SQLite
make seed
# Output: 6,000 transactions loaded to data/pfm.db
```

### Verify Installation & Start App

```bash
# Start the backend API
uvicorn src.pfm.api.main:app --reload --port 8000

# Start the frontend dashboard (in a separate terminal)
streamlit run app/main.py --server.port 8502
```

### Manual Setup (Alternative)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/seed_data.py
pytest tests/ -v
```

---

## ✅ Phase 1 Deliverables (Complete)

### Code & Infrastructure
- ✅ **Data loaders** — CSV, Excel (OpenPyXL), JSON with automatic format detection
- ✅ **Validation layer** — Business rule checks, data quality reports
- ✅ **Cleaning pipeline** — Missing values (median imputation), deduplication, category normalization
- ✅ **Feature engineering** — `day_of_week`, `is_weekend`, `month`, `quarter`, `rolling_30d_spend`
- ✅ **ETL orchestrator** — `extract()` → `transform()` → `load()` pattern
- ✅ **SQLite schema** — 5 ORM models with relationships and constraints
- ✅ **Synthetic data generator** — Faker-based, reproducible seeding

### Data Quality
- ✅ **6,000 transactions** — Meets 5,000+ requirement
- ✅ **4 named users** — Rajesh Sharma, Priya Singh, Amit Kumar, Tanishka Dhanwan
- ✅ **13 months history** — Jan 2024 to Jan 2025 (meets 12+ requirement)
- ✅ **15 spending categories** — Meets 10+ requirement
- ✅ **3 account types** — Checking, savings, credit (balanced distribution)
- ✅ **Zero missing values** — Perfect data quality across all fields
- ✅ **728 budget entries** — Monthly targets per user & category

### Testing & Quality Assurance
- ✅ **22 tests passing** — 100% success rate
- ✅ **78% code coverage** — 90% in src/pfm/ package
- ✅ **100% type hints** — Full type annotations in core modules
- ✅ **85%+ docstrings** — Documented functions and classes
- ✅ **PEP8 compliant** — Code quality standards met

---

## 📊 Dataset Overview

| Metric | Value | Requirement | Status |
|--------|-------|-------------|--------|
| **Transactions** | 6,000 rows | 5,000+ | ✅ |
| **Date Range** | 2024-01-01 to 2025-01-31 | 12+ months | ✅ |
| **Users** | 4 (Rajesh, Priya, Amit, Tanishka) | 2+ | ✅ |
| **Categories** | 15 categories | 10+ | ✅ |
| **Account Types** | 3 (checking, savings, credit) | 2+ | ✅ |
| **Missing Values** | 0 | None | ✅ |
| **Amount Range** | $5.17 – $4,498.29 | Realistic | ✅ |
| **Income Transactions** | 513 (8.6%) | Variable | ✅ |
| **Expense Transactions** | 5,487 (91.4%) | Variable | ✅ |
| **Budget Entries** | 728 | Complete | ✅ |

### Category Distribution
```
Housing (775)          ████████████████████ 12.9%
Groceries (658)        █████████████████ 11.0%
Dining (597)           ███████████████ 10.0%
Entertainment (583)    ███████████████ 9.7%
Income (513)           ████████████ 8.6%
Utilities (426)        ███████████ 7.1%
Transportation (401)   ██████████ 6.7%
Insurance (385)        ██████████ 6.4%
[Others: 664 rows]
```

---

## 🧪 Testing

The codebase features two test suites: the standard unit/integration test suite, and the advanced end-to-end integration and boundary stress test suite.

### Standard Test Suite
```bash
# Run standard unit tests
source .venv/bin/activate
PYTHONPATH=. pytest tests/ -v
```

### Advanced Stress Test Suite
```bash
# Run advanced integration & boundary stress tests
source .venv/bin/activate
PYTHONPATH=. pytest tests/test_advanced.py -v
```

### Coverage & Verification
```bash
# Run all tests with coverage reporting
make test

# View coverage report
open htmlcov/index.html      # macOS
firefox htmlcov/index.html   # Linux
```

**Test Results:**
```
✅ 97/97 tests passing (40 Standard, 57 Advanced)
✅ 80%+ overall code coverage
✅ All domains validated: ingestion, ETL, schema validation, multi-tenant isolation, ML models, API controllers
```

---

## ✅ Final Deliverables (Phases 1-5 Complete)

### Backend & API
- ✅ **FastAPI Integration**: Robust RESTful API covering all resources (`/transactions`, `/budgets`, `/goals`, `/bills`, `/dashboard`).
- ✅ **Database Enhancements**: Expanded ORM schema tracking goals, bills, and recurring transactions with 10 performance indexes.

### Core Features
- ✅ **Transactions**: Manual entry, auto-categorization, Receipt Scanner (OCR).
- ✅ **Budgets**: Real-time spending progress bars, 80% usage warnings, and over-budget alerts.
- ✅ **Savings Goals**: Target dates, progress metrics, and inline additions.
- ✅ **Bill Reminders**: Automated sorting (Overdue, Due Soon, Upcoming) and recurring expense scheduling.

### AI & Analytics
- ✅ **AI Advisor**: GenAI chat powered by your actual SQLite data for highly personalized financial insights.
- ✅ **Advanced Filters**: Dynamic global filters (Date Presets, Income/Expense, Multi-search) applied across all dashboards.
- ✅ **Forecasting & Anomalies**: ML-driven (Random Forest/XGBoost) expense projections and Isolation Forest fraud detection.

### UI/UX
- ✅ **Streamlit 1.30+**: Premium responsive design, multi-page sidebar navigation, dynamic Plotly charts (auto-sizing), and pagination.

---

## 🛠️ Tech Stack

| Category | Tools | Version |
|----------|-------|---------|
| **Language** | Python | 3.10+ |
| **Data** | Pandas, NumPy | 2.0+, 1.24+ |
| **Excel** | OpenPyXL | 3.1+ |
| **Database** | SQLite, SQLAlchemy | 2.0+ |
| **Testing** | Pytest, Coverage | 7.4+, 4.1+ |
| **Visualization** | Matplotlib, Seaborn, Plotly | 3.7+, 0.13+, 5.18+ |
| **ML** | Scikit-learn, XGBoost, Statsmodels, SHAP | 1.3+, 2.0+, 0.14+, 0.44+ |
| **Dashboard** | Streamlit | 1.30+ |
| **Data Gen** | Faker | 22.0+ |
| **Utilities** | python-dotenv, PyYAML | 1.0+, 6.0+ |

---

## 📌 Git Workflow

### Initial Setup (Day 1)
```bash
git init
git config user.name "Your Name"
git config user.email "your@email.com"
git add .
git commit -m "chore: initialize phase 1"
```

### Daily Commits
```bash
git add src/
git commit -m "feat(etl): add CSV extractor with type inference"
git push origin main
```

### Branching Strategy
```bash
main          ← production-ready (v0.1-phase1)
├── develop   ← integration branch
├── feature/phase2-eda
├── feature/phase3-ml
└── feature/phase4-dashboard
```

### Push to GitHub
```bash
git remote add origin https://github.com/dhanwantanishka/PFM-ANALYTICS.git
git branch -M main
git push -u origin main
git push origin v0.1-phase1  # Tag
```

---

## ⚙️ Configuration

### Setup Environment Variables

```bash
# Copy template
cp .env.example .env

# Edit .env with your values
cat .env
```

**Example .env:**
```
DB_PATH=data/pfm.db
RANDOM_SEED=42
LOG_LEVEL=INFO
RAW_DATA_DIR=data/raw
FAKER_SEED=42
STREAMLIT_SERVER_PORT=8501
```

---

## 🔧 Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'pfm'`
**Solution:**
```bash
# Make sure you're in project root
cd personal-finance-analytics

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Issue: `sqlite3.OperationalError: database is locked`
**Solution:**
```bash
# Close any open connections, then reset database
rm data/pfm.db
make seed  # Regenerate
```

### Issue: Tests fail with import errors
**Solution:**
```bash
# Update PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Or run pytest from project root
cd ~/personal-finance-analytics
pytest tests/ -v
```

### Issue: `make` command not found
**Solution:**
```bash
# Install make
sudo apt-get install build-essential  # Linux
brew install make                      # macOS

# Or run commands manually
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/seed_data.py
```

---

## 📞 Support & Resources

- **Blueprint:** `PFM_Master_Blueprint.md` — 45-day roadmap with detailed requirements
- **Addendum:** `PFM_Analytics_Master_Blueprint_Addendum_v1_1.md` — Additional specifications
- **Tests:** `tests/` folder — See test examples for usage patterns
- **Database:** `sqlite3 data/pfm.db` — Inspect schema and data

---

## 📄 License

Confidential — **Inventive BizPro Technologies Pvt. Ltd.** | Internship Assignment 2026

---

## ✨ Acknowledgments

- **Synthetic data:** Faker library with seeded randomization
- **Database:** SQLAlchemy ORM for elegant SQL abstraction
- **Testing:** Pytest framework with comprehensive coverage reporting
- **Code quality:** Type hints, docstrings, and PEP8 compliance

---

## 📍 Status Summary

```
╔════════════════════════════════════════════════════════════════╗
║  ALL PHASES COMPLETE: ✅ FINISHED                              ║
╠════════════════════════════════════════════════════════════════╣
║  Frontend (Streamlit) ✅  Dashboard, OCR, Budgets, AI Advisor  ║
║  Backend (FastAPI)    ✅  REST API, Pydantic, Pagination       ║
║  Database (SQLite)    ✅  7 models, 10 indexes, Live tracking  ║
║  Machine Learning     ✅  XGBoost, Isolation Forest, GPT-4o    ║
╚════════════════════════════════════════════════════════════════╝
```

---

**Last Updated:** July 2026 | **Project Status:** ✅ COMPLETE  
**Project:** [PFM-ANALYTICS](https://dhanwantanishka-pfm-analytics-appmain-lymgxe.streamlit.app/)
