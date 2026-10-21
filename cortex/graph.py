"""Multi-Agent Orchestration Graph & Execution Engine.

Coordinates the complete cognitive pipeline across Supervisor, Hybrid RAG, SQL Synthesis,
AST Governance, Warehouse Execution, Self-Healing Critic Loops, Statistical ML, and Synthesis.
"""

import time
import uuid
from typing import Any, Callable, Dict, Optional

from cortex.agents.critic_agent import critic_agent
from cortex.agents.schema_agent import schema_agent
from cortex.agents.sql_agent import sql_agent
from cortex.agents.state import AgentState
from cortex.agents.stats_agent import stats_agent
from cortex.agents.supervisor import supervisor_agent
from cortex.agents.synthesis_agent import synthesis_agent
from cortex.engine.warehouse import warehouse
from cortex.governance.ast_guard import ast_guard
from cortex.governance.pii_sanitizer import pii_sanitizer
from cortex.governance.telemetry import telemetry, QueryAuditTrail


class CortexAgentGraph:
    """Orchestrates the multi-agent state graph with conditional reflection loops."""

    def __init__(self):
        self.supervisor = supervisor_agent
        self.schema = schema_agent
        self.sql_gen = sql_agent
        self.critic = critic_agent
        self.stats = stats_agent
        self.synthesis = synthesis_agent

    def run(self, user_query: str, session_id: Optional[str] = None, step_callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> AgentState:
        """Executes the full agentic graph from user query to verified executive insight."""
        sess_id = session_id or str(uuid.uuid4())[:8]
        state = AgentState(session_id=sess_id, user_query=user_query)
        audit_trail = telemetry.start_trace(sess_id, user_query)

        def _notify(agent_name: str, message: str, status: str = "INFO"):
            if step_callback:
                step_callback({"agent": agent_name, "message": message, "status": status})

        # 1. Supervisor: Planning & Decomposition
        _notify("SupervisorAgent", "Analyzing analytical intent and classifying domain...")
        state = self.supervisor.run(state, audit_trail)

        # 2. Schema Retriever: Hybrid RRF RAG
        _notify("SchemaRetrieverAgent", "Executing hybrid RAG retrieval across enterprise catalog and SOPs...")
        state = self.schema.run(state, audit_trail)

        # 3. Iterative Execution & Reflection Loop
        while state.reflection_count <= state.max_reflections:
            # 3a. Synthesize candidate SQL
            _notify("SQLGeneratorAgent", f"Synthesizing dialect-correct SQL (Iteration {state.reflection_count + 1})...")
            state = self.sql_gen.run(state, audit_trail)

            # 3b. AST Governance Guard
            _notify("ASTGovernanceGuard", "Performing AST security inspection (read-only, whitelist, limits)...")
            start_ast = time.perf_counter()
            is_valid, modified_sql, violations = ast_guard.validate_and_sanitize(state.candidate_sql, dialect="duckdb")
            state.ast_valid = is_valid
            state.ast_violations = violations
            state.candidate_sql = modified_sql
            elapsed_ast = (time.perf_counter() - start_ast) * 1000

            telemetry.record_step(
                audit_trail,
                "ASTGovernanceGuard",
                "AST Policy Verification",
                elapsed_ast,
                status="SUCCESS" if is_valid else "FAILED",
                details={"valid": is_valid, "violations": violations}
            )

            # 3c. Execute in Warehouse if AST valid
            if is_valid:
                _notify("WarehouseEngine", "Executing analytical query against DuckDB OLAP engine...")
                start_exec = time.perf_counter()
                df_raw, exec_meta = warehouse.execute_query(state.candidate_sql)
                elapsed_exec = (time.perf_counter() - start_exec) * 1000

                # Apply PII Column Masking
                df_clean = pii_sanitizer.mask_dataframe(df_raw)
                state.query_result = df_clean
                state.execution_meta = exec_meta

                telemetry.record_step(
                    audit_trail,
                    "WarehouseEngine",
                    "OLAP Query Execution",
                    elapsed_exec,
                    status="SUCCESS" if exec_meta["success"] else "FAILED",
                    details=exec_meta
                )
            else:
                state.query_result = state.query_result  # empty
                state.execution_meta = {"success": False, "error": "; ".join(violations)}

            # 3d. Critic Agent Reflection Check
            _notify("CriticAgent", "Evaluating execution results and checking for anomalies...")
            state = self.critic.run(state, audit_trail)

            # If no retry needed, break out of reflection loop
            if not state.needs_retry:
                break

        # 4. Statistical Analyst Agent
        _notify("StatisticalAnalystAgent", "Computing Z-score outlier detection and IQR distribution fences...")
        state = self.stats.run(state, audit_trail)

        # 5. Executive Synthesis & Groundedness Audit
        _notify("ExecutiveSynthesisAgent", "Formulating executive briefing and verifying groundedness...")
        state = self.synthesis.run(state, audit_trail)

        # Finalize Audit Trail
        telemetry.finalize_trace(
            audit_trail,
            generated_sql=state.candidate_sql,
            rows=len(state.query_result),
            ast_passed=state.ast_valid,
            groundedness=state.groundedness_score,
            error=state.execution_meta.get("error")
        )

        _notify("CortexPlatform", "Cognitive data pipeline execution complete.", status="SUCCESS")
        return state


cortex_graph = CortexAgentGraph()
