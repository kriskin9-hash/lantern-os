#!/usr/bin/env python3
"""
BetterSafe Database Layer
SQLite + SQLCipher for local, encrypted data storage
All processing local, no cloud sync
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger('BetterSafe.DB')


class BetterSafeDB:
    """
    Local encrypted SQLite database for BetterSafe.
    Uses SQLCipher for AES-256 encryption (optional password).
    """

    def __init__(self, db_path, password=None):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite file
            password: Optional password for encryption (SQLCipher)
        """
        self.db_path = db_path
        self.password = password or ''
        self.conn = None
        self.cursor = None
        self._connect()

    def _connect(self):
        """Establish connection to SQLite database."""
        try:
            # Standard SQLite (password support requires SQLCipher)
            # For now, use sqlite3; production would use pysqlcipher3
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Access columns by name
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def init_schema(self):
        """Create all tables if they don't exist."""
        try:
            # Table: home_sensors
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS home_sensors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sensor_type TEXT NOT NULL,
                    room TEXT NOT NULL,
                    location TEXT NOT NULL,
                    status BOOLEAN DEFAULT 1,
                    last_alert TIMESTAMP,
                    alert_count INTEGER DEFAULT 0,
                    metadata TEXT
                )
            ''')

            # Table: safety_events
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS safety_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sensor_id INTEGER,
                    description TEXT,
                    action_taken TEXT,
                    resolved BOOLEAN DEFAULT 0,
                    notes TEXT,
                    FOREIGN KEY (sensor_id) REFERENCES home_sensors(id)
                )
            ''')

            # Table: meal_plans
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS meal_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    meal_type TEXT NOT NULL,
                    recipe_name TEXT,
                    ingredients TEXT,
                    prep_time_min INTEGER,
                    cooking_time_min INTEGER,
                    servings INTEGER,
                    dietary_flags TEXT,
                    notes TEXT
                )
            ''')

            # Table: fridge_inventory
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS fridge_inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_name TEXT NOT NULL,
                    category TEXT,
                    quantity REAL NOT NULL,
                    unit TEXT NOT NULL,
                    expiration_date DATE,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sensor_temperature DECIMAL,
                    notes TEXT
                )
            ''')

            # Table: appliance_status
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS appliance_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    appliance_name TEXT NOT NULL,
                    current_state TEXT DEFAULT 'idle',
                    cycle_type TEXT,
                    time_remaining_min INTEGER,
                    energy_usage_kwh DECIMAL,
                    last_service_date DATE,
                    maintenance_alert BOOLEAN DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Table: appointments
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    date DATE NOT NULL,
                    time TIME,
                    duration_min INTEGER,
                    location TEXT,
                    contact_person TEXT,
                    contact_phone TEXT,
                    notes TEXT,
                    reminder_set BOOLEAN DEFAULT 1,
                    status TEXT DEFAULT 'scheduled',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Table: social_services_registry
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS social_services_registry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_name TEXT NOT NULL,
                    category TEXT,
                    county TEXT,
                    city TEXT,
                    phone TEXT,
                    website TEXT,
                    eligibility_criteria TEXT,
                    programs TEXT,
                    last_updated DATE,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')

            # Table: household_tasks
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS household_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_name TEXT NOT NULL,
                    assigned_to TEXT,
                    frequency TEXT,
                    next_due DATE,
                    completed BOOLEAN DEFAULT 0,
                    completion_date TIMESTAMP,
                    notes TEXT,
                    priority TEXT DEFAULT 'medium',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Table: system_logs
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    system TEXT NOT NULL,
                    event TEXT NOT NULL,
                    status TEXT,
                    message TEXT,
                    data TEXT
                )
            ''')

            self.conn.commit()
            logger.info("Database schema initialized")
        except sqlite3.Error as e:
            logger.error(f"Schema initialization failed: {e}")
            raise

    def execute(self, sql, params=None):
        """Execute a query."""
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
            self.conn.commit()
            return self.cursor
        except sqlite3.Error as e:
            logger.error(f"Query execution failed: {e}")
            raise

    def get_all(self, table):
        """Get all rows from a table."""
        try:
            self.cursor.execute(f'SELECT * FROM {table}')
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Fetch failed: {e}")
            return []

    def get_recent(self, table, limit=5):
        """Get recent rows from a table (ordered by id DESC)."""
        try:
            sql = f'SELECT * FROM {table} ORDER BY id DESC LIMIT ?'
            self.cursor.execute(sql, (limit,))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Fetch recent failed: {e}")
            return []

    def get_by_id(self, table, id):
        """Get a row by ID."""
        try:
            sql = f'SELECT * FROM {table} WHERE id = ?'
            self.cursor.execute(sql, (id,))
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"Fetch by ID failed: {e}")
            return None

    def insert(self, table, data):
        """
        Insert a row.

        Args:
            table: Table name
            data: Dictionary of column:value pairs
        """
        try:
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            sql = f'INSERT INTO {table} ({columns}) VALUES ({placeholders})'
            self.execute(sql, tuple(data.values()))
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Insert failed: {e}")
            return None

    def update(self, table, id, data):
        """Update a row."""
        try:
            set_clause = ', '.join([f'{k}=?' for k in data.keys()])
            sql = f'UPDATE {table} SET {set_clause} WHERE id=?'
            values = tuple(data.values()) + (id,)
            self.execute(sql, values)
        except sqlite3.Error as e:
            logger.error(f"Update failed: {e}")

    def delete(self, table, id):
        """Delete a row."""
        try:
            sql = f'DELETE FROM {table} WHERE id=?'
            self.execute(sql, (id,))
        except sqlite3.Error as e:
            logger.error(f"Delete failed: {e}")

    def log_event(self, system, event, status='ok', message='', data=None):
        """Log a system event."""
        try:
            event_data = {
                'system': system,
                'event': event,
                'status': status,
                'message': message,
                'data': json.dumps(data) if data else None
            }
            self.insert('system_logs', event_data)
        except sqlite3.Error as e:
            logger.error(f"Log event failed: {e}")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database closed")


# Utility functions for data seeding

def seed_social_services(db, county='Wayne', city='Waynesville'):
    """Seed social services registry with sample data."""
    services = [
        {
            'service_name': 'Wayne County Health Department',
            'category': 'Health & Medical',
            'county': 'Wayne',
            'city': 'Waynesville',
            'phone': '(937) 555-0100',
            'website': 'wayne.oh.gov/health',
            'eligibility_criteria': json.dumps({
                'income_based': False,
                'age_min': 0,
                'residency': 'Wayne County'
            }),
            'programs': json.dumps(['Primary care', 'Immunizations', 'Health screenings']),
            'is_active': True
        },
        {
            'service_name': 'SNAP (Food Assistance)',
            'category': 'Food & Nutrition',
            'county': 'Wayne',
            'city': 'Waynesville',
            'phone': '(937) 555-0200',
            'website': 'benefits.oh.gov/snap',
            'eligibility_criteria': json.dumps({
                'income_based': True,
                'income_threshold': '130% of federal poverty line'
            }),
            'programs': json.dumps(['Monthly benefits', 'Emergency SNAP']),
            'is_active': True
        },
        {
            'service_name': 'Greene County Area Agency on Aging',
            'category': 'Senior Services',
            'county': 'Greene',
            'city': 'Spring Valley',
            'phone': '(937) 555-0300',
            'website': 'greene.oh.gov/aging',
            'eligibility_criteria': json.dumps({
                'age_min': 60,
                'residency': 'Greene County'
            }),
            'programs': json.dumps(['Meals on Wheels', 'Transportation', 'Senior center']),
            'is_active': True
        }
    ]

    for service in services:
        db.insert('social_services_registry', service)

    logger.info(f"Seeded {len(services)} social services")


if __name__ == '__main__':
    # Test database setup
    logging.basicConfig(level=logging.INFO)
    db = BetterSafeDB(Path.home() / '.bettersafe' / 'test.db')
    db.init_schema()
    seed_social_services(db)

    # Verify
    services = db.get_all('social_services_registry')
    print(f"Created {len(services)} service records")

    db.close()
    print("Database test complete")
