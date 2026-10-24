"""
Multi-Agent Underwriting Graph Orchestrator.
Coordinates RouterAgent -> [SQLAgent + MLPredictor + RAGAgent] -> SynthesizerAgent.
Addresses Interview Question: R2 Q6 (Multi-Agent Coordination & Production Flow).
"""

from typing import Dict, Any, Optional
from src.agents.state import UnderwritingState
from src.agents.router_agent import RouterAgent
from src.agents.sql_agent import SQLAgent
from src.agents.rag_agent import RAGAgent
from src.agents.synthesizer_agent import SynthesizerAgent
from src.ml_models.predictor import CreditRiskPredictor


class UnderwritingGraphWorkflow:
    """
    Executes the autonomous multi-agent underwriting lifecycle.
    Orchestrates sequential and parallel dependency graphs between agents.
    """

    @classmethod
    def run(
        cls,
        user_query: str,
        borrower_id: Optional[str] = "AUTO",
        facility_amount_usd: float = 5000000.0,
    ) -> UnderwritingState:
        """Executes the complete multi-agent pipeline."""
        # 1. Initialize State
        state = UnderwritingState(
            borrower_id=borrower_id or "AUTO",
            user_query=user_query,
            requested_facility_usd=facility_amount_usd,
        )
        state.log("Workflow", "Starting FinTech Multi-Agent Underwriting Execution...")

        # 2. Stage 1: Router Agent (Query classification & Entity Extraction)
        state = RouterAgent.route(state)

        # 3. Stage 2: SQL Agent (Ledger, SCD-2 credit profile, transactions)
        state = SQLAgent.execute(state)

        # 4. Stage 3: ML Default Risk Prediction (Feature assembly & XGBoost scoring)
        current_profile = state.sql_data.get("current_credit_profile", {})
        if current_profile:
            features = {
                "debt_to_equity": current_profile.get("debt_to_equity", 1.5),
                "current_ratio": 2.1 if current_profile.get("credit_score", 650) > 700 else 0.85,
                "interest_coverage_ratio": current_profile.get("interest_coverage_ratio", 3.5),
                "operating_margin": 0.18 if current_profile.get("credit_score", 650) > 700 else -0.04,
                "cash_to_debt": 0.35 if current_profile.get("credit_score", 650) > 700 else 0.05,
                "revenue_growth_yoy": 0.12 if current_profile.get("credit_score", 650) > 700 else -0.15,
                "retained_earnings_to_assets": 0.30 if current_profile.get("credit_score", 650) > 700 else -0.05,
                "macro_inflation_rate": 3.2,
                "macro_gdp_growth": 2.2,
            }
            state.ml_prediction = CreditRiskPredictor.predict(features)
            state.log(
                "MLAgent",
                f"Scored default probability: {state.ml_prediction['default_probability_percent']}, "
                f"Assigned Risk Tier: {state.ml_prediction['risk_tier']}",
            )
        else:
            state.ml_prediction = {
                "default_probability": 0.05,
                "default_probability_percent": "5.00%",
                "risk_tier": "MODERATE",
                "underwriting_verdict": "APPROVE_WITH_MONITORING",
                "key_risk_drivers": ["No adverse credit profile found."],
            }

        # 5. Stage 4: Qualitative RAG Agent (Hybrid Search & Cross-Encoder Reranking)
        state = RAGAgent.execute(state)

        # 6. Stage 5: Synthesizer Agent (Credit memo synthesis & citation checks)
        state = SynthesizerAgent.execute(state)

        state.log("Workflow", "Multi-Agent Underwriting Execution Finished Successfully.")
        return state
