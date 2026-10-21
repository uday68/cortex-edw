"""Enterprise Governance Telemetry & Audit Trail.

Maintains an immutable in-memory structured log of agent steps, execution latencies,
security policy validations, and data lineage for every query execution.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional


def _get_utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AgentStepLog:
    step_id: str
    agent_name: str
    action: str
    timestamp: str = field(default_factory=_get_utc_now_iso)
    duration_ms: float = 0.0
    status: str = "SUCCESS"  # SUCCESS, FAILED, RETRY
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryAuditTrail:
    session_id: str
    user_query: str
    start_time: str = field(default_factory=_get_utc_now_iso)
    end_time: Optional[str] = None
    total_latency_ms: float = 0.0
    steps: List[AgentStepLog] = field(default_factory=list)
    ast_check_passed: bool = False
    groundedness_score: float = 1.0
    rows_returned: int = 0
    generated_sql: Optional[str] = None
    error: Optional[str] = None


class TelemetryCollector:
    """Collects and aggregates real-time agent execution telemetry."""

    def __init__(self):
        self.audit_records: List[QueryAuditTrail] = []

    def start_trace(self, session_id: str, query: str) -> QueryAuditTrail:
        trail = QueryAuditTrail(session_id=session_id, user_query=query)
        self.audit_records.append(trail)
        return trail

    def record_step(self, trail: QueryAuditTrail, agent_name: str, action: str, duration_ms: float, status: str = "SUCCESS", details: Optional[Dict[str, Any]] = None) -> AgentStepLog:
        step = AgentStepLog(
            step_id=f"step_{len(trail.steps) + 1}",
            agent_name=agent_name,
            action=action,
            duration_ms=round(duration_ms, 2),
            status=status,
            details=details or {}
        )
        trail.steps.append(step)
        return step

    def finalize_trace(self, trail: QueryAuditTrail, generated_sql: Optional[str], rows: int, ast_passed: bool, groundedness: float, error: Optional[str] = None) -> None:
        trail.end_time = _get_utc_now_iso()
        trail.generated_sql = generated_sql
        trail.rows_returned = rows
        trail.ast_check_passed = ast_passed
        trail.groundedness_score = groundedness
        trail.error = error
        trail.total_latency_ms = sum(s.duration_ms for s in trail.steps)


telemetry = TelemetryCollector()
