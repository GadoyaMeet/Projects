"""
Credit Risk Inference Engine.
Loads trained XGBoost model and scores loan default probability with risk factor attribution.
"""

import os
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from xgboost import XGBClassifier
from src.ml_models.dataset_generator import FEATURE_NAMES

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "xgboost_default_model.json")
METADATA_PATH = os.path.join(MODEL_DIR, "model_metadata.json")


class CreditRiskPredictor:
    """Production predictor for borrower default risk and underwriting tiering."""

    _model: XGBClassifier = None
    _metadata: Dict[str, Any] = None

    @classmethod
    def get_model(cls) -> XGBClassifier:
        """Lazy-loads or auto-trains model if not loaded."""
        if cls._model is None:
            if not os.path.exists(MODEL_PATH):
                from src.ml_models.train import train_default_risk_model
                train_default_risk_model(save_artifacts=True)

            model = XGBClassifier()
            model.load_model(MODEL_PATH)
            cls._model = model

            if os.path.exists(METADATA_PATH):
                with open(METADATA_PATH, "r", encoding="utf-8") as f:
                    cls._metadata = json.load(f)
            else:
                cls._metadata = {"optimal_threshold": 0.45}

        return cls._model

    @classmethod
    def predict(cls, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculates default probability and risk rating from input financial features.
        """
        model = cls.get_model()

        # Build feature vector ensuring correct column order
        row_dict = {}
        for f in FEATURE_NAMES:
            if f not in features:
                # Fallback to standard market median defaults
                defaults_map = {
                    "debt_to_equity": 1.5,
                    "current_ratio": 1.8,
                    "interest_coverage_ratio": 4.0,
                    "operating_margin": 0.12,
                    "cash_to_debt": 0.25,
                    "revenue_growth_yoy": 0.08,
                    "retained_earnings_to_assets": 0.25,
                    "macro_inflation_rate": 3.2,
                    "macro_gdp_growth": 2.1,
                }
                row_dict[f] = defaults_map.get(f, 0.0)
            else:
                row_dict[f] = float(features[f])

        df_in = pd.DataFrame([row_dict])[FEATURE_NAMES]
        prob = float(model.predict_proba(df_in)[0, 1])

        threshold = cls._metadata.get("optimal_threshold", 0.45) if cls._metadata else 0.45
        will_default = bool(prob >= threshold)

        # Risk tiering
        if prob < 0.03:
            tier = "LOW"
            verdict = "APPROVE"
            action = "Eligible for prime interest rate and standard covenants."
        elif prob < 0.08:
            tier = "MODERATE"
            verdict = "APPROVE_WITH_MONITORING"
            action = "Eligible for standard facility with quarterly financial reporting."
        elif prob < 0.18:
            tier = "ELEVATED"
            verdict = "CONDITIONAL_APPROVAL"
            action = "Requires senior collateral pledge and 1.5x interest coverage covenant."
        elif prob < 0.35:
            tier = "HIGH"
            verdict = "REFER_TO_CREDIT_COMMITTEE"
            action = "High default probability. Requires personal/corporate guarantees."
        else:
            tier = "CRITICAL"
            verdict = "DECLINE"
            action = "Default probability exceeds risk tolerance threshold. Reject facility."

        # Risk factor attribution (Rule-based explainability flags)
        risk_factors: List[str] = []
        if row_dict["debt_to_equity"] > 2.5:
            risk_factors.append(f"Elevated Debt-to-Equity ({row_dict['debt_to_equity']:.2f}x > 2.50x benchmark)")
        if row_dict["current_ratio"] < 1.0:
            risk_factors.append(f"Working Capital Deficit: Current ratio ({row_dict['current_ratio']:.2f}x < 1.00x)")
        if row_dict["interest_coverage_ratio"] < 1.8:
            risk_factors.append(f"Weak Debt Service: Interest coverage ({row_dict['interest_coverage_ratio']:.2f}x < 1.80x)")
        if row_dict["operating_margin"] < 0:
            risk_factors.append(f"Negative Operating Margin ({row_dict['operating_margin']*100:.1f}%)")
        if row_dict["cash_to_debt"] < 0.10:
            risk_factors.append(f"Severely Strained Liquidity: Cash-to-Debt ({row_dict['cash_to_debt']:.2f}x < 0.10x)")

        return {
            "default_probability": round(prob, 4),
            "default_probability_percent": f"{prob * 100:.2f}%",
            "model_threshold_used": round(threshold, 4),
            "predicted_default": will_default,
            "risk_tier": tier,
            "underwriting_verdict": verdict,
            "recommended_action": action,
            "key_risk_drivers": risk_factors if risk_factors else ["No severe credit warning flags detected."],
            "input_features": row_dict,
        }
