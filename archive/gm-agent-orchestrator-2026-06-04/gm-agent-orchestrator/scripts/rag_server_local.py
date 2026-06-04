#!/usr/bin/env python3
"""
Lantern RAG Server — Local Flask endpoint for knowledge base queries
Wraps the RAG knowledge base with a simple REST API for agent access
"""

import os
import sys
import logging
from pathlib import Path
from flask import Flask, request, jsonify
import json

# Add scripts dir to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from rag_local_knowledge_base import LanternRAGLocal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] RAG-SERVER: %(message)s'
)
logger = logging.getLogger('RAG-Server')

# Initialize Flask app
app = Flask(__name__)

# Initialize RAG system
rag = LanternRAGLocal()
logger.info("RAG knowledge base initialized")


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    stats = rag.get_statistics()
    return jsonify({
        'status': 'ok',
        'service': 'rag-knowledge-base',
        'statistics': stats
    })


@app.route('/search', methods=['POST'])
def search():
    """Search the knowledge base."""
    data = request.get_json()
    query = data.get('query', '')
    limit = data.get('limit', 5)
    
    if not query:
        return jsonify({'error': 'query required'}), 400
    
    results = rag.search_knowledge_base(query, limit=limit)
    return jsonify({
        'query': query,
        'results': [
            {
                'chunk_id': r[0],
                'document_id': r[1],
                'filename': r[2],
                'content': r[3]
            }
            for r in results
        ]
    })


@app.route('/ingest', methods=['POST'])
def ingest():
    """Ingest a document into the knowledge base."""
    data = request.get_json()
    filepath = data.get('filepath', '')
    title = data.get('title')
    author = data.get('author')
    
    if not filepath:
        return jsonify({'error': 'filepath required'}), 400
    
    doc_id = rag.ingest_book(filepath, title=title, author=author)
    if doc_id:
        return jsonify({
            'status': 'ingested',
            'doc_id': doc_id
        }), 201
    else:
        return jsonify({'error': 'ingest failed'}), 400


@app.route('/stats', methods=['GET'])
def stats():
    """Get knowledge base statistics."""
    return jsonify(rag.get_statistics())


@app.route('/learning-loop', methods=['POST'])
def learning_loop():
    """Trigger autopilot learning cycle."""
    rag.autopilot_learning_loop()
    return jsonify({
        'status': 'learning_cycle_completed',
        'statistics': rag.get_statistics()
    })


if __name__ == '__main__':
    logger.info("Starting RAG server on 0.0.0.0:8767")
    app.run(host='0.0.0.0', port=8767, debug=False)
