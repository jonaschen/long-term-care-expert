#!/usr/bin/env python3
"""
tools/hpa_rag_search.py

Implements the search_hpa_guidelines MCP tool.

Performs hybrid search (dense cosine + sparse BM25) on the Qdrant
'hpa_knowledge' collection using BAAI/bge-m3 for query embedding.

Hard filters — always enforced regardless of caller parameters:
  1. medical_content == false
  2. audience != "internal_reasoning_only"  (AD-8 chunks — direct lookup only)

Optional category filter scopes retrieval to one of:
  fall_prevention | dementia_care | sleep_hygiene |
  chronic_disease_lifestyle | general_aging

Usage as a standalone search tool (for evaluation / debugging):
    python tools/hpa_rag_search.py "query text" [--category <cat>] [--top-k N]

MCP usage:
    Import search_hpa_guidelines() and register it with the FastMCP server.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
QDRANT_PATH = REPO_ROOT / "knowledge_base" / "vector_index" / "qdrant"
COLLECTION_NAME = "hpa_knowledge"
VALID_CATEGORIES = {
    "fall_prevention",
    "dementia_care",
    "sleep_hygiene",
    "chronic_disease_lifestyle",
    "general_aging",
}

# ---------------------------------------------------------------------------
# Lazy-loaded singletons (model + client loaded once per process)
# ---------------------------------------------------------------------------
_model = None
_client = None


def _get_model():
    global _model
    if _model is None:
        import torch
        from FlagEmbedding import BGEM3FlagModel
        use_fp16 = torch.cuda.is_available()
        _model = BGEM3FlagModel("BAAI/bge-m3", use_fp16=use_fp16)
    return _model


def _get_client():
    global _client
    if _client is None:
        from qdrant_client import QdrantClient
        _client = QdrantClient(path=str(QDRANT_PATH))
    return _client


# ---------------------------------------------------------------------------
# Core search function
# ---------------------------------------------------------------------------

def search_hpa_guidelines(
    query: str,
    category: str,
    top_k: int = 3,
    exclude_medical: bool = True,
) -> list[dict]:
    """
    Hybrid RAG search over the hpa_knowledge Qdrant collection.

    Parameters
    ----------
    query       : Natural language query string.
    category    : One of the five HPA RAG categories (required — scope is mandatory).
    top_k       : Number of results to return (default 3, max 5).
    exclude_medical : Always True — parameter exists for interface compatibility only.
                      Medical content is always excluded via hard payload filter.

    Returns
    -------
    List of dicts, each with keys:
        chunk_id, category, source, audience, score, content
    Ordered by relevance score (highest first).

    Raises
    ------
    ValueError  : If category is not one of the five valid values.
    RuntimeError: If the Qdrant collection does not exist.
    """
    if category not in VALID_CATEGORIES:
        raise ValueError(
            f"Invalid category '{category}'. "
            f"Must be one of: {sorted(VALID_CATEGORIES)}"
        )

    top_k = min(max(1, top_k), 5)

    # --- Embed query ---
    model = _get_model()
    output = model.encode(
        [query],
        return_dense=True,
        return_sparse=True,
        return_colbert_vecs=False,
        batch_size=1,
    )
    dense_vec = output["dense_vecs"][0].tolist()
    sparse_weights: dict = output["lexical_weights"][0]
    sparse_indices = [int(k) for k in sparse_weights.keys()]
    sparse_values = [float(v) for v in sparse_weights.values()]

    # --- Build Qdrant payload filter ---
    # Hard filters (non-negotiable):
    #   1. medical_content == false
    #   2. audience != "internal_reasoning_only"
    #   3. category == <requested category>
    from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchExcept

    must_conditions = [
        FieldCondition(key="medical_content", match=MatchValue(value=False)),
        FieldCondition(key="audience", match=MatchExcept(**{"except": ["internal_reasoning_only"]})),
        FieldCondition(key="category", match=MatchValue(value=category)),
    ]
    payload_filter = Filter(must=must_conditions)

    # --- Hybrid search: dense + sparse ---
    from qdrant_client.models import (
        SparseVector, NamedVector, NamedSparseVector, Prefetch, FusionQuery, Fusion
    )
    client = _get_client()

    try:
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            prefetch=[
                Prefetch(
                    query=dense_vec,
                    using="dense",
                    filter=payload_filter,
                    limit=top_k * 3,
                ),
                Prefetch(
                    query=SparseVector(indices=sparse_indices, values=sparse_values),
                    using="sparse",
                    filter=payload_filter,
                    limit=top_k * 3,
                ),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=top_k,
            with_payload=True,
        )
        points = results.points
    except Exception as e:
        # Fallback to dense-only if hybrid query fails (e.g., older qdrant-client)
        from qdrant_client.models import SearchRequest
        points = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=("dense", dense_vec),
            query_filter=payload_filter,
            limit=top_k,
            with_payload=True,
        )

    # --- Format results ---
    return [
        {
            "chunk_id": p.payload.get("chunk_id", ""),
            "category": p.payload.get("category", ""),
            "source": p.payload.get("source", ""),
            "audience": p.payload.get("audience", ""),
            "score": round(p.score, 4),
            "content": p.payload.get("content", ""),
        }
        for p in points
    ]


# ---------------------------------------------------------------------------
# AD-8 direct lookup (for dementia-behavior-expert internal reasoning only)
# ---------------------------------------------------------------------------

def lookup_ad8_chunks() -> list[dict]:
    """
    Returns all AD-8 internal reasoning chunks directly (no semantic search).
    For use by dementia-behavior-expert ONLY — never call this from L1 or other L2 skills.
    These chunks must never appear in family-facing output.
    """
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    client = _get_client()
    results, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(
            must=[
                FieldCondition(
                    key="audience",
                    match=MatchValue(value="internal_reasoning_only"),
                )
            ]
        ),
        limit=20,
        with_payload=True,
        with_vectors=False,
    )
    return [
        {
            "chunk_id": p.payload.get("chunk_id", ""),
            "category": p.payload.get("category", ""),
            "source": p.payload.get("source", ""),
            "content": p.payload.get("content", ""),
        }
        for p in results
    ]


# ---------------------------------------------------------------------------
# CLI — for evaluation and debugging
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Search the HPA knowledge base (search_hpa_guidelines)."
    )
    parser.add_argument("query", help="Natural language query")
    parser.add_argument(
        "--category", required=True,
        choices=sorted(VALID_CATEGORIES),
        help="RAG category to search within",
    )
    parser.add_argument(
        "--top-k", type=int, default=3, metavar="N",
        help="Number of results to return (default: 3, max: 5)",
    )
    parser.add_argument(
        "--ad8-lookup", action="store_true",
        help="Return all AD-8 internal chunks instead of running search (debug only)",
    )
    args = parser.parse_args()

    print(f"\nQuery: {args.query!r}")
    print(f"Category: {args.category}  |  top_k: {args.top_k}\n")
    print("Loading model and connecting to Qdrant...")

    try:
        if args.ad8_lookup:
            results = lookup_ad8_chunks()
            print(f"\n--- AD-8 Internal Chunks ({len(results)} total) ---\n")
        else:
            results = search_hpa_guidelines(
                query=args.query,
                category=args.category,
                top_k=args.top_k,
            )
            print(f"\n--- Results ({len(results)}) ---\n")
    except Exception as exc:
        print(f"Error: {exc}")
        return 1

    for i, r in enumerate(results, 1):
        score_str = f"  score={r['score']}" if "score" in r else ""
        print(f"[{i}] {r['chunk_id']}{score_str}")
        print(f"     source: {r['source']}")
        # Print first 300 chars of content
        preview = r["content"].replace("\n", " ")[:300]
        print(f"     {preview}...")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
