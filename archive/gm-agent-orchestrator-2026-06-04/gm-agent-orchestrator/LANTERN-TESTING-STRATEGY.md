# Lantern Desktop Testing Strategy

**Status:** Active  
**Last Updated:** 2026-05-25  
**Test Coverage Target:** 85%+  

---

## Test Categories

### 1. **Startup & Initialization**
- [ ] App launches without errors
- [ ] LM Studio auto-start logic executes
- [ ] Ollama auto-start logic executes
- [ ] Port detection works (1234, 11434)
- [ ] "Starting LLM services..." splash shows
- [ ] Auth UI appears after services initialize
- [ ] Grace period works (10 second timeout)

### 2. **Provider Authentication**
- [ ] Claude provider form shows API key field
- [ ] Gemini provider form shows API key field
- [ ] DeepSeek provider form shows API key field
- [ ] LM Studio form shows host/port fields (not API key)
- [ ] Ollama form shows host/port fields (not API key)
- [ ] API keys can be entered and saved
- [ ] Saved credentials persist in `~/.lantern/credentials/`
- [ ] Credentials are not visible in plaintext in UI

### 3. **Provider Selection & Status**
- [ ] Provider buttons show correct status (✅ Configured or ⭕ Not configured)
- [ ] DeepSeek button is clickable (KNOWN FIX: expanded layout)
- [ ] Only one provider can be set as primary
- [ ] Fallback provider can be set independently
- [ ] Provider selection updates config file

### 4. **Local LLM Integration**
- [ ] LM Studio accessible on localhost:1234
- [ ] Ollama accessible on localhost:11434
- [ ] Port detection doesn't hang app
- [ ] Services start in background (non-blocking)
- [ ] App continues if services unavailable
- [ ] Graceful fallback to cloud APIs

### 5. **Config File Integrity**
- [ ] `llm-configurations.json` loads without errors
- [ ] `providers.json` saves/loads correctly
- [ ] Credentials directory created with proper permissions
- [ ] File timestamps update on auth changes
- [ ] No file corruption on rapid updates

### 6. **UI/UX**
- [ ] Window resizable and responsive
- [ ] All buttons clickable and respond
- [ ] Form fields accept input
- [ ] Text is readable (font size, contrast)
- [ ] No console errors in Python execution
- [ ] Error messages are user-friendly

### 7. **Error Handling**
- [ ] Missing API keys show validation error
- [ ] Invalid API keys handled gracefully
- [ ] Network errors don't crash app
- [ ] Port conflicts handled (service already running)
- [ ] Disk write failures (credentials) reported

### 8. **Performance**
- [ ] Auth UI appears within 2 seconds of launch
- [ ] No memory leaks after 5 minutes of use
- [ ] CPU usage <5% idle
- [ ] Subprocess cleanup (no orphaned processes)

### 9. **Integration**
- [ ] Lantern Desktop → LM Studio communication works
- [ ] Lantern Desktop → Ollama communication works
- [ ] Cloud API keys work (Claude, Gemini, DeepSeek)
- [ ] Fallback routing works (primary unavailable → fallback)

---

## Test Execution Log

### Iteration 1: [TIMESTAMP]
- **Tests Run:** []
- **Passed:** []
- **Failed:** []
- **Issues Found:** []
- **Fixes Applied:** []

