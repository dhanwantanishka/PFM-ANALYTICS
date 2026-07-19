"""Receipt Scanner (OCR) — auto-extract merchant, amount, and date from receipts."""

from __future__ import annotations

import base64
import json
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any

_APP_DIR = Path(__file__).resolve().parents[1]
_SRC_DIR = _APP_DIR.parent / "src"
for _p in [str(_APP_DIR), str(_SRC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st
import utils.bootstrap  # noqa: F401

from components.layout import render_page_header

if "user_id" not in st.session_state:
    st.error("Please log in to use the receipt scanner.")
    st.stop()

user_id = st.session_state["user_id"]

render_page_header(
    "Receipt Scanner",
    "Upload a receipt to automatically extract the Merchant, Amount, and Date.",
    ":material/document_scanner:",
)

st.info(
    "💡 **How it works:** We use AI Vision to read your receipt. If configured in `st.secrets`, "
    "it uses GPT-4o for real OCR. Otherwise, it runs a local simulation for demo purposes."
)

uploaded_file = st.file_uploader("Upload Receipt Image", type=["png", "jpg", "jpeg"])


def _extract_via_openai(image_bytes: bytes, mime_type: str) -> dict[str, Any] | None:
    """Use GPT-4o Vision to extract receipt details."""
    try:
        api_key = st.secrets.get("openai", {}).get("api_key")
        if not api_key:
            return None

        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a receipt data extractor. Extract the merchant name, total amount, and date "
                        "from the receipt image. Output ONLY valid JSON with keys: "
                        "'merchant' (string), 'amount' (float), 'date' (YYYY-MM-DD string). "
                        "If a field cannot be found, use null."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract data from this receipt."},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}
                        }
                    ]
                }
            ],
            max_tokens=300,
        )
        content = response.choices[0].message.content
        if content:
            return json.loads(content)
        return None
    except Exception as e:
        st.error(f"OCR API Error: {e}")
        return None


def _mock_extract(filename: str) -> dict[str, Any]:
    """Simulate extraction if no API key is available."""
    # Try to guess from filename to make it feel slightly smart
    name_lower = filename.lower()
    merchant = "Local Store"
    amount = 450.0

    if "swiggy" in name_lower or "zomato" in name_lower:
        merchant = "Swiggy / Zomato"
        amount = 320.50
    elif "amazon" in name_lower:
        merchant = "Amazon India"
        amount = 1299.00
    elif "uber" in name_lower:
        merchant = "Uber"
        amount = 250.00
    elif "dmart" in name_lower:
        merchant = "DMart"
        amount = 2150.75

    return {
        "merchant": merchant,
        "amount": amount,
        "date": date.today().strftime("%Y-%m-%d")
    }


if uploaded_file:
    # Show preview
    st.image(uploaded_file, caption="Uploaded Receipt", width=300)

    if st.button("Scan Receipt", type="primary", use_container_width=True):
        with st.spinner("Scanning receipt..."):
            image_bytes = uploaded_file.read()
            mime = uploaded_file.type
            
            # Try API first, fallback to mock
            result = _extract_via_openai(image_bytes, mime)
            if not result:
                time.sleep(1.5)  # Simulate processing delay
                result = _mock_extract(uploaded_file.name)

            if result:
                st.session_state["scanner_result"] = {
                    "merchant": result.get("merchant"),
                    "amount": result.get("amount"),
                    "date": result.get("date"),
                    "description": f"Receipt upload: {result.get('merchant', 'Expense')}"
                }
                st.success("✅ Extraction successful!")
                st.rerun()

# ─── Review & Send to Add Transaction ──────────────────────────────────────────
if "scanner_result" in st.session_state:
    st.divider()
    st.subheader("Extracted Details")
    res = st.session_state["scanner_result"]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Merchant", res.get("merchant") or "Not found")
    col2.metric("Amount", f"₹{res.get('amount', 0):,.2f}")
    col3.metric("Date", res.get("date") or "Not found")

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Accept & Add Transaction", type="primary", use_container_width=True):
            # Pass data via session state to add_transaction page
            st.session_state["prefill_txn"] = res
            del st.session_state["scanner_result"]
            st.switch_page("pages/add_transaction.py")
    with c2:
        if st.button("Discard", use_container_width=True):
            del st.session_state["scanner_result"]
            st.rerun()
