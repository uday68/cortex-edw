"""Schema Retriever Agent.

Leverages Hybrid RAG (BM25 + Dense Semantic Cosine Similarity + Reciprocal Rank Fusion)
to fetch table schemas, column data types, business metric formulas, and operational guidelines.
"""

import time
from cortex.agents.state import AgentState
from cortex.governance.telemetry import telemetry, QueryAuditTrail
from cortex.rag.hybrid_retriever import hybrid_retriever


class SchemaRetrieverAgent:
    """Retrieves structured and unstructured schema context for the query."""

    def run(self, state: AgentState, audit_trail: QueryAuditTrail) -> AgentState:
        start_time = time.perf_counter()
        
        context = hybrid_retriever.get_prompt_context(state.user_query)
        state.retrieved_context = context
        
        table_names = [t.table_name for t in context["tables"]]
        metric_names = [m.metric_name for m in context["metrics"]]
        doc_ids = [d.doc_id for d in context["documents"]]

        state.log_thought(
            agent="SchemaRetrieverAgent",
            message=f"Linked {len(table_names)} tables ({', '.join(table_names)}) and {len(metric_names)} semantic metrics via RRF.",
            status="SUCCESS",
            data={
                "tables": table_names,
                "metrics": metric_names,
                "docs": doc_ids
            }
        )

        elapsed = (time.perf_counter() - start_time) * 1000
        telemetry.record_step(
            audit_trail,
            "SchemaRetrieverAgent",
            "Hybrid RRF Schema & Metric Retrieval",
            elapsed,
            status="SUCCESS",
            details={"tables": table_names, "metrics": metric_names}
        )
        return state


schema_agent = SchemaRetrieverAgent()
