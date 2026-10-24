"""
Integration and End-to-End API test suite for FastAPI backend and guardrails.
"""

import pytest
from fastapi.testclient import TestClient
from src.data_engine.seed_data import seed_database
from src.api.main import app

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def prepare_db():
    seed_database()


def test_get_borrowers_endpoint():
    """Validates /api/borrowers returns master entities with current active scores."""
    response = client.get("/api/borrowers")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5
    apex = next(b for b in data if b["borrower_id"] == "BORR-TECH-001")
    assert apex["current_rating_grade"] == "AA"


def test_scd2_history_endpoint():
    """Validates /api/scd2/history/{borrower_id} returns all chronological versions."""
    response = client.get("/api/scd2/history/BORR-TECH-001")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert [r["rating_grade"] for r in data] == ["BBB", "A", "AA"]


def test_scd2_time_travel_endpoint():
    """Validates /api/scd2/time-travel reconstructs historical state accurately (R2 Q4)."""
    # June 2024 -> BBB
    res_jun = client.get("/api/scd2/time-travel?borrower_id=BORR-TECH-001&date_str=2024-06-01")
    assert res_jun.status_code == 200
    assert res_jun.json()["rating_grade"] == "BBB"

    # Dec 2024 -> A
    res_dec = client.get("/api/scd2/time-travel?borrower_id=BORR-TECH-001&date_str=2024-12-01")
    assert res_dec.status_code == 200
    assert res_dec.json()["rating_grade"] == "A"


def test_ml_predict_endpoint():
    """Validates direct XGBoost risk inference."""
    payload = {
        "debt_to_equity": 1.2,
        "current_ratio": 2.2,
        "interest_coverage_ratio": 6.5,
        "operating_margin": 0.20,
        "cash_to_debt": 0.40,
        "revenue_growth_yoy": 0.12,
        "retained_earnings_to_assets": 0.35,
        "macro_inflation_rate": 3.0,
        "macro_gdp_growth": 2.4,
    }
    response = client.post("/api/ml/predict", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "default_probability" in res
    assert res["risk_tier"] in ["LOW", "MODERATE"]


def test_underwrite_endpoint_and_guardrails():
    """Validates /api/underwrite runs multi-agent workflow and enforces input guardrails."""
    # 1. Valid request
    valid_payload = {
        "borrower_id": "BORR-TECH-001",
        "user_query": "Evaluate Apex Cloud Solutions for a $10,000,000 credit facility expansion.",
        "requested_facility_usd": 10000000.0,
    }
    res = client.post("/api/underwrite", json=valid_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert "RECOMMEND APPROVAL" in data["underwriting_memo"]
    assert data["llmops_metrics"]["guardrail_status"] == "COMPLIANT"

    # 2. Malicious SQL Injection attempt -> must be blocked by input guardrails
    bad_payload = {
        "borrower_id": "BORR-TECH-001",
        "user_query": "SELECT * FROM borrowers; DROP TABLE borrowers; --",
        "requested_facility_usd": 10000000.0,
    }
    bad_res = client.post("/api/underwrite", json=bad_payload)
    assert bad_res.status_code == 422  # Pydantic validation error
