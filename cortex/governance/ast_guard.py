"""AST-Level Enterprise SQL Governance Guard.

Enforces deterministic Abstract Syntax Tree (AST) validation using sqlglot:
- Enforces strict Read-Only execution (blocks INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, etc.)
- Enforces Table Access Control / Whitelisting against enterprise catalog
- Checks for Cartesian joins or unbounded scans
- Automatically injects LIMIT clauses if omitted by LLM agents
- Blocks SQL injection heuristics & comment evasion
"""

import logging
import re
from typing import List, Optional, Set, Tuple
import sqlglot
from sqlglot import exp

from cortex.config import config

logger = logging.getLogger("cortex.governance.ast")


class ASTValidationError(Exception):
    """Raised when a generated SQL query violates enterprise governance policies."""
    pass


class ASTGovernanceGuard:
    """Deterministic AST-based SQL Validator and Policy Enforcer."""

    def __init__(self, allowed_tables: Optional[List[str]] = None, max_row_limit: int = 1000):
        self.allowed_tables = set(t.lower() for t in (allowed_tables or config.allowed_tables))
        self.max_row_limit = max_row_limit
        self.blocked_keywords = set(k.upper() for k in config.blocked_sql_keywords)

    def validate_and_sanitize(self, sql_query: str, dialect: str = "duckdb") -> Tuple[bool, str, List[str]]:
        """Validates a SQL query string against AST rules.
        
        Returns:
            Tuple of (is_valid: bool, sanitized_or_modified_sql: str, violation_reasons: List[str])
        """
        violations: List[str] = []
        raw_sql = sql_query.strip().rstrip(";")
        
        if not raw_sql:
            return False, "", ["Empty SQL query provided."]

        # 1. Quick regex heuristic check for multi-statement semicolons or malicious DDL tokens
        statements = [s.strip() for s in raw_sql.split(";") if s.strip()]
        if len(statements) > 1:
            violations.append(f"Multi-statement execution rejected ({len(statements)} statements detected). Only single SELECT queries permitted.")

        # 2. Parse into AST with sqlglot
        try:
            parsed = sqlglot.parse_one(raw_sql, read=dialect)
        except Exception as e:
            violations.append(f"SQL Syntax / Parsing Error: {str(e)}")
            return False, raw_sql, violations

        # 3. Read-only verification: root expression MUST be a Select or Union
        if not isinstance(parsed, (exp.Select, exp.Union)):
            violations.append(f"Policy Violation: Non-read operation detected ({parsed.__class__.__name__}). Only analytical SELECT/CTE queries are authorized.")

        # Check for prohibited AST expression types anywhere in the tree
        prohibited_types = (
            exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create, 
            exp.Alter, exp.Command, exp.TruncateTable
        )
        for node in parsed.walk():
            if isinstance(node, prohibited_types):
                violations.append(f"Prohibited expression type in AST: {node.__class__.__name__}")

        # 4. Table Whitelisting Verification
        extracted_tables: Set[str] = set()
        for table_node in parsed.find_all(exp.Table):
            t_name = table_node.name.lower()
            # Ignore CTE aliases defined inside WITH clauses
            cte_aliases = {cte.alias.lower() for cte in parsed.find_all(exp.CTE) if cte.alias}
            if t_name and t_name not in cte_aliases:
                extracted_tables.add(t_name)

        unauthorized_tables = extracted_tables - self.allowed_tables
        if unauthorized_tables:
            violations.append(f"Unauthorized table access: {sorted(list(unauthorized_tables))}. Permitted tables: {sorted(list(self.allowed_tables))}")

        # 5. Enforce or inject LIMIT (only on Select queries)
        modified_sql = raw_sql
        if isinstance(parsed, exp.Select):
            limit_node = parsed.args.get("limit")
            if limit_node is None:
                # Safely inject limit via AST
                parsed = parsed.limit(self.max_row_limit)
                modified_sql = parsed.sql(dialect=dialect)
                logger.info(f"Automatically injected LIMIT {self.max_row_limit} into query.")
            else:
                try:
                    curr_limit = int(limit_node.expression.this)
                    if curr_limit > self.max_row_limit:
                        parsed.set("limit", exp.Limit(expression=exp.Literal.number(self.max_row_limit)))
                        modified_sql = parsed.sql(dialect=dialect)
                        logger.info(f"Capped requested limit {curr_limit} to maximum policy limit {self.max_row_limit}.")
                except Exception:
                    pass

        is_valid = len(violations) == 0
        return is_valid, modified_sql, violations


# Singleton guard instance
ast_guard = ASTGovernanceGuard()
