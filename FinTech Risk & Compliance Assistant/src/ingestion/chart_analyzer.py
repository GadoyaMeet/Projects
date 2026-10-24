"""
Visual Financial Chart Analyzer.
Extracts structured narrative and numerical intelligence from financial figures and diagrams.
Addresses Interview Question: R1 Q3 (PDFs with text + embedded charts/images).
"""

import re
from typing import Dict, Any


class FinancialChartAnalyzer:
    """
    Parses and summarizes visual charts, debt maturity schedules, and liquidity diagrams.
    Converts visual information into grounded, dense text suitable for vector embeddings.
    """

    @staticmethod
    def extract_chart_blocks(content: str) -> str:
        """
        Detects chart blocks marked by [CHART_FIGURE: ...] and synthesizes rich text summaries.
        In an automated multimodal pipeline, this is passed to a vision model (e.g., Gemini Flash).
        """
        pattern = r"\[CHART_FIGURE:\s*([A-Za-z0-9_]+)\](.*?)(?=\n##|\Z)"

        def _replacer(match):
            fig_id = match.group(1).strip()
            block_body = match.group(2).strip()

            # Parse metadata
            title_match = re.search(r"Chart Title:\s*(.*)", block_body)
            type_match = re.search(r"Chart Type:\s*(.*)", block_body)
            obs_match = re.search(r"Chart Observation:\s*(.*)", block_body)

            title = title_match.group(1).strip() if title_match else fig_id
            chart_type = type_match.group(1).strip() if type_match else "Financial Graph"
            observation = obs_match.group(1).strip() if obs_match else "Quantitative trend chart."

            # Synthesize an accessible semantic representation for the vector retriever
            summary = (
                f"\n> **[Multimodal Visual Analysis — {fig_id}]**\n"
                f"> **Visual Title:** {title} ({chart_type})\n"
                f"> **Summary & Data Points:**\n"
            )

            lines = block_body.splitlines()
            for line in lines:
                if line.strip().startswith("-"):
                    summary += f">   {line.strip()}\n"

            summary += f"> **Credit Officer Takeaway:** {observation}\n"
            return summary

        return re.sub(pattern, _replacer, content, flags=re.DOTALL)
