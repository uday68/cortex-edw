"""Tests for Warehouse OLAP Engine and Synthetic Enterprise Data Seeding."""

import pytest
import pandas as pd
from cortex.engine.warehouse import WarehouseEngine


def test_warehouse_initialization_and_seeding():
    engine = WarehouseEngine(force_engine="duckdb")
    tables = engine.get_all_tables()
    
    assert len(tables) >= 8
    assert "retail_stores" in tables
    assert "retail_store_sales" in tables
    assert "applecare_incidents" in tables
    assert "supply_chain_shipments" in tables
    assert "services_subscriptions" in tables


def test_warehouse_query_execution():
    engine = WarehouseEngine(force_engine="duckdb")
    df, meta = engine.execute_query("SELECT store_name, region FROM retail_stores LIMIT 3")
    
    assert meta["success"] is True
    assert len(df) == 3
    assert "store_name" in df.columns
    assert "region" in df.columns
    assert meta["execution_time_ms"] > 0


def test_warehouse_error_handling():
    engine = WarehouseEngine(force_engine="duckdb")
    df, meta = engine.execute_query("SELECT * FROM non_existent_table_xyz")
    
    assert meta["success"] is False
    assert meta["error"] is not None
    assert len(df) == 0
