"""Read-only health probe for BetterSafe private release checks.

This module probes an explicit base URL and a fixed allowlist of read-only
endpoints. It does not write, authenticate, sync, start workers, or enable
runtime features.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from time import perf_counter
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


DEFAULT_HEALTH_PATHS = (
    "/",
    "/health",
    "/healthz",
    "/api/status",
    "/api/better-next/status",
    "/api/world/status",
    "/api/adoption/stats",
    "/api/adoption/nodes",
)


@dataclass(frozen=True)
class ProbeResult:
    path: str
    ok: bool
    status_code: int | None
    latency_ms: int | None
    error: str | None = None


def _validate_base_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("base_url must be an explicit http(s) URL")
    return base_url.rstrip("/") + "/"


def _validate_path(path: str, allowed_paths: Iterable[str]) -> None:
    if path not in set(allowed_paths):
        raise ValueError(f"path is not in read-only allowlist: {path}")


def probe_endpoint(
    base_url: str,
    path: str,
    *,
    timeout_seconds: float = 2.0,
    allowed_paths: Iterable[str] = DEFAULT_HEALTH_PATHS,
) -> ProbeResult:
    """Probe one read-only endpoint and return a structured result."""
    normalized_base = _validate_base_url(base_url)
    _validate_path(path, allowed_paths)

    url = urljoin(normalized_base, path.lstrip("/"))
    request = Request(url, method="GET", headers={"User-Agent": "hff-health-probe/1"})
    start = perf_counter()

    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            status_code = getattr(response, "status", None)
            latency_ms = int((perf_counter() - start) * 1000)
            return ProbeResult(
                path=path,
                ok=200 <= int(status_code) < 400,
                status_code=int(status_code),
                latency_ms=latency_ms,
            )
    except HTTPError as exc:
        latency_ms = int((perf_counter() - start) * 1000)
        return ProbeResult(
            path=path,
            ok=False,
            status_code=exc.code,
            latency_ms=latency_ms,
            error="http_error",
        )
    except (URLError, TimeoutError, OSError) as exc:
        latency_ms = int((perf_counter() - start) * 1000)
        return ProbeResult(
            path=path,
            ok=False,
            status_code=None,
            latency_ms=latency_ms,
            error=exc.__class__.__name__,
        )


def probe_health(
    base_url: str,
    *,
    paths: Iterable[str] = DEFAULT_HEALTH_PATHS,
    timeout_seconds: float = 2.0,
) -> dict:
    """Probe the read-only health allowlist and summarize results."""
    path_tuple = tuple(paths)
    results = [
        probe_endpoint(
            base_url,
            path,
            timeout_seconds=timeout_seconds,
            allowed_paths=DEFAULT_HEALTH_PATHS,
        )
        for path in path_tuple
    ]

    ok_count = sum(1 for result in results if result.ok)
    return {
        "base_url": _validate_base_url(base_url).rstrip("/"),
        "ok": ok_count == len(results),
        "ok_count": ok_count,
        "total_count": len(results),
        "results": [asdict(result) for result in results],
        "limits": {
            "read_only": True,
            "writes": False,
            "tokens": False,
            "mesh_sync": False,
            "live_sensors": False,
            "background_worker": False,
        },
    }
