"""
FastAPI Backend Server for FinTech Risk & Compliance Assistant.
Provides RESTful APIs for Multi-Agent Underwriting, SCD-2 Audit Queries, ML Scoring, and UI serving.
"""

import os
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.data_engine.database import get_db_session
from src.data_engine.models import Borrower
from src.data_engine.scd2_manager import SCD2CreditManager
from src.ml_models.predictor import CreditRiskPredictor
from src.agents.workflow import UnderwritingGraphWorkflow
from src.rag.retriever import HybridRetriever
from src.agents.rag_agent import RAGAgent
from src.api.guardrails import UnderwriteRequest, FinancialGuardrails

app = FastAPI(
    title="FinTech Risk & Compliance Assistant API",
    description="Enterprise Multi-Agent Underwriting, Temporal SCD-2 Audits, and Default ML Classifier",
    version="1.0.0",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# System LLMOps telemetry metrics
telemetry = {
    "total_requests": 0,
    "total_latency_ms": 0.0,
    "guardrails_passed": 0,
    "guardrails_flagged": 0,
}


@app.post("/api/underwrite")
def execute_underwriting(req: UnderwriteRequest) -> Dict[str, Any]:
    """
    Executes the full multi-agent underwriting lifecycle with input/output guardrails.
    """
    start_time = time.time()
    telemetry["total_requests"] += 1

    # 1. Input Guardrails: PII Masking
    clean_query = FinancialGuardrails.mask_pii(req.user_query)

    # 2. Execute Multi-Agent Workflow
    try:
        state = UnderwritingGraphWorkflow.run(
            user_query=clean_query,
            borrower_id=req.borrower_id,
            facility_amount_usd=req.requested_facility_usd,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent workflow error: {str(e)}")

    # 3. Output Compliance Guardrails: Citation & Veracity Verification
    is_compliant, coverage, warnings = FinancialGuardrails.verify_output_citations(
        memo=state.underwriting_memo or "",
        citations=state.citations,
    )

    if is_compliant:
        telemetry["guardrails_passed"] += 1
    else:
        telemetry["guardrails_flagged"] += 1

    latency_ms = round((time.time() - start_time) * 1000, 2)
    telemetry["total_latency_ms"] += latency_ms

    return {
        "status": "SUCCESS",
        "borrower_id": state.borrower_id,
        "company_name": state.sql_data.get("master", {}).get("company_name", state.borrower_id),
        "requested_facility_usd": req.requested_facility_usd,
        "underwriting_verdict": state.ml_prediction.get("underwriting_verdict", "PENDING"),
        "risk_tier": state.ml_prediction.get("risk_tier", "MODERATE"),
        "default_probability": state.ml_prediction.get("default_probability", 0.0),
        "default_probability_percent": state.ml_prediction.get("default_probability_percent", "0.0%"),
        "underwriting_memo": state.underwriting_memo,
        "citations": state.citations,
        "agent_logs": state.agent_logs,
        "llmops_metrics": {
            "latency_ms": latency_ms,
            "guardrail_status": "COMPLIANT" if is_compliant else "FLAGGED",
            "citation_grounding_score": coverage,
            "compliance_warnings": warnings,
            "estimated_token_cost_usd": 0.0018,
        },
    }


@app.get("/api/borrowers")
def get_all_borrowers() -> List[Dict[str, Any]]:
    """Returns all registered corporate entities with active SCD-2 risk profiles."""
    with get_db_session() as session:
        borrowers = session.query(Borrower).all()
        results = []
        for b in borrowers:
            profile = SCD2CreditManager.get_current_profile(b.borrower_id)
            results.append({
                "borrower_id": b.borrower_id,
                "company_name": b.company_name,
                "registration_no": b.registration_no,
                "industry": b.industry,
                "current_credit_score": profile["credit_score"] if profile else None,
                "current_rating_grade": profile["rating_grade"] if profile else None,
                "current_pd_estimate": f"{profile['pd_estimate']*100:.2f}%" if profile else None,
                "current_debt_to_equity": profile["debt_to_equity"] if profile else None,
            })
        return results


@app.get("/api/scd2/history/{borrower_id}")
def get_scd2_history(borrower_id: str) -> List[Dict[str, Any]]:
    """Returns the full temporal SCD-2 audit trail for a borrower."""
    trail = SCD2CreditManager.get_audit_trail(borrower_id)
    if not trail:
        raise HTTPException(status_code=404, detail=f"No credit history found for borrower {borrower_id}")
    return trail


@app.get("/api/scd2/time-travel")
def get_scd2_point_in_time(
    borrower_id: str = Query(..., description="Target borrower ID"),
    date_str: str = Query(..., description="Target date in YYYY-MM-DD format"),
) -> Dict[str, Any]:
    """Reconstructs the borrower's risk profile at target historical date (R2 Q4)."""
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Expected YYYY-MM-DD.")

    profile = SCD2CreditManager.get_profile_at_timestamp(borrower_id, target_date)
    if not profile:
        raise HTTPException(status_code=404, detail=f"No record active on {date_str} for borrower {borrower_id}")
    return profile


@app.post("/api/ml/predict")
def predict_default(features: Dict[str, float]) -> Dict[str, Any]:
    """Direct scoring of loan default risk using the trained XGBoost model."""
    return CreditRiskPredictor.predict(features)


@app.get("/api/metrics")
def get_llmops_metrics() -> Dict[str, Any]:
    """Returns LLMOps telemetry and reliability indicators."""
    total = max(telemetry["total_requests"], 1)
    avg_latency = telemetry["total_latency_ms"] / total
    compliance_rate = (telemetry["guardrails_passed"] / total) * 100

    return {
        "total_underwriting_requests": telemetry["total_requests"],
        "average_latency_ms": round(avg_latency, 2),
        "guardrail_compliance_rate": f"{compliance_rate:.1f}%",
        "active_models": {
            "ml_classifier": "XGBoost v3.4.1 (scale_pos_weight=51.5)",
            "retriever": "Hybrid BM25Okapi + SemanticDenseEmbedder",
            "reranker": "CrossEncoder Token-Numerical Reranker",
            "agent_orchestrator": "UnderwritingGraphWorkflow (4-Agent State Machine)",
        },
    }


# Static UI serving
UI_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ui")
if os.path.exists(UI_DIR):
    app.mount("/ui", StaticFiles(directory=UI_DIR), name="ui")


@app.get("/")
def serve_dashboard():
    """Serves the main web dashboard."""
    index_file = os.path.join(UI_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "FinTech Risk & Compliance Assistant API is live. Navigate to /docs for Swagger UI."}
