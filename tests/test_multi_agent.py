"""Tests for Multi-Agent Workflow Graph."""

import pytest
from cortex.graph import cortex_graph


def test_multi_agent_graph_retail_query():
    query = "Compare total net sales, units sold, and trade-in units across global flagship stores"
    state = cortex_graph.run(query)
    
    assert state.domain in ["Retail", "Cross-Domain / Retail"]
    assert state.ast_valid is True
    assert not state.query_result.empty
    assert len(state.query_result) > 0
    assert state.executive_narrative != ""
    assert state.groundedness_score >= 0.7
    assert state.chart_spec.get("type") in ["bar", "table"]
    assert len(state.thought_stream) >= 5


def test_multi_agent_graph_applecare_query():
    query = "What are the most frequent hardware repair subsystems, average turnaround time, and CSAT scores?"
    state = cortex_graph.run(query)
    
    assert state.domain == "AppleCare"
    assert state.ast_valid is True
    assert not state.query_result.empty
    assert "avg_csat_score" in state.query_result.columns or "avg_csat" in state.query_result.columns or "device_category" in state.query_result.columns
    assert len(state.thought_stream) >= 5
