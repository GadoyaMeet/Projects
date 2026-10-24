"""
Qualitative RAG Agent: Interrogates unstructured filings via Hybrid Search & Cross-Encoder Reranker.
Addresses Interview Question: R1 Q5 (Agentic RAG & Unstructured Data Retrieval).
"""

import os
from typing import List, Dict, Any
from src.agents.state import UnderwritingState
from src.ingestion.parser import CorporateReportParser
from src.rag.chunker import HierarchicalChunker, Chunk
from src.rag.retriever import HybridRetriever
from src.rag.reranker import CrossEncoderReranker


class RAGAgent:
    """Retrieves qualitative audit notes, debt covenant clauses, and tabular financial statements."""

    _retriever: HybridRetriever = None

    @classmethod
    def get_retriever(cls) -> HybridRetriever:
        """Initializes corpus chunks and hybrid index lazily."""
        if cls._retriever is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            raw_dir = os.path.join(base_dir, "data", "raw")

            apex_path = os.path.join(raw_dir, "apex_cloud_annual_report.md")
            omni_path = os.path.join(raw_dir, "omnicommerce_credit_memo.md")

            chunker = HierarchicalChunker(target_child_size=320)
            all_chunks: List[Chunk] = []

            if os.path.exists(apex_path):
                apex_doc = CorporateReportParser.parse_file(apex_path)
                all_chunks.extend(chunker.chunk_document(apex_doc, borrower_id="BORR-TECH-001"))

            if os.path.exists(omni_path):
                omni_doc = CorporateReportParser.parse_file(omni_path)
                all_chunks.extend(chunker.chunk_document(omni_doc, borrower_id="BORR-RETL-004"))

            cls._retriever = HybridRetriever(all_chunks)

        return cls._retriever

    @classmethod
    def execute(cls, state: UnderwritingState) -> UnderwritingState:
        retriever = cls.get_retriever()
        state.log("RAGAgent", f"Searching qualitative filings for borrower '{state.borrower_id}'...")

        # Craft domain query targeting covenants, liquidity, and debt terms
        b_name = state.sql_data.get("master", {}).get("company_name", state.borrower_id)
        search_query = f"{b_name} financial covenants liquidity debt maturity cash burn default risk"

        # 1. First stage: Hybrid Search (BM25 + Dense Vectors via RRF)
        candidates = retriever.search(
            query=search_query,
            top_k=6,
            borrower_filter=state.borrower_id,
        )

        # 2. Second stage: Cross-Encoder Reranker
        reranked_top = CrossEncoderReranker.rerank(
            query=f"{state.user_query} {search_query}",
            candidates=candidates,
            top_n=3,
        )

        state.rag_data = reranked_top
        state.log(
            "RAGAgent",
            f"Retrieved and reranked {len(reranked_top)} authoritative qualitative passages (including "
            f"{sum(1 for r in reranked_top if r.get('is_table'))} financial statements).",
        )

        return state
