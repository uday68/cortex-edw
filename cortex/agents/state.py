"""Agentic Workflow Shared State.

Defines the centralized state schema passed across supervisor, retrieval,
SQL generation, AST governance, execution, reflection, statistics, and synthesis agents.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import pandas as pd


@dataclass
class AgentState:
    session_id: str
    user_query: str
    domain: str = "Unknown"  # Retail, AppleCare, SupplyChain, Services, Cross-Domain
    intent: str = "Analytical"
    plan_steps: List[str] = field(default_factory=list)
    
    # RAG Context
    retrieved_context: Dict[str, Any] = field(default_factory=dict)
    
    # SQL Generation & Governance
    candidate_sql: str = ""
    ast_valid: bool = False
    ast_violations: List[str] = field(default_factory=list)
    
    # Execution
    query_result: pd.DataFrame = field(default_factory=pd.DataFrame)
    execution_meta: Dict[str, Any] = field(default_factory=dict)
    
    # Reflection & Self-Correction
    reflection_count: int = 0
    max_reflections: int = 3
    critique_feedback: Optional[str] = None
    needs_retry: bool = False
    
    # Statistical Diagnostics & Synthesis
    statistical_summary: Dict[str, Any] = field(default_factory=dict)
    executive_narrative: str = ""
    chart_spec: Dict[str, Any] = field(default_factory=dict)
    groundedness_score: float = 1.0
    
    # Thought Stream for UI
    thought_stream: List[Dict[str, Any]] = field(default_factory=list)

    def log_thought(self, agent: str, message: str, status: str = "INFO", data: Optional[Dict[str, Any]] = None) -> None:
        """Appends a timestamped structured thought to the stream."""
        self.thought_stream.append({
            "agent": agent,
            "message": message,
            "status": status,
            "data": data or {}
        })
