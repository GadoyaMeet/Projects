"""
Synthetic Financial Data Generator & Database Seeder.
Creates realistic corporate borrowers, temporal SCD-2 credit profiles,
and raw transaction streams containing intentional duplicate payloads.
"""

from datetime import datetime, timedelta
import random
from src.data_engine.database import Base, engine, get_db_session
from src.data_engine.models import Borrower, BorrowerCreditHistorySCD2, RawTransaction, CleanTransaction
from src.data_engine.scd2_manager import SCD2CreditManager


def seed_database():
    """Initializes tables and populates rich synthetic financial data."""
    print("Initializing database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with get_db_session() as session:
        print("Seeding Master Borrowers...")
        borrowers = [
            Borrower(
                borrower_id="BORR-TECH-001",
                company_name="Apex Cloud Solutions Inc.",
                registration_no="US-DEL-2018-94812",
                industry="Enterprise Cloud Software",
                jurisdiction="US",
                incorporated_date=datetime(2018, 4, 12),
            ),
            Borrower(
                borrower_id="BORR-HLTH-002",
                company_name="BioVanguard Therapeutics LLC",
                registration_no="US-MA-2015-33109",
                industry="Biotechnology & Pharmaceuticals",
                jurisdiction="US",
                incorporated_date=datetime(2015, 9, 23),
            ),
            Borrower(
                borrower_id="BORR-ENRG-003",
                company_name="Solaris Clean Energy Corp",
                registration_no="US-TX-2020-77412",
                industry="Renewable Energy Utilities",
                jurisdiction="US",
                incorporated_date=datetime(2020, 1, 10),
            ),
            Borrower(
                borrower_id="BORR-RETL-004",
                company_name="OmniCommerce Global Retail",
                registration_no="US-CA-2017-55091",
                industry="E-Commerce & Supply Chain Logistics",
                jurisdiction="US",
                incorporated_date=datetime(2017, 11, 5),
            ),
            Borrower(
                borrower_id="BORR-MANU-005",
                company_name="Titan Precision Manufacturing",
                registration_no="US-OH-2012-10843",
                industry="Industrial Machinery & Advanced Metals",
                jurisdiction="US",
                incorporated_date=datetime(2012, 6, 18),
            ),
        ]
        session.add_all(borrowers)
        session.commit()

    print("Seeding SCD-2 Credit Risk Evolution Trajectories...")
    # Seed temporal histories via SCD2CreditManager to test version transitions
    # Borrower 1: Growing Tech Company (Continuous Upgrades)
    SCD2CreditManager.upsert_credit_profile(
        borrower_id="BORR-TECH-001",
        credit_score=685,
        rating_grade="BBB",
        pd_estimate=0.032,
        debt_to_equity=1.85,
        interest_coverage_ratio=3.4,
        annual_revenue_usd=42000000.0,
        change_reason="Initial Loan Underwriting Assessment",
        effective_date=datetime(2024, 1, 15, 10, 0, 0),
    )
    SCD2CreditManager.upsert_credit_profile(
        borrower_id="BORR-TECH-001",
        credit_score=735,
        rating_grade="A",
        pd_estimate=0.015,
        debt_to_equity=1.35,
        interest_coverage_ratio=5.2,
        annual_revenue_usd=68000000.0,
        change_reason="Q3 Series C Capital Inflow & Revenue Growth",
        effective_date=datetime(2024, 9, 20, 14, 30, 0),
    )
    SCD2CreditManager.upsert_credit_profile(
        borrower_id="BORR-TECH-001",
        credit_score=780,
        rating_grade="AA",
        pd_estimate=0.007,
        debt_to_equity=0.92,
        interest_coverage_ratio=8.1,
        annual_revenue_usd=95000000.0,
        change_reason="EBITDA Margin Expansion & Refinanced Debt",
        effective_date=datetime(2025, 4, 10, 9, 0, 0),
    )

    # Borrower 4: Distressed Retail Company (Downgrade Trajectory)
    SCD2CreditManager.upsert_credit_profile(
        borrower_id="BORR-RETL-004",
        credit_score=640,
        rating_grade="BB",
        pd_estimate=0.058,
        debt_to_equity=2.40,
        interest_coverage_ratio=2.1,
        annual_revenue_usd=120000000.0,
        change_reason="Baseline Origination Profile",
        effective_date=datetime(2024, 2, 1, 10, 0, 0),
    )
    SCD2CreditManager.upsert_credit_profile(
        borrower_id="BORR-RETL-004",
        credit_score=575,
        rating_grade="B",
        pd_estimate=0.125,
        debt_to_equity=3.65,
        interest_coverage_ratio=1.3,
        annual_revenue_usd=98000000.0,
        change_reason="Inventory Write-Downs & Compressed Margins",
        effective_date=datetime(2024, 10, 15, 11, 0, 0),
    )
    SCD2CreditManager.upsert_credit_profile(
        borrower_id="BORR-RETL-004",
        credit_score=495,
        rating_grade="CCC",
        pd_estimate=0.285,
        debt_to_equity=5.10,
        interest_coverage_ratio=0.85,
        annual_revenue_usd=74000000.0,
        change_reason="Breach of Debt Service Coverage Covenant",
        effective_date=datetime(2025, 3, 5, 16, 0, 0),
    )

    # Seed remaining borrowers with baseline ratings
    for b_id, score, grade, pd, de, icr, rev in [
        ("BORR-HLTH-002", 710, "A-", 0.022, 1.10, 4.8, 55000000.0),
        ("BORR-ENRG-003", 670, "BBB-", 0.041, 2.15, 2.9, 140000000.0),
        ("BORR-MANU-005", 725, "A", 0.018, 1.45, 4.3, 85000000.0),
    ]:
        SCD2CreditManager.upsert_credit_profile(
            borrower_id=b_id,
            credit_score=score,
            rating_grade=grade,
            pd_estimate=pd,
            debt_to_equity=de,
            interest_coverage_ratio=icr,
            annual_revenue_usd=rev,
            change_reason="Baseline Rating Assignment",
            effective_date=datetime(2024, 3, 1, 9, 0, 0),
        )

    print("Seeding Raw Transactions with duplicate payloads...")
    # Generate 100 unique transactions, then duplicate 30 of them with slightly later ingested_at timestamps
    raw_txns = []
    base_date = datetime(2024, 6, 1)

    for i in range(1, 101):
        txn_ref = f"TXN-2024-{i:05d}"
        borrower_id = random.choice([
            "BORR-TECH-001", "BORR-HLTH-002", "BORR-ENRG-003", "BORR-RETL-004", "BORR-MANU-005"
        ])
        txn_type = random.choice(["REPAYMENT", "DISBURSEMENT", "INTEREST_PAYMENT", "FACILITY_FEE"])
        amount = round(random.uniform(5000.0, 750000.0), 2)
        txn_date = base_date + timedelta(days=i * 2, hours=random.randint(1, 12))
        ingest_time_1 = txn_date + timedelta(minutes=5)

        # Primary raw delivery
        raw_txns.append(
            RawTransaction(
                transaction_ref=txn_ref,
                borrower_id=borrower_id,
                amount=amount,
                currency="USD",
                transaction_type=txn_type,
                status="SUCCESS",
                transaction_date=txn_date,
                ingested_at=ingest_time_1,
                ingestion_batch_id="BATCH-001-PRIMARY",
            )
        )

        # Duplicate injection for 30 transactions (simulating network timeout retry / re-delivery)
        if i % 3 == 0:
            ingest_time_2 = ingest_time_1 + timedelta(seconds=random.randint(45, 300))
            raw_txns.append(
                RawTransaction(
                    transaction_ref=txn_ref,
                    borrower_id=borrower_id,
                    amount=amount,
                    currency="USD",
                    transaction_type=txn_type,
                    status="SUCCESS",
                    transaction_date=txn_date,
                    ingested_at=ingest_time_2,
                    ingestion_batch_id="BATCH-002-RETRY",
                )
            )

    with get_db_session() as session:
        session.add_all(raw_txns)
        session.commit()

    print(f"Database seeded successfully with {len(raw_txns)} raw records (including ~33 duplicates).")


if __name__ == "__main__":
    seed_database()
