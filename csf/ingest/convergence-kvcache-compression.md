# CSF Ingestion — KV Cache Compression for Multi-Turn Context

**Status:** queued  
**Priority:** 1 — highest token-cost reduction  
**Estimated effort:** 3–4 hours  
**Source:** [KVzip research, TechXplore 2025](https://techxplore.com/news/2025-11-ai-tech-compress-llm-chatbot.html), [FlowKV arxiv 2505.15347](https://arxiv.org/pdf/2505.15347)

## Problem

Every chat turn in `stream-chat.js` sends the full 6-turn history to the AI provider verbatim. At 1000 chars/turn × 6 turns = 6000 tokens of context per request, growing linearly. KVzip research shows 3–4× compression with no accuracy loss.

## Proposed Implementation

In `apps/lantern-garage/lib/stream-chat.js`, replace the raw `history` array passthrough with a tiered summariser before provider dispatch:

```js
function compressHistory(history) {
  // Turns 0-1 (most recent exchange): Full fidelity
  // Turns 2-3: Compressed — truncate to first 200 chars + "…"
  // Turns 4-5: Placeholder — "[user said: <10-word summary>]"
  return history.map((h, i) => {
    if (i >= history.length - 2) return h; // Full
    if (i >= history.length - 4) return { ...h, text: h.text.slice(0, 200) + (h.text.length > 200 ? '…' : '') };
    const words = h.text.split(' ').slice(0, 10).join(' ');
    return { ...h, text: `[${h.role === 'user' ? 'dreamer' : 'lantern'}: ${words}…]` };
  });
}
```

Apply at each provider's messages construction. FlowKV principle: only compress the *newly completed turn*, never re-compress what was already compressed.

## Files to Change
- `apps/lantern-garage/lib/stream-chat.js` — `compressHistory()` + apply to all 4 provider message arrays
- `tests/test_dream_chat_multiturns.js` — add test verifying compressed history still produces coherent reply

## Expected Outcome
~60% token reduction on sessions beyond turn 2. Faster TTFT (time to first token). No user-visible change.
