"""REST API controllers for the PFM application using FastAPI.

Run standalone with:
    cd /home/tanishka-dhanwan/pfm-analytics
    source .venv/bin/activate
    uvicorn pfm.api.main:app --reload --port 8000

Or import the router into an existing FastAPI app.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

try:
    from fastapi import FastAPI, HTTPException, Query, Depends
    from fastapi.middleware.cors import CORSMiddleware
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False
    print("FastAPI not installed. Install with: pip install fastapi uvicorn")

if _FASTAPI_AVAILABLE:
    from pfm.api.routers import transactions, budgets, accounts, goals, bills, dashboard, analytics

    app = FastAPI(
        title="PFM Analytics API",
        description="Personal Finance Management REST API",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
    app.include_router(budgets.router, prefix="/budgets", tags=["Budgets"])
    app.include_router(accounts.router, prefix="/accounts", tags=["Accounts"])
    app.include_router(goals.router, prefix="/goals", tags=["Goals"])
    app.include_router(bills.router, prefix="/bills", tags=["Bills"])
    app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
    app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])

    @app.get("/health")
    def health_check():
        return {"status": "ok", "version": "1.0.0"}
