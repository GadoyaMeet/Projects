"""
Multimodal Document & PDF Ingestion Engine for Corporate Credit Reports.
Addresses Interview Questions:
- R1 Q1: RAG Basics & Document Preprocessing
- R1 Q3: Handling PDFs with text, tables, and images
- R2 Q2: Structuring Unstructured Corporate Filings
"""

from src.ingestion.parser import CorporateReportParser
from src.ingestion.chart_analyzer import FinancialChartAnalyzer

__all__ = ["CorporateReportParser", "FinancialChartAnalyzer"]
