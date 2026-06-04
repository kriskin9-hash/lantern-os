#!/usr/bin/env python3
"""BetterSafe Household Tasks — Task tracking + reminders (local only)"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger('BetterSafe.Tasks')


class HouseholdTaskTracker:
    """Track household tasks + send reminders."""

    def __init__(self, db):
        self.db = db
        logger.info("Household Task Tracker initialized")

    def add_task(self, task_name, assigned_to, frequency='weekly', priority='medium', notes=''):
        """Add a household task."""
        next_due = self._calculate_next_due(frequency)
        data = {
            'task_name': task_name,
            'assigned_to': assigned_to,
            'frequency': frequency,
            'next_due': next_due,
            'priority': priority,
            'notes': notes,
            'completed': False
        }
        task_id = self.db.insert('household_tasks', data)
        logger.info(f"Added task {task_id}: {task_name} (assigned to {assigned_to})")
        return task_id

    def mark_complete(self, task_id):
        """Mark a task as complete."""
        data = {
            'completed': True,
            'completion_date': datetime.now()
        }
        self.db.update('household_tasks', task_id, data)

        # Reschedule if recurring
        task = self.db.get_by_id('household_tasks', task_id)
        if task and task[4] in ['daily', 'weekly', 'bi_weekly', 'monthly']:
            next_due = self._calculate_next_due(task[4])
            self.db.update('household_tasks', task_id, {'next_due': next_due, 'completed': False})

        logger.info(f"Completed task {task_id}")

    def get_due_today(self):
        """Get tasks due today."""
        today = datetime.now().date()
        self.db.cursor.execute(
            'SELECT * FROM household_tasks WHERE next_due <= ? AND completed = 0 ORDER BY priority DESC',
            (today,)
        )
        return self.db.cursor.fetchall()

    def get_all_tasks(self):
        """Get all tasks."""
        return self.db.get_all('household_tasks')

    def _calculate_next_due(self, frequency):
        """Calculate next due date based on frequency."""
        today = datetime.now().date()
        delta_map = {
            'daily': 1,
            'weekly': 7,
            'bi_weekly': 14,
            'monthly': 30
        }
        days = delta_map.get(frequency, 0)
        return today + timedelta(days=days)

    def get_status(self):
        """Get task tracking status."""
        all_tasks = self.get_all_tasks()
        due_today = self.get_due_today()
        completed = sum(1 for t in all_tasks if t[6])  # completed column
        return {
            'total_tasks': len(all_tasks),
            'due_today': len(due_today),
            'completed': completed,
            'pending': len(all_tasks) - completed
        }
