"""Tests for AI finance advisor."""

from app.services.advisor import answer_question


def test_advisor_savings_rate(sample_transactions, sample_budgets):
    answer = answer_question("What is my savings rate?", sample_transactions, sample_budgets, "user_a")
    assert "savings rate" in answer.lower()


def test_advisor_spending(sample_transactions, sample_budgets):
    answer = answer_question("Where did my money go?", sample_transactions, sample_budgets, "user_a")
    assert "category" in answer.lower() or "spend" in answer.lower()


def test_advisor_fallback(sample_transactions, sample_budgets):
    answer = answer_question("hello there", sample_transactions, sample_budgets, "user_a")
    assert "savings rate" in answer.lower() or "spending" in answer.lower()


def test_simple_vector_store(sample_transactions):
    from pfm.models.rag_advisor import SimpleTransactionVectorStore
    store = SimpleTransactionVectorStore()
    store.fit(sample_transactions)
    
    # Retrieve grocery records
    results = store.retrieve("Groceries at the Store", top_k=3)
    assert len(results) > 0
    assert any("Groceries" in doc for doc in results)

