"""Tests for Hybrid RAG Retriever and Reciprocal Rank Fusion."""

import pytest
from cortex.rag.hybrid_retriever import HybridRetriever


def test_hybrid_retriever_schema_linking():
    retriever = HybridRetriever()
    tables = retriever.retrieve_schemas("What are the total sales and revenue by store?", top_k=2)
    table_names = [t.table_name for t in tables]
    
    assert "retail_store_sales" in table_names or "retail_stores" in table_names


def test_hybrid_retriever_applecare_linking():
    retriever = HybridRetriever()
    tables = retriever.retrieve_schemas("Which hardware repairs have the highest turnaround time and lowest CSAT?", top_k=2)
    table_names = [t.table_name for t in tables]
    
    assert "applecare_incidents" in table_names


def test_hybrid_retriever_sop_documents():
    retriever = HybridRetriever()
    docs = retriever.retrieve_documents("What is the battery health replacement threshold?", top_k=1)
    
    assert len(docs) >= 1
    assert "AppleCare" in docs[0].domain or "battery" in docs[0].content.lower()


def test_hybrid_retriever_metric_identification():
    retriever = HybridRetriever()
    metrics = retriever.retrieve_metrics("What is our CSAT score and turnaround time?", top_k=2)
    metric_names = [m.metric_name for m in metrics]
    
    assert any("CSAT" in name or "Turnaround" in name for name in metric_names)
