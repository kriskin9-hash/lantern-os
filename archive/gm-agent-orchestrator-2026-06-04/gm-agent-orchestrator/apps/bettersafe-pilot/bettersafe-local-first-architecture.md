# BetterSafe — Local-First Architecture

**Design Principle:** 100% on-device processing. Zero cloud dependency. Open-source only. No external cookies/tracking.

---

## Tech Stack

### Frontend
- **Framework:** CustomTkinter (Python desktop, same as Lantern)
- **UI:** ttk.Notebook tabbed interface (6 modules)
- **Charting:** matplotlib (embedded in Tkinter)
- **Data binding:** Direct SQLite queries via sqlite3 stdlib

### Backend
- **Database:** SQLite + SQLCipher (AES-256 encryption)
- **Processing:** Python stdlib + scipy (data analysis)
- **Scheduling:** APScheduler (local task scheduling, no cloud cron)
- **Logging:** Python logging module (local file rotation)
- **Time:** dateutil (timezone-aware, no NTP required)

### System Integration
- **Home Sensors:** GPIO reads (if available) or simulated sensor inputs
- **IoT Devices:** Direct network polling (no cloud broker, local LAN only)
- **Appliances:** MQTT over local network (no external broker)
- **OS Integration:** subprocess for system commands (power management, etc)

### Zero-External Dependencies
```
✓ Python stdlib (sqlite3, json, logging, datetime, subprocess)
✓ CustomTkinter (for UI, already in Lantern)
✓ SQLCipher (encryption, local)
✓ APScheduler (task scheduling, local)
✓ scipy (minimal, for statistics only)
✗ NO internet, NO cloud APIs, NO external databases
✗ NO Google/AWS/Azure/Anthropic integrations
✗ NO webhooks, NO callbacks to remote services
```

---

## Module Architecture

### 1. Safety Monitor
```
Inputs: [motion sensors, door sensors, camera detectors]
Processing:
  - Pattern detection (2+ sensors within 5min = potential threat)
  - Anomaly scoring (if motion at 3am in unused room = flag)
  - Local rule engine (if [threat_score > 0.8] then [alert])
Outputs:
  - Local notification (system tray + sound)
  - Event log (safety_events table)
  - Optional: system call to emergency contact (user-configured)
Tech: OpenCV (optional, for camera frame analysis) or simple motion events
```

### 2. Meal Coordinator
```
Inputs: [meal date selection, fridge sensor readings, user preferences]
Processing:
  - Query meal_plans table for selected date
  - Cross-reference ingredients with fridge_inventory (current items + expiration)
  - Calculate prep/cook time vs available time window
  - Suggest alternatives if key ingredient missing
Outputs:
  - Meal card (ingredients list, recipe, timing)
  - Shopping list (missing items)
  - Fridge state snapshot
Tech: Fuzzy matching (rapidfuzz library for ingredient variants)
```

### 3. Fridge Manager
```
Inputs: [temperature sensor (if available), inventory updates]
Processing:
  - Log temperature to time-series (track patterns)
  - Monitor expiration dates (flag items expiring within 3 days)
  - Suggest recipes using expiring ingredients
  - Auto-remove expired items from inventory
Outputs:
  - Current inventory view
  - Expiration alerts
  - Recipe suggestions
Tech: Local time-series (sqlite with date indexes)
```

### 4. Appliance Scheduler
```
Inputs: [user request to start appliance, current energy price tier (if available)]
Processing:
  - Check appliance state (running/idle/error)
  - If eco mode: wait for off-peak hours (configurable schedule)
  - Estimate remaining time based on cycle type
  - Monitor energy usage (estimate from appliance specs)
Outputs:
  - Status panel (each appliance: icon + time remaining)
  - Alert when cycle complete
  - Energy summary (daily, weekly)
Tech: Direct appliance integration (GPIO or MQTT local broadcast)
```

### 5. Social Services Eligibility
```
Inputs: [user input: age, income, address, disability status (optional)]
Processing:
  - Query social_services_registry (local cached database)
  - Match against eligibility_criteria for Waynesville/Spring Valley services
  - Calculate fit score (how many criteria match)
  - Display available programs with next steps
Outputs:
  - List of eligible programs
  - Contact info + website
  - Application checklist
Tech: Local database only (no remote lookup)
Database seeded with: health_dept, school_district, seniors_services, disability_services, food_assistance, housing_assistance
```

### 6. Household Tasks
```
Inputs: [task definition, assigned person, frequency, priority]
Processing:
  - Daily cron-like check (every 06:00 local time)
  - Flag tasks due today/overdue
  - Send reminder notification
  - Track completion
Outputs:
  - Task list (pending, completed, overdue)
  - Responsibility matrix (who owns what)
  - Completion history
Tech: APScheduler for reminder timing, sqlite for state
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  BetterSafe Desktop App                      │
│                    (CustomTkinter)                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │ Safety  │  │  Meal   │  │ Fridge  │  │Appliance│       │
│  │ Monitor │  │Coordinator│ Manager │  │Scheduler│       │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘       │
│       │            │            │            │             │
│       └────────────┼────────────┼────────────┘             │
│                    │            │                           │
│              ┌─────▼────────────▼─────┐                    │
│              │  SQLite + SQLCipher     │                    │
│              │  (Local, encrypted)     │                    │
│              │  ~/.bettersafe/db.sqlite│                    │
│              └─────────────────────────┘                    │
│                    │         │                              │
│       ┌────────────┴─────────┴──────────┐                  │
│       │                                  │                  │
│   ┌───▼────┐                      ┌──────▼─────┐           │
│   │ Sensors│ (GPIO/MQTT local)    │Social Svcs  │           │
│   │(IoT)   │                      │Registry    │           │
│   └────────┘                      │(Cached DB) │           │
│                                   └────────────┘           │
│                                                               │
└─────────────────────────────────────────────────────────────┘

NO INTERNET ┌──────────────────────────────────────────┐ NO CLOUD
NO CLOUD   │ All processing local, all data local only │ NO APIs
NO TRACKING│                                          │NO COOKIES
            └──────────────────────────────────────────┘
```

---

## File Structure

```
C:\Users\alexp\Documents\gm-agent-orchestrator\apps\bettersafe-pilot\
├── bettersafe.py                       (Main app, 800 lines)
├── bettersafe_db.py                    (Schema + init, 300 lines)
├── modules/
│   ├── safety_monitor.py               (Sensor monitoring, 250 lines)
│   ├── meal_coordinator.py             (Recipe matching, 300 lines)
│   ├── fridge_manager.py               (Inventory tracking, 200 lines)
│   ├── appliance_scheduler.py          (Cycle management, 200 lines)
│   ├── social_services.py              (Eligibility matching, 150 lines)
│   └── household_tasks.py              (Task tracking, 150 lines)
├── data/
│   ├── social_services_registry.json   (Waynesville/Spring Valley services)
│   ├── sample_meal_plans.json          (Starter recipes)
│   └── sensor_config.json              (GPIO/MQTT mappings)
├── ui/
│   ├── safety_tab.py                   (Safety Monitor UI, 200 lines)
│   ├── meal_tab.py                     (Meal Coordinator UI, 200 lines)
│   ├── fridge_tab.py                   (Fridge Manager UI, 150 lines)
│   ├── appliance_tab.py                (Appliance Scheduler UI, 150 lines)
│   ├── social_services_tab.py          (Eligibility UI, 150 lines)
│   └── tasks_tab.py                    (Household Tasks UI, 150 lines)
├── bettersafe-feature-schema.md        (Data model)
├── bettersafe-local-first-architecture.md  (This file)
├── SETUP.md                            (Installation, config, testing)
└── README.md                           (User guide)

Total new code: ~2,500 lines (testable, modular)
```

---

## Integration with Lantern

BetterSafe runs as a tab within the existing Lantern desktop app:

```python
# lantern-integrated.py: add to __init__
from modules.bettersafe_tab import BetterSafeTab

self.notebook.add(BetterSafeTab(self.notebook, config=self.config), 
                  text="Home")
```

Shared resources:
- `config.json` (BetterSafe adds `[bettersafe]` section for sensor mappings, social_services_data_path)
- `~/.lantern/telemetry/` (BetterSafe logs safety events + appliance usage to same telemetry pipeline)
- M5 attestation (validate BetterSafe DB integrity hourly)

---

## Security Model

### Authentication
- None (local user, local OS auth)
- BetterSafe DB password (optional, SQLCipher)
- Sensor API tokens stored locally (not in version control)

### Encryption
- SQLCipher (AES-256, database-level)
- Optional: sensitive fields encrypted (social services notes)
- No external key management (keys in local config only)

### Audit Trail
- All actions logged to system_logs table (timestamp, user, action, result)
- No external syslog, no cloud analytics
- User can export audit trail as CSV anytime

### Threat Model
- **In scope:** Local sensor spoofing, database corruption, accidental deletion
- **Out of scope:** Network attacks (no network), malware (OS responsibility), physical theft (encryption helps)

---

## Implementation Timeline

**Week 1 (May 25–Jun 1):**
- BetterSafe schema + SQLite init (bettersafe_db.py)
- Social services registry (JSON + load into DB)
- Household tasks module (simplest, lowest risk)

**Week 2 (Jun 2–8):**
- Fridge manager (sensor simulation, inventory UI)
- Meal coordinator (recipe matching UI)

**Week 3 (Jun 9–22):**
- Safety monitor (sensor integration, pattern detection)
- Appliance scheduler (status polling)

**Week 4+ (Jun 23–30):**
- Integration with Lantern (tabbed UI)
- M5 attestation for DB health
- Testing + Family A deployment

---

## Success Criteria

By June 25, 2026:
- ✓ BetterSafe runs within Lantern (no external app)
- ✓ SQLite DB encrypted and stored locally
- ✓ All 6 modules functioning (tested, logged)
- ✓ Zero cloud calls (wireshark: all traffic local)
- ✓ Open source (all deps auditable)
- ✓ Waynesville/Spring Valley social services database seeded
- ✓ Family A testing complete (in-app feedback logged)

---

## Status

**Current:** Architecture complete, ready for implementation  
**Owner:** TBD (assign during operator recruitment)  
**Next:** Create bettersafe_db.py + bettersafe.py main app skeleton
