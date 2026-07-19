"""Individual router module files for FastAPI."""
# budgets.py
try:
    from fastapi import APIRouter
    from pfm.api.routers.stubs import budgets_router as router
except Exception:
    router = None
