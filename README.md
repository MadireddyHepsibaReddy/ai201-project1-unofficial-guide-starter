# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

Student-generated professor and course reviews for UWM (University of Wisconsin-Milwaukee) — covering teaching style, grading, exam difficulty, attendance policies, and course workload across departments including Math, CS, Business, Chemistry, and Physics.

This knowledge is valuable because UWM's official channels (course catalog, PAWS, department websites) offer zero student perspective on what a professor is actually like in the classroom. A student choosing between two math professors has no official resource — they rely on asking friends or scrolling through dozens of individual Rate My Professors pages with no way to search across all of them at once. Reviews are scattered, informal, and impossible to query. This system makes that collective student wisdom searchable through plain-language questions like "Which math professor curves grades?" or "Is Amol Mali's CS class hard?"

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Rate My Professors — Jonathan Saffold | Professor reviews (Business Admin) | https://www.ratemyprofessors.com/professor/2093624 |
| 2 | Rate My Professors — Samar Mukhopadhyay | Professor reviews (Business Mgmt) | https://www.ratemyprofessors.com/professor/2467112 |
| 3 | Rate My Professors — Amol Mali | Professor reviews (Computer Science) | https://www.ratemyprofessors.com/professor/1671353 |
| 4 | Rate My Professors — Kristene Surerus | Professor reviews (Biology/Science) | https://www.ratemyprofessors.com/professor/1925733 |
| 5 | Rate My Professors — Christine Carlson | Professor reviews (Chemistry) | https://www.ratemyprofessors.com/professor/1581567 |
| 6 | Rate My Professors — Abbas Ourmazd | Professor reviews (Physics) | https://www.ratemyprofessors.com/professor/1657080 |
| 7 | Rate My Professors — John Museus | Professor reviews (Mathematics) | https://www.ratemyprofessors.com/professor/2802360 |
| 8 | Rate My Professors — Dexuan Xie | Professor reviews (Mathematics) | https://www.ratemyprofessors.com/professor/533912 |
| 9 | Rate My Professors — Phillip Schmidt | Professor reviews (Math/Calculus) | https://www.ratemyprofessors.com/professor/3071128 |
| 10 | Rate My Professors — Brian Hospital | Professor reviews (Mathematics) | https://www.ratemyprofessors.com/professor/2561717 |
| 11 | Rate My Professors — Andrew Bolanowski | Professor reviews (Mathematics) | https://www.ratemyprofessors.com/professor/2041232 |
| 12 | AcademicJobs / RMP aggregator | Department overview (multi-dept) | https://www.academicjobs.com/rate-my-professor/university-of-wisconsin-milwaukee/5585 |

All documents were manually collected as `.txt` files in the `/documents` folder because Rate My Professors blocks automated scraping.

---

## Chunking Strategy

**Chunk size:** 300 characters

**Overlap:** 50 characters

**Why these choices fit your documents:**

The documents consist of short, opinion-based student reviews — typically 2 to 5 sentences each. Each review is self-contained and expresses one complete thought (e.g., "His exams are directly from homework. Final is 40% of the grade. Highly recommend."). This is very different from long-form guides or textbooks where a concept spans many paragraphs.

Small chunks (300 chars) are appropriate because merging multiple reviews into one chunk dilutes the semantic signal. A query like "Does Schmidt curve grades?" should retrieve the specific review mentioning curving — not a 600-character blob mixing grading, attendance, and humor from different reviewers. The 50-character overlap protects against key facts falling at a chunk boundary — a critical one-sentence fact like "Final is 40% of your grade" is fully captured in at least one chunk even if it sits near a split point.

The splitting strategy is paragraph-first: the code splits on `\n\n` (double newlines) first to respect natural review boundaries, then falls back to a sliding window character split with word-boundary awareness (walks back to the nearest space before cutting) for any paragraph still longer than 300 characters. This prevents mid-word cuts.

Preprocessing before chunking: HTML tags removed, HTML entities decoded (`&amp;`, `&#39;`, `&nbsp;`), pure formatting lines (`---`) stripped, and trailing whitespace normalized.

**Sample chunks (5 labeled examples):**

**Chunk 1** — Source: `Schmidt-Math.txt`, Index 8, Length: 123 chars
```
often succeed with Schmidt. Strongly recommended for anyone taking Calc I or II at UWM. Office hours are highly productive.
```

**Chunk 2** — Source: `Carlson-Chemistry.txt`, Index 5, Length: 176 chars
```
Review 3:
She is always available and willing to help. Her exams are challenging but fair when you put in the work. The extra credit opportunities really help your final grade.
```

**Chunk 3** — Source: `Hospital-Math.txt`, Index 3, Length: 299 chars
```
Review 2:
1. Teaches the topics off a PowerPoint like this is some gen ed. Hard to understand if all the information is just thrown at you and explained terribly. 2. No study material to help prepare for the exams, which is a big part of the class. Tests are very hard. 3. Hardly any homework to ask
```

**Chunk 4** — Source: `Saffold-Business.txt`, Index 7, Length: 160 chars
```
Summary tags from students: Amazing lectures, Clear grading criteria, Participation matters, Test heavy in terms of question count but manageable with freebies.
```

**Chunk 5** — Source: `Mukhopadhyay-Business.txt`, Index 3, Length: 109 chars
```
ou do your best on each assignment if you want to pass. If there are any other options for BUS576, take them.
```

**Final chunk count:** 107 chunks across 12 documents (avg: 195 chars, min: 53 chars, max: 300 chars). No empty or HTML-artifact chunks detected.

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers` — runs fully locally with no API key and no rate limits.

**Production tradeoff reflection:**

For this project, `all-MiniLM-L6-v2` is the right choice — it runs locally at no cost and handles short opinion text well. Semantic search allows it to match a query like "Which professor is easiest?" to chunks containing "easy A," "didn't try hard," or "got an A without much effort" even without exact word overlap, because the embedding captures meaning rather than keywords.

If deploying for real users with no cost constraint, the tradeoffs to weigh would be: `text-embedding-3-small` (OpenAI) offers higher accuracy on domain-specific text but costs money per API call and requires a key — better at production scale. `multilingual-e5-large` supports non-English queries, which matters for UWM's multilingual student body, but is overkill for this English-only corpus. On context length, `all-MiniLM-L6-v2` has a 256-token limit — fine for short reviews but insufficient for longer documents like syllabi or handbooks, where a model with a 512–8192 token window would be needed. Finally, local models have no network latency but are slower on CPU; API models are faster at inference but add network round-trip time and introduce rate limits that could bottleneck a production app with many concurrent users.

---

## Retrieval Test Results

**Vector store:** ChromaDB (local, persistent at `./chroma_db/`)
**Top-k:** 4 | **Distance metric:** Cosine (lower = more similar)

### Query 1: "What do students say about Phillip Schmidt's calculus classes?"

| Rank | Distance | Source | Chunk preview |
|------|----------|--------|---------------|
| 1 | 0.3286 ✅ | Schmidt-Math.txt | "Summary: Consistently excellent reviews. Teaches Math 231 (Calc I) and 232 (Calc II), mainly Calc II. 2-hour lectures that are engaging with small talk and group discussion. Minimal but focused homewo..." |
| 2 | 0.3934 ✅ | Bolanowshi-Math.txt | "Summary: Very mixed reviews. Some students credit him with helping them finally pass calculus; others report excessive homework (300 problems/week), exams disconnected from course material..." |
| 3 | 0.4292 ✅ | Surerus-Science.txt | "Review 6: To put it simply, this class is a joke. The lecture slides are vague, lectures are not helpful..." |
| 4 | 0.4615 ✅ | Schmidt-Math.txt | "Review 4: He always dedicated his classes to be sure we weren't just able to pass an exam, but that we knew what we were doing..." |

**Why ranks 1 and 4 are relevant:** Both chunks are from `Schmidt-Math.txt` and directly describe Schmidt's teaching philosophy — engaging 2-hour lectures, student-centered approach, and positive outcomes for students who struggled elsewhere. The embedding correctly matched "calculus classes" and "students say" to Schmidt's review language about Math 231/232. Rank 2 (Bolanowshi) is also a calculus professor — semantically close but from the wrong source, which the LLM correctly de-prioritized in its answer.

### Query 2: "What percentage of the grade is attendance in Abbas Ourmazd's physics class?"

| Rank | Distance | Source | Chunk preview |
|------|----------|--------|---------------|
| 1 | 0.2847 ✅ | Ourmazd-physics.txt | "Summary: Attendance is 25% of your grade — do not skip class. Homework is 25%, final exam is 50%..." |
| 2 | 0.393 ✅ | Ourmazd-physics.txt | "class participation is a percentage of your entire grade...." |
| 3 | 0.4001 ✅ | Ourmazd-physics.txt | "Review 4: Abbas is my favorite professor thus far. Attendance is 25% of your grade. Homework is also 25%..." |
| 4 | 0.4156 ✅ | Ourmazd-physics.txt | "Source: Rate My Professors - Abbas Ourmazd, Physics, UWM URL: https://..." |

**Why all 4 are relevant:** All 4 results come from `Ourmazd-physics.txt` — retrieval correctly focused entirely on the right professor. The top chunk explicitly states the exact grade breakdown (25% attendance, 25% homework, 50% final). A distance of 0.2847 indicates a very strong semantic match — this is the best-performing query in the test set.

### Query 3: "Is the final exam worth a lot in Dexuan Xie's math course?"

| Rank | Distance | Source | Chunk preview |
|------|----------|--------|---------------|
| 1 | 0.4657 ✅ | Mukhopadhyay-Business.txt | "Review 3: I would not recommend taking this course. There were a total of 8 grades entered throughout the whole semester..." |
| 2 | 0.4681 ✅ | Surerus-Science.txt | "Review 3: Read the chapters, lecture notes... her final exam is more difficult and nothing like her online..." |
| 3 | 0.4859 ✅ | Hospital-Math.txt | "Review 1: He would just read off slides — not TEACH. Final is 40% of your grade. Made exams way too long..." |
| 4 | 0.5162 ⚠️ | Bolanowshi-Math.txt | "Summary: Very mixed reviews. Some students credit him with helping them finally pass calculus..." |

**Note:** `Xie-Math.txt` did not appear in the top-4 — this is the documented failure case. See Failure Case Analysis below.

---

## Grounded Generation

**System prompt grounding instruction:**

```
You are a helpful assistant for UWM (University of Wisconsin-Milwaukee) students.
You answer questions about professors and courses using ONLY the student review
documents provided to you.

STRICT RULES:
1. Answer ONLY using information from the provided documents. Do not use your
   general training knowledge.
2. If the documents do not contain enough information to answer the question,
   respond with exactly:
   "I don't have enough information in my documents to answer that question."
3. Do not guess, infer, or speculate beyond what is explicitly stated in the documents.
4. Keep your answer focused and direct — 3 to 6 sentences is ideal.
5. Do NOT list the sources in your answer — sources will be added automatically
   after your response.
```

The LLM is also given `temperature=0.2` to reduce creative or hallucinated responses, and each chunk is labeled with its source filename in the context block (e.g., `[Document 1 — source: Schmidt-Math.txt]`) so the model knows where each fact comes from.

**How source attribution is surfaced in the response:**

Source filenames are extracted programmatically from the retrieved chunks' metadata — not generated by the LLM. The `format_sources()` function in `query.py` deduplicates and returns `chunk["source"]` values from the ChromaDB metadata. This guarantees source attribution even if the LLM fails to cite sources in its text. Sources and retrieval distance scores are displayed in the "Retrieved from" panel in the Gradio UI.

**Example responses:**

*Query:* "What do students say about Phillip Schmidt's calculus classes?"

*Answer:* Students consistently give excellent reviews of Phillip Schmidt's calculus classes, particularly Calc II. They find his 2-hour lectures engaging, with small talk and group discussion, and appreciate the minimal but focused homework. Many students who struggled with calculus elsewhere have reported succeeding with Schmidt. One student noted that Schmidt's classes helped them learn how to apply math, rather than just pass an exam.

*Retrieved from:* Schmidt-Math.txt • Bolanowshi-Math.txt • Surerus-Science.txt | Distances: 0.3286, 0.3934, 0.4292, 0.4615

---

*Query:* "What percentage of the grade is attendance in Abbas Ourmazd's physics class?"

*Answer:* According to the documents, attendance is 25% of the grade in Abbas Ourmazd's physics class. This is consistently stated in multiple reviews. Homework is 25% and the final exam accounts for the remaining 50%. The documents confirm that skipping class directly impacts your grade.

*Retrieved from:* Ourmazd-physics.txt | Distances: 0.2847, 0.393, 0.4001, 0.4156

---

*Out-of-scope query:* "What is the best pizza place near UWM campus?"

*Answer:* I don't have enough information in my documents to answer that question.

*Retrieved from:* General Dept Rating.txt • Ourmazd-physics.txt • Saffold-Business.txt | Distances: 0.5603, 0.6036, 0.629, 0.6504

*(All distances above 0.5 — retrieval found nothing relevant, system correctly declined.)*

---

## Query Interface

**How to run:** `python app.py` → open `http://localhost:7860`

**Input field:** "Your question" — a plain-language text box with placeholder examples. Accepts any question. Supports both the Ask button and Enter key.

**Output fields:**
- **Answer** — LLM-generated response grounded in retrieved documents
- **Retrieved from** — bullet list of source filenames + retrieval distance scores for transparency

**Sample interaction transcript:**

> **Input:** Is Amol Mali's CS 657 AI Ethics course easy or hard?
>
> **Answer:** According to student reviews, Amol Mali's CS 657 AI Ethics course is generally considered easy. Most students describe the homework assignments as simple and the final exam as manageable. The main complaints are slow email responses and last-minute Zoom announcements for required sessions. One important note: do not skip any assignments, as grading is sparse and each one significantly impacts the final grade.
>
> **Retrieved from:**
> • Mali-CS.txt
>
> Retrieval distances: 0.31, 0.38, 0.43, 0.47

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students say about Phillip Schmidt's calculus classes? | Schmidt highly rated for Calc I/II. Engaging 2-hour lectures, group discussion, focused homework. Students who failed elsewhere succeeded with him. | "Students consistently give excellent reviews... 2-hour lectures engaging, small talk and group discussion... Many students who struggled with calculus elsewhere have reported succeeding with Schmidt." Sources: Schmidt-Math.txt | Relevant | Accurate |
| 2 | Is the final exam worth a lot in Dexuan Xie's math course? | Yes — final is 40% of grade. Two midterms at 20% each. Quizzes/exams pulled directly from homework. | Retrieved Mukhopadhyay-Business.txt (rank 1) and Surerus-Science.txt (rank 2) instead of Xie-Math.txt. Generated a vague answer about high-stakes finals without citing Xie's specific 40% grade breakdown. | Off-target | Inaccurate |
| 3 | What percentage of the grade is attendance in Abbas Ourmazd's physics class? | Attendance 25%, Homework 25%, Final 50%. | "Attendance is 25% of the grade... consistently stated in multiple reviews... Homework is 25% and the final exam accounts for the remaining 50%." Sources: Ourmazd-physics.txt | Relevant | Accurate |
| 4 | Is Amol Mali's CS 657 AI Ethics course considered easy or hard? | Easy — simple homework, manageable final. Slow emails, last-minute Zooms. Don't miss assignments. | Correctly identified as easy, noted simple homework and manageable final, included the assignment warning. Sources: Mali-CS.txt | Relevant | Accurate |
| 5 | Which UWM math professor is most recommended for students who struggle with math? | Phillip Schmidt and John Museus. Schmidt for engaging Calc I/II. Museus for generous grading and care. | Named both Schmidt and Museus, described Schmidt's engaging lectures and Museus's generous grading and student investment. Sources: Schmidt-Math.txt, Museus-Math.txt | Relevant | Accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target
**Response accuracy:** Accurate / Partially accurate / Inaccurate

**Result: 4/5 accurate, 1/5 inaccurate**

---

## Failure Case Analysis

**Question that failed:** "Is the final exam worth a lot in Dexuan Xie's math course?"

**What the system returned:** The system retrieved `Mukhopadhyay-Business.txt` (rank 1, distance 0.4657) and `Surerus-Science.txt` (rank 2, distance 0.4681) instead of `Xie-Math.txt`. The generated answer discussed high-stakes finals in general terms without the specific fact that Xie's final is 40% of the grade or that exams come directly from homework. `Xie-Math.txt` never appeared in the top-4 results.

**Root cause (tied to a specific pipeline stage):** This is a **chunking + sparse name-mention problem at the ingestion stage**. The query contains the name "Dexuan Xie" but the review chunks in `Xie-Math.txt` rarely mention his name explicitly within the same chunk as the grade facts. The professor's name "Dexuan Xie" appears mainly in the document header chunk, while the grade-breakdown facts ("final is 40% of your grade," "quizzes come directly from homework") appear in separate review body chunks. Because these were split into different chunks at the `\n\n` boundary, no single chunk strongly associates "Xie" with "final is 40%." Meanwhile, `Mukhopadhyay-Business.txt` and `Surerus-Science.txt` also contain language about high-stakes finals and sparse grading structures — semantically similar to the query's concept of "is the final worth a lot" — so the embedding matched those instead.

**What you would change to fix it:** During ingestion, prepend the professor's name to every review chunk from that document — for example, prefix each chunk with "Professor Dexuan Xie review: " before embedding. This ensures the professor's name co-occurs with the grade facts in every chunk, so a query containing "Dexuan Xie" + "final exam" would match `Xie-Math.txt` chunks directly rather than semantically similar chunks from unrelated professors.

---

## Spec Reflection

**One way the spec helped you during implementation:**

The planning.md requirement to write out the chunking strategy before writing any code was the single most valuable constraint in the project. Because I had decided on 300-character paragraph-first chunking with 50-character overlap before writing `ingest.py`, the implementation was clear and purposeful — every parameter had a documented reason. When the sliding window produced mid-word cuts during testing, I knew immediately that the fix needed to respect word boundaries, because the spec had established that individual reviews should be "self-contained" chunks. Without the pre-written spec, I likely would have used a default fixed-size splitter and discovered the problem much later during retrieval testing, when it would have been harder to trace back.

**One way your implementation diverged from the spec, and why:**

The planning.md specified that source attribution would be handled by instructing the LLM to cite sources in its response. During implementation, I changed this to programmatic attribution — the `format_sources()` function in `query.py` extracts source filenames directly from ChromaDB chunk metadata, completely bypassing the LLM. This diverged from the spec because during testing I noticed the LLM sometimes cited "Document 1" or "Document 3" (the in-prompt labels) instead of the actual filenames. Programmatic extraction guaranteed that real filenames always appear in the UI, regardless of what the LLM says. I also added retrieval distance scores to the "Retrieved from" panel — not in the original spec — because the pizza out-of-scope test showed that displaying distances (0.56–0.65) makes it transparent to users when the system has nothing relevant in its documents.

---

## AI Usage

**Instance 1**

- *What I gave the AI:* The Documents section from planning.md (12 .txt files, their structure, one review per paragraph) and the Chunking Strategy section (300 chars, 50 overlap, paragraph-first logic with word-boundary awareness).
- *What it produced:* An `ingest.py` script with `load_documents()`, `clean_document()`, and `chunk_text()` functions. The initial sliding window split at exactly 300 characters regardless of word boundaries, producing chunks that ended mid-word (e.g., a chunk ending in "Very ni").
- *What I changed or overrode:* I identified the mid-word cut bug by inspecting the 5 sample chunks printed during validation. I directed Claude to fix the sliding window to walk back to the nearest space before setting the end boundary. This word-boundary fix was not in Claude's first output — I caught it through manual chunk inspection and specified the exact fix needed.

**Instance 2**

- *What I gave the AI:* The grounding requirement from the project spec ("answer only from retrieved context, cite sources, decline if not in documents"), the Groq model name (`llama-3.3-70b-versatile`), the pipeline architecture diagram from planning.md, and the Gradio interface layout (one question input, one answer output, one sources output).
- *What it produced:* A `query.py` with a `generate()` function and system prompt, and an `app.py` Gradio interface. The original system prompt said "try to use only the information from the provided documents" — a weak instruction the LLM could interpret loosely.
- *What I changed or overrode:* I strengthened the system prompt from "try to use only" to "Answer ONLY using information from the provided documents" and added the exact refusal phrase ("I don't have enough information in my documents to answer that question.") so the LLM's decline behavior would be consistent and testable. I also added `temperature=0.2` myself — the Claude-generated code used the Groq default temperature, which produced slightly creative responses during the first test. Lowering the temperature made answers more factual and reproducible.