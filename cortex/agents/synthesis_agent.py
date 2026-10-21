"""Executive Synthesis & Visualization Agent.

Synthesizes business-ready executive summaries, actionable strategic recommendations,
generates Vega-Lite/Altair visualization specs, and enforces groundedness verification.
"""

import time
from typing import Any, Dict
import pandas as pd

from cortex.agents.state import AgentState
from cortex.governance.groundedness import groundedness_guard
from cortex.governance.pii_sanitizer import pii_sanitizer
from cortex.governance.telemetry import telemetry, QueryAuditTrail


class ExecutiveSynthesisAgent:
    """Produces the final executive brief, chart specifications, and verifies faithfulness."""

    def run(self, state: AgentState, audit_trail: QueryAuditTrail) -> AgentState:
        start_time = time.perf_counter()
        df = state.query_result

        if df.empty:
            state.executive_narrative = "No data returned matching the specified query criteria. Please refine filters or table selections."
            state.groundedness_score = 1.0
            return state

        # 1. Build Narrative
        narrative = self._generate_narrative(state, df)
        # 2. Sanitize PII
        sanitized_narrative = pii_sanitizer.sanitize_text(narrative)
        state.executive_narrative = sanitized_narrative

        # 3. Faithfulness & Groundedness check
        score, ungrounded, audit = groundedness_guard.evaluate_groundedness(sanitized_narrative, df, state.statistical_summary)
        state.groundedness_score = score

        # 4. Generate Chart Specification
        state.chart_spec = self._build_chart_spec(df)

        state.log_thought(
            agent="ExecutiveSynthesisAgent",
            message=f"Formulated executive summary with {score * 100:.1f}% groundedness verification. Configured chart visualization.",
            status="SUCCESS",
            data={"groundedness_score": score, "chart_type": state.chart_spec.get("type")}
        )

        elapsed = (time.perf_counter() - start_time) * 1000
        telemetry.record_step(
            audit_trail,
            "ExecutiveSynthesisAgent",
            "Executive Synthesis & Groundedness Audit",
            elapsed,
            status="SUCCESS",
            details={"groundedness": score}
        )
        return state

    def _generate_narrative(self, state: AgentState, df: pd.DataFrame) -> str:
        """Assembles structured executive narrative from DataFrame and statistics."""
        first_row = df.iloc[0].to_dict()
        total_rows = len(df)
        
        lines = []
        lines.append(f"### Executive Briefing: {state.domain} Operations")
        lines.append(f"**Query Focus**: *\"{state.user_query}\"*")
        lines.append("")
        
        # Summary highlight
        lines.append("#### Key Performance Highlights")
        primary_dim = df.columns[0]
        primary_val = first_row.get(primary_dim)
        
        if "total_net_revenue" in df.columns:
            top_rev = first_row.get("total_net_revenue")
            lines.append(f"- **Top Performer**: **{primary_val}** leads with **${top_rev:,.2f}** in realized net sales across {total_rows} analyzed cohorts.")
        elif "avg_csat_score" in df.columns or "avg_csat" in df.columns:
            csat_col = "avg_csat_score" if "avg_csat_score" in df.columns else "avg_csat"
            top_csat = first_row.get(csat_col)
            lines.append(f"- **Service Quality**: **{primary_val}** reports an average CSAT rating of **{top_csat:.2f} / 5.0**.")
        elif "estimated_active_mrr" in df.columns:
            top_mrr = first_row.get("estimated_active_mrr")
            lines.append(f"- **Subscription Recurring Revenue**: **{primary_val}** delivers **${top_mrr:,.2f}** in monthly recurring revenue.")
        elif "on_time_rate_pct" in df.columns:
            top_rate = first_row.get("on_time_rate_pct")
            lines.append(f"- **Logistics Reliability**: **{primary_val}** maintained an on-time transit rate of **{top_rate:.1f}%**.")
        else:
            lines.append(f"- Primary leader **{primary_val}** spans {total_rows} recorded segments in the enterprise warehouse.")

        # Outlier notes
        anomalies = state.statistical_summary.get("anomalies_detected", [])
        if anomalies:
            lines.append("")
            lines.append("#### Statistical Diagnostics & Anomaly Alerts")
            for a in anomalies[:2]:
                lines.append(f"- **Statistical Outlier**: **{a['entity']}** exhibited {a['metric']} of {a['observed_value']} (z-score: {a['z_score']}, relative to mean {a['mean']}).")

        # Operational Recommendations
        lines.append("")
        lines.append("#### Strategic Recommendations for Business Drivers")
        if state.domain == "Retail":
            lines.append("1. **Inventory Buffering**: Accelerate automated stock transfers from regional distribution hubs to flagship locations operating below 5.0 days of supply.")
            lines.append("2. **Promotional Calibration**: Re-evaluate discount elasticity where discount rates exceed 3.5% without commensurate trade-in lift.")
        elif state.domain == "AppleCare":
            lines.append("1. **Depot Routing Optimization**: Shift high-volume display repairs from mail-in depots to retail Genius Bar same-day modules to preserve CSAT > 4.5.")
            lines.append("2. **Component Reliability Loop**: Escalate recurring subsystem diagnostic spikes directly to hardware quality and vendor procurement.")
        elif state.domain == "SupplyChain":
            lines.append("1. **Customs Mitigation**: Pre-clear Tier-1 wafer shipments with local regulatory brokers to prevent transit delays exceeding 48 hours.")
        else:
            lines.append("1. **Payment Recovery Enhancement**: Re-engage grace-period subscribers on Day 3 and Day 7 using dynamic recovery logic to reduce terminal churn.")

        return "\n".join(lines)

    def _build_chart_spec(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Constructs Vega-Lite / Plotly compatible chart spec."""
        if len(df) == 0:
            return {"type": "none"}

        cols = list(df.columns)
        cat_col = cols[0]
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()

        if not num_cols:
            return {"type": "table", "data": df.head(10).to_dict(orient="records")}

        target_num = num_cols[0]
        # Prefer net revenue or volume
        for col_name in ["total_net_revenue", "gross_revenue_usd", "total_units_sold", "units_sold", "estimated_active_mrr", "avg_csat_score"]:
            if col_name in num_cols:
                target_num = col_name
                break

        return {
            "type": "bar",
            "x_axis": cat_col,
            "y_axis": target_num,
            "title": f"{target_num.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}",
            "top_n": min(10, len(df))
        }


synthesis_agent = ExecutiveSynthesisAgent()
