"""Safety + auth invariants for the Lantern trading chat app."""
from __future__ import annotations

import base64
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from fastapi.testclient import TestClient

from app import auth, chat, main
from app.config import Settings
from app.kalshi import load_private_key, sign
from app.safety import OrderPlan, evaluate_gates


# --------------------------------------------------------------------------- #
# chat parsing
# --------------------------------------------------------------------------- #
def test_parse_order_basic():
    intent = chat.parse("buy 1 yes on KXBTC at 40c")
    assert intent.kind == "order"
    assert intent.plan.ticker == "KXBTC"
    assert intent.plan.side == "yes" and intent.plan.action == "buy"
    assert intent.plan.count == 1 and intent.plan.limit_cents == 40
    assert intent.live is False


def test_parse_live_flag_and_dryrun_override():
    assert chat.parse("live buy 2 no FED-25 limit 12").live is True
    assert chat.parse("dry run live buy 1 yes T at 5c").live is False


def test_parse_balance_help_unknown():
    assert chat.parse("balance").kind == "balance"
    assert chat.parse("help").kind == "help"
    assert chat.parse("hello there").kind == "unknown"


def test_parse_rejects_out_of_range_limit():
    assert chat.parse("buy 1 yes T at 150c").kind == "unknown"


# --------------------------------------------------------------------------- #
# safety gates
# --------------------------------------------------------------------------- #
def _settings(**kw) -> Settings:
    base = dict(
        allowed_logins=frozenset({"alex-place"}),
        environment="demo",
        api_key_id="id",
        private_key_pem="pem",
        live_enabled=True,
        max_per_order_usd=40.0,
        max_daily_loss_usd=40.0,
        max_trades_per_day=1,
        kill_switch_path=Path("/nonexistent/KILL"),
        ledger_path=Path("/nonexistent/ledger.jsonl"),
    )
    base.update(kw)
    return Settings(**base)


def test_live_disabled_blocks():
    s = _settings(live_enabled=False)
    blockers = evaluate_gates(s, OrderPlan("T", "yes", "buy", 1, 10), balance_usd=100)
    assert any("disabled" in b for b in blockers)


def test_kill_switch_blocks(tmp_path):
    kill = tmp_path / "KILL"
    kill.write_text("armed")
    s = _settings(kill_switch_path=kill)
    blockers = evaluate_gates(s, OrderPlan("T", "yes", "buy", 1, 10), balance_usd=100)
    assert any("Kill switch" in b for b in blockers)


def test_per_order_cap_blocks():
    s = _settings(max_per_order_usd=5.0)
    # 20 contracts @ 40c = $8.00 cost > $5 cap
    blockers = evaluate_gates(s, OrderPlan("T", "yes", "buy", 20, 40), balance_usd=100)
    assert any("Per-order cap" in b for b in blockers)


def test_insufficient_balance_blocks():
    s = _settings()
    blockers = evaluate_gates(s, OrderPlan("T", "yes", "buy", 1, 40), balance_usd=0.10)
    assert any("Insufficient balance" in b for b in blockers)


def test_clean_order_has_no_blockers():
    s = _settings()
    blockers = evaluate_gates(s, OrderPlan("T", "yes", "buy", 1, 10), balance_usd=100)
    assert blockers == []


# --------------------------------------------------------------------------- #
# key loading + signing
# --------------------------------------------------------------------------- #
def test_load_key_pem_and_headerless_and_sign():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    # well-formed PEM
    assert load_private_key(pem).key_size == 2048
    # header-less / whitespace-flattened base64 (Devin secret normalization)
    body = pem.replace("-----BEGIN PRIVATE KEY-----", "").replace("-----END PRIVATE KEY-----", "")
    flat = " ".join(body.split())
    loaded = load_private_key(flat)
    # signature round-trips against the public key
    msg = "1700000000000GET/trade-api/v2/portfolio/balance"
    sig = base64.b64decode(sign(loaded, msg))
    loaded.public_key().verify(
        sig, msg.encode(),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
        hashes.SHA256(),
    )


# --------------------------------------------------------------------------- #
# API auth gating
# --------------------------------------------------------------------------- #
@pytest.fixture
def client():
    return TestClient(main.app)


def test_health_is_public(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_protected_endpoints_require_login(client):
    assert client.get("/api/balance").status_code == 401
    assert client.post("/api/chat", json={"message": "balance"}).status_code == 401
    assert client.post("/api/order", json={"ticker": "T", "side": "yes", "count": 1, "limitCents": 10}).status_code == 401


def test_non_allowlisted_user_rejected(monkeypatch):
    # is_allowed must reject a login not in the allowlist
    s = _settings()
    assert s.is_allowed("alex-place") is True
    assert s.is_allowed("random-user") is False
    assert s.is_allowed(None) is False


def test_dry_run_when_authed(client, tmp_path, monkeypatch):
    monkeypatch.setattr(main, "settings", _settings(api_key_id="", private_key_pem="", ledger_path=tmp_path / "l.jsonl"))
    main.app.dependency_overrides[auth.require_user] = lambda: {"login": "alex-place"}
    try:
        r = client.post("/api/order", json={"ticker": "T", "side": "yes", "count": 1, "limitCents": 1, "live": False})
        assert r.status_code == 200
        assert r.json()["status"] == "dry_run"
        assert (tmp_path / "l.jsonl").exists()
    finally:
        main.app.dependency_overrides.clear()
