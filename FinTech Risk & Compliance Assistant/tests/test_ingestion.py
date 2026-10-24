"""
Unit test suite for Phase 3: Multimodal Report Ingestion & Financial Table Extraction.
"""

import os
import pytest
from src.ingestion.parser import CorporateReportParser
from src.ingestion.chart_analyzer import FinancialChartAnalyzer


@pytest.fixture
def sample_report_path():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(base_dir, "data", "raw", "apex_cloud_annual_report.md")


@pytest.fixture
def distressed_memo_path():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(base_dir, "data", "raw", "omnicommerce_credit_memo.md")


def test_parse_apex_report(sample_report_path):
    """Validates section count, title, and financial table extraction."""
    parsed = CorporateReportParser.parse_file(sample_report_path)

    assert "Apex Cloud Solutions Inc." in parsed["document_title"]
    assert parsed["total_sections"] == 5
    assert parsed["total_tables_found"] >= 1

    # Check table content
    table_text = parsed["sections"][1]["tables"][0]
    assert "FY2023" in table_text
    assert "FY2024" in table_text
    assert "Senior Secured Facility" in table_text


def test_chart_analyzer_multimodal_synthesis(sample_report_path):
    """Validates that [CHART_FIGURE: ...] tags are transformed into rich textual descriptions."""
    parsed = CorporateReportParser.parse_file(sample_report_path)
    text = parsed["raw_text"]

    assert "[CHART_FIGURE:" not in text
    assert "[Multimodal Visual Analysis — FIGURE_101_DEBT_MATURITY]" in text
    assert "Senior Balloon Facility" in text
    assert "Credit Officer Takeaway" in text


def test_parse_omnicommerce_covenant_breach(distressed_memo_path):
    """Validates that covenant breaches and cash burn tables are detected."""
    parsed = CorporateReportParser.parse_file(distressed_memo_path)

    assert parsed["total_sections"] == 4
    assert parsed["total_tables_found"] >= 1
    assert "Fixed Charge Coverage Ratio" in parsed["raw_text"]
    assert "[Multimodal Visual Analysis — FIGURE_202_CASH_BURN]" in parsed["raw_text"]
