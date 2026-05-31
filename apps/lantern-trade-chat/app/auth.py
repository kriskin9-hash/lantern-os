"""GitHub OAuth + session helpers.

Access is restricted to an allowlist of GitHub usernames (founder + Courtney).
A logged-in user not on the allowlist is rejected. All trading endpoints depend
on `require_user`, so an unauthenticated request can never reach the order path.
"""
from __future__ import annotations

from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, Request, status

from .config import Settings

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_BASE = "https://api.github.com/"


def build_oauth(settings: Settings) -> OAuth:
    oauth = OAuth()
    oauth.register(
        name="github",
        client_id=settings.github_client_id,
        client_secret=settings.github_client_secret,
        access_token_url=GITHUB_TOKEN_URL,
        authorize_url=GITHUB_AUTHORIZE_URL,
        api_base_url=GITHUB_API_BASE,
        client_kwargs={"scope": "read:user"},
    )
    return oauth


def current_user(request: Request) -> dict | None:
    return request.session.get("user")


def require_user(request: Request) -> dict:
    user = current_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required.")
    return user
