"""
Data Engineering Module for FinTech Risk & Compliance Assistant.
Provides database access, window-function deduplication, and SCD-2 credit tracking.
"""

from src.data_engine.database import Base, engine, get_db_session, SessionLocal
from src.data_engine.models import (
    Borrower,
    BorrowerCreditHistorySCD2,
    RawTransaction,
    CleanTransaction,
)

__all__ = [
    "Base",
    "engine",
    "get_db_session",
    "SessionLocal",
    "Borrower",
    "BorrowerCreditHistorySCD2",
    "RawTransaction",
    "CleanTransaction",
]
