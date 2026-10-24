"""
Router Agent: Classifies user query intent and extracts financial parameters.
Addresses Interview Question: R1 Q4 (Prompt Engineering & Intent Classification).
"""

import re
from src.agents.state import UnderwritingState


class RouterAgent:
    """Classifies user underwriting requests and extracts key entities."""

    @staticmethod
    def route(state: UnderwritingState) -> UnderwritingState:
        query = state.user_query.lower()

        # 1. Detect borrower ID if not already explicitly provided
        if not state.borrower_id or state.borrower_id == "AUTO":
            if "apex" in query or "tech-001" in query or "cloud" in query:
                state.borrower_id = "BORR-TECH-001"
            elif "omni" in query or "retl-004" in query or "retail" in query:
                state.borrower_id = "BORR-RETL-004"
            elif "bio" in query or "hlth-002" in query or "therapeutics" in query:
                state.borrower_id = "BORR-HLTH-002"
            elif "solaris" in query or "enrg-003" in query:
                state.borrower_id = "BORR-ENRG-003"
            elif "titan" in query or "manu-005" in query:
                state.borrower_id = "BORR-MANU-005"
            else:
                state.borrower_id = "BORR-TECH-001"  # Default fallback

        # 2. Extract requested dollar facility if mentioned
        amount_match = re.search(r"\$(\d+(?:\.\d+)?)\s*(m|million|k|thousand)?", query)
        if amount_match:
            num = float(amount_match.group(1))
            unit = (amount_match.group(2) or "").lower()
            if "m" in unit:
                state.requested_facility_usd = num * 1_000_000
            elif "k" in unit:
                state.requested_facility_usd = num * 1_000
            else:
                state.requested_facility_usd = num

        # 3. Classify Intent
        if any(w in query for w in ["audit", "time travel", "history", "scd2", "historical rating"]):
            state.intent = "SCD2_AUDIT_LOOKUP"
        elif any(w in query for w in ["covenant", "breach", "violation", "terms"]):
            state.intent = "COVENANT_ANALYSIS"
        elif any(w in query for w in ["underwrite", "memo", "approval", "loan", "decision", "credit committee"]):
            state.intent = "CREDIT_UNDERWRITING_MEMO"
        else:
            state.intent = "CREDIT_UNDERWRITING_MEMO"

        state.log("RouterAgent", f"Target Borrower: '{state.borrower_id}', Intent: '{state.intent}', Facility: ${state.requested_facility_usd:,.2f}")
        return state
