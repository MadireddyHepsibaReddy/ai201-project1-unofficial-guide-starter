# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

UWM (University of Wisconsin-Milwaukee) professor and course reviews — student-generated opinions on teaching style, grading, exam difficulty, attendance policies, and course workload across multiple departments. This knowledge is valuable because UWM's official channels (course catalog, department websites, PAWS) offer zero student perspective on what a professor is actually like in the classroom. Reviews are scattered across Rate My Professors and word-of-mouth conversations with no unified way to search them. A student trying to choose between two math professors has no official resource — they rely on asking friends or scrolling through dozens of individual RMP pages. This system makes that collective student wisdom searchable through plain-language questions like "Which math professor curves grades?" or "Is Amol Mali's CS class hard?"

---

## Documents

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Rate My Professors | Jonathan Saffold — Business Administration reviews (5 reviews) | https://www.ratemyprofessors.com/professor/2093624 |
| 2 | Rate My Professors | Samar Mukhopadhyay — Business Management reviews (6 reviews) | https://www.ratemyprofessors.com/professor/2467112 |
| 3 | Rate My Professors | Amol Mali — Computer Science / AI Ethics reviews (3 reviews) | https://www.ratemyprofessors.com/professor/1671353 |
| 4 | Rate My Professors | Kristene Surerus — Biology/Science reviews (6 reviews) | https://www.ratemyprofessors.com/professor/1925733 |
| 5 | Rate My Professors | Christine Carlson — Chemistry reviews (3 reviews) | https://www.ratemyprofessors.com/professor/1581567 |
| 6 | Rate My Professors | Abbas Ourmazd — Physics reviews (4 reviews) | https://www.ratemyprofessors.com/professor/1657080 |
| 7 | Rate My Professors | John Museus — Mathematics reviews (3 reviews) | https://www.ratemyprofessors.com/professor/2802360 |
| 8 | Rate My Professors | Dexuan Xie — Mathematics reviews (6 reviews) | https://www.ratemyprofessors.com/professor/533912 |
| 9 | Rate My Professors | Phillip Schmidt — Mathematics / Calculus reviews (4 reviews) | https://www.ratemyprofessors.com/professor/3071128 |
| 10 | Rate My Professors | Brian Hospital — Mathematics reviews (3 reviews) | https://www.ratemyprofessors.com/professor/2561717 |
| 11 | Rate My Professors | Andrew Bolanowski — Mathematics reviews (4 reviews) | https://www.ratemyprofessors.com/professor/2041232 |
| 12 | AcademicJobs / RMP aggregator | UWM general department ratings overview — Business, Engineering, Arts | https://www.academicjobs.com/rate-my-professor/university-of-wisconsin-milwaukee/5585 |

---

## Chunking Strategy

**Chunk size:** 300 characters

**Overlap:** 50 characters

**Reasoning:**

The documents consist of short, opinion-based student reviews — typically 2 to 5 sentences each. Each review is self-contained and expresses one complete thought (e.g., "His exams are directly from homework. Final is 40% of the grade. Highly recommend."). This is very different from long-form guides or textbooks where a concept spans many paragraphs.

- **Small chunks (300 chars) are appropriate** because each individual review is short. If we used large chunks (800+ chars), we would merge multiple unrelated reviews together, diluting the semantic signal. A query like "Does Saffold curve grades?" should retrieve the specific review that mentions curving — not a 600-character blob mixing grading, attendance, and humor.
- **50-character overlap** protects against key facts falling at a chunk boundary. A critical one-sentence fact like "Final is 40% of your grade" will be fully captured in at least one chunk even if it sits near a split point.
- **Paragraph-first splitting strategy:** We split on double newlines (`\n\n`) first to respect natural review boundaries, then fall back to character-based splitting for any remaining blocks longer than 300 characters.

If chunks are too small (< 100 chars): they become fragments like "He is very kind" with no professor name or course context — useless for retrieval. If chunks are too large (> 600 chars): multiple professors or topics get merged, making it impossible for a specific query to match precisely.

---

## Retrieval Approach

**Embedding model:** `all-MiniLM-L6-v2` via `sentence-transformers` (runs locally, no API key required)

**Top-k:** 4

**Production tradeoff reflection:**

For this project, `all-MiniLM-L6-v2` is the right choice — it runs fully locally with no cost, no rate limits, and handles short opinion text well. Semantic search allows it to match a query like "Which professor is easiest?" to chunks containing "easy A," "didn't try hard," or "got an A without much effort" even without exact word overlap, because the embedding captures meaning rather than keywords.

If deploying for real users with no cost constraint, the tradeoffs to consider would be:
- **`text-embedding-3-small` (OpenAI):** Higher accuracy on domain-specific text, but costs money per API call and requires a key. Better choice at scale.
- **`multilingual-e5-large`:** Supports non-English queries — overkill for this English-only corpus but important for a multilingual student body.
- **Context length:** `all-MiniLM-L6-v2` has a 256-token limit, which is fine for our short reviews. Longer documents would require a model with a larger context window.
- **Latency:** Local models have no network latency but are slower on CPU. API models are faster at inference but add network round-trip time.

Top-k = 4 gives the LLM roughly 1,200 characters of context — enough to synthesize a complete answer from multiple reviews without being flooded with loosely related content. Retrieving too few (k=1) risks missing the most relevant chunk; too many (k=8+) dilutes the answer with off-topic reviews from unrelated professors.

---

## Evaluation Plan

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What do students say about Phillip Schmidt's calculus classes? | Schmidt is highly rated for Calc I and II (Math 231/232). Students say he makes 2-hour lectures engaging, uses group discussion, gives focused homework, and genuinely wants students to learn. Multiple students who failed calculus elsewhere passed with him. |
| 2 | Is the final exam worth a lot in Dexuan Xie's math course? | Yes — the final is 40% of the grade. Two midterms are 20% each. Quizzes and exams are pulled directly from homework problems, so completing all homework is the key strategy. |
| 3 | What percentage of the grade is attendance in Abbas Ourmazd's physics class? | Attendance is 25% of the grade. Homework is 25%. The final exam is 50%. Students must attend every class because participation directly impacts their grade. |
| 4 | Is Amol Mali's CS 657 AI Ethics course considered easy or hard? | Most students describe it as easy — homework is simple and the final is manageable. Main complaints are slow email responses and last-minute Zoom announcements. Missing assignments is dangerous since grading is sparse. |
| 5 | Which UWM math professor is most recommended for students who struggle with math? | Phillip Schmidt and John Museus are the most recommended. Schmidt is praised for engaging Calc I/II lectures and patience. Museus is known for generous grading and genuine care for each student's success. |

---

## Anticipated Challenges

1. **Sparse coverage per professor leading to hallucination:** Each document has only 3–6 reviews. If a user asks something not covered (e.g., "Does Professor Xie offer extra credit?"), the system may not have relevant chunks to retrieve. Without a strict grounding prompt, the LLM could generate a plausible-sounding answer from its general training knowledge rather than the documents. Mitigation: the system prompt will explicitly instruct the model to say "I don't have enough information" when retrieved chunks don't address the question.

2. **Chunk boundary splitting key facts:** Many critical facts in these reviews are single sentences (e.g., "Final is 40% of your grade"). If that sentence falls exactly at a chunk boundary and the overlap is too small, neither chunk will contain the complete fact and retrieval will miss it. Mitigation: split on paragraph/review boundaries (`\n\n`) first before falling back to character-based splitting, and use 50-character overlap to catch boundary cases.

---

## Architecture

```
+------------------------------------------------------------------+
|              UWM UNOFFICIAL GUIDE - RAG PIPELINE                 |
+------------------------------------------------------------------+

  +----------------------+
  |   /documents/        |
  |   12 x .txt files    |
  |   (RMP reviews)      |
  +----------+-----------+
             |
             v
  +----------------------------------+
  |  STAGE 1: Document Ingestion     |
  |  Tool: Python (open / pathlib)   |
  |  - Load all .txt files           |
  |  - Strip blank lines/whitespace  |
  |  - Attach source filename as     |
  |    metadata to each document     |
  +------------+---------------------+
               |
               v
  +----------------------------------+
  |  STAGE 2: Chunking               |
  |  Tool: Custom Python function    |
  |  - Split on \n\n first           |
  |    (review boundaries)           |
  |  - Chunk size: 300 characters    |
  |  - Overlap: 50 characters        |
  |  - Output: list of dicts         |
  |    {text, source, chunk_index}   |
  +------------+---------------------+
               |
               v
  +----------------------------------------+
  |  STAGE 3: Embedding + Vector Store     |
  |  Embedding: all-MiniLM-L6-v2           |
  |             (sentence-transformers)    |
  |  Vector Store: ChromaDB (local)        |
  |  - Embed each chunk                    |
  |  - Store vector + metadata             |
  |    (source filename, chunk_index)      |
  +------------+---------------------------+
               |
               v  <---------------------+
  +----------------------------------+  |
  |  STAGE 4: Retrieval              |  | User query (text)
  |  Tool: ChromaDB .query()         |  |
  |  - Embed query with              +--+
  |    all-MiniLM-L6-v2              |
  |  - Semantic similarity search    |
  |  - Return top-k=4 chunks         |
  |    + source filenames + scores   |
  +------------+---------------------+
               |
               v
  +----------------------------------------+
  |  STAGE 5: Grounded Generation          |
  |  LLM: Groq llama-3.3-70b-versatile    |
  |  - System prompt: answer ONLY from     |
  |    retrieved chunks                    |
  |  - If not in context -> say so         |
  |  - Append source filenames to output   |
  +------------+---------------------------+
               |
               v
  +----------------------------------+
  |  QUERY INTERFACE                 |
  |  Tool: Gradio (app.py)           |
  |  - Input: question textbox       |
  |  - Output: answer text           |
  |  - Output: sources list          |
  |  - Run: python app.py            |
  |  - URL: http://localhost:7860    |
  +----------------------------------+
```

---

## AI Tool Plan

**Milestone 3 — Ingestion and chunking:**

I will give Claude the Documents section (file names and structure) and the Chunking Strategy section (300 chars, 50 overlap, paragraph-first logic) from this planning.md. I will ask Claude to produce two things: (1) an `ingest.py` script that loads all `.txt` files from the `/documents` folder, strips extra whitespace and blank lines, and returns a list of `{"text": ..., "source": ...}` dicts; and (2) a `chunk_text(text, source, chunk_size=300, overlap=50)` function that splits on `\n\n` first and falls back to character-based sliding window chunking. I will verify the output by printing 5 random chunks and checking each has a `source` field, is under 350 characters, and reads as a complete thought.

**Milestone 4 — Embedding and retrieval:**

I will give Claude the Retrieval Approach section (model: `all-MiniLM-L6-v2`, vector store: ChromaDB, top-k: 4) and the Architecture diagram from this planning.md. I will ask Claude to produce: (1) an `embed.py` script that takes the chunk list from `ingest.py`, embeds each chunk using `SentenceTransformer("all-MiniLM-L6-v2")`, and stores embeddings in a ChromaDB collection with `source` and `chunk_index` in the metadata; and (2) a `retrieve(query, k=4)` function that embeds the query and returns the top-4 chunks with their source filenames and distance scores. I will verify by running 3 of my 5 evaluation questions and checking that returned chunks visibly relate to each question and distance scores are below 0.5.

**Milestone 5 — Generation and interface:**

I will give Claude the grounding requirement (answer only from retrieved context, cite sources, say "I don't have enough information" if context is insufficient), the Groq model name (`llama-3.3-70b-versatile`), and the Gradio interface description (one textbox input, one answer output, one sources output). I will ask Claude to produce: (1) a `generate(query, chunks)` function with a system prompt that strictly enforces grounding and appends source filenames programmatically; and (2) an `app.py` Gradio Blocks interface that calls retrieve → generate end-to-end. I will verify grounding by asking a question my documents don't cover and confirming the system declines rather than hallucinating.