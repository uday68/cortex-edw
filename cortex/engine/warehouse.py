"""Enterprise Warehouse Engine Adapter.

Provides high-performance analytical query execution against OLAP databases (DuckDB & SQLite fallback)
with automated seeding, connection pooling, and schema introspection.
"""

import logging
import sqlite3
import time
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from cortex.config import config
from cortex.engine.seed_data import seed_all_tables

logger = logging.getLogger("cortex.engine.warehouse")

try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False


class WarehouseEngine:
    """Enterprise OLAP Warehouse Engine.
    
    Defaults to DuckDB for vectorized analytical OLAP operations (as typical in Apple AiDP EDW),
    with automatic in-memory SQLite compatibility fallback.
    """
    
    def __init__(self, db_path: Optional[str] = None, force_engine: Optional[str] = None):
        self.db_path = db_path or config.db_path
        self.engine_type = force_engine or ("duckdb" if DUCKDB_AVAILABLE else "sqlite")
        self.duck_conn = None
        self.sqlite_conn = None
        self._initialize_warehouse()
        
    def _initialize_warehouse(self) -> None:
        """Initializes the database connection and seeds enterprise tables."""
        start_time = time.time()
        logger.info(f"Initializing warehouse with engine: {self.engine_type}")
        
        tables = seed_all_tables()
        
        if self.engine_type == "duckdb" and DUCKDB_AVAILABLE:
            self.duck_conn = duckdb.connect(database=self.db_path if self.db_path != ":memory:" else ":memory:")
            for table_name, df in tables.items():
                self.duck_conn.register(f"temp_{table_name}", df)
                self.duck_conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM temp_{table_name}")
                self.duck_conn.unregister(f"temp_{table_name}")
        else:
            self.engine_type = "sqlite"
            self.sqlite_conn = sqlite3.connect(self.db_path if self.db_path != ":memory:" else ":memory:", check_same_thread=False)
            for table_name, df in tables.items():
                df.to_sql(table_name, self.sqlite_conn, if_exists="replace", index=False)
                
        duration = round((time.time() - start_time) * 1000, 2)
        logger.info(f"Warehouse initialized and seeded with {len(tables)} tables in {duration}ms")
        
    def execute_query(self, sql: str, params: Optional[Tuple[Any, ...]] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Executes a SQL query against the warehouse engine and returns a DataFrame and execution metrics."""
        start = time.perf_counter()
        
        # Strip trailing semicolon if needed
        clean_sql = sql.strip().rstrip(";")
        
        try:
            if self.engine_type == "duckdb" and self.duck_conn is not None:
                if params:
                    result = self.duck_conn.execute(clean_sql, params).fetchdf()
                else:
                    result = self.duck_conn.execute(clean_sql).fetchdf()
            else:
                if params:
                    result = pd.read_sql_query(clean_sql, self.sqlite_conn, params=params)
                else:
                    result = pd.read_sql_query(clean_sql, self.sqlite_conn)
                    
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            meta = {
                "success": True,
                "row_count": len(result),
                "columns": list(result.columns),
                "execution_time_ms": elapsed_ms,
                "engine": self.engine_type,
                "error": None
            }
            return result, meta
            
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            meta = {
                "success": False,
                "row_count": 0,
                "columns": [],
                "execution_time_ms": elapsed_ms,
                "engine": self.engine_type,
                "error": str(e)
            }
            return pd.DataFrame(), meta

    def get_table_schema(self, table_name: str) -> List[Dict[str, str]]:
        """Returns column names and types for a given table."""
        if self.engine_type == "duckdb" and self.duck_conn is not None:
            res = self.duck_conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()
            return [{"column_name": row[1], "data_type": row[2], "nullable": not row[3]} for row in res]
        else:
            cursor = self.sqlite_conn.cursor()
            res = cursor.execute(f"PRAGMA table_info('{table_name}')").fetchall()
            return [{"column_name": row[1], "data_type": row[2], "nullable": not row[3]} for row in res]

    def get_all_tables(self) -> List[str]:
        """Returns a list of all tables in the warehouse."""
        if self.engine_type == "duckdb" and self.duck_conn is not None:
            res = self.duck_conn.execute("SHOW TABLES").fetchall()
            return [row[0] for row in res]
        else:
            cursor = self.sqlite_conn.cursor()
            res = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            return [row[0] for row in res]
            
    def get_table_preview(self, table_name: str, limit: int = 5) -> pd.DataFrame:
        """Returns sample rows from a table."""
        df, _ = self.execute_query(f"SELECT * FROM {table_name} LIMIT {limit}")
        return df


# Singleton instance
warehouse = WarehouseEngine()
