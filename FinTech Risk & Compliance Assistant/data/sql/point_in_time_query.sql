-- ============================================================================
-- Slowly Changing Dimension Type 2 (SCD-2) Time-Travel Query
-- Target Interview Question: R2 Q4 (SCD Implementation & Auditability)
-- ============================================================================

-- Scenario:
-- An auditor or credit risk committee requests:
-- "What was Borrower 'BORR-TECH-001' credit rating, PD estimate, and debt-to-equity ratio
-- on 2025-06-15 when the $10,000,000 credit facility was approved?"
--
-- Query logic:
-- A record was active at target_timestamp T if and only if:
--   effective_start_date <= T AND (effective_end_date > T OR effective_end_date IS NULL)

SELECT 
    b.borrower_id,
    b.company_name,
    h.credit_score,
    h.rating_grade,
    h.pd_estimate,
    h.debt_to_equity,
    h.interest_coverage_ratio,
    h.effective_start_date,
    h.effective_end_date,
    h.is_current,
    h.change_reason
FROM borrowers b
JOIN borrower_credit_history_scd2 h ON b.borrower_id = h.borrower_id
WHERE b.borrower_id = 'BORR-TECH-001'
  AND h.effective_start_date <= '2025-06-15 00:00:00'
  AND (h.effective_end_date > '2025-06-15 00:00:00' OR h.effective_end_date IS NULL);

-- ============================================================================
-- Query Current Snapshot across All Active Borrowers
-- ============================================================================
SELECT 
    b.borrower_id,
    b.company_name,
    h.credit_score,
    h.rating_grade,
    h.pd_estimate,
    h.debt_to_equity,
    h.effective_start_date AS rating_effective_since
FROM borrowers b
JOIN borrower_credit_history_scd2 h ON b.borrower_id = h.borrower_id
WHERE h.is_current = 1;
