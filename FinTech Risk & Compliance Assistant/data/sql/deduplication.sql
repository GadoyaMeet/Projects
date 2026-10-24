-- ============================================================================
-- SQL Deduplication using Window Functions: ROW_NUMBER() OVER (PARTITION BY ...)
-- Target Interview Question: R2 Q5 (Transactional Deduplication)
-- ============================================================================

-- Explanation:
-- In distributed financial architectures (e.g. core banking sync, Kafka consumers, payment webhooks),
-- network hiccups or retry policies often cause duplicate transaction payloads to arrive.
--
-- Why simple 'DISTINCT' or 'GROUP BY' fails:
-- 1. GROUP BY requires every non-grouped column to use an aggregate function (MIN, MAX),
--    which can corrupt transaction record integrity if values differ slightly (e.g., latency timestamps).
-- 2. DISTINCT compares ALL columns across the row; if an ingestion timestamp differs by even 1 millisecond,
--    DISTINCT treats them as unique and fails to eliminate duplicates.
--
-- The Window Function Solution:
-- We partition by the unique business natural key (transaction_ref) and order by the system
-- audit timestamp (ingested_at DESC). The newest or most authoritative delivery receives rn = 1.

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
  -- Avoid re-inserting transactions that have already been cleaned in previous pipeline runs
  AND transaction_ref NOT IN (SELECT transaction_ref FROM transactions_clean);
