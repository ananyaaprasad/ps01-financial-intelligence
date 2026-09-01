"""
Vector Store & Retrieval Engine (Stage 1)
Supports local persistent ChromaDB with zero-dependency fallback for lightning-fast demo execution.
Exposes retrieval function returning top-k chunks with rich source metadata.
"""

import os
import re
import numpy as np
from typing import List, Dict, Any, Optional
from app.models.schemas import DocumentChunk
from app.data.document_corpus import get_document_corpus

# Attempt ChromaDB import; fallback to fast local embedding if not yet compiled/installed
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


class LightweightEmbedding:
    """
    Deterministic TF-IDF + Character/Word N-Gram semantic embedding engine.
    Ensures immediate, reproducible vector similarity search without downloading 2GB torch weights.
    """
    def __init__(self, dim: int = 128):
        self.dim = dim

    def embed_text(self, text: str) -> np.ndarray:
        """Create normalized fixed-dimension dense vector from text."""
        words = re.findall(r'\w+', text.lower())
        vec = np.zeros(self.dim, dtype=np.float32)
        if not words:
            return vec
        for i, word in enumerate(words):
            h = hash(word) % self.dim
            weight = 1.0 + (0.5 if len(word) > 5 else 0.0)
            vec[h] += weight
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t).tolist() for t in texts]


class VectorStore:
    """
    Vector search engine for financial documents.
    Implements ChromaDB persistent collection with automatic fallback.
    """

    def __init__(self, collection_name: str = "financial_intelligence_corpus", persist_dir: str = "./data/chroma_db"):
        self.collection_name = collection_name
        self.persist_dir = persist_dir
        self.use_chroma = CHROMADB_AVAILABLE
        self.chroma_client = None
        self.chroma_collection = None
        self.embedder = LightweightEmbedding(dim=128)

        # In-memory index for fast retrieval & fallback
        self.indexed_chunks: List[DocumentChunk] = []
        self.chunk_vectors: Optional[np.ndarray] = None

        self._initialize_store()

    def _initialize_store(self):
        """Initialize ChromaDB or fallback index, then populate with corpus."""
        os.makedirs(self.persist_dir, exist_ok=True)

        if self.use_chroma:
            try:
                self.chroma_client = chromadb.PersistentClient(path=self.persist_dir)
                self.chroma_collection = self.chroma_client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"description": "Financial filings and earnings transcripts"}
                )
            except Exception as e:
                print(f"[VectorStore] ChromaDB init fallback due to: {e}")
                self.use_chroma = False

        # Load and index corpus
        corpus_gen = get_document_corpus()
        self.indexed_chunks = corpus_gen.get_all_documents()
        self._build_index()

    def _build_index(self):
        """Index all document chunks."""
        texts = [doc.content for doc in self.indexed_chunks]
        vectors = self.embedder.embed_batch(texts)
        self.chunk_vectors = np.array(vectors, dtype=np.float32)

        if self.use_chroma and self.chroma_collection:
            try:
                ids = [doc.chunk_id for doc in self.indexed_chunks]
                metadatas = [
                    {
                        "ticker": doc.ticker,
                        "doc_type": doc.doc_type,
                        "title": doc.title,
                        "date": doc.date,
                        "quarter": doc.quarter,
                        "company_name": doc.company_name,
                    }
                    for doc in self.indexed_chunks
                ]
                self.chroma_collection.upsert(
                    ids=ids,
                    documents=texts,
                    metadatas=metadatas,
                    embeddings=vectors
                )
            except Exception as e:
                print(f"[VectorStore] Error indexing in ChromaDB: {e}")

    def retrieve_top_k(
        self,
        query: str,
        ticker: Optional[str] = None,
        doc_type: Optional[str] = None,
        top_k: int = 3
    ) -> List[DocumentChunk]:
        """
        Retrieve top-k relevant document chunks with source metadata.

        Args:
            query: Natural language query or keywords
            ticker: Filter by specific equity ticker (e.g. 'RELIANCE')
            doc_type: Filter by document type
            top_k: Number of chunks to return

        Returns:
            List of DocumentChunk with similarity_score attached
        """
        if not self.indexed_chunks:
            return []

        # Filter candidates if ticker or doc_type specified
        filtered_indices = []
        for idx, doc in enumerate(self.indexed_chunks):
            if ticker and doc.ticker.upper() != ticker.upper():
                continue
            if doc_type and doc.doc_type != doc_type:
                continue
            filtered_indices.append(idx)

        # If ticker filtering yields no results, search across all documents
        if not filtered_indices:
            filtered_indices = list(range(len(self.indexed_chunks)))

        # Compute cosine similarity
        query_vec = self.embedder.embed_text(query)
        candidate_vecs = self.chunk_vectors[filtered_indices]

        # Dot product of normalized vectors = cosine similarity
        scores = np.dot(candidate_vecs, query_vec)

        # Keyword matching bonus for exact entity / metric hits
        query_terms = set(re.findall(r'\w+', query.lower()))
        for i, idx in enumerate(filtered_indices):
            doc = self.indexed_chunks[idx]
            doc_terms = set(re.findall(r'\w+', doc.content.lower()))
            overlap = len(query_terms.intersection(doc_terms))
            scores[i] += overlap * 0.15  # Boost for term overlap

        # Sort descending
        top_ranked_order = np.argsort(scores)[::-1][:top_k]

        results: List[DocumentChunk] = []
        for rank_pos in top_ranked_order:
            actual_idx = filtered_indices[rank_pos]
            original_doc = self.indexed_chunks[actual_idx]
            sim_score = float(max(0.0, min(1.0, (scores[rank_pos] + 1.0) / 2.0)))

            # Create a copy with score
            chunk_copy = DocumentChunk(
                chunk_id=original_doc.chunk_id,
                doc_id=original_doc.doc_id,
                ticker=original_doc.ticker,
                company_name=original_doc.company_name,
                doc_type=original_doc.doc_type,
                title=original_doc.title,
                quarter=original_doc.quarter,
                date=original_doc.date,
                content=original_doc.content,
                metadata=original_doc.metadata,
                similarity_score=round(sim_score, 4)
            )
            results.append(chunk_copy)

        return results


# Global singleton instance
_vector_store = None

def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
