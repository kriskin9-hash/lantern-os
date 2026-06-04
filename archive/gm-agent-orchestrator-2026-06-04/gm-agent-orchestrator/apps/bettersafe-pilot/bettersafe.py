#!/usr/bin/env python3
"""
BetterSafe — Local-First Home Automation Hub
Part of Lantern Desktop (standalone or tabbed mode)
All processing local, all data encrypted, zero cloud dependency
"""

import tkinter as tk
from tkinter import ttk
import json
import os
import sqlite3
from pathlib import Path
from datetime import datetime
import logging
import sys

# Local imports
from bettersafe_db import BetterSafeDB
from modules.safety_monitor import SafetyMonitor
from modules.meal_coordinator import MealCoordinator
from modules.fridge_manager import FridgeManager
from modules.appliance_scheduler import ApplianceScheduler
from modules.social_services import SocialServicesEligibility
from modules.household_tasks import HouseholdTaskTracker

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser('~/.bettersafe/bettersafe.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('BetterSafe')


class BetterSafeApp:
    """
    BetterSafe Home Automation Hub
    6 modules: Safety, Meals, Fridge, Appliances, Social Services, Tasks
    """

    def __init__(self, parent_root=None, config_path=None):
        """
        Initialize BetterSafe.

        Args:
            parent_root: Parent tkinter window (if embedded in Lantern)
            config_path: Path to config.json (uses ~/.lantern/config.json by default)
        """
        self.config_path = config_path or os.path.expanduser('~/.lantern/config.json')
        self.config = self._load_config()
        self.db_path = os.path.expanduser('~/.bettersafe/bettersafe.db')

        # Ensure directories exist
        Path('~/.bettersafe/').expanduser().mkdir(parents=True, exist_ok=True)

        # Initialize database
        self.db = BetterSafeDB(self.db_path, password=self.config.get('bettersafe', {}).get('db_password'))
        self.db.init_schema()
        logger.info("Database initialized")

        # Initialize modules
        self.safety = SafetyMonitor(self.db)
        self.meals = MealCoordinator(self.db)
        self.fridge = FridgeManager(self.db)
        self.appliances = ApplianceScheduler(self.db)
        self.social_services = SocialServicesEligibility(self.db, self.config)
        self.tasks = HouseholdTaskTracker(self.db)

        # UI Setup
        if parent_root:
            # Embedded in Lantern as a tab
            self.root = None
            self.frame = ttk.Frame(parent_root)
            self._build_ui(self.frame)
        else:
            # Standalone window
            self.root = tk.Tk()
            self.root.title("BetterSafe — Home Automation Hub")
            self.root.geometry("1000x600")
            self._build_ui(self.root)

            # Bind close event
            self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _load_config(self):
        """Load config.json with BetterSafe section."""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                return config
        except FileNotFoundError:
            logger.warning(f"Config not found at {self.config_path}, using defaults")
            return {'bettersafe': {}}

    def _build_ui(self, parent):
        """Build tabbed interface with 6 modules."""
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: Safety Monitor
        safety_frame = ttk.Frame(self.notebook)
        self.notebook.add(safety_frame, text="🔒 Safety")
        self._build_safety_tab(safety_frame)

        # Tab 2: Meal Coordinator
        meal_frame = ttk.Frame(self.notebook)
        self.notebook.add(meal_frame, text="🍽️ Meals")
        self._build_meal_tab(meal_frame)

        # Tab 3: Fridge Manager
        fridge_frame = ttk.Frame(self.notebook)
        self.notebook.add(fridge_frame, text="❄️ Fridge")
        self._build_fridge_tab(fridge_frame)

        # Tab 4: Appliance Scheduler
        appliance_frame = ttk.Frame(self.notebook)
        self.notebook.add(appliance_frame, text="⚙️ Appliances")
        self._build_appliance_tab(appliance_frame)

        # Tab 5: Social Services
        services_frame = ttk.Frame(self.notebook)
        self.notebook.add(services_frame, text="🏛️ Services")
        self._build_services_tab(services_frame)

        # Tab 6: Household Tasks
        tasks_frame = ttk.Frame(self.notebook)
        self.notebook.add(tasks_frame, text="✅ Tasks")
        self._build_tasks_tab(tasks_frame)

        # Status bar
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = ttk.Label(status_frame, text="● Operational (BetterSafe initialized)")
        self.status_label.pack(side=tk.LEFT, padx=5, pady=2)

        logger.info("UI built successfully")

    def _build_safety_tab(self, parent):
        """Safety Monitor: Sensor status + threat detection."""
        frame = ttk.LabelFrame(parent, text="Home Safety")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Placeholder UI
        ttk.Label(frame, text="Sensors Status:", font=('Helvetica', 12, 'bold')).pack(anchor=tk.W)

        # Sensor list
        sensor_data = self.db.get_all('home_sensors')
        for sensor in sensor_data:
            status = "🟢 Armed" if sensor[4] else "🔴 Disarmed"
            ttk.Label(frame, text=f"  {sensor[3]} - {sensor[2]}: {status}").pack(anchor=tk.W)

        if not sensor_data:
            ttk.Label(frame, text="  (No sensors configured)").pack(anchor=tk.W)

        # Alert history
        ttk.Label(frame, text="Recent Alerts:", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(10, 0))
        alerts = self.db.get_recent('safety_events', 5)
        for alert in alerts:
            ttk.Label(frame, text=f"  {alert[2]}: {alert[8]}").pack(anchor=tk.W)

        if not alerts:
            ttk.Label(frame, text="  (No recent alerts)").pack(anchor=tk.W)

    def _build_meal_tab(self, parent):
        """Meal Coordinator: Recipe matching + shopping list."""
        frame = ttk.LabelFrame(parent, text="Meal Planning")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(frame, text="Today's Meal:", font=('Helvetica', 12, 'bold')).pack(anchor=tk.W)

        # Placeholder
        ttk.Label(frame, text="Select a date to view meal plans").pack(anchor=tk.W)

        # Date picker
        ttk.Button(frame, text="View Meal Plans").pack(pady=10)

    def _build_fridge_tab(self, parent):
        """Fridge Manager: Inventory + expiration tracking."""
        frame = ttk.LabelFrame(parent, text="Fridge Inventory")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(frame, text="Current Inventory:", font=('Helvetica', 12, 'bold')).pack(anchor=tk.W)

        # Inventory list
        inventory = self.db.get_all('fridge_inventory')
        for item in inventory:
            ttk.Label(frame, text=f"  {item[1]}: {item[4]} {item[5]}").pack(anchor=tk.W)

        if not inventory:
            ttk.Label(frame, text="  (Fridge is empty)").pack(anchor=tk.W)

        # Temperature status
        ttk.Label(frame, text="Temperature:", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=(10, 0))
        ttk.Label(frame, text="  38°F (optimal)").pack(anchor=tk.W)

    def _build_appliance_tab(self, parent):
        """Appliance Scheduler: Cycle status + energy usage."""
        frame = ttk.LabelFrame(parent, text="Appliance Status")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(frame, text="Connected Appliances:", font=('Helvetica', 12, 'bold')).pack(anchor=tk.W)

        # Appliance list
        appliances = self.db.get_all('appliance_status')
        for app in appliances:
            state = "Idle" if app[3] == 'idle' else app[3].title()
            ttk.Label(frame, text=f"  {app[1]}: {state}").pack(anchor=tk.W)

        if not appliances:
            ttk.Label(frame, text="  (No appliances connected)").pack(anchor=tk.W)

    def _build_services_tab(self, parent):
        """Social Services: Eligibility matching."""
        frame = ttk.LabelFrame(parent, text="Social Services Eligibility")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(frame, text="Find Services for Your Situation", font=('Helvetica', 12, 'bold')).pack(anchor=tk.W)

        # Input fields
        ttk.Label(frame, text="Age:").pack(anchor=tk.W)
        ttk.Entry(frame, width=30).pack(anchor=tk.W)

        ttk.Label(frame, text="Annual Income:").pack(anchor=tk.W)
        ttk.Entry(frame, width=30).pack(anchor=tk.W)

        ttk.Label(frame, text="Location:").pack(anchor=tk.W)
        ttk.Combobox(frame, values=["Waynesville", "Spring Valley"]).pack(anchor=tk.W)

        # Search button
        ttk.Button(frame, text="Find Eligible Services").pack(pady=10)

    def _build_tasks_tab(self, parent):
        """Household Tasks: Task list + reminders."""
        frame = ttk.LabelFrame(parent, text="Household Tasks")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(frame, text="Today's Tasks:", font=('Helvetica', 12, 'bold')).pack(anchor=tk.W)

        # Task list
        tasks = self.db.get_recent('household_tasks', 10)
        for task in tasks:
            status = "✓" if task[6] else "○"
            ttk.Label(frame, text=f"  {status} {task[1]}").pack(anchor=tk.W)

        if not tasks:
            ttk.Label(frame, text="  (No tasks scheduled)").pack(anchor=tk.W)

        # Add task button
        ttk.Button(frame, text="Add Task").pack(pady=10)

    def on_close(self):
        """Cleanup on window close."""
        logger.info("BetterSafe closing...")
        self.db.close()
        if self.root:
            self.root.destroy()
        logger.info("BetterSafe closed")

    def run(self):
        """Start the app (standalone mode)."""
        if self.root:
            self.root.mainloop()


if __name__ == '__main__':
    logger.info("Starting BetterSafe...")
    app = BetterSafeApp()
    app.run()
