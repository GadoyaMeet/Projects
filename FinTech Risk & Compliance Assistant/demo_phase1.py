"""
Interactive demonstration script for Phase 1: Data Engineering Layer.
Showcases:
1. Deduplication using ROW_NUMBER() window function.
2. SCD Type 2 Point-in-Time audit time-travel query.
3. Full chronological credit risk evolution trail.
"""

from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from src.data_engine.seed_data import seed_database
from src.data_engine.deduplicator import TransactionDeduplicator
from src.data_engine.scd2_manager import SCD2CreditManager

console = Console()


def run_phase1_demo():
    console.print(
        Panel.fit(
            "[bold cyan]FinTech Risk & Compliance Assistant[/bold cyan]\n"
            "[yellow]Phase 1: Financial Data Warehouse, Deduplication & SCD Type 2 Engine[/yellow]",
            border_style="cyan",
        )
    )

    # 1. Reset and Seed Database
    console.print("\n[bold green]Step 1: Ingesting Raw Financial Streams...[/bold green]")
    seed_database()

    # 2. Execute Deduplication Pipeline
    console.print("\n[bold green]Step 2: Executing Transaction Deduplication Pipeline...[/bold green]")
    report = TransactionDeduplicator.run_deduplication()

    dedup_table = Table(title="Transaction Deduplication Summary (ROW_NUMBER Window Function)", border_style="magenta")
    dedup_table.add_column("Metric", style="cyan", no_wrap=True)
    dedup_table.add_column("Count", style="bold white", justify="right")

    for k, v in report.items():
        dedup_table.add_row(k.replace("_", " ").title(), str(v))
    console.print(dedup_table)

    # 3. Demonstration of SCD-2 Time-Travel Query
    console.print("\n[bold green]Step 3: Point-in-Time Compliance Time-Travel Query (R2 Q4)[/bold green]")
    target_dates = [
        ("June 1, 2024", datetime(2024, 6, 1)),
        ("December 1, 2024", datetime(2024, 12, 1)),
        ("May 1, 2025", datetime(2025, 5, 1)),
    ]

    time_travel_table = Table(title="Borrower 'BORR-TECH-001' Point-in-Time Credit Reconstructions", border_style="blue")
    time_travel_table.add_column("Target Audit Date", style="yellow")
    time_travel_table.add_column("Rating Grade", style="bold green", justify="center")
    time_travel_table.add_column("Score", style="white", justify="right")
    time_travel_table.add_column("PD Estimate", style="cyan", justify="right")
    time_travel_table.add_column("D/E Ratio", style="magenta", justify="right")
    time_travel_table.add_column("Effective Range", style="dim white")
    time_travel_table.add_column("Is Current?", style="bold yellow", justify="center")

    for label, target_dt in target_dates:
        profile = SCD2CreditManager.get_profile_at_timestamp("BORR-TECH-001", target_dt)
        if profile:
            start = profile["effective_start_date"][:10]
            end = profile["effective_end_date"][:10] if profile["effective_end_date"] else "PRESENT"
            time_travel_table.add_row(
                label,
                profile["rating_grade"],
                str(profile["credit_score"]),
                f"{profile['pd_estimate']*100:.2f}%",
                f"{profile['debt_to_equity']:.2f}x",
                f"{start} -> {end}",
                "Yes" if profile["is_current"] else "No",
            )
    console.print(time_travel_table)

    # 4. Full Audit Trail for Distressed Borrower
    console.print("\n[bold green]Step 4: Regulatory Audit Trail for Distressed Entity ('BORR-RETL-004')[/bold green]")
    trail = SCD2CreditManager.get_audit_trail("BORR-RETL-004")

    audit_table = Table(title="SCD-2 Full Historical Audit Trail", border_style="red")
    audit_table.add_column("Version", style="dim white", justify="center")
    audit_table.add_column("Rating", style="bold red", justify="center")
    audit_table.add_column("Score", style="white", justify="right")
    audit_table.add_column("PD Estimate", style="cyan", justify="right")
    audit_table.add_column("Effective From", style="yellow")
    audit_table.add_column("Effective Until", style="yellow")
    audit_table.add_column("Reason / Event Trigger", style="italic white")
    audit_table.add_column("Active?", style="bold green", justify="center")

    for idx, r in enumerate(trail, start=1):
        end = r["effective_end_date"][:10] if r["effective_end_date"] else "ACTIVE"
        audit_table.add_row(
            f"v{idx}",
            r["rating_grade"],
            str(r["credit_score"]),
            f"{r['pd_estimate']*100:.2f}%",
            r["effective_start_date"][:10],
            end,
            r["change_reason"] or "N/A",
            "YES" if r["is_current"] else "NO",
        )
    console.print(audit_table)
    console.print("\n[bold green]Phase 1 Demonstration Completed Successfully![/bold green]\n")


if __name__ == "__main__":
    run_phase1_demo()
