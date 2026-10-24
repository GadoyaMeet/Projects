"""
Agent State Definition for Multi-Agent FinTech Underwriting Pipeline.
Addresses Interview Question: R2 Q6 (Multi-Agent State Sharing & Coordination).
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class UnderwritingState:
    """Shared state passed between specialized underwriting agents."""
    borrower_id: str
    user_query: str
    requested_facility_usd: float = 5000000.0
    intent: str = "CREDIT_UNDERWRITING_MEMO"

    # Agent outputs
    sql_data: Dict[str, Any] = field(default_factory=dict)
    rag_data: List[Dict[str, Any]] = field(default_factory=list)
    ml_prediction: Dict[str, Any] = field(default_factory=dict)
    underwriting_memo: Optional[str] = None
    citations: List[Dict[str, str]] = field(default_factory=list)
    agent_logs: List[str] = field(default_factory=list)

    def log(self, agent_name: str, message: str):
        """Appends a trace event to the execution history."""
        self.agent_logs.append(f"[{agent_name}] {message}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "borrower_id": self.borrower_id,
            "user_query": self.user_query,
            "requested_facility_usd": self.requested_facility_usd,
            "intent": self.intent,
            "sql_data": self.sql_data,
            "rag_data_count": len(self.rag_data),
            "ml_prediction": self.ml_prediction,
            "underwriting_memo": self.underwriting_memo,
            "citations_count": len(self.citations),
            "citations": self.citations,
            "agent_logs": self.agent_logs,
        }
