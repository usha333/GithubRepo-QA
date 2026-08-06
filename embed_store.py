from sentence_transformers import SentenceTransformer
import chromadb

_MODEL_NAME = "all-MiniLM-L6-v2"
_model = None  


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def build_index(chunks: list, collection_name: str = "repo_chunks"):
    """
    Embeds all chunks and stores them in an in-memory Chroma collection.
    Returns the collection, ready to be queried.
    """
    model = _get_model()

    
    client = chromadb.Client()

    
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    collection = client.create_collection(collection_name)

    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=False, batch_size=32).tolist()

    collection.add(
        ids=[c["chunk_id"] for c in chunks],
        embeddings=embeddings,
        documents=texts,
        metadatas=[{"filepath": c["filepath"]} for c in chunks],
    )
    return collection


def query_index(collection, question: str, top_k: int = 5):
    """
    Embeds the question and retrieves the top_k most relevant chunks.
    Returns a list of {"text": ..., "filepath": ...}.
    """
    model = _get_model()
    q_embedding = model.encode([question]).tolist()

    results = collection.query(query_embeddings=q_embedding, n_results=top_k)

    hits = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        hits.append({"text": doc, "filepath": meta["filepath"]})
    return hits
