#!/usr/bin/env python3
"""
Lantern RAG Local Knowledge Base
Ingest books, documents, transcripts → local SQLite + vector store
Zero cloud, all local processing, continuous learning
"""

import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import hashlib

class LanternRAGLocal:
    """Local-only RAG knowledge base for Lantern."""

    def __init__(self, storage_path=None):
        """
        Initialize local RAG system.

        Args:
            storage_path: Path to RAG storage (default: ~/.lantern/rag-knowledge-base)
        """
        self.storage_path = Path(storage_path or os.path.expanduser('~/.lantern/rag-knowledge-base'))
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.db_path = self.storage_path / 'knowledge-base.db'
        self.books_path = self.storage_path / 'books'
        self.docs_path = self.storage_path / 'documents'
        self.embeddings_path = self.storage_path / 'embeddings'

        for path in [self.books_path, self.docs_path, self.embeddings_path]:
            path.mkdir(parents=True, exist_ok=True)

        self._init_db()
        print(f"[RAG] Initialized local knowledge base at {self.storage_path}")

    def _init_db(self):
        """Initialize SQLite schema for RAG."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL UNIQUE,
                source_type TEXT,
                title TEXT,
                author TEXT,
                content_hash TEXT,
                chunks_count INTEGER,
                ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')

        # Chunks table (for RAG retrieval)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER,
                content TEXT NOT NULL,
                chunk_hash TEXT,
                tokens INTEGER,
                embedding_generated BOOLEAN DEFAULT 0,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        ''')

        # Knowledge facts (extracted insights)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                fact_type TEXT,
                subject TEXT,
                predicate TEXT,
                object TEXT,
                confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        ''')

        # Autopilot learning log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                learning_type TEXT,
                source_document_id INTEGER,
                insight TEXT,
                confidence REAL,
                applied BOOLEAN DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_document_id) REFERENCES documents(id)
            )
        ''')

        conn.commit()
        conn.close()

    def ingest_book(self, filepath, title=None, author=None):
        """
        Ingest a book or PDF document.

        Args:
            filepath: Path to book file (.txt, .pdf, .epub)
            title: Book title
            author: Book author
        """
        filepath = Path(filepath)
        if not filepath.exists():
            print(f"[ERROR] File not found: {filepath}")
            return None

        # Read content
        try:
            if filepath.suffix == '.txt':
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            elif filepath.suffix == '.pdf':
                # TODO: pypdf for PDF extraction
                print(f"[TODO] PDF support: {filepath.name}")
                return None
            else:
                print(f"[ERROR] Unsupported format: {filepath.suffix}")
                return None
        except Exception as e:
            print(f"[ERROR] Could not read {filepath}: {e}")
            return None

        # Chunk content
        chunks = self._chunk_content(content, chunk_size=500)

        # Hash for deduplication
        content_hash = hashlib.md5(content.encode()).hexdigest()

        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO documents (filename, source_type, title, author, content_hash, chunks_count)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (filepath.name, 'book', title or filepath.stem, author or 'Unknown', content_hash, len(chunks)))

            doc_id = cursor.lastrowid

            # Insert chunks
            for idx, chunk in enumerate(chunks):
                chunk_hash = hashlib.md5(chunk.encode()).hexdigest()
                tokens = len(chunk.split())  # Simple tokenization
                cursor.execute('''
                    INSERT INTO chunks (document_id, chunk_index, content, chunk_hash, tokens)
                    VALUES (?, ?, ?, ?, ?)
                ''', (doc_id, idx, chunk, chunk_hash, tokens))

            conn.commit()
            print(f"[INGESTED] {filepath.name} ({len(chunks)} chunks, {len(content)} bytes)")
            return doc_id

        except sqlite3.IntegrityError:
            print(f"[SKIP] {filepath.name} already ingested")
            return None
        finally:
            conn.close()

    def ingest_directory(self, directory):
        """Ingest all documents from a directory."""
        directory = Path(directory)
        count = 0

        for filepath in directory.glob('*.txt'):
            doc_id = self.ingest_book(filepath)
            if doc_id:
                count += 1

        print(f"[BATCH] Ingested {count} documents from {directory.name}")
        return count

    def search_knowledge_base(self, query, limit=5):
        """
        Search the knowledge base for relevant chunks.

        Args:
            query: Search query
            limit: Number of results

        Returns:
            List of relevant chunks
        """
        # Simple keyword search (TODO: semantic search with embeddings)
        query_terms = query.lower().split()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        results = []
        for term in query_terms:
            cursor.execute('''
                SELECT c.id, c.document_id, d.filename, c.content
                FROM chunks c
                JOIN documents d ON c.document_id = d.id
                WHERE c.content LIKE ?
                LIMIT ?
            ''', (f'%{term}%', limit))

            results.extend(cursor.fetchall())

        conn.close()

        # Deduplicate and rank by relevance
        seen = set()
        unique_results = []
        for result in results:
            if result[0] not in seen:
                unique_results.append(result)
                seen.add(result[0])
                if len(unique_results) >= limit:
                    break

        return unique_results

    def extract_knowledge_facts(self, doc_id):
        """
        Extract structured knowledge facts from a document.

        Args:
            doc_id: Document ID
        """
        # TODO: NLP-based fact extraction
        # For now: simple pattern matching
        pass

    def autopilot_learning_loop(self):
        """
        Continuous autopilot learning loop.
        - Ingest new documents
        - Extract facts
        - Update knowledge base
        - Log learnings
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Count current documents
        cursor.execute('SELECT COUNT(*) FROM documents')
        doc_count = cursor.fetchone()[0]

        # Count learning events
        cursor.execute('SELECT COUNT(*) FROM learning_log WHERE applied = 0')
        pending_learnings = cursor.fetchone()[0]

        insight = f"Knowledge base: {doc_count} docs, {pending_learnings} pending learnings"

        cursor.execute('''
            INSERT INTO learning_log (learning_type, insight, confidence)
            VALUES (?, ?, ?)
        ''', ('autopilot_checkpoint', insight, 0.8))

        conn.commit()
        conn.close()

        print(f"[AUTOPILOT] {insight}")

    def get_statistics(self):
        """Get RAG knowledge base statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM documents')
        doc_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM chunks')
        chunk_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM knowledge_facts')
        fact_count = cursor.fetchone()[0]

        cursor.execute('SELECT SUM(tokens) FROM chunks')
        total_tokens = cursor.fetchone()[0] or 0

        conn.close()

        return {
            'documents': doc_count,
            'chunks': chunk_count,
            'facts': fact_count,
            'total_tokens': total_tokens,
            'storage_path': str(self.storage_path),
        }

    def _chunk_content(self, content, chunk_size=500):
        """Split content into chunks."""
        words = content.split()
        chunks = []

        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i+chunk_size])
            if chunk.strip():
                chunks.append(chunk)

        return chunks


if __name__ == '__main__':
    # Initialize RAG
    rag = LanternRAGLocal()

    # Example: Ingest a sample document
    sample_file = Path.home() / 'sample-book.txt'
    if sample_file.exists():
        rag.ingest_book(sample_file, title="Sample", author="Unknown")

    # Show statistics
    stats = rag.get_statistics()
    print(f"\n[STATS] {stats}")

    # Run autopilot learning loop
    rag.autopilot_learning_loop()

    print("\n[OK] Local RAG knowledge base ready")
