"""Critic & Reflection Agent (Self-Healing Execution Loop).

Inspects SQL compilation, AST policy checks, and database runtime errors.
If an error or zero-row anomaly is detected, performs root-cause reflection
and routes the workflow back to the SQL Generator Agent with corrective feedback.
"""

import time
from cortex.agents.state import AgentState
from cortex.governance.telemetry import telemetry, QueryAuditTrail


class CriticAgent:
    """Evaluates query execution and governs self-correction loops."""

    def run(self, state: AgentState, audit_trail: QueryAuditTrail) -> AgentState:
        start_time = time.perf_counter()
        
        # Check 1: Did AST governance fail?
        if not state.ast_valid:
            state.needs_retry = state.reflection_count < state.max_reflections
            state.critique_feedback = f"AST Governance Rejection: {'; '.join(state.ast_violations)}. You MUST rectify these policy violations."
            state.reflection_count += 1
            state.log_thought(
                agent="CriticAgent",
                message=f"Critique Triggered (AST Failure): {state.critique_feedback}. Retry scheduled: {state.needs_retry}",
                status="RETRY" if state.needs_retry else "FAILED",
                data={"violations": state.ast_violations, "retry": state.needs_retry}
            )
            elapsed = (time.perf_counter() - start_time) * 1000
            telemetry.record_step(audit_trail, "CriticAgent", "AST Critique Generated", elapsed, status="RETRY" if state.needs_retry else "FAILED")
            return state

        # Check 2: Did database execution encounter a runtime error?
        exec_error = state.execution_meta.get("error")
        if exec_error:
            state.needs_retry = state.reflection_count < state.max_reflections
            state.critique_feedback = f"Database Runtime Exception: {exec_error}. Check column names and table joins."
            state.reflection_count += 1
            state.log_thought(
                agent="CriticAgent",
                message=f"Critique Triggered (Runtime Error): {exec_error}. Retrying ({state.reflection_count}/{state.max_reflections}).",
                status="RETRY" if state.needs_retry else "FAILED",
                data={"error": exec_error, "retry": state.needs_retry}
            )
            elapsed = (time.perf_counter() - start_time) * 1000
            telemetry.record_step(audit_trail, "CriticAgent", "Runtime Error Critique", elapsed, status="RETRY" if state.needs_retry else "FAILED")
            return state

        # Check 3: Zero-row return check (potential over-filtering or date mismatch)
        if len(state.query_result) == 0:
            if state.reflection_count < 1:  # allow 1 reflection for empty results
                state.needs_retry = True
                state.critique_feedback = "Query returned 0 rows. Broaden WHERE filters or check date boundaries."
                state.reflection_count += 1
                state.log_thought(
                    agent="CriticAgent",
                    message="Zero rows returned. Scheduling broadening reflection.",
                    status="RETRY"
                )
                elapsed = (time.perf_counter() - start_time) * 1000
                telemetry.record_step(audit_trail, "CriticAgent", "Empty Result Set Reflection", elapsed, status="RETRY")
                return state

        # All checks passed
        state.needs_retry = False
        state.critique_feedback = None
        state.log_thought(
            agent="CriticAgent",
            message=f"Execution verified successfully ({len(state.query_result)} rows, {state.execution_meta.get('execution_time_ms', 0)}ms). Proceeding to statistical diagnostics.",
            status="SUCCESS",
            data={"rows": len(state.query_result), "runtime_ms": state.execution_meta.get("execution_time_ms", 0)}
        )
        elapsed = (time.perf_counter() - start_time) * 1000
        telemetry.record_step(audit_trail, "CriticAgent", "Query Verified Valid", elapsed, status="SUCCESS")
        return state


critic_agent = CriticAgent()
