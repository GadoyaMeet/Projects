"""
Transaction Deduplication Engine using SQL Window Functions.
Addresses Interview Question: R2 Q5.
"""

from typing import Dict, Any
from sqlalchemy import text
from src.data_engine.database import get_db_session


class TransactionDeduplicator:
    """
    Executes an idempotent deduplication pipeline on raw transaction streams.
    Uses ROW_NUMBER() OVER (PARTITION BY transaction_ref ORDER BY ingested_at DESC).
    """

    @staticmethod
    def run_deduplication() -> Dict[str, Any]:
        """
        Executes the window function deduplication pipeline.
        Returns a summary report with counts of total raw, duplicate, and clean records.
        """
        with get_db_session() as session:
            # 1. Inspect raw count
            total_raw_count = session.execute(
                text("SELECT COUNT(*) FROM transactions_raw")
            ).scalar() or 0

            # 2. Count duplicates in raw table
            duplicate_count = session.execute(
                text("""
                SELECT COUNT(*) FROM (
                    SELECT transaction_ref, COUNT(*) as cnt
                    FROM transactions_raw
                    GROUP BY transaction_ref
                    HAVING COUNT(*) > 1
                )
                """)
            ).scalar() or 0

            # 3. Track clean count before insertion
            clean_count_before = session.execute(
                text("SELECT COUNT(*) FROM transactions_clean")
            ).scalar() or 0

            # 4. Deduplicate and insert into clean table using ROW_NUMBER()
            dedup_query = text("""
            WITH ranked_transactions AS (
                SELECT 
                    raw_id,
                    transaction_ref,
                    borrower_id,
                    amount,
                    currency,
                    transaction_type,
                    status,
                    transaction_date,
                    ingested_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY transaction_ref 
                        ORDER BY ingested_at DESC, raw_id DESC
                    ) AS rn
                FROM transactions_raw
            )
            INSERT INTO transactions_clean (
                transaction_ref,
                borrower_id,
                amount,
                currency,
                transaction_type,
                status,
                transaction_date,
                processed_at,
                source_raw_id
            )
            SELECT 
                transaction_ref,
                borrower_id,
                amount,
                currency,
                transaction_type,
                status,
                transaction_date,
                CURRENT_TIMESTAMP,
                raw_id
            FROM ranked_transactions
            WHERE rn = 1
              AND transaction_ref NOT IN (SELECT transaction_ref FROM transactions_clean);
            """)

            session.execute(dedup_query)

            # 5. Total clean count after insertion
            total_clean_count = session.execute(
                text("SELECT COUNT(*) FROM transactions_clean")
            ).scalar() or 0

            inserted_count = total_clean_count - clean_count_before

            return {
                "total_raw_records": total_raw_count,
                "duplicated_reference_keys": duplicate_count,
                "new_clean_inserted": inserted_count,
                "total_clean_warehouse_records": total_clean_count,
                "purged_duplicate_rows": total_raw_count - total_clean_count,
            }
