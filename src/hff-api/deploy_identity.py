"""Deployment identity helpers.

This module exposes explicit, non-secret deployment identity from environment
variables and known repo constants so live smoke tests can prove which code path
is running.
"""

from __future__ import annotations

import os
from typing import Any

APP_VERSION = "deploy-identity-v1"


def deployment_identity() -> dict[str, Any]:
    """Return non-secret deployment identity for live smoke tests."""
    return {
        "service": "human-flourishing-frameworks",
        "app_version": APP_VERSION,
        "expected_entrypoint": "safe_app:app",
        "git_commit": os.environ.get("RAILWAY_GIT_COMMIT_SHA")
        or os.environ.get("GIT_COMMIT")
        or os.environ.get("COMMIT_SHA")
        or "unknown",
        "git_branch": os.environ.get("RAILWAY_GIT_BRANCH")
        or os.environ.get("GIT_BRANCH")
        or "unknown",
        "railway_service_name": os.environ.get("RAILWAY_SERVICE_NAME", "unknown"),
        "railway_environment_name": os.environ.get("RAILWAY_ENVIRONMENT_NAME", "unknown"),
        "background_status_route": "/background/status",
        "health_route": "/healthz",
    }
