"""Cortex EDW Configuration Module.

Centralized configuration for Enterprise Data Warehouse Agentic Platform.
"""

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import List, Optional


@dataclass
class CortexConfig:
    # Environment
    app_env: str = os.getenv("CORTEX_ENV", "development")
    log_level: str = os.getenv("CORTEX_LOG_LEVEL", "INFO")
    
    # Engine Settings
    engine_type: str = os.getenv("CORTEX_ENGINE", "duckdb")  # duckdb or sqlite
    db_path: str = os.getenv("CORTEX_DB_PATH", ":memory:")
    max_query_time_sec: float = 15.0
    query_result_limit: int = 1000
    
    # LLM Settings (can run mock, local, or API)
    llm_provider: str = os.getenv("CORTEX_LLM_PROVIDER", "gemini")  # gemini, openai, mock
    llm_model: str = os.getenv("CORTEX_LLM_MODEL", "gemini-1.5-pro")
    temperature: float = 0.1
    max_reflection_loops: int = 3
    
    # Governance & Safety
    enforce_read_only: bool = True
    blocked_sql_keywords: List[str] = field(default_factory=lambda: [
        "DROP", "DELETE", "TRUNCATE", "ALTER", "INSERT", "UPDATE", "GRANT", "REVOKE", "EXEC", "EXECUTE"
    ])
    allowed_tables: List[str] = field(default_factory=lambda: [
        "retail_stores",
        "retail_store_sales",
        "retail_inventory",
        "applecare_incidents",
        "service_parts_inventory",
        "supply_chain_shipments",
        "component_suppliers",
        "services_subscriptions",
        "services_daily_metrics"
    ])
    mask_pii_columns: List[str] = field(default_factory=lambda: [
        "customer_email", "phone_number", "serial_number", "ip_address", "credit_card_last4"
    ])
    
    # Vector / Hybrid RAG
    vector_dimension: int = 384
    top_k_schemas: int = 5
    top_k_docs: int = 3
    rrf_k_constant: int = 60  # Reciprocal Rank Fusion constant

    # API & Dashboard
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    dashboard_port: int = 8501


config = CortexConfig()
