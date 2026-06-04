#!/usr/bin/env python3
"""BetterSafe Appliance Scheduler — Cycle management + energy tracking (local only)"""

import logging
from datetime import datetime

logger = logging.getLogger('BetterSafe.Appliances')


class ApplianceScheduler:
    """Manage connected appliances + track cycles."""

    def __init__(self, db):
        self.db = db
        logger.info("Appliance Scheduler initialized")

    def register_appliance(self, appliance_name):
        """Register a new appliance."""
        data = {
            'appliance_name': appliance_name,
            'current_state': 'idle',
            'energy_usage_kwh': 0.0
        }
        app_id = self.db.insert('appliance_status', data)
        logger.info(f"Registered appliance {app_id}: {appliance_name}")
        return app_id

    def start_cycle(self, appliance_id, cycle_type='normal', estimated_time_min=30):
        """Start an appliance cycle."""
        data = {
            'current_state': 'running',
            'cycle_type': cycle_type,
            'time_remaining_min': estimated_time_min
        }
        self.db.update('appliance_status', appliance_id, data)
        logger.info(f"Started {cycle_type} cycle on appliance {appliance_id}")

    def complete_cycle(self, appliance_id):
        """Mark a cycle as complete."""
        data = {
            'current_state': 'idle',
            'time_remaining_min': 0
        }
        self.db.update('appliance_status', appliance_id, data)
        logger.info(f"Cycle complete on appliance {appliance_id}")

    def get_status(self):
        """Get overall appliance status."""
        appliances = self.db.get_all('appliance_status')
        running = sum(1 for a in appliances if a[2] == 'running')  # current_state column
        return {
            'total_appliances': len(appliances),
            'running': running,
            'idle': len(appliances) - running
        }
