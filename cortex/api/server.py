"""Enterprise FastAPI Backend Service.

Provides asynchronous REST endpoints and Server-Sent Events (SSE) streaming for real-time
multi-agent reasoning traces, SQL generation, AST audits, and warehouse diagnostics.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from cortex.config import config
from cortex.engine.warehouse import warehouse
from cortex.governance.telemetry import telemetry
from cortex.graph import cortex_graph
from cortex.rag.metadata_catalog import ENTERPRISE_METRICS, ENTERPRISE_TABLES

logger = logging.getLogger("cortex.api")

app = FastAPI(
    title="Cortex EDW: Enterprise Data-Centric Agent Platform",
    description="Multi-agent cognitive engine for petabyte enterprise data warehouses (Apple AiDP Blueprint)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language enterprise question")
    session_id: Optional[str] = Field(None, description="Optional persistent session identifier")


class QueryResponse(BaseModel):
    session_id: str
    domain: str
    generated_sql: str
    ast_valid: bool
    ast_violations: List[str]
    row_count: int
    execution_time_ms: float
    groundedness_score: float
    executive_narrative: str
    chart_spec: Dict[str, Any]
    preview_data: List[Dict[str, Any]]
    thought_stream: List[Dict[str, Any]]


@app.get("/api/v1/health")
async def health_check():
    """Health and status check for warehouse engine and agent platform."""
    tables = warehouse.get_all_tables()
    return {
        "status": "healthy",
        "engine": warehouse.engine_type,
        "active_tables_count": len(tables),
        "tables": tables,
        "environment": config.app_env
    }


@app.get("/api/v1/catalog")
async def get_catalog():
    """Returns the structured enterprise table catalog."""
    return [
        {
            "table_name": t.table_name,
            "domain": t.domain,
            "description": t.description,
            "business_owner": t.business_owner,
            "refresh_frequency": t.refresh_frequency,
            "columns": [{"name": c.name, "type": c.data_type, "desc": c.description} for c in t.columns]
        }
        for t in ENTERPRISE_TABLES
    ]


@app.get("/api/v1/metrics")
async def get_metrics():
    """Returns semantic business metric formulas and descriptions."""
    return [
        {
            "name": m.metric_name,
            "domain": m.domain,
            "formula": m.formula,
            "description": m.description,
            "tables": m.target_tables
        }
        for m in ENTERPRISE_METRICS
    ]


@app.post("/api/v1/query", response_model=QueryResponse)
async def execute_query(req: QueryRequest):
    """Executes the full multi-agent workflow for an analytical business question."""
    try:
        state = cortex_graph.run(req.query, session_id=req.session_id)
        
        # Prepare preview records
        preview = state.query_result.head(25).to_dict(orient="records") if not state.query_result.empty else []
        
        return QueryResponse(
            session_id=state.session_id,
            domain=state.domain,
            generated_sql=state.candidate_sql,
            ast_valid=state.ast_valid,
            ast_violations=state.ast_violations,
            row_count=len(state.query_result),
            execution_time_ms=state.execution_meta.get("execution_time_ms", 0.0),
            groundedness_score=state.groundedness_score,
            executive_narrative=state.executive_narrative,
            chart_spec=state.chart_spec,
            preview_data=preview,
            thought_stream=state.thought_stream
        )
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/query/stream")
async def stream_query(query: str = Query(..., description="Business analytical query")):
    """Server-Sent Events (SSE) streaming endpoint emitting real-time agent thoughts."""
    
    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def _step_callback(event: Dict[str, Any]):
            loop.call_soon_threadsafe(queue.put_nowait, event)

        # Run synchronous multi-agent graph in a separate thread pool
        task = loop.run_in_executor(None, cortex_graph.run, query, None, _step_callback)

        while not task.done() or not queue.empty():
            try:
                event = await asyncio.wait_for(queue.get(), timeout=0.1)
                yield f"data: {json.dumps(event)}\n\n"
            except asyncio.TimeoutError:
                await asyncio.sleep(0.05)

        # Obtain final state
        state = await task
        final_payload = {
            "type": "FINAL_RESULT",
            "session_id": state.session_id,
            "domain": state.domain,
            "sql": state.candidate_sql,
            "rows": len(state.query_result),
            "groundedness": state.groundedness_score,
            "narrative": state.executive_narrative,
            "chart_spec": state.chart_spec,
            "data_preview": state.query_result.head(10).to_dict(orient="records") if not state.query_result.empty else []
        }
        yield f"data: {json.dumps(final_payload)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/v1/audit/trails")
async def get_audit_trails(limit: int = 10):
    """Retrieves recent governance and agent telemetry audit trails."""
    records = telemetry.audit_records[-limit:]
    return [
        {
            "session_id": r.session_id,
            "query": r.user_query,
            "start_time": r.start_time,
            "total_latency_ms": r.total_latency_ms,
            "ast_passed": r.ast_check_passed,
            "groundedness": r.groundedness_score,
            "steps_count": len(r.steps),
            "steps": [s.__dict__ for s in r.steps]
        }
        for r in records
    ]
