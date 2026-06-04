#!/usr/bin/env python3
"""
Foundry CRDT Consensus Layer
Distributed synchronization of learning_log + knowledge_facts across operator network
Uses Last-Write-Wins (LWW) CRDT for conflict-free replicated data types
"""

import json
import hashlib
import sqlite3
import uuid
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import os


class FoundryCRDT:
    """CRDT-based consensus for distributed foundry synchronization."""

    def __init__(self, operator_id: str = None, db_path: str = None):
        """
        Initialize CRDT consensus.

        Args:
            operator_id: Unique ID for this operator (defaults to hostname)
            db_path: Path to RAG database
        """
        self.operator_id = operator_id or os.getenv('OPERATOR_ID', hashlib.md5(
            os.getenv('HOSTNAME', 'operator-0').encode()
        ).hexdigest()[:8])

        self.db_path = db_path or os.path.expanduser('~/.lantern/rag-knowledge-base/knowledge-base.db')
        self.state_path = Path.home() / '.lantern' / 'state'
        self.state_path.mkdir(parents=True, exist_ok=True)

        self.clock = 0  # Lamport clock for causal ordering
        self.peers = {}  # Known peer operators and their clock values
        self._init_crdt_tables()

    def _init_crdt_tables(self):
        """Initialize CRDT metadata tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # CRDT tombstone table for deletions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crdt_tombstones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_type TEXT,
                resource_id INTEGER,
                operator_id TEXT,
                timestamp REAL,
                lamport_clock INTEGER,
                UNIQUE(resource_type, resource_id, operator_id)
            )
        ''')

        # CRDT vector clock table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crdt_vector_clock (
                operator_id TEXT PRIMARY KEY,
                clock_value INTEGER,
                last_update TIMESTAMP
            )
        ''')

        # Insert self
        cursor.execute('''
            INSERT OR REPLACE INTO crdt_vector_clock (operator_id, clock_value, last_update)
            VALUES (?, ?, ?)
        ''', (self.operator_id, self.clock, datetime.now().isoformat()))

        conn.commit()
        conn.close()

    def increment_lamport_clock(self):
        """Increment Lamport clock for causal ordering."""
        self.clock += 1

    def merge_clock(self, peer_clock: int):
        """Merge Lamport clock from peer (max(local, peer) + 1)."""
        self.clock = max(self.clock, peer_clock) + 1

    def create_fact_replica(self, fact_id: int, fact_data: Dict[str, Any]) -> Dict:
        """
        Create a CRDT replica of a knowledge fact.

        Returns: Replica with metadata (operator_id, timestamp, lamport_clock)
        """
        self.increment_lamport_clock()

        replica = {
            'id': fact_id,
            'data': fact_data,
            'operator_id': self.operator_id,
            'timestamp': time.time(),
            'lamport_clock': self.clock,
            'replica_id': str(uuid.uuid4())
        }

        return replica

    def merge_replicas(self, local_replica: Dict, peer_replica: Dict) -> Dict:
        """
        Merge two replicas using Last-Write-Wins (LWW) CRDT strategy.

        Returns: Merged replica (winner determined by timestamp + operator_id tie-breaker)
        """
        local_time = local_replica.get('timestamp', 0)
        peer_time = peer_replica.get('timestamp', 0)

        if local_time > peer_time:
            return local_replica
        elif peer_time > local_time:
            return peer_replica
        else:
            # Tie-breaker: lexicographically compare operator IDs
            local_op = local_replica.get('operator_id', '')
            peer_op = peer_replica.get('operator_id', '')
            if local_op >= peer_op:
                return local_replica
            else:
                return peer_replica

    def tombstone_fact(self, fact_id: int, resource_type: str = 'knowledge_facts'):
        """Mark a fact as deleted (CRDT tombstone)."""
        self.increment_lamport_clock()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO crdt_tombstones (resource_type, resource_id, operator_id, timestamp, lamport_clock)
            VALUES (?, ?, ?, ?, ?)
        ''', (resource_type, fact_id, self.operator_id, time.time(), self.clock))

        conn.commit()
        conn.close()

    def is_tombstoned(self, fact_id: int, resource_type: str = 'knowledge_facts') -> bool:
        """Check if a fact has been tombstoned (deleted)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT COUNT(*) FROM crdt_tombstones
            WHERE resource_type = ? AND resource_id = ?
        ''', (resource_type, fact_id))

        count = cursor.fetchone()[0]
        conn.close()

        return count > 0

    def export_learning_log_for_sync(self) -> Dict:
        """Export learning log as CRDT replicas for peer synchronization."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT id, learning_type, insight, confidence FROM learning_log')
        logs = cursor.fetchall()

        replicas = []
        for log_id, learning_type, insight, confidence in logs:
            if not self.is_tombstoned(log_id, 'learning_log'):
                replica = self.create_fact_replica(log_id, {
                    'learning_type': learning_type,
                    'insight': insight,
                    'confidence': confidence
                })
                replicas.append(replica)

        conn.close()

        return {
            'operator_id': self.operator_id,
            'lamport_clock': self.clock,
            'replicas': replicas,
            'timestamp': datetime.now().isoformat()
        }

    def import_learning_log_from_peer(self, peer_export: Dict) -> int:
        """Import learning log replicas from a peer and merge conflicts."""
        peer_replicas = peer_export.get('replicas', [])
        merged_count = 0

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for peer_replica in peer_replicas:
            fact_id = peer_replica['id']

            # Get local replica if exists
            cursor.execute('''
                SELECT learning_type, insight, confidence
                FROM learning_log
                WHERE id = ?
            ''', (fact_id,))

            local_row = cursor.fetchone()

            if local_row:
                local_replica = {
                    'id': fact_id,
                    'data': {
                        'learning_type': local_row[0],
                        'insight': local_row[1],
                        'confidence': local_row[2]
                    },
                    'operator_id': self.operator_id,
                    'timestamp': 0  # Placeholder
                }

                # Merge using LWW
                winner = self.merge_replicas(local_replica, peer_replica)

                if winner == peer_replica:
                    # Update local with peer data
                    cursor.execute('''
                        UPDATE learning_log
                        SET learning_type = ?, insight = ?, confidence = ?
                        WHERE id = ?
                    ''', (
                        peer_replica['data']['learning_type'],
                        peer_replica['data']['insight'],
                        peer_replica['data']['confidence'],
                        fact_id
                    ))
                    merged_count += 1
            else:
                # Insert new replica from peer
                cursor.execute('''
                    INSERT INTO learning_log (learning_type, insight, confidence)
                    VALUES (?, ?, ?)
                ''', (
                    peer_replica['data']['learning_type'],
                    peer_replica['data']['insight'],
                    peer_replica['data']['confidence']
                ))
                merged_count += 1

        # Update peer clock
        self.merge_clock(peer_export.get('lamport_clock', 0))

        conn.commit()
        conn.close()

        return merged_count

    def get_sync_status(self) -> Dict:
        """Get status of CRDT synchronization."""
        return {
            'operator_id': self.operator_id,
            'lamport_clock': self.clock,
            'peers': self.peers,
            'timestamp': datetime.now().isoformat()
        }
