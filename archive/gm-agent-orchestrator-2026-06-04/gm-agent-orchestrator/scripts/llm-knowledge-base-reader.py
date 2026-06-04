#!/usr/bin/env python3
"""
Lantern LLM Knowledge Base Reader
Loads lantern-docs-database.jsonl and makes it available to local LLMs (Ollama, LM Studio)
Also serves as embeddings source for RAG (Retrieval-Augmented Generation)
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

KB_PATH = Path.home() / "lantern-docs-database.jsonl"


class LanternKnowledgeBase:
    """Local knowledge base for Lantern documentation"""

    def __init__(self, kb_path: Path = KB_PATH):
        self.kb_path = kb_path
        self.docs = []
        self.index = {}
        self.load()

    def load(self) -> None:
        """Load JSONL knowledge base"""
        if not self.kb_path.exists():
            print(f"Warning: Knowledge base not found at {self.kb_path}")
            return

        with open(self.kb_path) as f:
            for line in f:
                doc = json.loads(line)
                self.docs.append(doc)
                self.index[doc['doc_id']] = doc

        print(f"Loaded {len(self.docs)} documents from knowledge base")

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search knowledge base by keyword"""
        query_lower = query.lower()
        results = []

        for doc in self.docs:
            # Search in title, content, tags
            title_match = query_lower in doc.get('title', '').lower()
            content_match = query_lower in doc.get('content', '').lower()
            tags_match = any(query_lower in tag.lower() for tag in doc.get('tags', []))

            if title_match or content_match or tags_match:
                score = sum([title_match * 3, content_match * 1, tags_match * 2])
                results.append((score, doc))

        # Sort by relevance score
        results.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in results[:top_k]]

    def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        return self.index.get(doc_id)

    def get_by_type(self, doc_type: str) -> List[Dict[str, Any]]:
        """Get all documents of a type"""
        return [doc for doc in self.docs if doc['type'] == doc_type]

    def get_tutorial_sequence(self) -> List[Dict[str, Any]]:
        """Get tutorial steps in order"""
        tutorial_docs = self.get_by_type('tutorial')
        # Sort by step number in title
        tutorial_docs.sort(
            key=lambda x: int(x['title'].split(':')[0].split()[-1])
        )
        return tutorial_docs

    def export_for_local_llm(self, output_path: Path = None) -> str:
        """Export knowledge base in format suitable for Ollama/LM Studio RAG"""
        if output_path is None:
            output_path = Path.home() / ".lantern" / "kb-for-ollama.txt"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            f.write("# Lantern Knowledge Base\n\n")

            # Group by type
            types = set(doc['type'] for doc in self.docs)
            for doc_type in sorted(types):
                f.write(f"\n## {doc_type.upper()}\n\n")

                type_docs = self.get_by_type(doc_type)
                for doc in type_docs:
                    f.write(f"### {doc['title']}\n\n")
                    f.write(f"{doc['content']}\n\n")
                    f.write(f"**Tags:** {', '.join(doc.get('tags', []))}\n\n")
                    f.write("---\n\n")

        print(f"Exported knowledge base to: {output_path}")
        return str(output_path)

    def get_context_for_query(self, query: str, max_tokens: int = 2000) -> str:
        """Get knowledge base context for LLM prompt (for RAG)"""
        results = self.search(query, top_k=10)

        context = "# Lantern Knowledge Base Context\n\n"
        total_tokens = 0

        for doc in results:
            doc_text = f"## {doc['title']}\n\n{doc['content']}\n\n"
            doc_tokens = len(doc_text.split())

            if total_tokens + doc_tokens > max_tokens:
                break

            context += doc_text
            total_tokens += doc_tokens

        return context


def main():
    """Test knowledge base"""
    kb = LanternKnowledgeBase()

    print("\n=== Lantern Knowledge Base Test ===\n")

    # Test search
    print("Test 1: Search for 'Claude'")
    results = kb.search("Claude", top_k=3)
    for doc in results:
        print(f"  - {doc['title']}")

    # Test tutorial sequence
    print("\nTest 2: Tutorial Sequence")
    steps = kb.get_tutorial_sequence()
    for step in steps:
        print(f"  - {step['title']}")

    # Test export
    print("\nTest 3: Export for Local LLM")
    export_path = kb.export_for_local_llm()
    print(f"  Exported to: {export_path}")

    # Test RAG context
    print("\nTest 4: RAG Context for 'How do I set up Claude?'")
    context = kb.get_context_for_query("How do I set up Claude?", max_tokens=500)
    print(f"  Context length: {len(context)} chars")
    print(f"  First 200 chars:\n  {context[:200]}...")

    print("\n=== Knowledge Base Ready for Local LLMs ===")
    print(f"Total documents: {len(kb.docs)}")
    print(f"Document types: {', '.join(sorted(set(d['type'] for d in kb.docs)))}")


if __name__ == "__main__":
    main()
