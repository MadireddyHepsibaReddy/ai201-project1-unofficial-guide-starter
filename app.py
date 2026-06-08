"""
app.py — Gradio Web Interface
UWM Unofficial Guide | Milestone 5

Run with: python app.py
Then open: http://localhost:7860
"""

import gradio as gr
from query import ask
from embed import build_vector_store, get_collection
from ingest import run_pipeline


# ─── ENSURE VECTOR STORE IS READY ─────────────────────────────────────────────

def ensure_vector_store():
    """Build the vector store on startup if it doesn't exist yet."""
    try:
        get_collection()
        print("✅ Vector store ready")
    except Exception:
        print("Building vector store on startup...")
        chunks = run_pipeline()
        build_vector_store(chunks)
        print("✅ Vector store built")

ensure_vector_store()


# ─── QUERY HANDLER ────────────────────────────────────────────────────────────

def handle_query(question: str):
    """
    Called by Gradio on every button click or Enter press.
    Returns (answer_text, sources_text) for display in the UI.
    """
    question = question.strip()

    if not question:
        return "Please enter a question.", ""

    try:
        result  = ask(question)
        answer  = result["answer"]
        sources = result["sources"]
        chunks  = result["chunks"]

        # Format sources with bullet points
        sources_text = "\n".join(f"• {s}" for s in sources)

        # Append distance scores for transparency
        scores_text = "\n\nRetrieval distances: " + ", ".join(
            str(c["distance"]) for c in chunks
        )

        return answer, sources_text + scores_text

    except Exception as e:
        return f"Error: {str(e)}", ""


# ─── GRADIO INTERFACE ─────────────────────────────────────────────────────────

with gr.Blocks(title="UWM Unofficial Guide", theme=gr.themes.Soft()) as demo:

    gr.Markdown("""
    # 🐾 UWM Unofficial Guide
    ### Student-powered professor & course reviews for UW-Milwaukee
    Ask a plain-language question about any UWM professor or course.
    Answers are grounded in real student reviews — sources are always shown.
    """)

    with gr.Row():
        with gr.Column(scale=3):
            inp = gr.Textbox(
                label       = "Your question",
                placeholder = "e.g. Is Phillip Schmidt good for calculus? What is attendance worth in Ourmazd's class?",
                lines       = 2,
            )
            btn = gr.Button("Ask", variant="primary")

    with gr.Row():
        with gr.Column(scale=3):
            answer_box = gr.Textbox(
                label = "Answer",
                lines = 8,
                interactive = False,
            )
        with gr.Column(scale=1):
            sources_box = gr.Textbox(
                label = "Retrieved from",
                lines = 8,
                interactive = False,
            )

    gr.Markdown("""
    ---
    **Example questions to try:**
    - What do students say about Phillip Schmidt's calculus classes?
    - Is the final exam worth a lot in Dexuan Xie's math course?
    - What percentage of the grade is attendance in Abbas Ourmazd's physics class?
    - Is Amol Mali's CS 657 AI Ethics course easy or hard?
    - Which UWM math professor is recommended for students who struggle with math?
    """)

    # Wire up button click and Enter key
    btn.click(
        fn      = handle_query,
        inputs  = inp,
        outputs = [answer_box, sources_box],
    )
    inp.submit(
        fn      = handle_query,
        inputs  = inp,
        outputs = [answer_box, sources_box],
    )

# ─── LAUNCH ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    demo.launch()