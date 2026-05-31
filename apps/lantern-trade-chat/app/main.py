"""Lantern OS trading chat app — OAuth-gated Kalshi order desk.

Founder + Courtney only (GitHub username allowlist). Live trading is OFF unless
the deployment explicitly arms it; every order still passes the kill switch and
risk caps. The public/demo deployment runs without LANTERN_LIVE_ENABLED, so it
previews orders (dry-run) and shows balance but never spends real money.
"""
from __future__ import annotations

import secrets
from pathlib import Path

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from . import auth, chat
from .config import Settings, load_settings
from .kalshi import KalshiClient
from .safety import OrderPlan, append_ledger, evaluate_gates, kill_switch_active, today_summary

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

settings: Settings = load_settings()
oauth = auth.build_oauth(settings)

app = FastAPI(title="Lantern Trade Chat", version="0.1.0")
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret or secrets.token_urlsafe(32),
    same_site="lax",
    https_only=False,
)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _kalshi_client() -> KalshiClient | None:
    if not settings.has_credentials:
        return None
    try:
        return KalshiClient(
            base_url=settings.base_url,
            api_key_id=settings.api_key_id,
            private_key_pem=settings.private_key_pem,
        )
    except ValueError:
        return None


def _balance_usd(client: KalshiClient | None) -> float | None:
    if client is None:
        return None
    try:
        data = client.get_balance()
    except (httpx.HTTPError, ValueError):
        return None
    cents = data.get("balance")
    if cents is None:
        return None
    return round(float(cents) / 100.0, 2)


# --------------------------------------------------------------------------- #
# Auth routes
# --------------------------------------------------------------------------- #
@app.get("/login")
async def login(request: Request):
    if not settings.oauth_configured:
        raise HTTPException(status_code=503, detail="OAuth is not configured on this deployment.")
    redirect_uri = request.url_for("auth_callback")
    return await oauth.github.authorize_redirect(request, redirect_uri)


@app.get("/auth/callback", name="auth_callback")
async def auth_callback(request: Request):
    token = await oauth.github.authorize_access_token(request)
    resp = await oauth.github.get("user", token=token)
    profile = resp.json()
    login_name = (profile.get("login") or "").strip()
    if not settings.is_allowed(login_name):
        request.session.clear()
        return HTMLResponse(
            f"<h1>Access denied</h1><p><code>{login_name or 'unknown'}</code> is not on the allowlist.</p>"
            "<p><a href='/'>Back</a></p>",
            status_code=403,
        )
    request.session["user"] = {
        "login": login_name,
        "name": profile.get("name") or login_name,
        "avatar": profile.get("avatar_url"),
    }
    return RedirectResponse(url="/")


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")


# --------------------------------------------------------------------------- #
# API routes
# --------------------------------------------------------------------------- #
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "environment": settings.environment,
        "liveEnabled": settings.live_enabled,
        "killSwitchActive": kill_switch_active(settings),
        "credentialsConfigured": settings.has_credentials,
        "oauthConfigured": settings.oauth_configured,
    }


@app.get("/api/me")
async def me(request: Request):
    user = auth.current_user(request)
    return {"authenticated": bool(user), "user": user}


@app.get("/api/balance")
async def balance(user: dict = Depends(auth.require_user)):
    client = _kalshi_client()
    if client is None:
        raise HTTPException(status_code=503, detail="No Kalshi credentials configured.")
    bal = _balance_usd(client)
    if bal is None:
        raise HTTPException(status_code=502, detail="Could not read Kalshi balance.")
    trades_today, risk_today = today_summary(settings)
    return {
        "balanceUsd": bal,
        "environment": settings.environment,
        "tradesToday": trades_today,
        "riskTodayUsd": risk_today,
        "caps": {
            "maxPerOrderUsd": settings.max_per_order_usd,
            "maxDailyLossUsd": settings.max_daily_loss_usd,
            "maxTradesPerDay": settings.max_trades_per_day,
        },
    }


@app.get("/api/status")
async def trading_status(user: dict = Depends(auth.require_user)):
    """Read-only account status: connectivity, orders, positions, fills, settlement warnings."""
    client = _kalshi_client()
    if client is None:
        raise HTTPException(status_code=503, detail="No Kalshi credentials configured.")
    result: dict = {"environment": settings.environment, "credentialsOk": True}
    errors: list[str] = []

    for key, fn, kwargs in [
        ("balance",     lambda: client.get_balance(),        {}),
        ("openOrders",  lambda: client.get_orders("resting"), {}),
        ("positions",   lambda: client.get_positions(),       {}),
        ("recentFills", lambda: client.get_fills(),           {}),
        ("settlements", lambda: client.get_settlements(),     {}),
    ]:
        try:
            result[key] = fn()
        except Exception as exc:  # noqa: BLE001
            result[key] = None
            errors.append(f"{key}: {exc}")

    result["errors"] = errors
    result["settlementWarnings"] = _settlement_warnings(result.get("settlements"))
    return result


def _settlement_warnings(settlements: dict | None) -> list[str]:
    if not settlements:
        return []
    warnings: list[str] = []
    for s in (settlements.get("settlements") or []):
        status = (s.get("status") or "").lower()
        if status in {"voided", "disputed", "pending"}:
            warnings.append(
                f"{s.get('market_result_ticker', '?')} — {status} — "
                f"${round(float(s.get('revenue', 0)) / 100, 2)}"
            )
    return warnings


@app.post("/api/chat")
async def chat_endpoint(request: Request, user: dict = Depends(auth.require_user)):
    body = await request.json()
    intent = chat.parse(str(body.get("message", "")))

    if intent.kind == "help":
        return {"reply": _help_text(), "intent": "help"}
    if intent.kind == "balance":
        client = _kalshi_client()
        bal = _balance_usd(client)
        if bal is None:
            return {"reply": "Balance unavailable (no credentials or upstream error).", "intent": "balance"}
        return {"reply": f"Balance: ${bal:.2f} ({settings.environment}).", "intent": "balance", "balanceUsd": bal}
    if intent.kind != "order" or intent.plan is None:
        return {"reply": intent.message, "intent": "unknown"}

    plan = intent.plan
    client = _kalshi_client()
    bal = _balance_usd(client)
    blockers = evaluate_gates(settings, plan, bal)
    plan_text = (
        f"{plan.action.upper()} {plan.count} {plan.side.upper()} {plan.ticker} "
        f"@ {plan.limit_cents}c  (cost/risk ${plan.cost_usd:.2f}, {settings.environment})"
    )
    return {
        "intent": "order",
        "plan": {
            "ticker": plan.ticker, "side": plan.side, "action": plan.action,
            "count": plan.count, "limitCents": plan.limit_cents, "costUsd": plan.cost_usd,
        },
        "live": intent.live,
        "blockers": blockers,
        "reply": (
            f"Order plan: {plan_text}.\n"
            + ("Add 'live' to place real money. " if not intent.live else "")
            + ("BLOCKED: " + "; ".join(blockers) if blockers else "Ready to submit.")
        ),
    }


@app.post("/api/order")
async def order(request: Request, user: dict = Depends(auth.require_user)):
    body = await request.json()
    try:
        plan = OrderPlan(
            ticker=str(body["ticker"]).upper(),
            side=str(body["side"]).lower(),
            action=str(body.get("action", "buy")).lower(),
            count=int(body["count"]),
            limit_cents=int(body["limitCents"]),
        )
    except (KeyError, ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid order payload.")

    live = bool(body.get("live", False))
    client = _kalshi_client()
    bal = _balance_usd(client)
    blockers = evaluate_gates(settings, plan, bal)

    if not live:
        append_ledger(settings, "dry_run", plan, actor=user["login"])
        return {"status": "dry_run", "plan_cost_usd": plan.cost_usd, "blockers": blockers}

    if blockers:
        return JSONResponse(status_code=409, content={"status": "blocked", "blockers": blockers})
    if client is None:
        raise HTTPException(status_code=503, detail="No Kalshi credentials configured.")

    try:
        result = client.create_order(
            ticker=plan.ticker, side=plan.side, action=plan.action,
            count=plan.count, limit_cents=plan.limit_cents, order_type=plan.order_type,
        )
    except (httpx.HTTPError, ValueError) as err:
        return JSONResponse(status_code=502, content={"status": "error", "detail": str(err)})

    append_ledger(settings, "live_order_submitted", plan, actor=user["login"], extra={"response": result})
    return {"status": "submitted", "plan_cost_usd": plan.cost_usd, "response": result}


def _help_text() -> str:
    return (
        "Commands:\n"
        "  buy 1 yes on TICKER at 40c   — preview an order (dry-run)\n"
        "  live buy 1 yes on TICKER at 40c — place real money (if armed)\n"
        "  balance — show account balance\n"
        f"Caps: ${settings.max_per_order_usd:.0f}/order, ${settings.max_daily_loss_usd:.0f}/day, "
        f"{settings.max_trades_per_day} trade(s)/day. Environment: {settings.environment}."
    )


@app.get("/", response_class=HTMLResponse)
async def index():
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")
