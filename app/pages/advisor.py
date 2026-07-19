"""AI finance advisor — data-driven natural-language Q&A about your finances."""

from __future__ import annotations

import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parents[1]
_SRC_DIR = _APP_DIR.parent / "src"
for _p in [str(_APP_DIR), str(_SRC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st

import utils.bootstrap  # noqa: F401

from components.layout import render_page_header
from components.page_context import load_page_context
from services.advisor import answer_question, try_api_answer, _build_rich_context

ctx = load_page_context(require_data=False)
if ctx is None:
    st.stop()

render_page_header(
    "AI Finance Advisor",
    "Personalised insights based on your actual transaction history — no guesswork.",
    ":material/smart_toy:",
)

# ─── Live snapshot from real data ─────────────────────────────────────────────
data_ctx = _build_rich_context(ctx.transactions, ctx.budgets, ctx.filters.user_id)

if data_ctx.get("no_data"):
    st.info(
        "You don't have any transactions yet. Go to **Manage → Add Transaction** to record your "
        "first transaction. Then come back here for personalised AI insights!"
    )
    st.stop()

# Show live snapshot metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("Health Score", f"{data_ctx.get('health_score', 0)}/100")
m2.metric("Savings Rate", f"{data_ctx.get('savings_rate_pct', 0)}%")
m3.metric("This Month Spend", f"₹{data_ctx.get('month_expenses', 0):,.0f}")
m4.metric("This Month Income", f"₹{data_ctx.get('month_income', 0):,.0f}")

st.markdown("---")

# ─── Suggested questions as chips ─────────────────────────────────────────────
st.markdown("**💡 Suggested questions — click to ask:**")
suggestions = [
    "What is my savings rate?",
    "Where am I spending the most?",
    "Which categories are over budget?",
    "How is my 50/30/20 breakdown?",
    "What is my financial health score?",
    "Show me my top merchants",
    "Give me tips to save more",
    "When do I spend the most?",
    "Summarise this month",
]

cols = st.columns(3)
for i, suggestion in enumerate(suggestions):
    with cols[i % 3]:
        if st.button(suggestion, key=f"sug_{i}", use_container_width=True):
            st.session_state["pending_question"] = suggestion

st.markdown("---")

# ─── Chat interface ────────────────────────────────────────────────────────────
if "advisor_messages" not in st.session_state:
    st.session_state.advisor_messages = [
        {
            "role": "assistant",
            "content": (
                f"Hello **{ctx.filters.user_name}**! 👋\n\n"
                f"I've analysed your real transaction data ({data_ctx.get('total_transactions', 0)} transactions, "
                f"₹{data_ctx.get('total_income', 0):,.0f} income, "
                f"₹{data_ctx.get('total_expenses', 0):,.0f} expenses). "
                f"Your financial health score is **{data_ctx.get('health_score', 0)}/100**.\n\n"
                "Ask me anything about your finances!"
            ),
        }
    ]

for message in st.session_state.advisor_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle suggested question clicks
if "pending_question" in st.session_state:
    prompt = st.session_state.pop("pending_question")
else:
    prompt = st.chat_input("Ask about your finances…")

if prompt:
    st.session_state.advisor_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analysing your data…"):
            # Try LLM first with real context injected, fall back to rule engine
            response = try_api_answer(prompt, data_ctx) or answer_question(
                prompt,
                ctx.transactions,
                ctx.budgets,
                ctx.filters.user_id,
            )
        st.markdown(response)

    st.session_state.advisor_messages.append({"role": "assistant", "content": response})

st.markdown("---")
if st.button("🗑️ Clear conversation"):
    st.session_state.advisor_messages = []
    st.rerun()

st.caption(
    "All insights are derived from your actual transaction history stored in the database. "
    "Configure `st.secrets['openai']['api_key']` for GPT-4o powered responses."
)
