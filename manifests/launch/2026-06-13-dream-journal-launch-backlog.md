## Dream Journal Saturday Index Slimming

Decision:
Production index is Dream Journal-only by default. Full panel index is dev/override only.

Flag:
- 4177 default: slim
- 4178 default: full
- ?full=1: full
- ?full=0: slim

Files changed:
- apps/lantern-garage/public/index.html

Validation:
- 4177 slim: [x] verified (server already running on 4177)
- 4177 ?full=1: [ ] verified (manual check needed)
- 4177 ?full=0: [ ] verified (manual check needed)
- 4178 full if available: [ ] N/A (dual-server not running)
- Open Journal CTA: [x] verified (routes to /dream-chat.html)
- validate: [x] verified (12/12 API endpoints passed)
- API tests: [x] verified (18/18 passed)
- multiturn tests: [x] verified (11/11 passed)
