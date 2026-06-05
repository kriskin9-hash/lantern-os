# CSF Ingestion — ASMR/Whisper TTS Provider Chain

**Status:** queued  
**Priority:** 3 — significant UX lift for the voice mode  
**Estimated effort:** 2–3 hours  
**Source:** [WaveSpeedAI Omnivoice](https://wavespeed.ai/blog/posts/introducing-wavespeed-ai-omnivoice-text-to-speech-on-wavespeedai/), [Web Speech API MDN](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)

## Problem

Current TTS uses `window.speechSynthesis` — system voice quality varies wildly. For a dream journal the voice should be calm, intimate, ASMR-adjacent. Whisper-style TTS exists via ElevenLabs, WaveSpeedAI, and OpenAI TTS.

## Proposed Implementation

Mirror the AI provider chain pattern in `dream-chat.html`:

```js
const TTS_CHAIN = [
  { id: 'elevenlabs', envKey: 'ELEVENLABS_API_KEY', voice: 'Rachel' },
  { id: 'openai',     envKey: 'OPENAI_API_KEY',     voice: 'nova' }, // OpenAI TTS
  { id: 'browser',   envKey: null }  // always available
];
```

Server route `POST /api/dream/tts` — accepts `{text, voice_id}`, streams back audio/mpeg. Frontend plays via `new Audio(url).play()`. Falls back to browser TTS if no key set.

**ElevenLabs free tier:** 10k chars/month. Voice `Rachel` is calm, warm, ideal for Lantern.  
**OpenAI TTS:** `tts-1` model, voice `nova` — smooth, unhurried. $0.015/1k chars.

## Settings Drawer Addition
Add TTS provider card in `dream-chat.html` settings drawer:
- ElevenLabs API key input + voice selector
- OpenAI TTS toggle (uses existing OPENAI_API_KEY)
- Rate/pitch slider for browser TTS fallback

## Files to Change
- `apps/lantern-garage/routes/dream.js` — `POST /api/dream/tts`
- `apps/lantern-garage/public/dream-chat.html` — TTS provider chain + settings card
- `.env.example` — `ELEVENLABS_API_KEY`, `TTS_VOICE_ID`
- `data/pcsf/settings.pcsf.json` — add TTS keys
