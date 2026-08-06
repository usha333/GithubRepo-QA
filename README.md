# Repo Q&A — understand any GitHub repo in minutes

Paste a public GitHub repo URL and get:
- An instant plain-language **overview** of what the project does
- A **file map** — one-line description per file
- A **chat** to ask specific questions, answered with file-path citations grounded in the actual code (not guesses)

## Who this helps
Students exploring open source, bootcamp grads facing an unfamiliar codebase in an interview task, junior PMs/designers who need to understand a repo without reading code, contributors looking for where to make a first PR, and engineers onboarding onto a new team's code.

## Setup (5 minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Get a free Groq API key at https://console.groq.com
export GROQ_API_KEY="gsk_..."

# 3. Run
streamlit run app.py
```

Then open the local URL Streamlit prints, paste a public GitHub repo URL, and click **Analyze repo**.

## Architecture

```
GitHub URL
   │
   ▼
repo_loader.py   → clones repo locally (GitPython, shallow clone)
   │
   ▼
chunker.py       → walks files, splits into chunks with filepath metadata
   │
   ▼
embed_store.py   → embeds chunks (sentence-transformers) into ChromaDB
   │
   ├──▶ summarizer.py → auto-overview + file map (runs once, on load)
   │
   └──▶ qa.py          → retrieval + LLM answer with citations (runs per question)
                │
                ▼
            llm.py (Groq)
```

## Why each tool, vs. the alternatives

| Stage | Chosen | Instead of | Why |
|---|---|---|---|
| Cloning | GitPython | `subprocess` + raw git CLI | Python object API, cleaner error handling |
| Chunking | Custom, file/function-aware | LangChain `RecursiveCharacterTextSplitter` | Character-based splitting can cut a function in half, which produces garbled context for code Q&A. Keeping whole files/functions intact matters more here than for prose |
| Embeddings | `sentence-transformers` (local) | OpenAI/Cohere embeddings API | Free, no per-repo cost, no API key, works offline after first model download |
| Vector store | ChromaDB (in-memory) | Pinecone / Weaviate / raw FAISS | No server to run, no account, handles metadata (filepaths) natively — FAISS alone would need you to hand-roll that |
| LLM | Groq (Llama 3.1 8B) | OpenAI GPT-4 / local Ollama model | Free tier, very fast inference (snappy chat UX); a local model works too but needs a beefier machine and a multi-GB download |
| UI | Streamlit | Flask/FastAPI + hand-written HTML/JS | Chat UI, sidebar, and spinners come as single function calls — much faster to ship, and this project's audience includes non-technical users who benefit from a real web UI |

## Scope guardrails (intentional, for a 1-day build)

- ❌ No private repo support (would need GitHub OAuth)
- ❌ No multi-turn conversation memory — each question is answered independently against the retrieved context
- ❌ Repos capped at 500 indexed files, files over ~200KB skipped (generated/data files add noise, not signal)

## Extending it later

- **Persistent index**: swap `chromadb.Client()` for `chromadb.PersistentClient(path=...)` in `embed_store.py` to cache popular repos between runs instead of re-embedding every time
- **Private repos**: add GitHub OAuth in `repo_loader.py` and pass a token to `Repo.clone_from`
- **Conversation memory**: pass `st.session_state.messages` history into the prompt in `qa.py`
- **Offline LLM**: add an `llm_ollama.py` with the same `ask_llm()` signature and swap the import in `qa.py`/`summarizer.py` if you want zero external API dependency
