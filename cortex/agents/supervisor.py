"""Supervisor Agent: Intent Decomposition & Planning.

Analyzes natural language business queries, classifies the operational domain
(Retail, AppleCare, Supply Chain, Services), identifies analytical intent,
and constructs a multi-step execution plan.
"""

import time
from cortex.agents.state import AgentState
from cortex.governance.telemetry import telemetry, QueryAuditTrail


class SupervisorAgent:
    """Orchestrates query decomposition and constructs the agent execution DAG."""

    DOMAIN_KEYWORDS = {
        "Retail": ["store", "sales", "revenue", "discount", "trade-in", "retail", "units", "bkc", "fifth avenue", "regent street"],
        "AppleCare": ["repair", "incident", "csat", "genius bar", "turnaround", "tat", "subsystem", "battery", "display", "warranty"],
        "SupplyChain": ["shipment", "supplier", "tsmc", "foxconn", "delay", "logistics", "hub", "transit", "carbon", "component"],
        "Services": ["subscription", "mrr", "churn", "icloud", "apple one", "apple music", "tv+", "tenure", "renewal"]
    }

    def run(self, state: AgentState, audit_trail: QueryAuditTrail) -> AgentState:
        start_time = time.perf_counter()
        query_lower = state.user_query.lower()
        
        # 1. Classify Domain
        domain_scores = {dom: 0 for dom in self.DOMAIN_KEYWORDS}
        for dom, kws in self.DOMAIN_KEYWORDS.items():
            for kw in kws:
                if kw in query_lower:
                    domain_scores[dom] += 1
                    
        top_domain = max(domain_scores, key=domain_scores.get)
        state.domain = top_domain if domain_scores[top_domain] > 0 else "Cross-Domain / Retail"

        # 2. Decompose Intent & Steps
        state.plan_steps = [
            f"1. Retrieve schemas and metric definitions for domain [{state.domain}].",
            "2. Generate dialect-correct analytical SQL query with aggregations.",
            "3. Enforce deterministic AST governance (read-only, table whitelisting, limit injection).",
            "4. Execute query against DuckDB warehouse engine.",
            "5. Inspect execution metrics; trigger self-correction reflection if errors or zero rows occur.",
            "6. Compute automated statistical diagnostics (outliers, trends, Z-scores).",
            "7. Synthesize executive business narrative and verify groundedness."
        ]

        state.log_thought(
            agent="SupervisorAgent",
            message=f"Query classified under domain: {state.domain}. Constructed 7-stage analytical execution plan.",
            status="SUCCESS",
            data={"domain": state.domain, "plan": state.plan_steps}
        )

        elapsed = (time.perf_counter() - start_time) * 1000
        telemetry.record_step(audit_trail, "SupervisorAgent", "Intent Decomposed & Planned", elapsed, status="SUCCESS", details={"domain": state.domain})
        return state


supervisor_agent = SupervisorAgent()
