"""
Unit test suite for Phase 2: Predictive ML Modeling.
Tests:
1. Imbalanced data generation & distribution
2. XGBoost training & PR-AUC performance vs baseline
3. CreditRiskPredictor inference & tiering for low-risk vs high-risk borrowers
"""

import pytest
from src.ml_models.dataset_generator import generate_loan_default_dataset
from src.ml_models.train import train_default_risk_model
from src.ml_models.predictor import CreditRiskPredictor


def test_dataset_generation_and_imbalance():
    """Validates that default rate is realistically imbalanced (< 8%)."""
    df = generate_loan_default_dataset(n_samples=1000, random_seed=42)
    assert len(df) == 1000
    assert "defaulted" in df.columns
    default_rate = df["defaulted"].mean()
    assert 0.01 <= default_rate <= 0.08, f"Unexpected default rate: {default_rate}"


def test_model_training_and_metrics():
    """Validates that the trained model outperforms the baseline PR-AUC significantly."""
    results = train_default_risk_model(save_artifacts=True)
    meta = results["metadata"]

    assert meta["model_type"] == "XGBClassifier"
    assert meta["roc_auc"] > 0.80
    # PR-AUC must be substantially higher than random baseline
    assert meta["pr_auc"] > meta["baseline_pr_auc"] * 5
    assert "feature_importance_gain" in meta
    assert len(meta["feature_importance_gain"]) == 9


def test_predictor_healthy_borrower_tier():
    """Validates that a financially strong company receives LOW or MODERATE risk tier."""
    healthy_features = {
        "debt_to_equity": 0.85,
        "current_ratio": 2.4,
        "interest_coverage_ratio": 8.5,
        "operating_margin": 0.22,
        "cash_to_debt": 0.45,
        "revenue_growth_yoy": 0.15,
        "retained_earnings_to_assets": 0.40,
        "macro_inflation_rate": 2.8,
        "macro_gdp_growth": 2.5,
    }
    prediction = CreditRiskPredictor.predict(healthy_features)

    assert prediction["default_probability"] < 0.15
    assert prediction["risk_tier"] in ["LOW", "MODERATE"]
    assert "APPROVE" in prediction["underwriting_verdict"]


def test_predictor_distressed_borrower_tier():
    """Validates that a highly leveraged company with negative coverage receives HIGH or CRITICAL risk."""
    distressed_features = {
        "debt_to_equity": 5.2,
        "current_ratio": 0.65,
        "interest_coverage_ratio": 0.70,
        "operating_margin": -0.08,
        "cash_to_debt": 0.03,
        "revenue_growth_yoy": -0.18,
        "retained_earnings_to_assets": -0.10,
        "macro_inflation_rate": 5.5,
        "macro_gdp_growth": 0.8,
    }
    prediction = CreditRiskPredictor.predict(distressed_features)

    assert prediction["default_probability"] > 0.30
    assert prediction["risk_tier"] in ["HIGH", "CRITICAL"]
    assert len(prediction["key_risk_drivers"]) >= 3
