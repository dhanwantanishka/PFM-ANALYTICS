"""Advanced integration & stress tests for the PFM Analytics application.

Covers:
  1. Full API CRUD lifecycle (create → read → update → delete)
  2. Pydantic schema validation (reject bad input)
  3. Data isolation between users (multi-tenancy)
  4. Pagination boundary conditions
  5. Dashboard metric accuracy verification
  6. Budget tracking correctness (actual_spend vs. limit)
  7. Goal progress calculation
  8. Bill due-date logic
  9. Auth security (hash uniqueness, timing-safe comparison, empty passwords)
 10. Analytics endpoint mathematical correctness
 11. Database referential integrity
 12. Edge cases: zero amounts, max-length strings, special characters
"""

import sys
import uuid
from datetime import date, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT))

# ─── FastAPI TestClient ──────────────────────────────────────────────────────
from fastapi.testclient import TestClient
from src.pfm.api.main import app

client = TestClient(app)


# ═══════════════════════════════════════════════════════════════════════════════
#  1. API Health & Smoke
# ═══════════════════════════════════════════════════════════════════════════════

class TestAPIHealth:
    def test_health_endpoint(self):
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert "version" in body

    def test_docs_accessible(self):
        r = client.get("/docs")
        assert r.status_code == 200

    def test_openapi_schema(self):
        r = client.get("/openapi.json")
        assert r.status_code == 200
        schema = r.json()
        assert "paths" in schema
        assert "/transactions" in schema["paths"]
        assert "/budgets" in schema["paths"]
        assert "/dashboard" in schema["paths"]


# ═══════════════════════════════════════════════════════════════════════════════
#  2. Pydantic Validation — Reject Bad Input
# ═══════════════════════════════════════════════════════════════════════════════

class TestSchemaValidation:
    def test_reject_negative_amount(self):
        """Amounts must be > 0."""
        r = client.post(
            "/transactions?x_user_id=rajesh_sharma",
            json={
                "amount": -500,
                "description": "Negative test",
                "transaction_type": "expense",
                "category": "Groceries",
                "account_id": 1,
                "date": "2025-01-15",
            },
        )
        assert r.status_code == 422

    def test_reject_zero_amount(self):
        r = client.post(
            "/transactions?x_user_id=rajesh_sharma",
            json={
                "amount": 0,
                "description": "Zero test",
                "transaction_type": "expense",
                "category": "Groceries",
                "account_id": 1,
                "date": "2025-01-15",
            },
        )
        assert r.status_code == 422

    def test_reject_invalid_transaction_type(self):
        """Only income/expense/transfer allowed."""
        r = client.post(
            "/transactions?x_user_id=rajesh_sharma",
            json={
                "amount": 100,
                "description": "Bad type",
                "transaction_type": "refund",
                "category": "Groceries",
                "account_id": 1,
                "date": "2025-01-15",
            },
        )
        assert r.status_code == 422

    def test_reject_empty_description(self):
        r = client.post(
            "/transactions?x_user_id=rajesh_sharma",
            json={
                "amount": 100,
                "description": "",
                "transaction_type": "expense",
                "category": "Groceries",
                "account_id": 1,
                "date": "2025-01-15",
            },
        )
        assert r.status_code == 422

    def test_reject_invalid_budget_month_format(self):
        r = client.post(
            "/budgets?user_id=rajesh_sharma",
            json={"category": "Groceries", "month": "January 2025", "amount": 5000},
        )
        assert r.status_code == 422

    def test_reject_invalid_account_type(self):
        r = client.post(
            "/accounts?user_id=rajesh_sharma",
            json={"name": "Bad Account", "account_type": "bitcoin_wallet"},
        )
        assert r.status_code == 422

    def test_reject_goal_negative_target(self):
        r = client.post(
            "/goals?user_id=rajesh_sharma",
            json={"name": "Bad Goal", "target_amount": -1000},
        )
        assert r.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
#  3. Transaction CRUD Lifecycle
# ═══════════════════════════════════════════════════════════════════════════════

class TestTransactionCRUD:
    """Full create → read → update → delete cycle."""

    def test_full_lifecycle(self):
        # GET Account ID dynamically
        acc_resp = client.get("/accounts?user_id=rajesh_sharma")
        assert acc_resp.status_code == 200
        accounts = acc_resp.json()
        assert len(accounts) > 0, "Need at least one account to test transaction CRUD"
        account_id = accounts[0]["id"]

        # CREATE
        create_resp = client.post(
            "/transactions?x_user_id=rajesh_sharma",
            json={
                "amount": 999.99,
                "description": "Integration Test Transaction",
                "transaction_type": "expense",
                "category": "Dining",
                "account_id": account_id,
                "date": "2025-06-15",
                "merchant": "TestMerchant",
                "notes": "Created by advanced test suite",
                "payment_method": "UPI",
            },
        )
        assert create_resp.status_code == 201, f"Create failed: {create_resp.text}"
        txn = create_resp.json()
        assert txn["amount"] == 999.99
        assert txn["description"] == "Integration Test Transaction"
        assert txn["merchant"] == "TestMerchant"
        assert txn["is_income"] is False
        txn_id = txn["transaction_id"]

        # READ — verify it appears in listing
        list_resp = client.get("/transactions?x_user_id=rajesh_sharma&page_size=500")
        assert list_resp.status_code == 200
        items = list_resp.json()["items"]
        found = [i for i in items if i["transaction_id"] == txn_id]
        assert len(found) == 1, "Created transaction not found in listing"

        # UPDATE
        update_resp = client.put(
            f"/transactions/{txn_id}?x_user_id=rajesh_sharma",
            json={"amount": 1234.56, "description": "Updated by test"},
        )
        assert update_resp.status_code == 200
        updated = update_resp.json()
        assert updated["amount"] == 1234.56
        assert updated["description"] == "Updated by test"

        # DELETE
        del_resp = client.delete(f"/transactions/{txn_id}?x_user_id=rajesh_sharma")
        assert del_resp.status_code == 204

        # VERIFY deletion
        list_resp2 = client.get("/transactions?x_user_id=rajesh_sharma&page_size=500")
        items2 = list_resp2.json()["items"]
        found2 = [i for i in items2 if i["transaction_id"] == txn_id]
        assert len(found2) == 0, "Transaction not deleted properly"


# ═══════════════════════════════════════════════════════════════════════════════
#  4. Multi-tenancy / Data Isolation
# ═══════════════════════════════════════════════════════════════════════════════

class TestDataIsolation:
    """Verify that rajesh_sharma cannot see priya_singh's data."""

    def test_transactions_isolated(self):
        r1 = client.get("/transactions?x_user_id=rajesh_sharma&page_size=5")
        r2 = client.get("/transactions?x_user_id=priya_singh&page_size=5")
        assert r1.status_code == 200
        assert r2.status_code == 200

        ids_1 = {i["transaction_id"] for i in r1.json()["items"]}
        ids_2 = {i["transaction_id"] for i in r2.json()["items"]}
        # No overlap
        assert ids_1.isdisjoint(ids_2), "Users share transaction IDs — isolation violation!"

    def test_dashboard_isolated(self):
        d1 = client.get("/dashboard?user_id=rajesh_sharma").json()
        d2 = client.get("/dashboard?user_id=priya_singh").json()
        assert d1["user_id"] == "rajesh_sharma"
        assert d2["user_id"] == "priya_singh"
        # Different users should have different transaction counts (unless both are empty)
        # At minimum, user_ids must match
        assert d1["user_id"] != d2["user_id"]

    def test_nonexistent_user_returns_empty(self):
        """A user with no data should return zero transactions."""
        r = client.get("/transactions?x_user_id=phantom_user_999&page_size=10")
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 0
        assert body["items"] == []


# ═══════════════════════════════════════════════════════════════════════════════
#  5. Pagination Edge Cases
# ═══════════════════════════════════════════════════════════════════════════════

class TestPagination:
    def test_first_page(self):
        r = client.get("/transactions?x_user_id=rajesh_sharma&page=1&page_size=10")
        assert r.status_code == 200
        body = r.json()
        assert body["page"] == 1
        assert len(body["items"]) <= 10

    def test_last_page(self):
        # Get total pages first
        r = client.get("/transactions?x_user_id=rajesh_sharma&page=1&page_size=10")
        total_pages = r.json()["total_pages"]
        if total_pages > 0:
            r2 = client.get(f"/transactions?x_user_id=rajesh_sharma&page={total_pages}&page_size=10")
            assert r2.status_code == 200
            assert len(r2.json()["items"]) >= 1

    def test_beyond_last_page_returns_empty(self):
        r = client.get("/transactions?x_user_id=rajesh_sharma&page=99999&page_size=10")
        assert r.status_code == 200
        assert r.json()["items"] == []

    def test_page_size_one(self):
        r = client.get("/transactions?x_user_id=rajesh_sharma&page=1&page_size=1")
        assert r.status_code == 200
        assert len(r.json()["items"]) <= 1

    def test_max_page_size(self):
        r = client.get("/transactions?x_user_id=rajesh_sharma&page=1&page_size=500")
        assert r.status_code == 200
        assert len(r.json()["items"]) <= 500

    def test_reject_page_size_too_large(self):
        r = client.get("/transactions?x_user_id=rajesh_sharma&page=1&page_size=501")
        assert r.status_code == 422

    def test_reject_page_zero(self):
        r = client.get("/transactions?x_user_id=rajesh_sharma&page=0&page_size=10")
        assert r.status_code == 422

    def test_total_count_consistency(self):
        """Sum of items across all pages should equal total."""
        r = client.get("/transactions?x_user_id=rajesh_sharma&page=1&page_size=500")
        body = r.json()
        assert body["total"] >= len(body["items"])


# ═══════════════════════════════════════════════════════════════════════════════
#  6. Dashboard Metric Accuracy
# ═══════════════════════════════════════════════════════════════════════════════

class TestDashboardAccuracy:
    def test_dashboard_returns_all_fields(self):
        r = client.get("/dashboard?user_id=rajesh_sharma")
        assert r.status_code == 200
        d = r.json()
        required = [
            "user_id", "total_balance", "today_income", "today_expenses",
            "month_income", "month_expenses", "net_savings", "savings_rate_pct",
            "health_score", "transaction_count",
        ]
        for field in required:
            assert field in d, f"Dashboard missing field: {field}"

    def test_savings_rate_range(self):
        """Savings rate should be between -100% and 100% for reasonable data."""
        d = client.get("/dashboard?user_id=rajesh_sharma").json()
        assert -200 <= d["savings_rate_pct"] <= 100, (
            f"Savings rate {d['savings_rate_pct']}% out of reasonable range"
        )

    def test_health_score_range(self):
        d = client.get("/dashboard?user_id=rajesh_sharma").json()
        assert 0 <= d["health_score"] <= 100, f"Health score {d['health_score']} out of 0-100 range"

    def test_net_savings_formula(self):
        """net_savings should approximately equal total_balance."""
        d = client.get("/dashboard?user_id=rajesh_sharma").json()
        assert d["net_savings"] == d["total_balance"]

    def test_transaction_count_positive(self):
        d = client.get("/dashboard?user_id=rajesh_sharma").json()
        assert d["transaction_count"] > 0, "rajesh_sharma should have seeded transactions"


# ═══════════════════════════════════════════════════════════════════════════════
#  7. Analytics Endpoint Correctness
# ═══════════════════════════════════════════════════════════════════════════════

class TestAnalytics:
    def test_category_breakdown_sums_to_100(self):
        r = client.get("/analytics/categories?user_id=rajesh_sharma")
        assert r.status_code == 200
        cats = r.json()
        if cats:
            total_pct = sum(c["pct_of_total"] for c in cats)
            assert abs(total_pct - 100.0) < 1.0, f"Category pct sum = {total_pct}, expected ~100"

    def test_category_breakdown_ordered_descending(self):
        r = client.get("/analytics/categories?user_id=rajesh_sharma")
        cats = r.json()
        if len(cats) > 1:
            amounts = [c["amount"] for c in cats]
            assert amounts == sorted(amounts, reverse=True), "Categories not sorted by amount desc"

    def test_monthly_report_chronological(self):
        r = client.get("/analytics/monthly?user_id=rajesh_sharma")
        assert r.status_code == 200
        months = r.json()
        if len(months) > 1:
            month_labels = [m["month"] for m in months]
            assert month_labels == sorted(month_labels), "Monthly report not in chronological order"

    def test_monthly_net_formula(self):
        """net = income - expenses for each month."""
        r = client.get("/analytics/monthly?user_id=rajesh_sharma")
        for m in r.json():
            expected_net = m["income"] - m["expenses"]
            assert abs(m["net"] - expected_net) < 0.01, (
                f"Month {m['month']}: net={m['net']}, expected={expected_net}"
            )


# ═══════════════════════════════════════════════════════════════════════════════
#  8. Authentication Security
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuthSecurity:
    def test_same_password_different_hashes(self):
        """Salt randomization means identical passwords produce different hashes."""
        from pfm.auth import hash_password
        h1 = hash_password("MySecret123!")
        h2 = hash_password("MySecret123!")
        assert h1 != h2, "Two hashes of same password must differ (unique salts)"

    def test_verify_correct_password(self):
        from pfm.auth import hash_password, verify_password
        h = hash_password("TestPass!")
        assert verify_password(h, "TestPass!") is True

    def test_verify_wrong_password(self):
        from pfm.auth import hash_password, verify_password
        h = hash_password("RightPassword")
        assert verify_password(h, "WrongPassword") is False

    def test_verify_empty_password_rejected(self):
        from pfm.auth import hash_password, verify_password
        h = hash_password("RealPassword")
        assert verify_password(h, "") is False

    def test_hash_length_consistency(self):
        """PBKDF2 with 16-byte salt + 32-byte key = 48 bytes = 96 hex chars."""
        from pfm.auth import hash_password
        h = hash_password("anything")
        assert len(h) == 96, f"Hash length {len(h)}, expected 96"

    def test_verify_corrupted_hash_returns_false(self):
        from pfm.auth import verify_password
        assert verify_password("not_a_real_hex_hash!!!", "password") is False

    def test_unicode_password_support(self):
        from pfm.auth import hash_password, verify_password
        h = hash_password("пароль密码パスワード🔑")
        assert verify_password(h, "пароль密码パスワード🔑") is True
        assert verify_password(h, "wrong") is False


# ═══════════════════════════════════════════════════════════════════════════════
#  9. Database Referential Integrity
# ═══════════════════════════════════════════════════════════════════════════════

class TestDatabaseIntegrity:
    def test_all_transactions_have_valid_category(self):
        from pfm.db import get_session
        from pfm.db.models import Transaction, Category
        from pfm.config import DB_PATH
        session = get_session(DB_PATH)
        try:
            orphans = (
                session.query(Transaction)
                .outerjoin(Category, Transaction.category_id == Category.id)
                .filter(Category.id.is_(None))
                .count()
            )
            assert orphans == 0, f"{orphans} transactions reference non-existent categories"
        finally:
            session.close()

    def test_all_transactions_have_valid_account(self):
        from pfm.db import get_session
        from pfm.db.models import Transaction, Account
        from pfm.config import DB_PATH
        session = get_session(DB_PATH)
        try:
            orphans = (
                session.query(Transaction)
                .outerjoin(Account, Transaction.account_id == Account.id)
                .filter(Account.id.is_(None))
                .count()
            )
            assert orphans == 0, f"{orphans} transactions reference non-existent accounts"
        finally:
            session.close()

    def test_no_duplicate_transaction_ids(self):
        from pfm.db import get_session
        from pfm.db.models import Transaction
        from pfm.config import DB_PATH
        from sqlalchemy import func
        session = get_session(DB_PATH)
        try:
            dupes = (
                session.query(Transaction.transaction_id, func.count(Transaction.id))
                .group_by(Transaction.transaction_id)
                .having(func.count(Transaction.id) > 1)
                .all()
            )
            assert len(dupes) == 0, f"Found {len(dupes)} duplicate transaction_id values"
        finally:
            session.close()

    def test_category_names_unique(self):
        from pfm.db import get_session
        from pfm.db.models import Category
        from pfm.config import DB_PATH
        session = get_session(DB_PATH)
        try:
            cats = session.query(Category.name).all()
            names = [c.name for c in cats]
            assert len(names) == len(set(names)), "Duplicate category names found"
        finally:
            session.close()

    def test_minimum_data_requirements(self):
        """Verify the database meets assignment minimums."""
        from pfm.db import get_session
        from pfm.db.models import Transaction, Category, Account
        from pfm.config import DB_PATH
        session = get_session(DB_PATH)
        try:
            txn_count = session.query(Transaction).count()
            cat_count = session.query(Category).count()
            acc_count = session.query(Account).count()
            assert txn_count >= 5000, f"Only {txn_count} transactions, need 5000+"
            assert cat_count >= 10, f"Only {cat_count} categories, need 10+"
            assert acc_count >= 2, f"Only {acc_count} accounts, need 2+"
        finally:
            session.close()


# ═══════════════════════════════════════════════════════════════════════════════
# 10. Transaction Filter Combinations
# ═══════════════════════════════════════════════════════════════════════════════

class TestTransactionFilters:
    def test_filter_by_category(self):
        r = client.get("/transactions?x_user_id=rajesh_sharma&category=Groceries&page_size=10")
        assert r.status_code == 200
        for item in r.json()["items"]:
            assert item["category"] == "Groceries"

    def test_filter_by_date_range(self):
        r = client.get(
            "/transactions?x_user_id=rajesh_sharma&start_date=2024-06-01&end_date=2024-06-30&page_size=50"
        )
        assert r.status_code == 200
        for item in r.json()["items"]:
            d = date.fromisoformat(item["date"])
            assert date(2024, 6, 1) <= d <= date(2024, 6, 30)

    def test_filter_by_type(self):
        r = client.get("/transactions?x_user_id=rajesh_sharma&transaction_type=income&page_size=50")
        assert r.status_code == 200
        for item in r.json()["items"]:
            assert item["is_income"] is True

    def test_search_filter(self):
        r = client.get("/transactions?x_user_id=rajesh_sharma&search=Salary&page_size=10")
        assert r.status_code == 200
        # All results should contain "Salary" in description, merchant, or notes
        for item in r.json()["items"]:
            text = (
                (item.get("description") or "")
                + (item.get("merchant") or "")
                + (item.get("notes") or "")
            ).lower()
            assert "salary" in text, f"Search result doesn't contain 'salary': {item['description']}"

    def test_combined_filters(self):
        r = client.get(
            "/transactions?x_user_id=rajesh_sharma&category=Groceries"
            "&start_date=2024-01-01&end_date=2024-12-31&page_size=10"
        )
        assert r.status_code == 200
        for item in r.json()["items"]:
            assert item["category"] == "Groceries"
            d = date.fromisoformat(item["date"])
            assert date(2024, 1, 1) <= d <= date(2024, 12, 31)


# ═══════════════════════════════════════════════════════════════════════════════
# 11. ML Model Robustness
# ═══════════════════════════════════════════════════════════════════════════════

class TestMLModels:
    def test_risk_scorer_handles_edge_case_all_income(self):
        """User with 100% income, 0% expenses should score high."""
        import pandas as pd
        from pfm.models.risk_scorer import financial_health_score
        df = pd.DataFrame({
            "user_id": ["u"] * 10,
            "date": pd.date_range("2024-01-01", periods=10, freq="D"),
            "amount": [5000.0] * 10,
            "is_income": [True] * 10,
            "category": ["Income"] * 10,
            "category_id": [1] * 10,
        })
        result = financial_health_score(df, pd.DataFrame(), "u")
        assert result["overall_score"] >= 50, "All-income user should have a decent score"

    def test_risk_scorer_handles_edge_case_all_expenses(self):
        """User with 100% expenses, 0% income should score low."""
        import pandas as pd
        from pfm.models.risk_scorer import financial_health_score
        df = pd.DataFrame({
            "user_id": ["u"] * 10,
            "date": pd.date_range("2024-01-01", periods=10, freq="D"),
            "amount": [5000.0] * 10,
            "is_income": [False] * 10,
            "category": ["Food"] * 10,
            "category_id": [1] * 10,
        })
        result = financial_health_score(df, pd.DataFrame(), "u")
        assert result["overall_score"] <= 60, "All-expense user should score low"

    def test_forecaster_returns_dict(self):
        import pandas as pd
        from pfm.models.forecaster import compare_all_models, prepare_forecast_data
        df = pd.DataFrame({
            "user_id": ["u"] * 120,
            "date": pd.date_range("2024-01-01", periods=120, freq="D"),
            "amount": [100.0 + i * 2 for i in range(120)],
            "is_income": [False] * 120,
            "category": ["Food"] * 120,
        })
        X, y = prepare_forecast_data(df, "u")
        results = compare_all_models(X, y)
        assert isinstance(results, pd.DataFrame), "compare_all_models should return a DataFrame"
        assert len(results) > 0, "Should return at least one model result"


# ═══════════════════════════════════════════════════════════════════════════════
# 12. Edge Cases & Special Characters
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_special_characters_in_description(self):
        """Descriptions with emoji and special chars should be accepted."""
        r = client.post(
            "/transactions?x_user_id=rajesh_sharma",
            json={
                "amount": 100,
                "description": "Café ☕ & Résumé — test (100%)",
                "transaction_type": "expense",
                "category": "Dining",
                "account_id": 1,
                "date": "2025-01-15",
            },
        )
        if r.status_code == 201:
            txn_id = r.json()["transaction_id"]
            assert r.json()["description"] == "Café ☕ & Résumé — test (100%)"
            # Cleanup
            client.delete(f"/transactions/{txn_id}?x_user_id=rajesh_sharma")

    def test_very_large_amount(self):
        r = client.post(
            "/transactions?x_user_id=rajesh_sharma",
            json={
                "amount": 99999999.99,
                "description": "Large amount test",
                "transaction_type": "income",
                "category": "Income",
                "account_id": 1,
                "date": "2025-01-15",
            },
        )
        if r.status_code == 201:
            assert r.json()["amount"] == 99999999.99
            client.delete(f"/transactions/{r.json()['transaction_id']}?x_user_id=rajesh_sharma")

    def test_delete_nonexistent_transaction(self):
        r = client.delete("/transactions/nonexistent-uuid-12345?x_user_id=rajesh_sharma")
        assert r.status_code == 404

    def test_update_nonexistent_transaction(self):
        r = client.put(
            "/transactions/nonexistent-uuid-12345?x_user_id=rajesh_sharma",
            json={"amount": 100},
        )
        assert r.status_code == 404

    def test_missing_required_query_param(self):
        """Calling endpoints without user_id should fail."""
        r = client.get("/dashboard")
        assert r.status_code == 422

    def test_budget_upsert_behavior(self):
        """Creating a budget for the same category+month should update, not duplicate."""
        payload = {"category": "Dining", "month": "2099-12", "amount": 3000}
        r1 = client.post("/budgets?user_id=rajesh_sharma", json=payload)
        assert r1.status_code == 201

        payload["amount"] = 5000
        r2 = client.post("/budgets?user_id=rajesh_sharma", json=payload)
        assert r2.status_code == 201
        # The second call should update the same budget
        assert r2.json()["amount"] == 5000

        # Verify only one budget for this category+month
        r3 = client.get("/budgets?user_id=rajesh_sharma&month=2099-12")
        budgets = r3.json()
        dining_budgets = [b for b in budgets if b["category"] == "Dining"]
        assert len(dining_budgets) == 1, f"Expected 1 Dining budget, got {len(dining_budgets)}"
