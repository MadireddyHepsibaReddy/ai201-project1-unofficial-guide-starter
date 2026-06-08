"""
ingest.py — Document Ingestion and Chunking Pipeline
UWM Unofficial Guide | Milestone 3

Loads all .txt files from /documents, cleans them, and splits into
chunks using a paragraph-first strategy (300 chars, 50 char overlap).
"""

import os
import re


# ─── CONFIGURATION ────────────────────────────────────────────────────────────

DOCUMENTS_DIR = "documents"
CHUNK_SIZE = 300       # characters
OVERLAP = 50           # characters


# ─── STEP 1: LOAD DOCUMENTS ───────────────────────────────────────────────────

def load_documents(doc_dir: str) -> list[dict]:
    """
    Load all .txt files from the given directory.
    Returns a list of {"text": ..., "source": ...} dicts.
    """
    documents = []
    files = sorted(f for f in os.listdir(doc_dir) if f.endswith(".txt"))

    for filename in files:
        filepath = os.path.join(doc_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            raw_text = f.read()
        documents.append({
            "text": raw_text,
            "source": filename
        })
        print(f"  Loaded: {filename} ({len(raw_text)} chars)")

    print(f"\n Loaded {len(documents)} documents\n")
    return documents


# ─── STEP 2: CLEAN DOCUMENTS ──────────────────────────────────────────────────

def clean_document(text: str) -> str:
    """
    Clean a raw document string:
    - Remove HTML tags and entities
    - Remove repeated separator lines (---) that are just formatting
    - Normalize whitespace
    - Keep: review text, professor names, course info, opinions, ratings
    """
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Decode common HTML entities
    text = text.replace("&amp;", "&")
    text = text.replace("&nbsp;", " ")
    text = text.replace("&quot;", '"')
    text = text.replace("&#39;", "'")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")

    # Remove lines that are purely formatting (e.g., "---", "===")
    text = re.sub(r"^[-=]{3,}\s*$", "", text, flags=re.MULTILINE)

    # Collapse 3+ consecutive newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip trailing whitespace from each line
    lines = [line.rstrip() for line in text.splitlines()]
    text = "\n".join(lines)

    # Strip leading/trailing whitespace from the whole document
    text = text.strip()

    return text


def clean_all(documents: list[dict]) -> list[dict]:
    """Clean all documents and return updated list."""
    cleaned = []
    for doc in documents:
        cleaned_text = clean_document(doc["text"])
        cleaned.append({
            "text": cleaned_text,
            "source": doc["source"]
        })
    print(f"Cleaned {len(cleaned)} documents\n")
    return cleaned


# ─── STEP 3: CHUNKING ─────────────────────────────────────────────────────────

def chunk_text(text: str, source: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[dict]:
    """
    Split a document into chunks using a paragraph-first strategy:
    1. Split on double newlines (\\n\\n) to respect natural review boundaries.
    2. For any paragraph still longer than chunk_size, apply a sliding
       window character split with the specified overlap.

    Returns a list of {"text": ..., "source": ..., "chunk_index": ...} dicts.
    """
    chunks = []
    chunk_index = 0

    # Split into paragraphs first
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    for para in paragraphs:
        if len(para) <= chunk_size:
            # Paragraph fits in one chunk — keep it whole
            chunks.append({
                "text": para,
                "source": source,
                "chunk_index": chunk_index
            })
            chunk_index += 1
        else:
            # Paragraph is too long — apply sliding window split on word boundaries
            start = 0
            while start < len(para):
                end = start + chunk_size
                if end < len(para):
                    # Walk back to the nearest space so we don't cut mid-word
                    while end > start and para[end] != " ":
                        end -= 1
                chunk_str = para[start:end].strip()
                if chunk_str:
                    chunks.append({
                        "text": chunk_str,
                        "source": source,
                        "chunk_index": chunk_index
                    })
                    chunk_index += 1
                start += chunk_size - overlap  # slide forward with overlap

    return chunks


def chunk_all(documents: list[dict]) -> list[dict]:
    """Chunk all documents and return a flat list of all chunks."""
    all_chunks = []
    for doc in documents:
        doc_chunks = chunk_text(doc["text"], doc["source"])
        all_chunks.extend(doc_chunks)
        print(f"  {doc['source']}: {len(doc_chunks)} chunks")

    print(f"\n Total chunks produced: {len(all_chunks)}\n")
    return all_chunks


# ─── STEP 4: VALIDATION ───────────────────────────────────────────────────────

def validate_chunks(chunks: list[dict], sample_size: int = 5):
    """
    Print a sample of chunks for manual inspection.
    Also checks for common problems: empty chunks, very short chunks,
    and chunks missing metadata.
    """
    print("=" * 60)
    print(f"CHUNK VALIDATION — showing {sample_size} samples")
    print("=" * 60)

    # Check for problems
    empty = [c for c in chunks if not c["text"].strip()]
    tiny = [c for c in chunks if 0 < len(c["text"]) < 50]
    no_source = [c for c in chunks if not c.get("source")]

    if empty:
        print(f"WARNING: {len(empty)} empty chunks found — check your splitter")
    if tiny:
        print(f"WARNING: {len(tiny)} very short chunks (< 50 chars) — may be too small")
    if no_source:
        print(f"WARNING: {len(no_source)} chunks missing 'source' metadata")

    if not empty and not tiny and not no_source:
        print("No obvious problems detected\n")

    # Print sample chunks
    import random
    sample = random.sample(chunks, min(sample_size, len(chunks)))

    for i, chunk in enumerate(sample, 1):
        print(f"\n--- Sample Chunk {i} ---")
        print(f"Source : {chunk['source']}")
        print(f"Index  : {chunk['chunk_index']}")
        print(f"Length : {len(chunk['text'])} chars")
        print(f"Text   :\n{chunk['text']}")

    print("\n" + "=" * 60)
    print(f"Total chunks: {len(chunks)}")
    lengths = [len(c["text"]) for c in chunks]
    print(f"Avg chunk length: {sum(lengths) // len(lengths)} chars")
    print(f"Min chunk length: {min(lengths)} chars")
    print(f"Max chunk length: {max(lengths)} chars")
    print("=" * 60)


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def run_pipeline() -> list[dict]:
    """
    Run the full ingestion pipeline:
      Load → Clean → Chunk → Validate
    Returns the final list of chunks for use in embed.py.
    """
    print("\nSTEP 1: Loading documents...")
    documents = load_documents(DOCUMENTS_DIR)

    print("STEP 2: Cleaning documents...")
    documents = clean_all(documents)

    print("STEP 3: Chunking documents...")
    chunks = chunk_all(documents)

    print("STEP 4: Validating chunks...")
    validate_chunks(chunks)

    return chunks


if __name__ == "__main__":
    chunks = run_pipeline()