"""
MILD + WBTB Lucid Dreaming Protocol Module for Lantern OS

Provides:
- Mnemonic intention statement generation (MILD)
- Wake-Back-To-Bed timing calculator and activity suggestions
- Reality check prompt library (daytime + dream-use)
- Minimal daily ritual scaffolding

All functions are pure and local. Results are meant to be copied into
your Dream Journal entries (lucidity field + tags) and analyzed via
the mirror_prompt system or Bayesian World Model.

References (evidence discipline):
- LaBerge, S. (various papers and "Lucid Dreaming" 1985/2009)
- Standard WBTB + MILD combination used in most successful home lucid dreaming studies
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import random


@dataclass
class WBTBSchedule:
    bedtime: str
    first_wake: str
    activity_duration_min: int
    return_to_bed: str
    recommended_activities: List[str]
    mild_window_note: str


def generate_mild_intention(
    last_dream_summary: str = "",
    personal_goals: Optional[List[str]] = None,
    style: str = "classic",
) -> str:
    """
    Return a short, present-tense, memorable MILD intention phrase.

    Incorporates a fragment of the last dream when provided (increases
    personal relevance and recall priming).
    """
    goals = personal_goals or []
    goal_fragment = ""
    if goals:
        goal_fragment = f" and remember my intention around {random.choice(goals)}"

    base = "The next time I am dreaming, I will realize I am dreaming."

    if style == "classic":
        phrase = base
    elif style == "vivid":
        phrase = "I am dreaming. I notice the impossible and become lucid."
    else:
        phrase = base

    if last_dream_summary:
        # Extract a short evocative phrase (very naive but effective for priming)
        words = last_dream_summary.split()
        key = " ".join(words[:6]) + ("..." if len(words) > 6 else "")
        phrase = f"Next time I dream — especially if I see {key} — I will know I am dreaming{goal_fragment}."

    return phrase


def wbtb_schedule(
    sleep_time: str = "23:00",
    target_wake_hours: float = 5.5,
    activity_minutes: int = 30,
) -> WBTBSchedule:
    """
    Calculate a practical WBTB window.

    sleep_time: "HH:MM" 24h format (approximate bedtime)
    target_wake_hours: hours after sleep onset for first awakening (classic 5–6 h)
    """
    try:
        bed_h, bed_m = map(int, sleep_time.split(":"))
    except ValueError:
        bed_h, bed_m = 23, 0

    bedtime_dt = datetime.now().replace(hour=bed_h, minute=bed_m, second=0, microsecond=0)
    wake_dt = bedtime_dt + timedelta(hours=target_wake_hours)
    return_dt = wake_dt + timedelta(minutes=activity_minutes)

    activities = [
        "Read last 2–3 dream journal entries (no phone)",
        "Gentle reality checks (hands, text, breathing)",
        "Write or speak today's MILD intention aloud",
        "Light stretching or 2 min cold water on face (stay upright)",
        "Avoid bright screens; use warm low light if reading",
    ]

    return WBTBSchedule(
        bedtime=sleep_time,
        first_wake=wake_dt.strftime("%H:%M"),
        activity_duration_min=activity_minutes,
        return_to_bed=return_dt.strftime("%H:%M"),
        recommended_activities=activities,
        mild_window_note="During the activity window and again as you fall back asleep, repeat your MILD intention while visualizing a recent dream becoming lucid.",
    )


def reality_check_prompts(count: int = 6, include_night: bool = True) -> List[str]:
    """Return a shuffled selection of practical reality checks."""
    checks = [
        "Look at your hands — do they have the normal number of fingers?",
        "Read a line of text, look away, read it again. Did it change?",
        "Check a digital clock or watch twice. Does the time make sense?",
        "Try to push a finger through your palm. What happens?",
        "Breathe through a pinched nose. Can you still breathe?",
        "Ask yourself: 'Am I dreaming right now?' and really mean the question.",
        "Look at a distant object, then something close. Does the focus behave normally?",
        "Recall: what did you do 10 minutes ago? Is the memory stable?",
    ]
    if include_night:
        checks.append("In a dream: perform a reality check the moment anything feels slightly off or wondrous.")

    random.shuffle(checks)
    return checks[:count]


def daily_lucid_ritual_template() -> str:
    """Minimal daily structure you can copy into templates/daily/ or a notebook."""
    return """# Daily Lucid Dreaming Ritual (MILD + WBTB foundation)

## Morning (within 5 min of waking)
- [ ] Recall dream in as much detail as possible before moving or checking phone
- [ ] Write or voice-note into Dream Journal (content + lucidity 0–10 + emotions + tags)
- [ ] One-sentence "what felt different?" note

## Daytime (spread across waking hours)
- [ ] 8–12 reality checks using prompts from the protocol (mix visual, cognitive, body)
- [ ] Each RC: ask "Am I dreaming?" with genuine curiosity for 3–5 seconds
- [ ] Optional: set 3 random phone alarms labeled "RC" as training wheels (remove after 2 weeks)

## Evening / Pre-sleep
- [ ] Review today's RC successes and any dream fragments
- [ ] Generate fresh MILD intention (use mild_wbtb_protocol.generate_mild_intention)
- [ ] 2–3 minutes of present-tense visualization of becoming lucid in a recent dream scene
- [ ] Repeat the intention phrase as you drift off

## WBTB nights (3–4× per week recommended)
- [ ] Set intention to wake naturally ~5.5–6 h after sleep onset
- [ ] When awake: 20–45 min upright, journal + light RC + re-enter with strong MILD
- [ ] Log the night outcome the next morning regardless of result

Track lucidity trend weekly in Dream Journal + Bayesian World Model.
"""


# --------------------------------------------------------------------------- #
# Self-demo / quick start
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    print("=== Lantern OS Lucid Dreaming Protocol Demo ===\n")

    intention = generate_mild_intention(
        last_dream_summary="I walked through a blue door into a room filled with starlight and a silver river",
        personal_goals=["increase dream lucidity", "explore symbolic meaning of rivers"],
    )
    print("MILD Intention:\n", intention, "\n")

    sched = wbtb_schedule(sleep_time="23:15", target_wake_hours=5.5, activity_minutes=35)
    print("WBTB Schedule:")
    print(f"  Bedtime: {sched.bedtime}")
    print(f"  Wake window: {sched.first_wake} for ~{sched.activity_duration_min} min")
    print(f"  Return to bed: {sched.return_to_bed}")
    print("  Activities:")
    for a in sched.recommended_activities:
        print(f"    - {a}")
    print()

    print("Sample Reality Checks:")
    for rc in reality_check_prompts(4):
        print(f"  • {rc}")
    print()

    print("Daily ritual template available via daily_lucid_ritual_template()")
    print("\n✅ mild_wbtb_protocol.py self-test complete. Use the generators tonight.")
