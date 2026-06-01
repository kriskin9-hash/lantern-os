#!/usr/bin/env python3
"""BetterSafe Fridge Manager — Inventory tracking + expiration alerts (local only)"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger('BetterSafe.Fridge')


class FridgeManager:
    """Manage fridge inventory + track expiration."""

    def __init__(self, db):
        self.db = db
        logger.info("Fridge Manager initialized")

    def add_item(self, item_name, category, quantity, unit, expiration_date=None, notes=''):
        """Add an item to the fridge inventory."""
        data = {
            'item_name': item_name,
            'category': category,
            'quantity': quantity,
            'unit': unit,
            'expiration_date': expiration_date,
            'notes': notes
        }
        item_id = self.db.insert('fridge_inventory', data)
        logger.info(f"Added to fridge: {item_name} ({quantity} {unit})")
        return item_id

    def get_inventory(self):
        """Get current fridge contents."""
        return self.db.get_all('fridge_inventory')

    def flag_expiring(self, days_until=3):
        """Find items expiring in N days."""
        today = datetime.now().date()
        cutoff = today + timedelta(days=days_until)

        self.db.cursor.execute(
            'SELECT * FROM fridge_inventory WHERE expiration_date BETWEEN ? AND ?',
            (today, cutoff)
        )
        return self.db.cursor.fetchall()

    def remove_expired(self):
        """Remove items past expiration date."""
        today = datetime.now().date()
        self.db.cursor.execute(
            'DELETE FROM fridge_inventory WHERE expiration_date < ?',
            (today,)
        )
        self.db.log_event('fridge', 'auto_cleanup', status='ok', message=f"Removed expired items")
        logger.info("Removed expired items from inventory")

    def log_temperature(self, temp_fahrenheit):
        """Log current fridge temperature."""
        self.db.cursor.execute(
            'UPDATE fridge_inventory SET sensor_temperature = ? LIMIT 1',
            (temp_fahrenheit,)
        )
        self.db.log_event('fridge', 'temperature_logged', status='ok',
                         message=f"Temperature: {temp_fahrenheit}°F")

    def get_status(self):
        """Get fridge status."""
        inventory = self.get_inventory()
        expiring_soon = self.flag_expiring(days_until=3)
        return {
            'items_count': len(inventory),
            'expiring_soon': len(expiring_soon),
            'last_temperature': 38.0  # TODO: get from sensor
        }
