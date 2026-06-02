#!/usr/bin/env python3
"""
Founder Wellness & Lifestyle Tracker

Track daily events: sleep, work, meals, exercise, mood, creativity.
Personal version of BetterSafe for self-observation.

Data stored locally: ~/.foundry/wellness.json (never synced)

Usage:
  python scripts/founder-wellness-tracker.py log-sleep 7.5
  python scripts/founder-wellness-tracker.py log-work 6 --focus high
  python scripts/founder-wellness-tracker.py log-food breakfast "coffee, eggs"
  python scripts/founder-wellness-tracker.py log-mood happy --energy 8
  python scripts/founder-wellness-tracker.py daily-summary
  python scripts/founder-wellness-tracker.py week-summary
"""

import json
from pathlib import Path
from datetime import datetime, timedelta

WELLNESS_FILE = Path.home() / ".foundry" / "wellness.json"


class WellnessTracker:
    """Self-tracking for founder health & productivity."""

    def __init__(self):
        self.data = self._load()

    def _load(self):
        if WELLNESS_FILE.exists():
            with open(WELLNESS_FILE) as f:
                return json.load(f)
        return {"entries": []}

    def _save(self):
        WELLNESS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(WELLNESS_FILE, "w") as f:
            json.dump(self.data, f, indent=2)

    def log_sleep(self, hours: float, notes: str = ""):
        """Log sleep duration."""
        entry = {
            "type": "sleep",
            "hours": hours,
            "timestamp": datetime.now().isoformat(),
            "notes": notes,
        }
        self.data["entries"].append(entry)
        self._save()
        print(f"[OK] Logged sleep: {hours}h")

    def log_work(self, hours: float, focus: str = "medium", project: str = ""):
        """Log work session."""
        entry = {
            "type": "work",
            "hours": hours,
            "focus": focus,  # low, medium, high
            "project": project,
            "timestamp": datetime.now().isoformat(),
        }
        self.data["entries"].append(entry)
        self._save()
        print(f"[OK] Logged work: {hours}h ({focus} focus)")

    def log_food(self, meal: str, items: str = ""):
        """Log meal."""
        entry = {
            "type": "food",
            "meal": meal,  # breakfast, lunch, dinner, snack
            "items": items,
            "timestamp": datetime.now().isoformat(),
        }
        self.data["entries"].append(entry)
        self._save()
        print(f"[OK] Logged {meal}: {items}")

    def log_drink(self, drink_type: str = "water", volume: str = ""):
        """Log hydration."""
        entry = {
            "type": "drink",
            "drink": drink_type,
            "volume": volume,
            "timestamp": datetime.now().isoformat(),
        }
        self.data["entries"].append(entry)
        self._save()
        print(f"[OK] Logged drink: {drink_type}")

    def log_sex(self, notes: str = ""):
        """Log sexual activity."""
        entry = {
            "type": "sex",
            "timestamp": datetime.now().isoformat(),
            "notes": notes,
        }
        self.data["entries"].append(entry)
        self._save()
        print(f"[OK] Logged sexual activity")

    def log_exercise(self, activity: str, duration: float, intensity: str = "medium"):
        """Log exercise."""
        entry = {
            "type": "exercise",
            "activity": activity,
            "duration_min": duration,
            "intensity": intensity,
            "timestamp": datetime.now().isoformat(),
        }
        self.data["entries"].append(entry)
        self._save()
        print(f"[OK] Logged exercise: {activity} ({duration}min, {intensity})")

    def log_mood(self, mood: str, energy: int = 5, notes: str = ""):
        """Log mood & energy (1-10 scale)."""
        entry = {
            "type": "mood",
            "mood": mood,  # happy, sad, anxious, focused, scattered, etc
            "energy": energy,  # 1-10
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
        }
        self.data["entries"].append(entry)
        self._save()
        print(f"[OK] Logged mood: {mood} (energy: {energy}/10)")

    def daily_summary(self, date: str = None):
        """Get today's summary."""
        if date is None:
            target_date = datetime.now().date()
        else:
            target_date = datetime.fromisoformat(date).date()

        day_entries = [
            e
            for e in self.data["entries"]
            if datetime.fromisoformat(e["timestamp"]).date() == target_date
        ]

        if not day_entries:
            print(f"No entries for {target_date}")
            return

        print(f"\n=== Daily Summary: {target_date} ===\n")

        # Aggregate
        sleep_hours = sum(
            e.get("hours", 0) for e in day_entries if e["type"] == "sleep"
        )
        work_hours = sum(
            e.get("hours", 0) for e in day_entries if e["type"] == "work"
        )
        meals = len([e for e in day_entries if e["type"] == "food"])
        exercise = [
            e for e in day_entries if e["type"] == "exercise"
        ]
        moods = [e for e in day_entries if e["type"] == "mood"]
        sex = len([e for e in day_entries if e["type"] == "sex"])

        print(f"Sleep:         {sleep_hours}h")
        print(f"Work:          {work_hours}h")
        print(f"Meals:         {meals}")
        print(f"Sex:           {sex} times")
        print(f"Exercise:      {len(exercise)} sessions")

        if exercise:
            total_exercise = sum(e.get("duration_min", 0) for e in exercise)
            print(f"               ({total_exercise} min total)")

        if moods:
            avg_energy = sum(e.get("energy", 5) for e in moods) / len(moods)
            print(f"Mood:          {moods[-1]['mood']} (avg energy: {avg_energy:.1f}/10)")

        print()

    def week_summary(self):
        """Get last 7 days summary."""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=6)

        week_entries = [
            e
            for e in self.data["entries"]
            if start_date <= datetime.fromisoformat(e["timestamp"]).date() <= end_date
        ]

        if not week_entries:
            print("No entries for this week")
            return

        print(f"\n=== Weekly Summary ({start_date} to {end_date}) ===\n")

        sleep_hours = sum(
            e.get("hours", 0) for e in week_entries if e["type"] == "sleep"
        )
        work_hours = sum(
            e.get("hours", 0) for e in week_entries if e["type"] == "work"
        )
        avg_sleep = sleep_hours / 7
        avg_work = work_hours / 7

        print(f"Sleep:         {sleep_hours}h total ({avg_sleep:.1f}h/night avg)")
        print(f"Work:          {work_hours}h total ({avg_work:.1f}h/day avg)")
        print(f"Meals:         {len([e for e in week_entries if e['type'] == 'food'])} meals")
        print(f"Sex:           {len([e for e in week_entries if e['type'] == 'sex'])} times")
        print(f"Exercise:      {len([e for e in week_entries if e['type'] == 'exercise'])} sessions")

        moods = [e for e in week_entries if e["type"] == "mood"]
        if moods:
            avg_energy = sum(e.get("energy", 5) for e in moods) / len(moods)
            print(f"Avg Energy:    {avg_energy:.1f}/10")

        print()


def main():
    import sys

    tracker = WellnessTracker()

    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]

    if command == "log-sleep":
        hours = float(sys.argv[2]) if len(sys.argv) > 2 else 8
        notes = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else ""
        tracker.log_sleep(hours, notes)

    elif command == "log-work":
        hours = float(sys.argv[2]) if len(sys.argv) > 2 else 8
        focus = sys.argv[4] if len(sys.argv) > 4 else "medium"
        tracker.log_work(hours, focus)

    elif command == "log-food":
        meal = sys.argv[2] if len(sys.argv) > 2 else "snack"
        items = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else ""
        tracker.log_food(meal, items)

    elif command == "log-drink":
        drink = sys.argv[2] if len(sys.argv) > 2 else "water"
        tracker.log_drink(drink)

    elif command == "log-sex":
        notes = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        tracker.log_sex(notes)

    elif command == "log-exercise":
        activity = sys.argv[2] if len(sys.argv) > 2 else "walk"
        duration = float(sys.argv[3]) if len(sys.argv) > 3 else 30
        intensity = sys.argv[5] if len(sys.argv) > 5 else "medium"
        tracker.log_exercise(activity, duration, intensity)

    elif command == "log-mood":
        mood = sys.argv[2] if len(sys.argv) > 2 else "neutral"
        energy = int(sys.argv[4]) if len(sys.argv) > 4 else 5
        notes = " ".join(sys.argv[6:]) if len(sys.argv) > 6 else ""
        tracker.log_mood(mood, energy, notes)

    elif command == "daily":
        date = sys.argv[2] if len(sys.argv) > 2 else None
        tracker.daily_summary(date)

    elif command == "week":
        tracker.week_summary()

    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
