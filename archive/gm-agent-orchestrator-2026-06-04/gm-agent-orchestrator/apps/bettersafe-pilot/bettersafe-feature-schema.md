# BetterSafe Feature Schema — Local-First Data Model

**Version:** 0.1 | **Date:** 2026-05-25 | **Storage:** SQLite (local, encrypted)

---

## Database Schema (SQLite)

### Table: `home_sensors`
```
id (INTEGER PRIMARY KEY)
sensor_type (TEXT) — motion, temperature, door_open, camera_detect
room (TEXT) — bedroom, kitchen, bathroom, living_room, etc
status (BOOLEAN) — armed/disarmed
last_alert (TIMESTAMP)
alert_count (INTEGER) — count in past 24h
metadata (JSON) — sensor-specific config
```

### Table: `safety_events`
```
id (INTEGER PRIMARY KEY)
event_type (TEXT) — motion_detected, door_unlock, unauthorized_person, system_failure
severity (TEXT) — low, medium, high, critical
timestamp (TIMESTAMP)
sensor_id (FK to home_sensors)
description (TEXT)
action_taken (TEXT) — alert sent, police called, etc
resolved (BOOLEAN)
notes (TEXT)
```

### Table: `meal_plans`
```
id (INTEGER PRIMARY KEY)
date (DATE)
meal_type (TEXT) — breakfast, lunch, dinner, snack
recipe_name (TEXT)
ingredients (JSON) — [name, qty, unit, available]
prep_time_min (INTEGER)
cooking_time_min (INTEGER)
servings (INTEGER)
dietary_flags (JSON) — [vegetarian, gluten_free, nut_allergy]
fridge_status (FK to fridge_inventory)
```

### Table: `fridge_inventory`
```
id (INTEGER PRIMARY KEY)
item_name (TEXT)
category (TEXT) — produce, dairy, meat, pantry
quantity (REAL)
unit (TEXT) — lbs, count, oz, cups
expiration_date (DATE)
date_added (TIMESTAMP)
sensor_temperature (DECIMAL) — last recorded fridge temp
```

### Table: `appliance_status`
```
id (INTEGER PRIMARY KEY)
appliance_name (TEXT) — dishwasher, washing_machine, dryer, oven
current_state (TEXT) — idle, running, complete, error
cycle_type (TEXT) — normal, eco, quick, etc
time_remaining_min (INTEGER)
energy_usage_kwh (DECIMAL)
last_service_date (DATE)
maintenance_alert (BOOLEAN)
```

### Table: `appointments`
```
id (INTEGER PRIMARY KEY)
event_type (TEXT) — doctor, school, household_service, social_services
title (TEXT)
date (DATE)
time (TIME)
duration_min (INTEGER)
location (TEXT)
contact_person (TEXT)
contact_phone (TEXT)
notes (TEXT)
reminder_set (BOOLEAN)
status (TEXT) — scheduled, completed, cancelled, no_show
```

### Table: `social_services_registry`
```
id (INTEGER PRIMARY KEY)
service_name (TEXT) — health_dept, school_district, meals_on_wheels, elderly_services
county (TEXT) — Wayne, Greene
city (TEXT) — Waynesville, Spring Valley
phone (TEXT)
website (TEXT)
eligibility_criteria (JSON) — [age_min, income_threshold, address_required]
programs (JSON) — [program_name, description]
last_updated (DATE)
```

### Table: `household_tasks`
```
id (INTEGER PRIMARY KEY)
task_name (TEXT) — vacuuming, laundry, dishes, bathroom_clean
assigned_to (TEXT)
frequency (TEXT) — daily, weekly, bi_weekly, monthly
next_due (DATE)
completed (BOOLEAN)
completion_date (TIMESTAMP)
notes (TEXT)
priority (TEXT) — low, medium, high
```

### Table: `system_logs`
```
id (INTEGER PRIMARY KEY)
timestamp (TIMESTAMP)
system (TEXT) — sensors, fridge, appliances, social_services_sync
event (TEXT) — startup, sync, error, alert
status (TEXT) — ok, warning, error
message (TEXT)
data (JSON)
```

---

## Local Processing Pipelines

### Safety Monitor
```
[sensor_input] → [motion/door detection] → [check threat patterns] 
→ [if threat] → [alert_user + log] → [optional: call emergency]
```

### Meal Coordinator
```
[user_input: meal date] → [query meal_plans] → [check fridge_inventory] 
→ [match ingredients] → [flag missing items] → [suggest alternatives]
```

### Fridge Manager
```
[sensor: temperature] → [log to fridge_inventory] → [check expiration_dates] 
→ [if expired soon] → [suggest meal use] → [remove from inventory]
```

### Appliance Scheduler
```
[user_input: start dishwasher] → [check water temp, energy off-peak] 
→ [start cycle] → [monitor progress] → [alert when done]
```

### Social Services Eligibility
```
[user_input: income, age, address] → [query social_services_registry] 
→ [match eligibility_criteria] → [display available programs] → [log inquiry]
```

### Household Task Tracker
```
[daily reminder] → [check household_tasks.next_due] 
→ [notify assigned_to] → [track completion] → [reschedule]
```

---

## Data Privacy & Security

### What's stored locally (on-device only):
- All sensor data
- Meal plans and fridge inventory
- Appointment calendar
- Household task list
- System logs

### What's NOT stored:
- Personally identifiable names in alert logs (use family_id instead)
- Camera footage (sensor detections only, no video/images)
- Medical details (only appointment scheduling)
- Financial data (income thresholds for eligibility matching only, not stored)

### Encryption:
- SQLite database encrypted via SQLCipher (AES-256)
- Password protected access to sensitive tables (social_services_registry, appointment contact info)
- No cloud sync, no external backup (user controls manual export if needed)

---

## Integration Points (Lantern)

BetterSafe runs as an optional desktop feature within Lantern (new tab):
```
Lantern Desktop
├── Chat (Claude/Gemini)
├── Music (public domain)
├── Games (RetroArch)
├── Browser (local URLs)
├── Videos (local files)
├── Email (SMTP placeholder)
├── Reminders (basic calendar)
└── BetterSafe (HOME AUTOMATION HUB)
    ├── Safety Monitor
    ├── Meal Coordinator
    ├── Fridge Manager
    ├── Appliance Status
    ├── Social Services Eligibility
    └── Household Tasks
```

All data stays local. No external APIs except optional manual social services lookup (local database cached).

---

## Status

**Current:** Schema definition complete (19 tables, 6 processing pipelines)
**Next:** Create SQLite init script + UI mockups for each module
**Architecture:** See bettersafe-local-first-architecture.md
