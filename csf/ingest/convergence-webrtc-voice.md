# CSF Ingestion — WebRTC Voice Streaming to Local Ollama

**Status:** queued — future, high impact  
**Priority:** 4  
**Effort:** 8–12 hours  
**Source:** [On-Premise Voice AI with Ollama + Pipecat](https://webrtc.ventures/2025/03/on-premise-voice-ai-creating-local-agents-with-llama-ollama-and-pipecat/)

## Problem

Current voice uses Web Speech API (browser TTS/STT) — quality varies, no streaming, no local model integration. When `lantern-dream-v1` LoRA model runs in Ollama, voice should stream through WebRTC P2P with sub-100ms latency.

## Architecture

```
Browser (microphone) → WebRTC → Pipecat → Ollama (lantern-dream-v1) → Pipecat → WebRTC → Browser (speaker)
```

### Components
- **Pipecat** — media framework for AI agents, handles WebRTC ↔ Ollama bridge
- **FastRTC** — lightweight WebRTC server for local AI
- **Ollama** — local model serving (llama3.2 or fine-tuned lantern-dream-v1)

### Why WebRTC
- P2P: browser connects directly to local Ollama, no cloud relay
- Sub-100ms latency: real-time voice conversation
- Zero cloud cost: all processing local
- NAT traversal handled by WebRTC ICE framework

## Files to Create
- `services/voice-bridge/server.py` — Pipecat + FastRTC bridge
- `apps/lantern-garage/public/dream-chat.html` — WebRTC voice mode toggle
- `requirements.txt` — add pipecat, fastrtc dependencies
- `.env.example` — VOICE_BRIDGE_PORT

## Hardware Requirements
- Ollama running with llama3.2:3b (4GB RAM minimum)
- Microphone + speaker (standard on laptops/phones)
- No GPU required for 3B model on CPU
