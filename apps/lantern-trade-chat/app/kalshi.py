"""Authenticated Kalshi REST client (Python port of Invoke-KalshiLiveOrder.ps1).

Auth scheme (Kalshi trade-api/v2):
    signature = base64(RSA-PSS-SHA256(timestamp_ms + METHOD + request_path))
sent as three headers:
    KALSHI-ACCESS-KEY, KALSHI-ACCESS-TIMESTAMP, KALSHI-ACCESS-SIGNATURE
"""
from __future__ import annotations

import base64
import time
import uuid
from dataclasses import dataclass
from urllib.parse import urlsplit

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


def load_private_key(pem_text: str) -> rsa.RSAPrivateKey:
    """Load an RSA private key from PEM, or a header-less / whitespace-flattened
    base64 blob (the Devin secret store may normalize formatting)."""
    raw = (pem_text or "").strip()
    if not raw:
        raise ValueError("No private key provided (set KALSHI_PRIVATE_KEY).")
    candidates = [raw]
    if "-----BEGIN" not in raw:
        b64 = "".join(raw.split())
        wrapped = "\n".join(b64[i : i + 64] for i in range(0, len(b64), 64))
        candidates.append(f"-----BEGIN PRIVATE KEY-----\n{wrapped}\n-----END PRIVATE KEY-----\n")
        candidates.append(f"-----BEGIN RSA PRIVATE KEY-----\n{wrapped}\n-----END RSA PRIVATE KEY-----\n")
    last_err: Exception | None = None
    for candidate in candidates:
        try:
            key = serialization.load_pem_private_key(candidate.encode("utf-8"), password=None)
            if isinstance(key, rsa.RSAPrivateKey):
                return key
        except Exception as err:  # noqa: BLE001 - try next candidate
            last_err = err
    raise ValueError(f"KALSHI_PRIVATE_KEY could not be parsed as an RSA private key: {last_err}")


def sign(key: rsa.RSAPrivateKey, message: str) -> str:
    signature = key.sign(
        message.encode("utf-8"),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode("ascii")


@dataclass
class KalshiClient:
    base_url: str
    api_key_id: str
    private_key_pem: str
    timeout: float = 20.0

    def __post_init__(self) -> None:
        self._key = load_private_key(self.private_key_pem)

    def _headers(self, method: str, path: str) -> dict[str, str]:
        ts = str(int(time.time() * 1000))
        signature = sign(self._key, ts + method.upper() + path)
        return {
            "KALSHI-ACCESS-KEY": self.api_key_id,
            "KALSHI-ACCESS-TIMESTAMP": ts,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, json_body: dict | None = None) -> dict:
        url = self.base_url + path
        sign_path = urlsplit(url).path
        headers = self._headers(method, sign_path)
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.request(method, url, headers=headers, json=json_body)
        resp.raise_for_status()
        return resp.json()

    def get_balance(self) -> dict:
        """Read-only account balance. Returns {'balance': cents}."""
        return self._request("GET", "/trade-api/v2/portfolio/balance")

    def get_orders(self, status: str = "resting", limit: int = 20) -> dict:
        """Open/resting orders. status: resting | all | canceled | executed."""
        return self._request("GET", f"/trade-api/v2/portfolio/orders?status={status}&limit={limit}")

    def get_positions(self, limit: int = 50) -> dict:
        """Current open positions."""
        return self._request("GET", f"/trade-api/v2/portfolio/positions?limit={limit}")

    def get_fills(self, limit: int = 20) -> dict:
        """Recent fills (executed trades)."""
        return self._request("GET", f"/trade-api/v2/portfolio/fills?limit={limit}")

    def get_settlements(self, limit: int = 20) -> dict:
        """Recent settlement history — includes held/disputed markets."""
        return self._request("GET", f"/trade-api/v2/portfolio/settlements?limit={limit}")

    def create_order(
        self,
        *,
        ticker: str,
        side: str,
        action: str,
        count: int,
        limit_cents: int,
        order_type: str = "limit",
    ) -> dict:
        body: dict = {
            "ticker": ticker,
            "client_order_id": str(uuid.uuid4()),
            "side": side,
            "action": action,
            "count": count,
            "type": order_type,
        }
        if order_type == "limit":
            if side == "yes":
                body["yes_price"] = limit_cents
            else:
                body["no_price"] = limit_cents
        return self._request("POST", "/trade-api/v2/portfolio/orders", json_body=body)
