-- ============================================================================
-- Enterprise FinTech Risk & Compliance Warehouse Schema
-- Compatible with PostgreSQL & SQLite
-- ============================================================================

-- 1. Master Borrower Table
CREATE TABLE IF NOT EXISTS borrowers (
    borrower_id VARCHAR(50) PRIMARY KEY,
    company_name VARCHAR(200) NOT NULL,
    registration_no VARCHAR(100) UNIQUE NOT NULL,
    industry VARCHAR(100) NOT NULL,
    jurisdiction VARCHAR(50) NOT NULL DEFAULT 'US',
    incorporated_date TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Slowly Changing Dimension Type 2 (SCD-2) Credit & Risk History
CREATE TABLE IF NOT EXISTS borrower_credit_history_scd2 (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    borrower_id VARCHAR(50) NOT NULL REFERENCES borrowers(borrower_id) ON DELETE CASCADE,
    credit_score INTEGER NOT NULL CHECK (credit_score BETWEEN 300 AND 850),
    rating_grade VARCHAR(10) NOT NULL,
    pd_estimate FLOAT NOT NULL CHECK (pd_estimate BETWEEN 0.0 AND 1.0),
    debt_to_equity FLOAT NOT NULL,
    interest_coverage_ratio FLOAT NOT NULL,
    annual_revenue_usd FLOAT NOT NULL,
    effective_start_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    effective_end_date TIMESTAMP NULL,
    is_current BOOLEAN NOT NULL DEFAULT 1,
    change_reason VARCHAR(255) NULL
);

CREATE INDEX IF NOT EXISTS idx_scd2_borrower_current 
ON borrower_credit_history_scd2 (borrower_id, is_current);

CREATE INDEX IF NOT EXISTS idx_scd2_temporal_range 
ON borrower_credit_history_scd2 (borrower_id, effective_start_date, effective_end_date);

-- 3. Staging Raw Transactions (Subject to duplicates from network retries/batch syncs)
CREATE TABLE IF NOT EXISTS transactions_raw (
    raw_id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_ref VARCHAR(100) NOT NULL,
    borrower_id VARCHAR(50) NOT NULL REFERENCES borrowers(borrower_id),
    amount FLOAT NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    transaction_type VARCHAR(50) NOT NULL,
    status VARCHAR(30) NOT NULL,
    transaction_date TIMESTAMP NOT NULL,
    ingested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ingestion_batch_id VARCHAR(100) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_raw_txn_ref ON transactions_raw (transaction_ref);
CREATE INDEX IF NOT EXISTS idx_raw_borrower ON transactions_raw (borrower_id);

-- 4. Deduplicated Production Transactions Table
CREATE TABLE IF NOT EXISTS transactions_clean (
    clean_id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_ref VARCHAR(100) UNIQUE NOT NULL,
    borrower_id VARCHAR(50) NOT NULL REFERENCES borrowers(borrower_id),
    amount FLOAT NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    transaction_type VARCHAR(50) NOT NULL,
    status VARCHAR(30) NOT NULL,
    transaction_date TIMESTAMP NOT NULL,
    processed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_raw_id INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_clean_borrower ON transactions_clean (borrower_id);
