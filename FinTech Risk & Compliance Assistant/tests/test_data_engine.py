"""
Unit and integration test suite for Phase 1: Data Engineering Layer.
Tests:
1. Window Function Deduplication (ROW_NUMBER() OVER ...)
2. SCD Type 2 State Transitions & Idempotency
3. Temporal Point-in-Time Time-Travel Queries
"""

import pytest
from datetime import datetime
from src.data_engine.seed_data import seed_database
from src.data_engine.deduplicator import TransactionDeduplicator
from src.data_engine.scd2_manager import SCD2CreditManager


@pytest.fixture(scope="module", autouse=True)
def setup_test_database():
    """Seeds the database once before all tests in this module."""
    seed_database()


def test_transaction_deduplication_pipeline():
    """
    Validates that:
    - Exactly 100 unique transactions are inserted into transactions_clean
    - 33 duplicate raw records are filtered out
    - Running the pipeline a second time is strictly idempotent (0 new inserts)
    """
    report = TransactionDeduplicator.run_deduplication()

    assert report["total_raw_records"] == 133
    assert report["duplicated_reference_keys"] == 33
    assert report["new_clean_inserted"] == 100
    assert report["total_clean_warehouse_records"] == 100
    assert report["purged_duplicate_rows"] == 33

    # Test Idempotency: re-running should insert 0 new records
    second_run = TransactionDeduplicator.run_deduplication()
    assert second_run["new_clean_inserted"] == 0
    assert second_run["total_clean_warehouse_records"] == 100


def test_scd2_time_travel_queries():
    """
    Validates temporal auditability for BORR-TECH-001:
    - 2024-06-01: Rating should be 'BBB' (Score 685)
    - 2024-12-01: Rating should be 'A' (Score 735)
    - 2025-05-01: Rating should be 'AA' (Score 780)
    """
    borrower_id = "BORR-TECH-001"

    # Query 1: June 2024 (Before Series C upgrade)
    profile_jun_2024 = SCD2CreditManager.get_profile_at_timestamp(
        borrower_id=borrower_id,
        target_time=datetime(2024, 6, 1, 0, 0, 0),
    )
    assert profile_jun_2024 is not None
    assert profile_jun_2024["rating_grade"] == "BBB"
    assert profile_jun_2024["credit_score"] == 685
    assert profile_jun_2024["is_current"] is False

    # Query 2: Dec 2024 (After Series C upgrade, before 2025 upgrade)
    profile_dec_2024 = SCD2CreditManager.get_profile_at_timestamp(
        borrower_id=borrower_id,
        target_time=datetime(2024, 12, 1, 0, 0, 0),
    )
    assert profile_dec_2024 is not None
    assert profile_dec_2024["rating_grade"] == "A"
    assert profile_dec_2024["credit_score"] == 735
    assert profile_dec_2024["is_current"] is False

    # Query 3: May 2025 (Latest active state)
    profile_may_2025 = SCD2CreditManager.get_profile_at_timestamp(
        borrower_id=borrower_id,
        target_time=datetime(2025, 5, 1, 0, 0, 0),
    )
    assert profile_may_2025 is not None
    assert profile_may_2025["rating_grade"] == "AA"
    assert profile_may_2025["credit_score"] == 780
    assert profile_may_2025["is_current"] is True


def test_scd2_current_profile_and_audit_trail():
    """
    Validates that:
    - get_current_profile returns only the active is_current=True record
    - get_audit_trail returns all versions in ascending chronological sequence
    """
    borrower_id = "BORR-RETL-004"

    # Distressed borrower should currently be CCC
    current = SCD2CreditManager.get_current_profile(borrower_id)
    assert current is not None
    assert current["rating_grade"] == "CCC"
    assert current["credit_score"] == 495
    assert current["is_current"] is True
    assert current["effective_end_date"] is None

    # Audit trail should have 3 distinct historical stages (BB -> B -> CCC)
    trail = SCD2CreditManager.get_audit_trail(borrower_id)
    assert len(trail) == 3
    assert [r["rating_grade"] for r in trail] == ["BB", "B", "CCC"]
    assert [r["is_current"] for r in trail] == [False, False, True]


def test_scd2_idempotency_when_no_change():
    """Validates that updating with identical data does not create redundant history rows."""
    borrower_id = "BORR-HLTH-002"
    trail_before = SCD2CreditManager.get_audit_trail(borrower_id)

    # Attempt upsert with unchanged metrics
    result = SCD2CreditManager.upsert_credit_profile(
        borrower_id=borrower_id,
        credit_score=710,
        rating_grade="A-",
        pd_estimate=0.022,
        debt_to_equity=1.10,
        interest_coverage_ratio=4.8,
        annual_revenue_usd=55000000.0,
        change_reason="Duplicate check",
    )

    assert result["status"] == "NO_OP"
    trail_after = SCD2CreditManager.get_audit_trail(borrower_id)
    assert len(trail_before) == len(trail_after)
