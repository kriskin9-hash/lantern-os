import json
import os


def load_slots(path=None):
    """Load agent slots from agent-slots.json"""
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "..", "..", ".claude", "agent-slots.json")
    with open(path) as f:
        data = json.load(f)
    return {s["id"]: s for s in data["slots"]}


def get_affinity_map(slots):
    """Build responsibility -> slot_id affinity map"""
    affinity = {}
    for slot_id, slot in slots.items():
        for resp in slot.get("responsibilities", []):
            if resp not in affinity:
                affinity[resp] = slot_id
    return affinity


def get_fallback_chain(slots, start_slot_id, max_depth=8):
    """Get fallback chain from a slot until dead end or cycle detected"""
    chain = []
    seen = {start_slot_id}
    current = start_slot_id
    for _ in range(max_depth):
        slot = slots.get(current, {})
        nxt = slot.get("quotaTracking", {}).get("fallbackAgent")
        if not nxt or nxt in seen:
            break
        chain.append(nxt)
        seen.add(nxt)
        current = nxt
    return chain


def get_boot_order(path=None):
    """Get the daily boot order from agent-slots.json routing config"""
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "..", "..", ".claude", "agent-slots.json")
    with open(path) as f:
        data = json.load(f)
    return data.get("routing", {}).get("dailyBootOrder", [s["id"] for s in data["slots"]])
