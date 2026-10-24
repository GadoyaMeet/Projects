"""
SQLAlchemy ORM models defining the FinTech Risk Data Warehouse schema.
Includes master borrower data, Slowly Changing Dimension Type 2 (SCD-2) credit history,
and transaction tables with raw staging and deduplicated clean states.
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from src.data_engine.database import Base


class Borrower(Base):
    """
    Borrower Master entity representing corporate commercial entities.
    Stores immutable or slowly-evolving natural identifiers.
    """
    __tablename__ = "borrowers"

    borrower_id = Column(String(50), primary_key=True, index=True)
    company_name = Column(String(200), nullable=False)
    registration_no = Column(String(100), unique=True, nullable=False)
    industry = Column(String(100), nullable=False)
    jurisdiction = Column(String(50), nullable=False, default="US")
    incorporated_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    # Relationships
    credit_histories = relationship("BorrowerCreditHistorySCD2", back_populates="borrower", cascade="all, delete-orphan")
    clean_transactions = relationship("CleanTransaction", back_populates="borrower", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Borrower(id={self.borrower_id}, name='{self.company_name}')>"


class BorrowerCreditHistorySCD2(Base):
    """
    Slowly Changing Dimension Type 2 (SCD-2) table for tracking historical credit risk metrics.
    Enables point-in-time time-travel queries for compliance, underwriting audits, and regulatory models.
    """
    __tablename__ = "borrower_credit_history_scd2"

    # Surrogate Key: Unique identifier for each historical version of a borrower's record
    history_id = Column(Integer, primary_key=True, autoincrement=True)

    # Natural Key: References the business entity
    borrower_id = Column(String(50), ForeignKey("borrowers.borrower_id"), nullable=False, index=True)

    # Tracked Attributes
    credit_score = Column(Integer, nullable=False)  # 300 - 850
    rating_grade = Column(String(10), nullable=False)  # AAA, AA, A, BBB, BB, B, CCC, D
    pd_estimate = Column(Float, nullable=False)  # Probability of Default (0.0 to 1.0)
    debt_to_equity = Column(Float, nullable=False)  # Leverage ratio
    interest_coverage_ratio = Column(Float, nullable=False)  # Operating income / interest expense
    annual_revenue_usd = Column(Float, nullable=False)  # Annual revenue in USD

    # SCD Type 2 Metadata Columns
    effective_start_date = Column(DateTime, nullable=False, default=datetime.now)
    effective_end_date = Column(DateTime, nullable=True)  # NULL represents currently active record
    is_current = Column(Boolean, nullable=False, default=True, index=True)
    change_reason = Column(String(255), nullable=True)  # e.g., 'Annual Audit', 'Downgrade', 'New Filing'

    # Relationship
    borrower = relationship("Borrower", back_populates="credit_histories")

    # Composite Index for fast point-in-time and active-record lookups
    __table_args__ = (
        Index("idx_scd2_borrower_current", "borrower_id", "is_current"),
        Index("idx_scd2_temporal_range", "borrower_id", "effective_start_date", "effective_end_date"),
    )

    def __repr__(self):
        return (
            f"<BorrowerCreditHistorySCD2(id={self.history_id}, borrower_id='{self.borrower_id}', "
            f"rating='{self.rating_grade}', score={self.credit_score}, is_current={self.is_current})>"
        )


class RawTransaction(Base):
    """
    Staging / Ingestion table for raw transactional feeds (ACH, Wire, Core Banking sync).
    May contain accidental duplicate deliveries from network retries, batch re-runs, or webhook re-deliveries.
    """
    __tablename__ = "transactions_raw"

    raw_id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_ref = Column(String(100), nullable=False, index=True)  # External transaction reference
    borrower_id = Column(String(50), ForeignKey("borrowers.borrower_id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    transaction_type = Column(String(50), nullable=False)  # DISBURSEMENT, REPAYMENT, INTEREST, FEE
    status = Column(String(30), nullable=False)  # SUCCESS, PENDING, FAILED
    transaction_date = Column(DateTime, nullable=False)
    ingested_at = Column(DateTime, nullable=False, default=datetime.now)  # Used for deduplication ranking
    ingestion_batch_id = Column(String(100), nullable=False)

    def __repr__(self):
        return f"<RawTransaction(ref='{self.transaction_ref}', amount={self.amount}, ingested_at='{self.ingested_at}')>"


class CleanTransaction(Base):
    """
    Deduplicated production transaction warehouse table.
    Enforces strict uniqueness on transaction_ref.
    Populated by the deduplication window function pipeline.
    """
    __tablename__ = "transactions_clean"

    clean_id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_ref = Column(String(100), unique=True, nullable=False, index=True)
    borrower_id = Column(String(50), ForeignKey("borrowers.borrower_id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    transaction_type = Column(String(50), nullable=False)
    status = Column(String(30), nullable=False)
    transaction_date = Column(DateTime, nullable=False)
    processed_at = Column(DateTime, nullable=False, default=datetime.now)
    source_raw_id = Column(Integer, nullable=False)

    borrower = relationship("Borrower", back_populates="clean_transactions")

    def __repr__(self):
        return f"<CleanTransaction(ref='{self.transaction_ref}', borrower='{self.borrower_id}', amount={self.amount})>"
