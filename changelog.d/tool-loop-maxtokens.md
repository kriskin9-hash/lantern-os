### Chat tool loop: raise per-turn token cap so multi-call answers don't truncate

- The native tool-use loop capped each model turn at 1024 tokens, so a `web_search` answer that reasoned across multiple tool calls got cut off mid-sentence ("⚠ truncated"). Raised the tool-loop cap to 4096 (Gemini + Anthropic paths) so the model has room to reason and write a complete, cited answer. Fixes #1210.
