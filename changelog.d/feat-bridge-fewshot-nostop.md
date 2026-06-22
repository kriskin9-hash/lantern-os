feat(bridge): forced-positive few-shot + OURO_NO_STOP=1 startup check

- `_render_tools()`: appends a concrete CALL example (using first tool's
  name + required args) and a NO-CALL example after the tool listing.
  Highest-leverage prompt fix for positive-trigger failure without tool_choice.
- `_check_upstream()`: probes upstream on bridge startup, warns if unreachable,
  and reminds operator to set OURO_NO_STOP=1 on ouro_serve (stop-strings
  \n\n\n / \n``` can truncate <tool_call> JSON before the closing tag).
