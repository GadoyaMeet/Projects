"""
Synthetic Financial Dataset Generator for Loan Default Risk Modeling.
Generates realistic corporate accounting metrics and macroeconomic indicators
with an authentic class imbalance (~5% default rate).
Addresses Interview Questions: R1 Q6 (Handling Imbalanced Data), R2 Q2 (Feature Selection).
"""

import numpy as np
import pandas as pd
from typing import Tuple


FEATURE_NAMES = [
    "debt_to_equity",
    "current_ratio",
    "interest_coverage_ratio",
    "operating_margin",
    "cash_to_debt",
    "revenue_growth_yoy",
    "retained_earnings_to_assets",
    "macro_inflation_rate",
    "macro_gdp_growth",
]


def generate_loan_default_dataset(n_samples: int = 3000, random_seed: int = 42) -> pd.DataFrame:
    """
    Generates synthetic corporate credit records with realistic distributions.
    Features:
    - debt_to_equity: Log-normal, median ~1.5x, higher in distressed firms.
    - current_ratio: Normal, mean ~1.8x, distressed < 1.0x (working capital deficit).
    - interest_coverage_ratio: EBITDA / Interest, mean ~4.5x, < 1.5x indicates high risk.
    - operating_margin: Mean ~12%, negative in struggling firms.
    - cash_to_debt: Mean ~0.25x, low liquidity in defaults.
    - revenue_growth_yoy: Mean ~8%, negative in declining businesses.
    - retained_earnings_to_assets: Altman Z component, lower in defaults.
    - macro_inflation_rate: Macro shock variable (2.0% - 6.5%).
    - macro_gdp_growth: Macro GDP growth (0.5% - 4.0%).
    """
    np.random.seed(random_seed)

    # 1. Base corporate metrics
    debt_to_equity = np.random.lognormal(mean=0.35, sigma=0.55, size=n_samples)
    current_ratio = np.random.normal(loc=1.85, scale=0.6, size=n_samples)
    current_ratio = np.clip(current_ratio, 0.4, 5.0)

    interest_coverage = np.random.normal(loc=4.2, scale=2.5, size=n_samples)
    interest_coverage = np.clip(interest_coverage, -1.0, 15.0)

    operating_margin = np.random.normal(loc=0.14, scale=0.10, size=n_samples)
    cash_to_debt = np.random.exponential(scale=0.25, size=n_samples)
    cash_to_debt = np.clip(cash_to_debt, 0.01, 1.5)

    revenue_growth = np.random.normal(loc=0.07, scale=0.15, size=n_samples)
    retained_earnings_ratio = np.random.normal(loc=0.28, scale=0.18, size=n_samples)

    # Macroeconomic environment
    macro_inflation = np.random.uniform(2.0, 6.0, size=n_samples)
    macro_gdp = np.random.uniform(0.5, 3.5, size=n_samples)

    # 2. Non-linear default risk score (Log-odds calculation)
    # Severe leverage, negative coverage, illiquid cash, and high inflation push log-odds up
    log_odds = (
        -4.2  # Base negative intercept ensures ~5% default rate
        + 0.85 * (debt_to_equity - 1.5)
        - 1.10 * (current_ratio - 1.8)
        - 0.55 * (interest_coverage - 4.0)
        - 4.50 * (operating_margin - 0.12)
        - 2.80 * (cash_to_debt - 0.25)
        - 2.20 * revenue_growth
        - 3.10 * retained_earnings_ratio
        + 0.25 * (macro_inflation - 3.5)
        - 0.40 * (macro_gdp - 2.0)
    )

    # Add realistic market noise
    noise = np.random.logistic(loc=0, scale=0.8, size=n_samples)
    latent_risk = log_odds + noise

    # Convert to probability and binary target
    prob_default = 1.0 / (1.0 + np.exp(-latent_risk))
    defaulted = (prob_default > 0.5).astype(int)

    df = pd.DataFrame({
        "debt_to_equity": np.round(debt_to_equity, 3),
        "current_ratio": np.round(current_ratio, 3),
        "interest_coverage_ratio": np.round(interest_coverage, 2),
        "operating_margin": np.round(operating_margin, 4),
        "cash_to_debt": np.round(cash_to_debt, 3),
        "revenue_growth_yoy": np.round(revenue_growth, 4),
        "retained_earnings_to_assets": np.round(retained_earnings_ratio, 3),
        "macro_inflation_rate": np.round(macro_inflation, 2),
        "macro_gdp_growth": np.round(macro_gdp, 2),
        "defaulted": defaulted,
    })

    return df


if __name__ == "__main__":
    data = generate_loan_default_dataset()
    default_count = data["defaulted"].sum()
    default_pct = (default_count / len(data)) * 100
    print(f"Dataset generated with {len(data)} rows.")
    print(f"Defaults: {default_count} / {len(data)} ({default_pct:.2f}% imbalanced default rate).")
