"""RAG retrieval models for transaction semantic search.

Includes:
1. SimpleTransactionVectorStore: Zero-dependency scikit-learn + numpy Cosine Similarity.
2. LangChainFaissRetriever: Full LangChain + FAISS + OpenAI Embeddings integration.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SimpleTransactionVectorStore:
    """Zero-dependency custom vector store for semantic transaction search.
    
    Uses TF-IDF Vectorizer and Cosine Similarity to find relevant transactions.
    """

    def __init__(self) -> None:
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.documents: list[str] = []
        self.transactions_ref: list[dict] = []
        self.tfidf_matrix: np.ndarray | None = None

    def fit(self, df: pd.DataFrame) -> None:
        """Convert transactions into document strings and fit the TF-IDF index.
        
        Args:
            df: Filtered user transactions dataframe.
        """
        if df.empty:
            return

        docs = []
        txns = []
        for _, row in df.iterrows():
            # Standardize transaction elements into a readable text document
            tx_type = "received income of" if row.get("is_income") else "spent"
            merchant_str = f" at {row.get('merchant')}" if pd.notna(row.get("merchant")) else ""
            notes_str = f" (Notes: {row.get('notes')})" if pd.notna(row.get("notes")) else ""
            category = row.get("category", "Unknown Category")
            amount = row.get("amount", 0.0)
            date_str = (
                row["date"].strftime("%Y-%m-%d")
                if isinstance(row["date"], pd.Timestamp)
                else str(row["date"])
            )

            doc = (
                f"On {date_str}, {tx_type} Rs. {amount:,.2f} for category '{category}'"
                f"{merchant_str}. Description: {row.get('description', '')}{notes_str}."
            )
            docs.append(doc)
            txns.append(row.to_dict())

        self.documents = docs
        self.transactions_ref = txns
        self.tfidf_matrix = self.vectorizer.fit_transform(docs)

    def retrieve(self, query: str, top_k: int = 5) -> list[str]:
        """Retrieve the top K transaction documents matching the query.
        
        Args:
            query: The user's search query (e.g. 'Coffee shops in May').
            top_k: Number of transaction records to return.
        
        Returns:
            A list of matching string summaries.
        """
        if not self.documents or self.tfidf_matrix is None:
            return []

        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        # Sort indices by highest similarity
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            # Only return records that have a minimal relevance match
            if similarities[idx] > 0.0:
                results.append(self.documents[idx])

        return results


class LangChainFaissRetriever:
    """Retrieval model using LangChain and FAISS for semantic similarity searches.
    
    Requires external libraries:
        pip install langchain langchain-community langchain-openai faiss-cpu
    """

    def __init__(self, openai_api_key: str) -> None:
        self.api_key = openai_api_key
        self.vector_store = None

    def fit_and_index(self, df: pd.DataFrame) -> None:
        """Convert transactions into LangChain documents and compile the FAISS Index."""
        try:
            from langchain_core.documents import Document
            from langchain_openai import OpenAIEmbeddings
            from langchain_community.vectorstores import FAISS
        except ImportError:
            raise ImportError(
                "LangChain/FAISS dependencies not found. Please install: "
                "pip install langchain langchain-community langchain-openai faiss-cpu"
            )

        if df.empty:
            return

        docs = []
        for _, row in df.iterrows():
            tx_type = "received income of" if row.get("is_income") else "spent"
            merchant_str = f" at {row.get('merchant')}" if pd.notna(row.get("merchant")) else ""
            notes_str = f" (Notes: {row.get('notes')})" if pd.notna(row.get("notes")) else ""
            category = row.get("category", "Unknown Category")
            amount = row.get("amount", 0.0)
            date_str = (
                row["date"].strftime("%Y-%m-%d")
                if isinstance(row["date"], pd.Timestamp)
                else str(row["date"])
            )

            doc_content = (
                f"On {date_str}, {tx_type} Rs. {amount:,.2f} for category '{category}'"
                f"{merchant_str}. Description: {row.get('description', '')}{notes_str}."
            )
            docs.append(Document(page_content=doc_content, metadata=row.to_dict()))

        embeddings = OpenAIEmbeddings(openai_api_key=self.api_key)
        self.vector_store = FAISS.from_documents(docs, embeddings)

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """Perform semantic search using FAISS vector similarity."""
        if not self.vector_store:
            return []
        
        matches = self.vector_store.similarity_search(query, k=top_k)
        return [{"content": doc.page_content, "metadata": doc.metadata} for doc in matches]
