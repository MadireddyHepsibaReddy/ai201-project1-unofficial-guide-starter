"""
query.py — Grounded Response Generation
UWM Unofficial Guide | Milestone 5

Uses retrieved chunks from embed.py as context and passes them
to Groq's llama-3.3-70b-versatile to generate a grounded answer.
Source attribution is appended programmatically — not left to the LLM.

Usage:
    python query.py              # runs 3 end-to-end test queries
    from query import ask        # import into app.py
"""

import os
from groq import Groq
from dotenv import load_dotenv
from embed import retrieve, build_vector_store, get_collection
from ingest import run_pipeline

# Load GROQ_API_KEY from .env
load_dotenv()


# ─── CONFIGURATION ────────────────────────────────────────────────────────────

GROQ_MODEL = "llama-3.3-70b-versatile"
TOP_K      = 4


# ─── GROQ CLIENT ──────────────────────────────────────────────────────────────

def get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found. "
            "Make sure your .env file exists and contains: GROQ_API_KEY=your_key_here"
        )
    return Groq(api_key=api_key)


# ─── SYSTEM PROMPT ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a helpful assistant for UWM (University of Wisconsin-Milwaukee) students.
You answer questions about professors and courses using ONLY the student review documents provided to you.

STRICT RULES:
1. Answer ONLY using information from the provided documents. Do not use your general training knowledge.
2. If the documents do not contain enough information to answer the question, respond with exactly:
   "I don't have enough information in my documents to answer that question."
3. Do not guess, infer, or speculate beyond what is explicitly stated in the documents.
4. Keep your answer focused and direct — 3 to 6 sentences is ideal.
5. Do NOT list the sources in your answer — sources will be added automatically after your response.
"""


# ─── GENERATION ───────────────────────────────────────────────────────────────

def build_context(chunks: list[dict]) -> str:
    """
    Format retrieved chunks into a context block for the LLM prompt.
    Each chunk is labeled with its source filename.
    """
    lines = []
    for i, chunk in enumerate(chunks, 1):
        lines.append(f"[Document {i} — source: {chunk['source']}]")
        lines.append(chunk["text"])
        lines.append("")  # blank line between chunks
    return "\n".join(lines)


def generate(query: str, chunks: list[dict]) -> str:
    """
    Send retrieved chunks + user query to Groq and return the LLM's answer.
    Grounding is enforced via the system prompt.
    """
    client  = get_client()
    context = build_context(chunks)

    user_message = f"""Here are the relevant student reviews from UWM:

{context}

Question: {query}

Answer using only the documents above."""

    response = client.chat.completions.create(
        model    = GROQ_MODEL,
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        temperature = 0.2,   # low temperature = more factual, less creative
        max_tokens  = 512,
    )

    return response.choices[0].message.content.strip()


# ─── SOURCE ATTRIBUTION ───────────────────────────────────────────────────────

def format_sources(chunks: list[dict]) -> list[str]:
    """
    Extract unique source filenames from retrieved chunks.
    Programmatically guaranteed — not dependent on LLM to cite.
    """
    seen   = set()
    sources = []
    for chunk in chunks:
        src = chunk["source"]
        if src not in seen:
            seen.add(src)
            sources.append(src)
    return sources


# ─── END-TO-END FUNCTION ──────────────────────────────────────────────────────

def ask(question: str, k: int = TOP_K) -> dict:
    """
    Full RAG pipeline: retrieve → generate → attribute sources.

    Returns:
    {
        "answer":  str,         # LLM-generated grounded answer
        "sources": list[str],   # unique source filenames, programmatically extracted
        "chunks":  list[dict],  # raw retrieved chunks (for debugging)
    }
    """
    # 1. Retrieve relevant chunks
    chunks = retrieve(question, k=k)

    # 2. Generate grounded answer
    answer = generate(question, chunks)

    # 3. Extract sources programmatically
    sources = format_sources(chunks)

    return {
        "answer":  answer,
        "sources": sources,
        "chunks":  chunks,
    }


# ─── TEST QUERIES ─────────────────────────────────────────────────────────────

def test_generation():
    """
    Run 3 end-to-end tests:
    - 2 queries the system should answer well
    - 1 out-of-scope query the system should decline
    """
    test_cases = [
        {
            "query": "What do students say about Phillip Schmidt's calculus classes?",
            "expect": "grounded answer from Schmidt-Math.txt"
        },
        {
            "query": "What percentage of the grade is attendance in Abbas Ourmazd's physics class?",
            "expect": "grounded answer from Ourmazd-physics.txt"
        },
        {
            "query": "What is the best pizza place near UWM campus?",
            "expect": "system should decline — not in documents"
        },
    ]

    print("=" * 65)
    print("GENERATION TEST — end-to-end grounding check")
    print("=" * 65)

    for i, case in enumerate(test_cases, 1):
        print(f"\n{'='*65}")
        print(f"Test {i}: {case['query']}")
        print(f"Expected: {case['expect']}")
        print("-" * 65)

        result = ask(case["query"])

        print(f"Answer:\n{result['answer']}")
        print(f"\nSources ({len(result['sources'])}):")
        for src in result["sources"]:
            print(f"  • {src}")

        print(f"\nRetrieved chunks: {len(result['chunks'])}, "
              f"distances: {[c['distance'] for c in result['chunks']]}")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Make sure vector store is built before testing
    try:
        get_collection()
        print("Vector store already loaded\n")
    except Exception:
        print("Building vector store first...")
        chunks = run_pipeline()
        build_vector_store(chunks)

    test_generation()