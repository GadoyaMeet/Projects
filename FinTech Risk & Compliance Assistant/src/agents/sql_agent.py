"""
SQL Agent: Queries the relational database for quantitative borrower history and SCD-2 records.
Addresses Interview Question: R1 Q5 (Agentic Tool Use & SQL Warehouse Interrogation).
"""

from sqlalchemy import text
from src.data_engine.database import get_db_session
from src.data_engine.models import Borrower
from src.data_engine.scd2_manager import SCD2CreditManager
from src.agents.state import UnderwritingState


class SQLAgent:
    """Extracts master corporate profile, SCD-2 credit trajectories, and transaction payment health."""

    @staticmethod
    def execute(state: UnderwritingState) -> UnderwritingState:
        borrower_id = state.borrower_id
        state.log("SQLAgent", f"Querying financial warehouse for borrower '{borrower_id}'...")

        with get_db_session() as session:
            # 1. Master Borrower Entity
            borrower = session.query(Borrower).filter_by(borrower_id=borrower_id).first()
            if not borrower:
                state.log("SQLAgent", f"Warning: Borrower '{borrower_id}' not found in master records.")
                state.sql_data = {"error": f"Borrower {borrower_id} not registered"}
                return state

            borrower_meta = {
                "borrower_id": borrower.borrower_id,
                "company_name": borrower.company_name,
                "registration_no": borrower.registration_no,
                "industry": borrower.industry,
                "jurisdiction": borrower.jurisdiction,
            }

            # 2. SCD-2 Credit Risk Profiles (Current Active + Full Evolution Audit Trail)
            current_profile = SCD2CreditManager.get_current_profile(borrower_id)
            audit_trail = SCD2CreditManager.get_audit_trail(borrower_id)

            # 3. Clean Transaction Payment History
            txn_stats = session.execute(
                text("""
                SELECT 
                    COUNT(*) as total_txns,
                    SUM(CASE WHEN transaction_type = 'DISBURSEMENT' THEN amount ELSE 0 END) as total_disbursed,
                    SUM(CASE WHEN transaction_type = 'REPAYMENT' THEN amount ELSE 0 END) as total_repaid,
                    SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful_txns
                FROM transactions_clean
                WHERE borrower_id = :b_id
                """),
                {"b_id": borrower_id},
            ).fetchone()

            total_txns = txn_stats[0] or 0
            total_disbursed = float(txn_stats[1] or 0.0)
            total_repaid = float(txn_stats[2] or 0.0)
            successful_txns = txn_stats[3] or 0
            repayment_ratio = (total_repaid / total_disbursed) if total_disbursed > 0 else 1.0

            state.sql_data = {
                "master": borrower_meta,
                "current_credit_profile": current_profile,
                "audit_trail_count": len(audit_trail),
                "rating_trajectory": [r["rating_grade"] for r in audit_trail],
                "transaction_metrics": {
                    "total_clean_transactions": total_txns,
                    "total_disbursed_usd": round(total_disbursed, 2),
                    "total_repaid_usd": round(total_repaid, 2),
                    "repayment_coverage_ratio": round(repayment_ratio, 2),
                    "transaction_success_rate": f"{(successful_txns / total_txns * 100):.1f}%" if total_txns else "100%",
                },
            }

            state.log(
                "SQLAgent",
                f"Retrieved active rating {current_profile.get('rating_grade') if current_profile else 'N/A'}, "
                f"Score {current_profile.get('credit_score') if current_profile else 'N/A'}, "
                f"{len(audit_trail)} historical SCD-2 versions, and {total_txns} clean ledger transactions.",
            )

        return state
