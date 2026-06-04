# Lantern Chat — Quick Start Guide

**Status:** ✅ Implemented and Ready  
**Real-time:** ✅ Streaming enabled  
**Local Only:** ✅ No cloud tokens required  

---

## How to Run

### Option 1: Quick Launcher (Easiest)
```bash
scripts\start-lantern-chat.bat
```
Double-click and chat starts immediately.

### Option 2: Python Direct
```bash
python scripts\lantern-desktop-auth-ui.py
```
Auth screen → Configure providers → Chat interface launches.

---

## What You Get

✅ **Real-time Chat**
- Type message → Send (Ctrl+Enter)
- Instant streaming responses from local LLM
- Word-by-word display as LLM generates text
- Timestamped messages

✅ **Local Inference Only**
- Connects to LM Studio (localhost:1234) OR Ollama (localhost:11434)
- No cloud API calls
- No token usage
- Works offline once LLM is running

✅ **Visual Features**
- Dark theme (terminal-style)
- Color-coded: User messages (green), Bot responses (cyan)
- Error messages (red)
- Message counter
- Live status bar
- Scrolling chat history

---

## Prerequisites

**Choose ONE of these:**

### LM Studio (Recommended)
```
1. Download: https://lmstudio.ai/
2. Install and launch
3. Download a model (Qwen, Llama2, etc.)
4. Start server (default: localhost:1234)
5. Run Lantern Chat
```

### Ollama
```
1. Download: https://ollama.ai/
2. Install: ollama pull llama2 (or another model)
3. Ollama runs on localhost:11434
4. Run Lantern Chat
```

---

## Using the Chat

### Sending Messages
```
Type your message in the text box
Press Ctrl+Enter OR click Send button
→ Message appears in green
→ LLM response streams in cyan, word-by-word
```

### Switching Providers (After Restart)
```
Edit scripts/lantern-chat-ui.py line 108:
  selected_provider="lm_studio"  # Change to "ollama" to switch
OR configure in auth UI before chat launches
```

### Troubleshooting

**"Cannot connect to lm_studio"**
- Is LM Studio running? (Check: `netstat -ano | findstr :1234`)
- Is a model downloaded in LM Studio?
- Did you click "Start Server"?

**"Cannot connect to ollama"**
- Is Ollama running? (Check: `netstat -ano | findstr :11434`)
- Did you pull a model? (`ollama pull llama2`)

**Chat not responding**
- Wait a few seconds (models can be slow)
- Check message in error color for details
- Try a shorter prompt first

---

## Architecture

```
Lantern Desktop
├── Auth UI (lantern-desktop-auth-ui.py)
│   └── Select provider + set primary
└── Chat UI (lantern-chat-ui.py)
    ├── Text input area
    ├── Message display (scrolled)
    └── LLM streaming client
        ├── Connects to LM Studio:1234
        └── OR Ollama:11434
            └── Streams response in real-time
```

---

## Code Structure

**Key Methods in `lantern-chat-ui.py`:**

| Method | Purpose |
|--------|---------|
| `_build_ui()` | Creates text input, display, buttons |
| `send_message()` | Takes input, displays user msg, calls LLM |
| `_get_llm_response()` | Connects to LLM endpoint, streams response |
| `_stream_response()` | Real-time word-by-word display |
| `_display_message()` | Adds timestamped message to chat |

**Real-time Features:**
- Threading: LLM calls don't block UI (`threading.Thread`)
- Streaming: `response.iter_lines()` for real-time tokens
- Display: `root.update()` after each word for instant feedback

---

## Performance Notes

- **Latency:** Depends on LLM model size
  - Fast: Qwen 7B (~2 sec for 50 tokens)
  - Medium: Llama2 13B (~5 sec)
  - Slow: Larger models on CPU (~10+ sec)

- **Streaming:** Word-by-word display means you see response immediately
  - No wait for full response
  - Natural reading experience

- **Memory:** Python + Tkinter + requests ~50-100MB idle

---

## Future Enhancements

```
[ ] Save chat history to disk
[ ] Export conversation as JSON
[ ] Provider switching mid-chat
[ ] Custom system prompts
[ ] Model temperature / token controls
[ ] Voice input (Vosk STT)
[ ] Voice output (TTS)
[ ] Multi-file context (RAG)
```

---

## Architecture Decisions

**Why streaming?**
- Immediate feedback (don't wait for full response)
- Better UX on slow hardware
- Shows that system is working

**Why local only?**
- No API keys needed
- Works offline
- No rate limits
- Privacy preserved

**Why Tkinter?**
- No dependencies (built-in Python)
- Simple, lightweight
- Works on Windows/Mac/Linux

---

**Ready to chat. Start with `scripts/start-lantern-chat.bat`** 🚀
