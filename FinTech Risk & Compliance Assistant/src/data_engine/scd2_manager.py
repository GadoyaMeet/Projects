"""
Slowly Changing Dimension Type 2 (SCD-2) Manager.
Maintains temporal credit risk auditability and supports point-in-time time-travel queries.
Addresses Interview Question: R2 Q4.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import text, and_, or_
from src.data_engine.database import get_db_session
from src.data_engine.models import BorrowerCreditHistorySCD2, Borrower


class SCD2CreditManager:
    """
    Manages the lifecycle of borrower credit risk assessments using SCD Type 2 logic.
    Ensures zero data loss when credit metrics, PD estimates, or ratings evolve.
    """

    @staticmethod
    def upsert_credit_profile(
        borrower_id: str,
        credit_score: int,
        rating_grade: str,
        pd_estimate: float,
        debt_to_equity: float,
        interest_coverage_ratio: float,
        annual_revenue_usd: float,
        change_reason: str,
        effective_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Atomically evolves a borrower's credit profile under SCD Type 2 semantics:
        1. Identifies the currently active record (is_current = True).
        2. If values have changed, marks old record as is_current = False, setting effective_end_date.
        3. Creates a new record with is_current = True and effective_start_date.
        """
        effective_ts = effective_date or datetime.now()

        with get_db_session() as session:
            # Verify borrower exists
            borrower = session.query(Borrower).filter_by(borrower_id=borrower_id).first()
            if not borrower:
                raise ValueError(f"Borrower with ID '{borrower_id}' does not exist in the master table.")

            # Retrieve the active current record
            current_record = (
                session.query(BorrowerCreditHistorySCD2)
                .filter(
                    BorrowerCreditHistorySCD2.borrower_id == borrower_id,
                    BorrowerCreditHistorySCD2.is_current == True,
                )
                .first()
            )

            # If an active record exists, check if any tracked metric changed
            if current_record:
                has_changed = (
                    current_record.credit_score != credit_score
                    or current_record.rating_grade != rating_grade
                    or round(current_record.pd_estimate, 4) != round(pd_estimate, 4)
                    or round(current_record.debt_to_equity, 2) != round(debt_to_equity, 2)
                    or round(current_record.interest_coverage_ratio, 2) != round(interest_coverage_ratio, 2)
                    or round(current_record.annual_revenue_usd, 2) != round(annual_revenue_usd, 2)
                )

                if not has_changed:
                    return {
                        "status": "NO_OP",
                        "message": "No tracked attributes changed; existing SCD-2 record remains valid.",
                        "history_id": current_record.history_id,
                    }

                # Close out the old active record
                current_record.effective_end_date = effective_ts
                current_record.is_current = False
                session.add(current_record)

            # Insert the new active version
            new_record = BorrowerCreditHistorySCD2(
                borrower_id=borrower_id,
                credit_score=credit_score,
                rating_grade=rating_grade,
                pd_estimate=pd_estimate,
                debt_to_equity=debt_to_equity,
                interest_coverage_ratio=interest_coverage_ratio,
                annual_revenue_usd=annual_revenue_usd,
                effective_start_date=effective_ts,
                effective_end_date=None,
                is_current=True,
                change_reason=change_reason,
            )
            session.add(new_record)
            session.flush()

            return {
                "status": "UPDATED" if current_record else "INITIAL_VERSION",
                "borrower_id": borrower_id,
                "new_history_id": new_record.history_id,
                "effective_start_date": effective_ts.isoformat(),
                "rating_grade": rating_grade,
                "credit_score": credit_score,
            }

    @staticmethod
    def get_current_profile(borrower_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the active (current) credit rating profile for a borrower."""
        with get_db_session() as session:
            record = (
                session.query(BorrowerCreditHistorySCD2)
                .filter(
                    BorrowerCreditHistorySCD2.borrower_id == borrower_id,
                    BorrowerCreditHistorySCD2.is_current == True,
                )
                .first()
            )
            return SCD2CreditManager._serialize_record(record) if record else None

    @staticmethod
    def get_profile_at_timestamp(borrower_id: str, target_time: datetime) -> Optional[Dict[str, Any]]:
        """
        Executes a point-in-time time-travel query.
        Returns the exact credit risk state of the borrower as it existed on target_time.
        Formula: effective_start_date <= T AND (effective_end_date > T OR effective_end_date IS NULL)
        """
        with get_db_session() as session:
            record = (
                session.query(BorrowerCreditHistorySCD2)
                .filter(
                    BorrowerCreditHistorySCD2.borrower_id == borrower_id,
                    BorrowerCreditHistorySCD2.effective_start_date <= target_time,
                    or_(
                        BorrowerCreditHistorySCD2.effective_end_date > target_time,
                        BorrowerCreditHistorySCD2.effective_end_date.is_(None),
                    ),
                )
                .first()
            )
            return SCD2CreditManager._serialize_record(record) if record else None

    @staticmethod
    def get_audit_trail(borrower_id: str) -> List[Dict[str, Any]]:
        """Returns the full chronological evolution of a borrower's credit ratings."""
        with get_db_session() as session:
            records = (
                session.query(BorrowerCreditHistorySCD2)
                .filter(BorrowerCreditHistorySCD2.borrower_id == borrower_id)
                .order_by(BorrowerCreditHistorySCD2.effective_start_date.asc())
                .all()
            )
            return [SCD2CreditManager._serialize_record(r) for r in records]

    @staticmethod
    def _serialize_record(record: BorrowerCreditHistorySCD2) -> Dict[str, Any]:
        return {
            "history_id": record.history_id,
            "borrower_id": record.borrower_id,
            "credit_score": record.credit_score,
            "rating_grade": record.rating_grade,
            "pd_estimate": record.pd_estimate,
            "debt_to_equity": record.debt_to_equity,
            "interest_coverage_ratio": record.interest_coverage_ratio,
            "annual_revenue_usd": record.annual_revenue_usd,
            "effective_start_date": record.effective_start_date.isoformat() if record.effective_start_date else None,
            "effective_end_date": record.effective_end_date.isoformat() if record.effective_end_date else None,
            "is_current": record.is_current,
            "change_reason": record.change_reason,
        }
