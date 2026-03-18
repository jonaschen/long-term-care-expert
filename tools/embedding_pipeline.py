#!/usr/bin/env python3
"""
tools/embedding_pipeline.py

Reads all HPA knowledge chunks from knowledge_base/processed_chunks/,
embeds them using BAAI/bge-m3 (dense + sparse vectors), and indexes
them into the Qdrant 'hpa_knowledge' collection.

Architecture decisions:
  - Vector store: Qdrant (embedded local mode, no server required)
  - Embedding model: BAAI/bge-m3 (multilingual Chinese + English,
    native dense + sparse for hybrid search)
  - Collection: 'hpa_knowledge' with named vectors 'dense' and 'sparse'

AD-8 isolation rule:
  Chunks with audience == 'internal_reasoning_only' (currently
  dementia_care_004 and dementia_care_008 — the AD-8 scale) are stored
  in the collection but EXCLUDED from general RAG queries by a hard
  payload filter. The dementia-behavior-expert skill accesses them via
  direct audience-filtered lookup only. They must never appear in
  search_hpa_guidelines results.

Usage:
    python tools/embedding_pipeline.py [--reset] [--batch-size N] [--dry-run]

Options:
    --reset       Drop and recreate the collection before indexing
    --batch-size  Chunks to embed per model call (default: 8; reduce if OOM)
    --dry-run     Parse and validate chunks without embedding or indexing
"""

import argparse
import re
import sys
import uuid
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
CHUNKS_DIR = REPO_ROOT / "knowledge_base" / "processed_chunks"
QDRANT_PATH = REPO_ROOT / "knowledge_base" / "vector_index" / "qdrant"
COLLECTION_NAME = "hpa_knowledge"
DENSE_DIM = 1024  # bge-m3 dense output dimension

# ---------------------------------------------------------------------------
# Chunk parsing
# ---------------------------------------------------------------------------
METADATA_FIELDS = {
    "Category:": "category",
    "Medical Content:": "medical_content",
    "Source:": "source",
    "Audience:": "audience",
    "Update Date:": "update_date",
    "Chunk ID:": "chunk_id",
}

# Lines that are part of the metadata preamble (not body content)
PREAMBLE_PATTERNS = [
    re.compile(r"^#\s+"),           # H1 title line
    re.compile(r"^⚠"),              # internal-use warning
    re.compile(r"^This chunk is"),  # internal-use warning continuation
    re.compile(r"^(Category|Medical Content|Source|Audience|Update Date|Chunk ID):"),
]


def parse_chunk(filepath: Path) -> Optional[dict]:
    """
    Parse a processed chunk .md file into a dict with metadata and body text.
    Returns None if required fields (chunk_id, category) are missing.
    """
    text = filepath.read_text(encoding="utf-8")
    lines = text.splitlines()

    meta: dict = {"filename": filepath.name}
    body_lines: list[str] = []

    for line in lines:
        matched = False
        for prefix, key in METADATA_FIELDS.items():
            if line.startswith(prefix):
                value = line[len(prefix):].strip()
                if key == "medical_content":
                    value = value.lower() == "true"
                meta[key] = value
                matched = True
                break
        if matched:
            continue
        # Skip preamble-only lines (title, internal warning text)
        if any(p.match(line) for p in PREAMBLE_PATTERNS):
            continue
        body_lines.append(line)

    meta["body"] = "\n".join(body_lines).strip()
    meta["full_text"] = text  # keep full text for payload storage

    if "chunk_id" not in meta or "category" not in meta:
        return None
    return meta


def chunk_to_point_id(chunk_id: str) -> str:
    """Stable UUID derived from chunk_id. Qdrant accepts UUID strings."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"ltc-hpa:{chunk_id}"))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Embed HPA knowledge chunks into Qdrant hpa_knowledge collection."
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Drop and recreate the collection before indexing"
    )
    parser.add_argument(
        "--batch-size", type=int, default=8, metavar="N",
        help="Chunks per embedding batch (default: 8; reduce to 4 if OOM)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Parse and validate chunks without embedding or writing to Qdrant"
    )
    args = parser.parse_args()

    # --- Load and validate chunks ---
    chunk_files = sorted(CHUNKS_DIR.glob("*.md"))
    if not chunk_files:
        print(f"No .md files found in {CHUNKS_DIR}")
        return 1

    chunks: list[dict] = []
    skipped: list[str] = []
    for f in chunk_files:
        meta = parse_chunk(f)
        if meta is None:
            skipped.append(f.name)
        else:
            chunks.append(meta)

    general = [c for c in chunks if c.get("audience") != "internal_reasoning_only"]
    internal = [c for c in chunks if c.get("audience") == "internal_reasoning_only"]

    print("=" * 60)
    print("  HPA Knowledge Base — Embedding Pipeline")
    print("=" * 60)
    print(f"  Chunks found:      {len(chunks)}")
    print(f"  General RAG:       {len(general)}")
    print(f"  Internal-only:     {len(internal)}  (AD-8 — audience filter enforced)")
    if skipped:
        print(f"  Skipped (no metadata): {skipped}")
    if args.dry_run:
        print("\n  [dry-run] Chunk parsing OK — not embedding or indexing.")
        print("\n  Chunks that would be indexed:")
        for c in chunks:
            tag = " [INTERNAL]" if c.get("audience") == "internal_reasoning_only" else ""
            print(f"    {c['chunk_id']:<45} {c['category']}{tag}")
        return 0

    # --- Load embedding model ---
    print("\nLoading BAAI/bge-m3 (first run downloads ~2.3 GB to ~/.cache/huggingface) ...")
    try:
        import torch
        from FlagEmbedding import BGEM3FlagModel
    except ImportError:
        print("Missing dependencies. Run: pip install -r tools/requirements.txt")
        return 1

    use_fp16 = torch.cuda.is_available()
    device = "cuda" if use_fp16 else "cpu"
    print(f"  Device: {device}  (fp16: {use_fp16})")
    model = BGEM3FlagModel("BAAI/bge-m3", use_fp16=use_fp16)
    print("  Model loaded.\n")

    # --- Connect to Qdrant ---
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import (
            Distance, VectorParams,
            SparseVectorParams, SparseIndexParams,
            PointStruct, SparseVector,
        )
    except ImportError:
        print("Missing qdrant-client. Run: pip install -r tools/requirements.txt")
        return 1

    QDRANT_PATH.mkdir(parents=True, exist_ok=True)
    client = QdrantClient(path=str(QDRANT_PATH))

    existing_names = [c.name for c in client.get_collections().collections]

    if args.reset and COLLECTION_NAME in existing_names:
        client.delete_collection(COLLECTION_NAME)
        existing_names.remove(COLLECTION_NAME)
        print(f"Collection '{COLLECTION_NAME}' dropped.")

    if COLLECTION_NAME not in existing_names:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={
                "dense": VectorParams(size=DENSE_DIM, distance=Distance.COSINE),
            },
            sparse_vectors_config={
                "sparse": SparseVectorParams(
                    index=SparseIndexParams(on_disk=False)
                ),
            },
        )
        print(f"Collection '{COLLECTION_NAME}' created  (dense={DENSE_DIM} cosine + sparse BM25).")
    else:
        print(f"Collection '{COLLECTION_NAME}' exists — upserting.")

    # --- Embed and index in batches ---
    print(f"\nIndexing {len(chunks)} chunks (batch size={args.batch_size}) ...\n")
    total = 0

    for batch_start in range(0, len(chunks), args.batch_size):
        batch = chunks[batch_start: batch_start + args.batch_size]

        # Embed the body text (not the raw metadata header lines)
        texts = [c["body"] for c in batch]

        output = model.encode(
            texts,
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=False,
            batch_size=args.batch_size,
        )

        points: list[PointStruct] = []
        for i, chunk in enumerate(batch):
            dense_vec = output["dense_vecs"][i].tolist()
            sparse_weights: dict = output["lexical_weights"][i]

            sparse_indices = [int(k) for k in sparse_weights.keys()]
            sparse_values = [float(v) for v in sparse_weights.values()]

            tag = " [INTERNAL ONLY]" if chunk.get("audience") == "internal_reasoning_only" else ""
            print(f"  [{batch_start + i + 1:02d}/{len(chunks)}] {chunk['chunk_id']}{tag}")

            points.append(
                PointStruct(
                    id=chunk_to_point_id(chunk["chunk_id"]),
                    vector={
                        "dense": dense_vec,
                        "sparse": SparseVector(
                            indices=sparse_indices,
                            values=sparse_values,
                        ),
                    },
                    payload={
                        "chunk_id": chunk["chunk_id"],
                        "category": chunk.get("category", ""),
                        "medical_content": chunk.get("medical_content", False),
                        "source": chunk.get("source", ""),
                        "audience": chunk.get("audience", "family_caregiver"),
                        "update_date": chunk.get("update_date", ""),
                        "filename": chunk["filename"],
                        "content": chunk["full_text"],
                    },
                )
            )

        client.upsert(collection_name=COLLECTION_NAME, points=points)
        total += len(points)

    # --- Summary ---
    info = client.get_collection(COLLECTION_NAME)
    print(f"\n{'=' * 60}")
    print("  SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Indexed:           {total} chunks")
    print(f"  General RAG:       {len(general)} chunks  (audience != internal_reasoning_only)")
    print(f"  Internal-only:     {len(internal)} chunks  (AD-8 — direct lookup only)")
    print(f"  Collection points: {info.points_count}")
    print(f"  Vector index:      {QDRANT_PATH}")
    print()
    print("  AD-8 isolation: apply  audience != 'internal_reasoning_only'")
    print("  to ALL search_hpa_guidelines queries. These chunks are stored")
    print("  but must never appear in general RAG results.")
    print(f"{'=' * 60}")
    print()
    print("  Next steps:")
    print("    1. Run 30-query manual RAG evaluation")
    print("    2. Implement tools/hpa_rag_search.py (search_hpa_guidelines MCP tool)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
