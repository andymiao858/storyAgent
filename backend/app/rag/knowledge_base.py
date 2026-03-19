"""RAG knowledge base management using FAISS + HuggingFace embeddings."""
import os
import json
from typing import List, Optional

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.core.config import settings

_vectorstore: Optional[FAISS] = None
_embeddings: Optional[HuggingFaceEmbeddings] = None


def get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL_NAME,
            model_kwargs={"device": "mps"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings


def _load_rag_documents() -> List[Document]:
    """Load all RAG seed documents from rag_data directory."""
    docs = []
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), settings.RAG_DATA_DIR)

    if not os.path.exists(base_dir):
        return docs

    for category_dir in os.listdir(base_dir):
        category_path = os.path.join(base_dir, category_dir)
        if not os.path.isdir(category_path):
            continue
        for filename in os.listdir(category_path):
            filepath = os.path.join(category_path, filename)
            if not filename.endswith(".json"):
                continue
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                for item in data:
                    doc = Document(
                        page_content=item.get("content", ""),
                        metadata={
                            "category": category_dir,
                            "age_group": item.get("age_group", ""),
                            "theme": item.get("theme", ""),
                            "scene_type": item.get("scene_type", ""),
                            "education_goal": item.get("education_goal", ""),
                            "style": item.get("style", ""),
                            "safety_level": item.get("safety_level", "safe"),
                            "source": filename,
                        },
                    )
                    docs.append(doc)
    return docs


def get_vectorstore() -> FAISS:
    """Get or create the FAISS vector store."""
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    embeddings = get_embeddings()
    index_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        settings.FAISS_INDEX_DIR,
    )

    if os.path.exists(index_dir):
        _vectorstore = FAISS.load_local(index_dir, embeddings, allow_dangerous_deserialization=True)
    else:
        docs = _load_rag_documents()
        if not docs:
            docs = [Document(page_content="儿童故事知识库初始化文档", metadata={"category": "init"})]
        _vectorstore = FAISS.from_documents(docs, embeddings)
        os.makedirs(index_dir, exist_ok=True)
        _vectorstore.save_local(index_dir)

    return _vectorstore


def search_knowledge(query: str, top_k: int = None, filter_metadata: dict = None) -> List[Document]:
    """Search the knowledge base with optional metadata filtering."""
    if top_k is None:
        top_k = settings.RAG_TOP_K
    vs = get_vectorstore()
    results = vs.similarity_search(query, k=top_k)

    if filter_metadata:
        filtered = []
        for doc in results:
            match = True
            for key, value in filter_metadata.items():
                if key in doc.metadata and doc.metadata[key] and doc.metadata[key] != value:
                    match = False
                    break
            if match:
                filtered.append(doc)
        return filtered if filtered else results

    return results


def rebuild_index():
    """Rebuild the FAISS index from rag_data."""
    global _vectorstore
    docs = _load_rag_documents()
    if not docs:
        docs = [Document(page_content="儿童故事知识库初始化文档", metadata={"category": "init"})]
    embeddings = get_embeddings()
    _vectorstore = FAISS.from_documents(docs, embeddings)
    index_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        settings.FAISS_INDEX_DIR,
    )
    os.makedirs(index_dir, exist_ok=True)
    _vectorstore.save_local(index_dir)
    return len(docs)
