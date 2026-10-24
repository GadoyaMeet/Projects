"""
Unit test suite for Phase 5: Agentic Workflow & Multi-Agent Underwriting Coordination.
"""

import pytest
from src.data_engine.seed_data import seed_database
from src.agents.workflow import UnderwritingGraphWorkflow


@pytest.fixture(scope="module", autouse=True)
def prepare_database():
    seed_database()


def test_multi_agent_workflow_healthy_borrower():
    """
    Validates end-to-end multi-agent underwriting for Apex Cloud Solutions:
    - Router extracts entity
    - SQL agent fetches AA rating
    - ML model outputs LOW default risk
    - RAG agent pulls debt maturity schedule
    - Synthesizer generates formal credit memo with APPROVED verdict and citations
    """
    query = "Please prepare a comprehensive credit committee underwriting memo for Apex Cloud Solutions requesting a $10M revolving facility."
    state = UnderwritingGraphWorkflow.run(
        user_query=query,
        borrower_id="BORR-TECH-001",
        facility_amount_usd=10000000.0,
    )

    assert state.borrower_id == "BORR-TECH-001"
    assert state.sql_data["master"]["company_name"] == "Apex Cloud Solutions Inc."
    assert state.sql_data["current_credit_profile"]["rating_grade"] == "AA"
    assert state.ml_prediction["risk_tier"] in ["LOW", "MODERATE"]
    assert state.rag_data is not None and len(state.rag_data) > 0
    assert state.underwriting_memo is not None
    assert "RECOMMEND APPROVAL" in state.underwriting_memo
    assert len(state.citations) >= 3
    assert len(state.agent_logs) >= 5


def test_multi_agent_workflow_distressed_borrower():
    """
    Validates end-to-end multi-agent underwriting for distressed OmniCommerce:
    - SQL agent fetches CCC rating
    - ML model flags elevated/critical default risk
    - RAG agent pulls covenant breach notice
    - Synthesizer generates formal DECLINE credit decision
    """
    query = "Review OmniCommerce retail request for credit extension of $5M."
    state = UnderwritingGraphWorkflow.run(
        user_query=query,
        borrower_id="BORR-RETL-004",
        facility_amount_usd=5000000.0,
    )

    assert state.borrower_id == "BORR-RETL-004"
    assert state.sql_data["current_credit_profile"]["rating_grade"] == "CCC"
    assert state.ml_prediction["risk_tier"] in ["HIGH", "CRITICAL"]
    assert "DECLINE" in state.underwriting_memo or "REJECTED" in state.underwriting_memo
    assert len(state.citations) >= 3
