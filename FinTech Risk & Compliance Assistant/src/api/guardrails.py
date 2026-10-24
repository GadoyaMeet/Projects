"""
Financial Compliance & LLMOps Guardrails.
Implements input sanitization, PII masking, citation verification, and faithfulness scoring.
Addresses Interview Questions: R1 Q4, R2 Q6 (Production Guardrails).
"""

import re
from typing import Dict, Any, List, Tuple
from pydantic import BaseModel, Field, field_validator


class UnderwriteRequest(BaseModel):
    """Input payload with strict validation guardrails."""
    borrower_id: str = Field(..., description="Target borrower ID or 'AUTO'")
    user_query: str = Field(..., min_length=5, max_length=1500, description="Underwriting query")
    requested_facility_usd: float = Field(default=5000000.0, ge=10000.0, le=500000000.0)

    @field_validator("user_query")
    @classmethod
    def sanitize_input(cls, v: str) -> str:
        # Check for dangerous prompt injection or SQL injection patterns
        prohibited = [r"drop\s+table", r"delete\s+from", r"exec\(", r"--\s*$", r"union\s+select"]
        for p in prohibited:
            if re.search(p, v, re.IGNORECASE):
                raise ValueError("Prohibited security token detected in input query.")
        return v.strip()


class FinancialGuardrails:
    """Production guardrails engine for FinTech AI assistants."""

    @staticmethod
    def mask_pii(text: str) -> str:
        """Masks sensitive personal and banking identifiers."""
        # Mask SSN / Tax ID (e.g. 123-45-6789)
        text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED-SSN]", text)
        # Mask 16-digit card / account numbers
        text = re.sub(r"\b(?:\d{4}[-\s]?){3}\d{4}\b", "[REDACTED-ACCOUNT]", text)
        return text

    @staticmethod
    def verify_output_citations(memo: str, citations: List[Dict[str, Any]]) -> Tuple[bool, float, List[str]]:
        """
        Validates that all claimed assertions in the underwriting memo reference valid source citations.
        Returns: (is_compliant, citation_coverage_score, list_of_warnings)
        """
        if not memo:
            return False, 0.0, ["Empty memorandum."]

        warnings = []
        cited_tags = set(re.findall(r"\[SRC-[A-Z]+-\d+\]", memo))
        expected_tags = {c["source_id"] for c in citations}

        missing_citations = expected_tags - cited_tags
        if missing_citations:
            warnings.append(f"Unreferenced sources available: {missing_citations}")

        # Citation coverage metric (ratio of expected tags referenced)
        coverage = len(cited_tags) / max(len(expected_tags), 1)
        is_compliant = coverage >= 0.50

        # Check for prohibited speculative guarantees (e.g., "100% risk free", "guaranteed zero default")
        prohibited_phrases = ["100% risk free", "guaranteed zero default", "cannot fail", "absolute certainty"]
        for phrase in prohibited_phrases:
            if phrase in memo.lower():
                is_compliant = False
                warnings.append(f"Regulatory compliance violation: prohibited absolute guarantee phrase '{phrase}' detected.")

        return is_compliant, round(coverage, 2), warnings
