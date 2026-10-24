"""
Unit test suite for Phase 4: Advanced RAG, Hybrid Retrieval & Cross-Encoder Reranking.
"""

import os
import pytest
from src.ingestion.parser import CorporateReportParser
from src.rag.chunker import HierarchicalChunker
from src.rag.retriever import HybridRetriever
from src.rag.reranker import CrossEncoderReranker


@pytest.fixture(scope="module")
def parsed_apex_doc():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    file_path = os.path.join(base_dir, "data", "raw", "apex_cloud_annual_report.md")
    return CorporateReportParser.parse_file(file_path)


@pytest.fixture(scope="module")
def parsed_omnicommerce_doc():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    file_path = os.path.join(base_dir, "data", "raw", "omnicommerce_credit_memo.md")
    return CorporateReportParser.parse_file(file_path)


def test_hierarchical_chunker_parent_child(parsed_apex_doc):
    """Validates that child chunks retain the full parent section text and tables are preserved."""
    chunker = HierarchicalChunker(target_child_size=300)
    chunks = chunker.chunk_document(parsed_apex_doc, borrower_id="BORR-TECH-001")

    assert len(chunks) >= 5
    # Find table chunk
    table_chunks = [c for c in chunks if c.is_table]
    assert len(table_chunks) >= 1
    assert "Balance Sheet Line Item" in table_chunks[0].text
    # Verify parent text is much larger than child text
    assert len(table_chunks[0].parent_text) > len(table_chunks[0].text)


def test_hybrid_retriever_bm25_and_dense(parsed_apex_doc, parsed_omnicommerce_doc):
    """Validates that Hybrid Search successfully ranks both keyword and semantic matches via RRF."""
    chunker = HierarchicalChunker()
    all_chunks = chunker.chunk_document(parsed_apex_doc, borrower_id="BORR-TECH-001") + \
                 chunker.chunk_document(parsed_omnicommerce_doc, borrower_id="BORR-RETL-004")

    retriever = HybridRetriever(all_chunks)

    # 1. Lexical search for exact financial covenant numbers
    lexical_query = "Minimum Interest Coverage Ratio 3.00:1.00"
    results = retriever.search(lexical_query, top_k=3)

    assert len(results) == 3
    top = results[0]
    assert "bm25_raw_score" in top
    assert "dense_cosine_score" in top
    assert "rrf_score" in top
    assert "3.00" in top["text"] or "coverage" in top["text"].lower()


def test_cross_encoder_reranker_boost(parsed_omnicommerce_doc):
    """Validates that Cross-Encoder boosts the exact covenant breach clause to the top rank."""
    chunker = HierarchicalChunker()
    chunks = chunker.chunk_document(parsed_omnicommerce_doc, borrower_id="BORR-RETL-004")
    retriever = HybridRetriever(chunks)

    query = "Section 7.2 Event of Default Fixed Charge Coverage 0.85x"
    candidates = retriever.search(query, top_k=5)

    reranked = CrossEncoderReranker.rerank(query, candidates, top_n=2)
    assert len(reranked) == 2
    assert "cross_encoder_score" in reranked[0]
    # The top reranked chunk should contain the exact violation clause
    top_text = reranked[0]["text"]
    assert "0.85x" in top_text or "Default" in top_text or "Covenant" in top_text
