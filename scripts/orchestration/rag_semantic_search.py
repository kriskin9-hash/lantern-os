#!/usr/bin/env python3
"""
Semantic Search Module for RAG Knowledge Base
Replaces keyword-only search with vector similarity matching
Uses all-MiniLM-l6-v2 embeddings (22MB, fast, local-only)
"""

import sqlite3
import numpy as np
from pathlib import Path
from typing import List, Tuple
import json
import os

# Try importing sentence_transformers; fall back to keyword search if unavailable
try:
    from sentence_transformers import SentenceTransformer
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    print("[WARNING] sentence-transformers not installed; falling back to keyword search")


class SemanticRAG:
    """Semantic search layer for RAG knowledge base."""

    def __init__(self, storage_path=None, model_name="all-MiniLM-L6-v2"):
        """
        Initialize semantic search.
        
        Args:
            storage_path: Path to RAG storage (default: ~/.lantern/rag-knowledge-base)
            model_name: HuggingFace model ID for embeddings
        """
        self.storage_path = Path(storage_path or os.path.expanduser('~/.lantern/rag-knowledge-base'))
        self.db_path = self.storage_path / 'knowledge-base.db'
        self.embeddings_path = self.storage_path / 'embeddings'
        self.embeddings_path.mkdir(parents=True, exist_ok=True)
        
        self.model = None
        self.model_name = model_name
        self.embeddings_cache = {}
        
        if SEMANTIC_AVAILABLE:
            try:
                print(f"[SEMANTIC] Loading {model_name} (22MB)...")
                self.model = SentenceTransformer(model_name)
                print("[SEMANTIC] Model loaded successfully")
            except Exception as e:
                print(f"[WARNING] Could not load model: {e}")
                self.model = None
        
        self._load_embeddings_cache()

    def _load_embeddings_cache(self):
        """Load cached embeddings from disk."""
        cache_file = self.embeddings_path / 'embeddings_cache.json'
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    self.embeddings_cache = json.load(f)
                print(f"[SEMANTIC] Loaded {len(self.embeddings_cache)} cached embeddings")
            except Exception as e:
                print(f"[WARNING] Could not load embeddings cache: {e}")

    def _save_embeddings_cache(self):
        """Save embeddings cache to disk."""
        cache_file = self.embeddings_path / 'embeddings_cache.json'
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.embeddings_cache, f)
        except Exception as e:
            print(f"[WARNING] Could not save embeddings cache: {e}")

    def embed_chunk(self, chunk_id: int, content: str) -> np.ndarray:
        """Embed a chunk and cache it."""
        if not self.model:
            return None
        
        chunk_id_str = str(chunk_id)
        
        # Check cache
        if chunk_id_str in self.embeddings_cache:
            return np.array(self.embeddings_cache[chunk_id_str])
        
        # Generate embedding
        try:
            embedding = self.model.encode(content, convert_to_numpy=True)
            self.embeddings_cache[chunk_id_str] = embedding.tolist()
            return embedding
        except Exception as e:
            print(f"[ERROR] Could not embed chunk {chunk_id}: {e}")
            return None

    def semantic_search(self, query: str, limit: int = 5) -> List[Tuple]:
        """
        Semantic search using vector similarity.
        
        Args:
            query: Search query (natural language)
            limit: Number of results
        
        Returns:
            List of (chunk_id, document_id, filename, content, similarity_score)
        """
        if not self.model:
            print("[WARNING] Semantic search unavailable; use keyword search instead")
            return []
        
        try:
            # Embed query
            query_embedding = self.model.encode(query, convert_to_numpy=True)
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Fetch all chunks and their IDs
            cursor.execute('''
                SELECT c.id, c.document_id, d.filename, c.content
                FROM chunks c
                JOIN documents d ON c.document_id = d.id
            ''')
            
            results = []
            for chunk_id, doc_id, filename, content in cursor.fetchall():
                # Embed chunk
                chunk_embedding = self.embed_chunk(chunk_id, content)
                if chunk_embedding is None:
                    continue
                
                # Compute cosine similarity
                similarity = self._cosine_similarity(query_embedding, chunk_embedding)
                results.append((chunk_id, doc_id, filename, content, similarity))
            
            conn.close()
            
            # Sort by similarity and return top-k
            results.sort(key=lambda x: x[4], reverse=True)
            return results[:limit]
        
        except Exception as e:
            print(f"[ERROR] Semantic search failed: {e}")
            return []

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return np.dot(a, b) / (norm_a * norm_b)

    def batch_embed_documents(self):
        """Embed all documents in the knowledge base."""
        if not self.model:
            print("[ERROR] Model not loaded; cannot batch embed")
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all chunks
        cursor.execute('SELECT id, content FROM chunks WHERE embedding_generated = 0')
        chunks = cursor.fetchall()
        
        embedded_count = 0
        for chunk_id, content in chunks:
            embedding = self.embed_chunk(chunk_id, content)
            if embedding is not None:
                # Mark as embedded
                cursor.execute('UPDATE chunks SET embedding_generated = 1 WHERE id = ?', (chunk_id,))
                embedded_count += 1
        
        conn.commit()
        conn.close()
        
        self._save_embeddings_cache()
        print(f"[SEMANTIC] Embedded {embedded_count} chunks")


if __name__ == '__main__':
    rag = SemanticRAG()
    
    # Example search
    if rag.model:
        results = rag.semantic_search("What is the fastest way to learn?", limit=3)
        for chunk_id, doc_id, filename, content, score in results:
            print(f"\n[Score: {score:.3f}] {filename}")
            print(f"  {content[:200]}...")
    else:
        print("[INFO] Semantic search not available; install sentence-transformers")
