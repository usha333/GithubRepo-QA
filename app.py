import streamlit as st

from repo_loader import clone_repo, cleanup_repo
from chunker import chunk_repo
from embed_store import build_index
from summarizer import generate_overview, generate_file_map
from qa import answer_question

st.set_page_config(page_title="Repo Q&A", page_icon="📦", layout="wide")


st.markdown("""
<style>
    .block-container { padding-top: 2.5rem; max-width: 900px; }
    .repo-hero {
        text-align: center;
        padding: 0.5rem 0 1.5rem 0;
    }
    .repo-hero h1 { margin-bottom: 0.25rem; }
    .repo-hero p { color: var(--text-color-secondary, #888); font-size: 1.05rem; }
    div[data-testid="stForm"] {
        border: 1px solid rgba(128,128,128,0.25);
        border-radius: 14px;
        padding: 1.5rem 1.5rem 1rem 1.5rem;
        background: rgba(128,128,128,0.04);
    }
    .repo-badge {
        display: inline-block;
        padding: 0.3rem 0.9rem;
        border-radius: 999px;
        background: rgba(46, 160, 67, 0.12);
        color: #2ea043;
        font-weight: 600;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
    }
    .repo-logo {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.6rem;
    }
    .repo-logo svg { display: block; }
</style>
""", unsafe_allow_html=True)

for key in ("collection", "chunks", "overview", "file_map", "messages", "repo_name"):
    if key not in st.session_state:
        st.session_state[key] = None
if st.session_state.messages is None:
    st.session_state.messages = []

st.markdown(
    """
    <div class="repo-hero">
        <div class="repo-logo">
            <svg width="40" height="40" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
                <path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38
                    0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53
                    .63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95
                    0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0
                    1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15
                    0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38
                    A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z"/>
            </svg>
            <h1 style="margin:0;">Repo Q&A</h1>
        </div>
        <p>Paste a public GitHub repo URL. Get an instant overview, a file map, and a chat to ask anything about the code.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

load_clicked = False
repo_url = ""

if not st.session_state.overview:
    col_l, col_c, col_r = st.columns([1, 3, 1])
    with col_c:
        with st.form("load_repo_form", clear_on_submit=False):
            repo_url = st.text_input(
                "GitHub URL",
                placeholder="https://github.com/user/repo",
                label_visibility="collapsed",
            )
            load_clicked = st.form_submit_button("🚀 Analyze repo", type="primary", use_container_width=True)
else:
    top_l, top_r = st.columns([4, 1])
    with top_l:
        st.markdown(f'<span class="repo-badge">✓ Loaded</span>', unsafe_allow_html=True)
    with top_r:
        if st.button("🔄 Load another repo", use_container_width=True):
            st.session_state.collection = None
            st.session_state.chunks = None
            st.session_state.overview = None
            st.session_state.file_map = None
            st.session_state.messages = []
            st.session_state.repo_name = None
            st.rerun()

if load_clicked and repo_url:
    st.session_state.messages = []
    local_path = None
    try:
        with st.spinner("Cloning repo..."):
            local_path = clone_repo(repo_url)

        with st.spinner("Reading and chunking files..."):
            chunks = chunk_repo(local_path)
            if not chunks:
                st.error("No indexable code/doc files found in this repo.")
                st.stop()

        with st.spinner(f"Embedding {len(chunks)} chunks..."):
            collection = build_index(chunks)

        with st.spinner("Generating project overview..."):
            overview = generate_overview(local_path)

        with st.spinner("Building file map..."):
            file_map = generate_file_map(chunks)

        st.session_state.collection = collection
        st.session_state.chunks = chunks
        st.session_state.overview = overview
        st.session_state.file_map = file_map
        st.session_state.repo_name = repo_url.rstrip("/").split("/")[-1]

    except ValueError as e:
        st.error(str(e))
    except Exception as e:
        st.error(f"Something went wrong: {e}")
    finally:
        if local_path:
            cleanup_repo(local_path)

    st.rerun()

if st.session_state.overview:
    st.subheader(f"Overview — {st.session_state.repo_name}")
    st.write(st.session_state.overview)

    if st.session_state.file_map:
        with st.expander("📁 File map", expanded=False):
            for path, desc in st.session_state.file_map.items():
                st.markdown(f"**`{path}`**  \n{desc}")

    st.divider()

    st.subheader("💬 Ask about this repo")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg.get("sources"):
                st.caption("Sources: " + ", ".join(f"`{s}`" for s in msg["sources"]))

    question = st.chat_input("e.g. Where would I add a new API route?")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = answer_question(st.session_state.collection, question)
            st.write(result["answer"])
            if result["sources"]:
                st.caption("Sources: " + ", ".join(f"`{s}`" for s in result["sources"]))

        st.session_state.messages.append({
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
        })
