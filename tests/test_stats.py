"""Tests for Statistical Analyst Agent and Anomaly Detection."""

import pytest
import pandas as pd
from cortex.agents.stats_agent import StatisticalAnalystAgent
from cortex.agents.state import AgentState
from cortex.governance.telemetry import QueryAuditTrail


def test_statistical_diagnostics_outlier_detection():
    agent = StatisticalAnalystAgent()
    # Create dataset with clear outlier
    df = pd.DataFrame({
        "store_name": [f"Store_{i}" for i in range(20)],
        "revenue": [100.0] * 19 + [10000.0]
    })
    
    state = AgentState(session_id="test_stat", user_query="test", query_result=df)
    trail = QueryAuditTrail(session_id="test_stat", user_query="test")
    
    state = agent.run(state, trail)
    
    assert "revenue" in state.statistical_summary["metrics"]
    stats = state.statistical_summary["metrics"]["revenue"]
    assert stats["outlier_count"] >= 1
    assert len(state.statistical_summary["anomalies_detected"]) >= 1
