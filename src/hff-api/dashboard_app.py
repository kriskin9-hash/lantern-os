"""Railway compatibility entrypoint for Human Flourishing Frameworks.

Railway service logs showed the production container trying to start:

    python /app/dashboard_app.py

The repo's safe public WSGI entrypoint is currently ``safe_app.py``. This shim
keeps the Railway-configured filename working without changing public-write,
sensor, mesh-sync, agent, database, secret, SDK/APK, or actuator behavior.

Preferred production WSGI target remains:

    gunicorn safe_app:app --bind 0.0.0.0:$PORT --log-file -

This module exists only so a stale Railway start command can boot the same safe
Flask app until the service setting is corrected.
"""

from __future__ import annotations

import os

from safe_app import app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
