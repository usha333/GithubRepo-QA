from embed_store import query_index
from llm import ask_llm


def answer_question(collection, question: str, top_k: int = 5) -> dict:
    """
    Returns {"answer": str, "sources": [filepaths used]}.
    """
    hits = query_index(collection, question, top_k=top_k)

    if not hits:
        return {"answer": "I couldn't find anything relevant in this repo for that question.", "sources": []}

    context_blocks = []
    for h in hits:
        context_blocks.append(f"--- {h['filepath']} ---\n{h['text']}")
    context = "\n\n".join(context_blocks)

    prompt = f"""You are answering questions about a specific codebase using ONLY the
context below. Do not invent files, functions, or behavior that isn't shown here.

CONTEXT:
{context}

QUESTION: {question}

Answer clearly and concisely. Whenever you reference something specific,
cite the file path in backticks, e.g. `backend/middleware/auth.js`.
If the context doesn't contain enough information to answer confidently,
say so explicitly rather than guessing."""

    answer = ask_llm(prompt)
    sources = sorted(set(h["filepath"] for h in hits))
    return {"answer": answer, "sources": sources}
