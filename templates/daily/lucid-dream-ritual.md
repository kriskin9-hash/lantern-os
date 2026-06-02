# Daily Lucid Dream Ritual (Lantern OS)

Use with `skills/lucid_dreaming/mild_wbtb_protocol.py`

## Morning Recall (do before phone or movement)
- Record full dream into Dream Journal (content, lucidity 0-10, emotions, tags, linked goals)
- Note one "what felt off or wondrous?"

## Daytime Reality Checks (8–12 total)
Run these with genuine curiosity:
- Hands / finger count
- Read text twice
- Clock / time check
- Nose pinch breathing test
- "Am I dreaming right now?" (hold the question)

## Evening Intention (10–15 min before bed)
1. Review today's dreams + RCs
2. Generate MILD phrase:
   ```python
   from skills.lucid_dreaming.mild_wbtb_protocol import generate_mild_intention
   intention = generate_mild_intention(last_dream_summary="...", personal_goals=["..."])
   print(intention)
   ```
3. Visualize becoming lucid in a recent dream scene while repeating the phrase

## WBTB (3–4 nights/week)
- Natural or gentle alarm at ~5.5 hours after bedtime
- 20–45 min upright: journal, light movement, RCs, re-state intention
- Return to bed with fresh visualization

Track weekly lucidity average in `skills/dream_journal/`.

See full protocol and schedule calculator in the skill module.
