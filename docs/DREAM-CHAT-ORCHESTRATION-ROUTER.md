# Dream Chat Orchestration Router

Dream Chat is the front door for Lantern OS. It does not become an engineer,
roleplay persona, trading agent, or exporter. It classifies the user request,
selects the target agent/surface, and either delegates through convergence or
stays on the direct Dream Chat surface.

## Route Decision

Every request can be reduced to:

```json
{
  "intent": "code | rp_game | strategy | memory_export | dream_analysis | trading",
  "agent": "keystone | founder | lantern | three_doors | csf | trading",
  "surface": "dream_chat | three_doors | convergence | csf_export",
  "confidence": 0.0,
  "reason": "Matched routing evidence",
  "requires_convergence": false
}
```

The deterministic classifier lives in
`apps/lantern-garage/lib/intent-router.js`. The registry is extensible by
adding a capability object with `intents`, `triggers`, `input_contract`,
`output_contract`, `surface`, `converges`, and `blocking`.

## Runtime Contract

- `POST /api/dream/route` returns the route decision and public registry view.
- `POST /api/dream/chat/stream` independently classifies the message before
  provider streaming.
- If `requires_convergence` is true, the stream delegates to
  `apps/lantern-garage/lib/convergence-adapter.js`.
- The adapter invokes `src/convergence_io_engine.py converge --message ...`.
- Dream Chat uses `CONVERGENCE_ROUTE_TIMEOUT_MS` for routed waits, defaulting
  to 8000 ms. Timeout returns a failed convergence result instead of silently
  blocking the chat.
- The UI shows a route card before the first streamed result so blocking work
  is visible instead of silently hanging.

## Surface Rules

- Code and GitHub work route to `keystone` on the `convergence` surface.
- Strategy routes to `founder` on the `convergence` surface.
- Trading routes to `trading` on the `convergence` surface.
- Explicit Three Doors requests route to `three_doors` on the `three_doors`
  surface.
- Memory export routes to `csf` on the `csf_export` surface.
- Ambiguous or reflective input defaults to `lantern` on `dream_chat`.

Bare symbolic words like `door`, `dream`, or `journal` do not switch Dream Chat
into RP game mode by themselves. Three Doors requires explicit game/roleplay
language such as `!three-doors`, `play three doors`, or `roleplay`.
