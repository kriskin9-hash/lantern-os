#!/usr/bin/env python3
"""
Node Adoption Tracker
Tracks how many nodes are running and reporting in
Syncs with central server for global adoption visibility
"""

import json
import sqlite3
from datetime import datetime, timedelta
import os
import requests
import threading

DB_PATH = "./data/adoption.db"
CENTRAL_SERVER = os.environ.get('CENTRAL_SERVER', 'https://human-flourishing-frameworks.onrender.com')
SYNC_ENABLED = os.environ.get('ENABLE_ADOPTION_SYNC', '').lower() in {
    '1', 'true', 'yes', 'on'
}
ADOPTION_SYNC_TOKEN = os.environ.get(
    'HFF_ADOPTION_SYNC_TOKEN',
    os.environ.get('HFF_WRITE_TOKEN', '')
)


def _write_headers():
    """Return central adoption-grant headers when a token is configured."""
    if not ADOPTION_SYNC_TOKEN:
        return {}
    return {'Authorization': f'Bearer {ADOPTION_SYNC_TOKEN}'}

def init_adoption_db():
    """Initialize adoption tracking database"""
    os.makedirs("./data", exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create nodes table
    c.execute('''
        CREATE TABLE IF NOT EXISTS nodes (
            id INTEGER PRIMARY KEY,
            node_id TEXT UNIQUE,
            node_name TEXT,
            platform TEXT,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            version TEXT,
            region TEXT,
            operator_type TEXT,
            deployment_type TEXT,
            node_public_key TEXT,
            verified INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active'
        )
    ''')

    for column, definition in {
        "region": "TEXT",
        "operator_type": "TEXT",
        "deployment_type": "TEXT",
        "node_public_key": "TEXT",
        "verified": "INTEGER DEFAULT 0",
    }.items():
        try:
            c.execute(f"ALTER TABLE nodes ADD COLUMN {column} {definition}")
        except sqlite3.OperationalError:
            pass
    
    # Create adoption history (daily snapshots)
    c.execute('''
        CREATE TABLE IF NOT EXISTS adoption_history (
            id INTEGER PRIMARY KEY,
            date DATE UNIQUE,
            node_count INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def sync_to_central_server(
    node_id, node_name, platform, version="1.0.0",
    region="", operator_type="", deployment_type="", node_public_key=""
):
    """Send node registration to central server"""
    if not SYNC_ENABLED or CENTRAL_SERVER.startswith('http://localhost'):
        return

    try:
        response = requests.post(
            f'{CENTRAL_SERVER}/api/adoption/register',
            headers=_write_headers(),
            json={
                'node_id': node_id,
                'node_name': node_name,
                'platform': platform,
                'version': version,
                'region': region,
                'operator_type': operator_type,
                'deployment_type': deployment_type,
                'node_public_key': node_public_key
            },
            timeout=5
        )
        if response.status_code == 200:
            return True
    except Exception as e:
        pass
    return False

def register_node(
    node_id, node_name, platform, version="1.0.0",
    region="", operator_type="", deployment_type="", node_public_key=""
):
    """Register a new node or update existing (locally and on central server)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        c.execute('''
            INSERT INTO nodes
            (node_id, node_name, platform, version, region, operator_type,
             deployment_type, node_public_key, verified, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP)
        ''', (node_id, node_name, platform, version, region, operator_type,
              deployment_type, node_public_key))
    except sqlite3.IntegrityError:
        # Node exists, update last_seen
        c.execute('''
            UPDATE nodes
            SET last_seen = CURRENT_TIMESTAMP,
                status = 'active',
                node_name = ?,
                platform = ?,
                version = ?,
                region = ?,
                operator_type = ?,
                deployment_type = ?,
                node_public_key = ?
            WHERE node_id = ?
        ''', (node_name, platform, version, region, operator_type,
              deployment_type, node_public_key, node_id))

    conn.commit()
    conn.close()

    # Sync to central server in background
    if SYNC_ENABLED and not CENTRAL_SERVER.startswith('http://localhost'):
        thread = threading.Thread(
            target=sync_to_central_server,
            args=(node_id, node_name, platform, version, region, operator_type,
                  deployment_type, node_public_key),
            daemon=True
        )
        thread.start()

def get_active_nodes(minutes=30):
    """Get count of nodes active in last N minutes"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
    
    c.execute('''
        SELECT COUNT(*) FROM nodes 
        WHERE last_seen > ?
    ''', (cutoff_time.isoformat(),))
    
    count = c.fetchone()[0]
    conn.close()
    
    return count

def get_total_nodes():
    """Get total count of all nodes ever registered"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM nodes')
    count = c.fetchone()[0]
    conn.close()
    
    return count

def get_verified_node_count(minutes=None):
    """Get count of admitted verified nodes, optionally active in the last N minutes."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if minutes is None:
        c.execute("SELECT COUNT(*) FROM nodes WHERE verified = 1")
    else:
        c.execute('''
            SELECT COUNT(*) FROM nodes
            WHERE verified = 1 AND last_seen > datetime('now', ?)
        ''', (f'-{int(minutes)} minutes',))

    count = c.fetchone()[0]
    conn.close()
    return count

def get_adoption_stats():
    """Get comprehensive adoption statistics"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Total nodes
    c.execute('SELECT COUNT(*) FROM nodes')
    total = c.fetchone()[0]
    
    # Active in last hour
    c.execute('''
        SELECT COUNT(*) FROM nodes 
        WHERE last_seen > datetime('now', '-1 hour')
    ''')
    active_1h = c.fetchone()[0]
    
    # Active in last 24 hours
    c.execute('''
        SELECT COUNT(*) FROM nodes 
        WHERE last_seen > datetime('now', '-24 hours')
    ''')
    active_24h = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM nodes WHERE verified = 1")
    verified_total = c.fetchone()[0]

    c.execute('''
        SELECT COUNT(*) FROM nodes
        WHERE verified = 1 AND last_seen > datetime('now', '-1 hour')
    ''')
    verified_active_1h = c.fetchone()[0]
    
    # By platform
    c.execute('''
        SELECT platform, COUNT(*) as count 
        FROM nodes 
        GROUP BY platform
        ORDER BY count DESC
    ''')
    by_platform = {row[0]: row[1] for row in c.fetchall()}

    c.execute('''
        SELECT COALESCE(NULLIF(region, ''), 'unspecified'), COUNT(*) as count
        FROM nodes
        GROUP BY COALESCE(NULLIF(region, ''), 'unspecified')
        ORDER BY count DESC
    ''')
    by_region = {row[0]: row[1] for row in c.fetchall()}
    
    # Recent nodes (last 7 days)
    c.execute('''
        SELECT COUNT(*) FROM nodes 
        WHERE first_seen > datetime('now', '-7 days')
    ''')
    last_7d = c.fetchone()[0]
    
    conn.close()
    
    return {
        "total_nodes": total,
        "active_last_hour": active_1h,
        "active_last_24h": active_24h,
        "verified_nodes": verified_total,
        "verified_active_last_hour": verified_active_1h,
        "security_node_count": verified_active_1h,
        "last_7_days": last_7d,
        "by_platform": by_platform,
        "by_region": by_region,
        "verification": "self_reported_visible_nodes_verified_nodes_count_for_security",
        "timestamp": datetime.utcnow().isoformat()
    }

def get_nodes_list(limit=50):
    """Get list of recent nodes"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        SELECT node_name, platform, first_seen, last_seen, status, region,
               operator_type, deployment_type, node_public_key, verified
        FROM nodes
        ORDER BY last_seen DESC
        LIMIT ?
    ''', (limit,))
    
    nodes = [
        {
            "name": row[0],
            "platform": row[1],
            "first_seen": row[2],
            "last_seen": row[3],
            "status": row[4],
            "region": row[5] or "",
            "operator_type": row[6] or "",
            "deployment_type": row[7] or "",
            "node_public_key": row[8] or "",
            "verified": bool(row[9])
        }
        for row in c.fetchall()
    ]
    
    conn.close()
    return nodes

def start_heartbeat(
    node_id, node_name, platform, interval=60,
    region="", operator_type="", deployment_type="", node_public_key=""
):
    """Periodically ping central server to keep node visible"""
    def heartbeat_loop():
        while SYNC_ENABLED:
            try:
                requests.post(
                    f'{CENTRAL_SERVER}/api/adoption/register',
                    headers=_write_headers(),
                    json={
                        'node_id': node_id,
                        'node_name': node_name,
                        'platform': platform,
                        'version': '1.0.0',
                        'region': region,
                        'operator_type': operator_type,
                        'deployment_type': deployment_type,
                        'node_public_key': node_public_key
                    },
                    timeout=3
                )
            except:
                pass

            import time
            time.sleep(interval)

    if SYNC_ENABLED and not CENTRAL_SERVER.startswith('http://localhost'):
        thread = threading.Thread(target=heartbeat_loop, daemon=True)
        thread.start()

if __name__ == "__main__":
    init_adoption_db()
    print("Adoption tracker initialized")
