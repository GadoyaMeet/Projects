"""
XGBoost Model Training & Evaluation on Imbalanced Financial Loan Data.
Addresses Interview Questions:
- R1 Q6: Handling Imbalanced Data (scale_pos_weight vs SMOTE, cost-sensitive learning)
- R2 Q2: Feature Selection & Risk Drivers
- R2 Q3: Model Evaluation (PR-AUC, F1-score vs Accuracy)
"""

import os
import json
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
    precision_recall_curve,
    f1_score,
    confusion_matrix,
    classification_report,
)
from src.ml_models.dataset_generator import generate_loan_default_dataset, FEATURE_NAMES

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "xgboost_default_model.json")
METADATA_PATH = os.path.join(MODEL_DIR, "model_metadata.json")


def train_default_risk_model(save_artifacts: bool = True) -> dict:
    """
    Trains an XGBoost binary classification model to predict corporate loan default.
    Handles class imbalance using scale_pos_weight and evaluates primarily via PR-AUC and F1.
    """
    os.makedirs(MODEL_DIR, exist_ok=True)

    # 1. Generate & prepare data
    df = generate_loan_default_dataset(n_samples=3500, random_seed=42)
    X = df[FEATURE_NAMES]
    y = df["defaulted"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    n_neg = int((y_train == 0).sum())
    n_pos = int((y_train == 1).sum())
    scale_pos_weight = n_neg / n_pos

    print(f"Training Samples: {len(X_train)} (Non-Defaults: {n_neg}, Defaults: {n_pos})")
    print(f"Class Imbalance Ratio: {scale_pos_weight:.2f}:1 -> Setting scale_pos_weight = {scale_pos_weight:.2f}")

    # 2. Configure & Train XGBoost
    model = XGBClassifier(
        n_estimators=180,
        max_depth=4,
        learning_rate=0.04,
        subsample=0.85,
        colsample_bytree=0.85,
        scale_pos_weight=scale_pos_weight,
        eval_metric="aucpr",
        random_state=42,
    )

    model.fit(X_train, y_train)

    # 3. Predict probabilities on unseen test set
    y_prob = model.predict_proba(X_test)[:, 1]

    # 4. Evaluation Metrics
    # Area Under Precision-Recall Curve (PR-AUC) is the gold standard for rare-event financial risk
    pr_auc = float(average_precision_score(y_test, y_prob))
    roc_auc = float(roc_auc_score(y_test, y_prob))
    baseline_pr_auc = float(y_test.mean())

    # Find optimal classification threshold maximizing F1-score
    precisions, recalls, thresholds = precision_recall_curve(y_test, y_prob)
    f1_scores = (2 * precisions * recalls) / (precisions + recalls + 1e-10)
    best_idx = int(np.argmax(f1_scores))
    optimal_threshold = float(thresholds[min(best_idx, len(thresholds) - 1)])
    best_f1 = float(f1_scores[best_idx])

    y_pred_optimal = (y_prob >= optimal_threshold).astype(int)
    cm = confusion_matrix(y_test, y_pred_optimal).tolist()

    # Feature Importance (Gain)
    importance_dict = dict(zip(FEATURE_NAMES, [float(x) for x in model.feature_importances_]))
    sorted_importance = dict(sorted(importance_dict.items(), key=lambda item: item[1], reverse=True))

    metadata = {
        "model_type": "XGBClassifier",
        "scale_pos_weight": round(scale_pos_weight, 2),
        "test_samples": len(y_test),
        "test_default_count": int(y_test.sum()),
        "baseline_pr_auc": round(baseline_pr_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "roc_auc": round(roc_auc, 4),
        "optimal_threshold": round(optimal_threshold, 4),
        "f1_at_optimal_threshold": round(best_f1, 4),
        "confusion_matrix": {
            "true_negatives": cm[0][0],
            "false_positives": cm[0][1],
            "false_negatives": cm[1][0],
            "true_positives": cm[1][1],
        },
        "feature_importance_gain": sorted_importance,
    }

    if save_artifacts:
        model.save_model(MODEL_PATH)
        with open(METADATA_PATH, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        print(f"Model saved to: {MODEL_PATH}")
        print(f"Metadata saved to: {METADATA_PATH}")

    return {
        "model": model,
        "metadata": metadata,
    }


if __name__ == "__main__":
    results = train_default_risk_model()
    print("\n--- Training Results Summary ---")
    print(json.dumps(results["metadata"], indent=2))
