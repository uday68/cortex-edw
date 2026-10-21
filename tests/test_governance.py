"""Tests for AST-Level SQL Governance, Policy Guard, and PII Sanitizer."""

import pytest
import pandas as pd
from cortex.governance.ast_guard import ASTGovernanceGuard
from cortex.governance.pii_sanitizer import PIISanitizer
from cortex.governance.groundedness import GroundednessGuard


def test_ast_blocks_drop_table():
    guard = ASTGovernanceGuard()
    is_valid, _, violations = guard.validate_and_sanitize("DROP TABLE retail_stores;")
    assert is_valid is False
    assert any("Non-read operation" in v or "Prohibited" in v for v in violations)


def test_ast_blocks_delete_and_update():
    guard = ASTGovernanceGuard()
    is_valid, _, violations = guard.validate_and_sanitize("DELETE FROM retail_store_sales WHERE units_sold = 0")
    assert is_valid is False

    is_valid2, _, violations2 = guard.validate_and_sanitize("UPDATE retail_stores SET square_feet = 99999")
    assert is_valid2 is False


def test_ast_blocks_multi_statement_injection():
    guard = ASTGovernanceGuard()
    is_valid, _, violations = guard.validate_and_sanitize("SELECT * FROM retail_stores; DROP TABLE retail_stores;")
    assert is_valid is False
    assert any("Multi-statement" in v for v in violations)


def test_ast_blocks_unauthorized_tables():
    guard = ASTGovernanceGuard(allowed_tables=["retail_stores"])
    is_valid, _, violations = guard.validate_and_sanitize("SELECT * FROM confidential_internal_payroll")
    assert is_valid is False
    assert any("Unauthorized table access" in v for v in violations)


def test_ast_injects_limit_clause():
    guard = ASTGovernanceGuard(max_row_limit=500)
    is_valid, modified_sql, violations = guard.validate_and_sanitize("SELECT store_name FROM retail_stores")
    assert is_valid is True
    assert "LIMIT 500" in modified_sql.upper()


def test_pii_sanitizer_dataframe():
    sanitizer = PIISanitizer()
    df = pd.DataFrame({
        "customer_email": ["tim.cook@apple.com", "craig.f@apple.com"],
        "units": [10, 20]
    })
    masked = sanitizer.mask_dataframe(df)
    assert masked["customer_email"].iloc[0] != "tim.cook@apple.com"
    assert "****" in masked["customer_email"].iloc[0]


def test_groundedness_guard():
    guard = GroundednessGuard()
    df = pd.DataFrame({"total_net_revenue": [125000.50], "store_name": ["Apple BKC"]})
    narrative = "Apple BKC achieved $125000.50 in total revenue."
    score, ungrounded, _ = guard.evaluate_groundedness(narrative, df)
    assert score == 1.0
    assert len(ungrounded) == 0
