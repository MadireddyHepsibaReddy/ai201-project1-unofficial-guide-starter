"""
embed.py — Embedding, Vector Store, and Retrieval
UWM Unofficial Guide | Milestone 4

Embeds chunks from ingest.py using all-MiniLM-L6-v2,
stores them in ChromaDB, and provides a retrieve() function
for semantic similarity search.

Usage:
    python embed.py              # builds the vector store and tests retrieval
    from embed import retrieve   # import into other scripts
"""

import os
import chromadb
from sentence_transformers import SentenceTransformer
from ingest import run_pipeline


# ─── CONFIGURATION ────────────────────────────────────────────────────────────

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "uwm_professor_reviews"
CHROMA_DIR      = "./chroma_db"   # local persistent ChromaDB storage
TOP_K           = 4


# ─── GLOBALS (loaded once, reused across calls) ────────────────────────────────

_model      = None
_collection = None


def get_model() -> SentenceTransformer:
    """Load embedding model (cached after first call)."""
    global _model
    if _model is None:
        print(f"  Loading embedding model: {EMBEDDING_MODEL} ...")
        _model = SentenceTransformer(EMBEDDING_MODEL)
        print("Model loaded\n")
    return _model


def get_collection() -> chromadb.Collection:
    """Return existing ChromaDB collection (cached after first call)."""
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        _collection = client.get_collection(name=COLLECTION_NAME)
    return _collection


# ─── STEP 1: EMBED AND STORE ──────────────────────────────────────────────────

def build_vector_store(chunks: list[dict]) -> chromadb.Collection:
    """
    Embed all chunks and store them in ChromaDB with metadata.

    Each document stored in ChromaDB has:
      - id:        unique string  e.g. "chunk_0042"
      - embedding: vector from all-MiniLM-L6-v2
      - document:  the raw chunk text (ChromaDB stores this for us)
      - metadata:  {"source": filename, "chunk_index": int}
    """
    global _collection

    model  = get_model()
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Delete and recreate the collection so re-runs start fresh
    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        client.delete_collection(name=COLLECTION_NAME)
        print(f"  Deleted existing collection '{COLLECTION_NAME}'")

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}   # cosine distance — better for text
    )
    _collection = collection

    print(f"  Embedding {len(chunks)} chunks...")

    # Embed in batches of 64 to avoid memory spikes
    batch_size = 64
    for batch_start in range(0, len(chunks), batch_size):
        batch = chunks[batch_start : batch_start + batch_size]

        texts     = [c["text"]        for c in batch]
        ids       = [f"chunk_{batch_start + i:04d}" for i in range(len(batch))]
        metadatas = [{"source": c["source"], "chunk_index": c["chunk_index"]} for c in batch]

        embeddings = model.encode(texts, show_progress_bar=False).tolist()

        collection.add(
            ids        = ids,
            embeddings = embeddings,
            documents  = texts,
            metadatas  = metadatas
        )

        print(f"    Stored chunks {batch_start}–{batch_start + len(batch) - 1}")

    print(f"\nVector store built — {collection.count()} chunks indexed\n")
    return collection


# ─── STEP 2: RETRIEVAL ────────────────────────────────────────────────────────

def retrieve(query: str, k: int = TOP_K) -> list[dict]:
    """
    Embed a query and return the top-k most similar chunks.

    Returns a list of dicts:
    [
      {
        "text":        str,   # chunk text
        "source":      str,   # filename e.g. "09_rmp_schmidt_phillip_math_calc.txt"
        "chunk_index": int,   # position of chunk within its source document
        "distance":    float  # cosine distance — lower = more similar (0 = identical)
      },
      ...
    ]
    """
    model      = get_model()
    collection = get_collection()

    query_embedding = model.encode([query]).tolist()

    results = collection.query(
        query_embeddings = query_embedding,
        n_results        = k,
        include          = ["documents", "metadatas", "distances"]
    )

    # Unpack ChromaDB result structure
    retrieved = []
    for text, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        retrieved.append({
            "text":        text,
            "source":      meta["source"],
            "chunk_index": meta["chunk_index"],
            "distance":    round(dist, 4)
        })

    return retrieved


# ─── STEP 3: TEST RETRIEVAL ───────────────────────────────────────────────────

def test_retrieval():
    """
    Run 3 of the 5 evaluation plan queries and print results.
    Used to manually verify retrieval quality before wiring in an LLM.
    """
    test_queries = [
        "What do students say about Phillip Schmidt's calculus classes?",
        "Is the final exam worth a lot in Dexuan Xie's math course?",
        "What percentage of the grade is attendance in Abbas Ourmazd's physics class?",
    ]

    print("=" * 65)
    print("RETRIEVAL TEST — 3 evaluation queries")
    print("=" * 65)

    all_passed = True

    for query in test_queries:
        print(f"\n Query: {query}\n")
        results = retrieve(query, k=TOP_K)

        for rank, chunk in enumerate(results, 1):
            status = "✅" if chunk["distance"] < 0.5 else "⚠️ "
            if chunk["distance"] >= 0.5:
                all_passed = False
            print(f"  Rank {rank} | distance: {chunk['distance']} {status}")
            print(f"  Source : {chunk['source']}")
            print(f"  Text   : {chunk['text'][:200]}...")
            print()

        print("-" * 65)

    if all_passed:
        print("\nAll top results have distance < 0.5 — retrieval looks good!")
    else:
        print("\nSome results have distance ≥ 0.5 — consider adjusting chunk size or top-k.")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\nRunning ingestion pipeline first...")
    chunks = run_pipeline()

    print(" Building vector store...")
    build_vector_store(chunks)

    print("Testing retrieval with evaluation queries...")
    test_retrieval()