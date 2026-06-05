# CSF Ingestion — Patreon Tier Structure

**Status:** ready_to_wire  
**Priority:** 1 — monetization for morning launch  
**Effort:** 2–3 hours UI gating

## Tier Structure

Already defined in `src/convergence_io/pcsf.py` as `DreamerTier` + `TIER_QUOTA_LIMITS`:

| Tier | Price | Features | Quota |
|------|-------|----------|-------|
| Wanderer (free) | $0 | Dream journal, 3 agents (Lantern/Blinkbug/Keystone), CTF symbols, offline, JSONL export | 100 chat/mo, 15 art gen, 5 3-door plays |
| Deep Dreamer | $5/mo | All 6 agents, unlimited AI chat, priority Gemini grounding, voice TTS, CSV export | Unlimited |
| Synthesasia Guild | $15/mo | Everything + early features, founder Discord access, custom LoRA training slot, priority provider routing | Unlimited + priority boost |

## Implementation

### Phase 1: Client-side gating (no auth needed)
```js
// dream-chat.html — check localStorage for tier
const tier = localStorage.getItem('dreamer_tier') || 'wanderer';
const TIER_LIMITS = { wanderer: { chat: 100, agents: 3 }, deep_dreamer: { chat: Infinity, agents: 6 }, synthesasia_guild: { chat: Infinity, agents: 6 } };
```

Patreon link: `https://www.patreon.com/c/lanterndreamjournal`
On Patreon confirmation, user enters a tier code in settings drawer → stored in localStorage.

### Phase 2: Server-side quota (later)
Wire `TIER_QUOTA_LIMITS` from `src/convergence_io/pcsf.py` into `routes/dream.js` to enforce server-side rate limits.

## Files to Change
- `apps/lantern-garage/public/dream-chat.html` — tier check before sendMessage, agent selector filter
- `apps/lantern-garage/public/dream-chat.html` — tier card in settings drawer
- `data/pcsf/settings.pcsf.json` — add DREAMER_TIER key
