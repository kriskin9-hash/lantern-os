#!/usr/bin/env python3
"""BetterSafe Safety Monitor — Sensor detection + threat analysis (local only)"""

import logging
from datetime import datetime

logger = logging.getLogger('BetterSafe.Safety')


class SafetyMonitor:
    """Monitor home sensors + detect threats locally."""

    def __init__(self, db):
        self.db = db
        logger.info("Safety Monitor initialized")

    def add_sensor(self, sensor_type, room, location, metadata=None):
        """Register a new sensor."""
        data = {
            'sensor_type': sensor_type,
            'room': room,
            'location': location,
            'status': True,
            'metadata': metadata or '{}'
        }
        sensor_id = self.db.insert('home_sensors', data)
        logger.info(f"Registered sensor {sensor_id}: {sensor_type} in {room}/{location}")
        return sensor_id

    def detect_motion(self, sensor_id, room):
        """Log motion detection."""
        sensor = self.db.get_by_id('home_sensors', sensor_id)
        if not sensor or sensor['sensor_type'] != 'motion':
            return False

        # Check threat pattern (motion in unusual place at unusual time)
        threat_score = self._calculate_threat_score(room)

        if threat_score > 0.7:
            self._log_event('motion_detected', 'high', f"Unusual motion in {room}", sensor_id)
            return True

        return False

    def detect_door_unlock(self, sensor_id, room):
        """Log unauthorized door unlock."""
        event_data = {
            'event_type': 'door_unlock',
            'severity': 'medium',
            'sensor_id': sensor_id,
            'description': f"Door unlocked in {room}",
            'resolved': False
        }
        self.db.insert('safety_events', event_data)
        logger.warning(f"Door unlock detected: {room}")

    def _calculate_threat_score(self, room):
        """Simple threat heuristic (0.0-1.0)."""
        # Placeholder: real implementation would check time, previous patterns, etc.
        return 0.3

    def _log_event(self, event_type, severity, description, sensor_id=None):
        """Log a safety event."""
        event_data = {
            'event_type': event_type,
            'severity': severity,
            'sensor_id': sensor_id,
            'description': description,
            'resolved': False
        }
        self.db.insert('safety_events', event_data)
        self.db.log_event('safety', event_type, status=severity, message=description)
        logger.info(f"Safety event logged: {event_type} ({severity})")

    def get_status(self):
        """Get current safety status."""
        sensors = self.db.get_all('home_sensors')
        armed_count = sum(1 for s in sensors if s[4])  # status column
        return {
            'total_sensors': len(sensors),
            'armed': armed_count,
            'disarmed': len(sensors) - armed_count,
            'recent_alerts': len(self.db.get_recent('safety_events', 5))
        }
