"""
Corporate Credit Report & 10-K Ingestion Parser.
Extracts sections, converts financial tables to Markdown, and enriches charts.
Addresses Interview Questions: R1 Q1, R1 Q3, R2 Q2.
"""

import os
import re
from typing import List, Dict, Any, Optional
from src.ingestion.chart_analyzer import FinancialChartAnalyzer


class ParsedSection:
    """Represents a coherent section of a corporate filing."""

    def __init__(self, title: str, content: str, tables: List[str], section_index: int):
        self.title = title
        self.content = content
        self.tables = tables
        self.section_index = section_index

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "tables_count": len(self.tables),
            "tables": self.tables,
            "section_index": self.section_index,
        }


class CorporateReportParser:
    """Ingests and structures multi-page financial filings."""

    @staticmethod
    def parse_file(file_path: str) -> Dict[str, Any]:
        """Reads file, parses sections, preserves markdown tables, and processes charts."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Filing not found at: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            raw_text = CorporateReportParser._read_pdf(file_path)
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_text = f.read()

        # Enrich visual charts into structured textual descriptions
        processed_text = FinancialChartAnalyzer.extract_chart_blocks(raw_text)

        # Extract title and sections
        title_match = re.search(r"^#\s+(.*)", processed_text, re.MULTILINE)
        doc_title = title_match.group(1).strip() if title_match else os.path.basename(file_path)

        # Split into sections based on '## Section' or '## '
        sections = CorporateReportParser._extract_sections(processed_text)

        # Detect all Markdown tables
        all_tables = CorporateReportParser._extract_all_tables(processed_text)

        return {
            "file_path": file_path,
            "document_title": doc_title,
            "total_sections": len(sections),
            "total_tables_found": len(all_tables),
            "sections": [s.to_dict() for s in sections],
            "raw_text": processed_text,
        }

    @staticmethod
    def _read_pdf(pdf_path: str) -> str:
        """Extracts text from PDF via pypdf."""
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        pages_text = []
        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages_text.append(f"\n--- Page {idx + 1} ---\n" + text)
        return "\n".join(pages_text)

    @staticmethod
    def _extract_sections(text: str) -> List[ParsedSection]:
        """Splits markdown text into cohesive sections by ## headers."""
        section_pattern = r"(##\s+[^\n]+)(.*?)(?=\n##|\Z)"
        matches = list(re.finditer(section_pattern, text, flags=re.DOTALL))

        parsed_sections = []
        if not matches:
            # Entire text is one section
            tables = CorporateReportParser._extract_all_tables(text)
            return [ParsedSection(title="Full Document", content=text.strip(), tables=tables, section_index=0)]

        for idx, match in enumerate(matches):
            header = match.group(1).replace("##", "").strip()
            body = match.group(2).strip()
            full_section_content = f"## {header}\n{body}"
            tables = CorporateReportParser._extract_all_tables(body)
            parsed_sections.append(
                ParsedSection(title=header, content=full_section_content, tables=tables, section_index=idx)
            )

        return parsed_sections

    @staticmethod
    def _extract_all_tables(text: str) -> List[str]:
        """Finds markdown tables (header row, separator row, and data rows)."""
        table_pattern = r"(\|[^\n]+\|\r?\n\|[-:\s|]+\|\r?\n(?:\|[^\n]+\|\r?\n?)+)"
        matches = re.findall(table_pattern, text)
        return [m.strip() for m in matches]
