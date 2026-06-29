"""
1st 4 Mobile — Google OAuth Routes

One-click login via Google. Three roles determined by email:
  - barry@1st4.mobi -> owner (full dashboard)
  - @1st4.mobi -> staff (limited view)
  - any other email -> client (their portal)

Requires GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET env vars.
"""
from __future__ import annotations

import logging
import os
import secrets
import time

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

logger = logging.getLogger("1st4backend.oauth")

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Google OAuth config
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
REDIRECT_URI = os.environ.get(
    "REDIRECT_URI", "https://www.1st4.mobi/api/auth/google/callback"
)

# Owner whitelist
OWNER_EMAILS = {
    "barry@1st4.mobi",
    os.environ.get("OWNER_EMAIL", "").lower(),
}

# Session store (simple dict; use Redis in production)
_sessions: dict[str, dict] = {}
SESSION_DURATION = 30 * 24 * 3600  # 30 days


def _get_role(email: str) -> str:
    email_lower = email.lower()
    if email_lower in OWNER_EMAILS:
        return "owner"
    return "client"


def _get_redirect(role: str) -> str:
    if role == "owner":
        return "/owner"
    return "/portal"


@router.get("/login")
async def login():
    """Redirect user to Google's OAuth consent screen."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")

    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(16)

    # Store state temporarily to verify on callback
    _sessions["oauth_state"] = {"state": state, "nonce": nonce, "created": time.time()}

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "nonce": nonce,
    }
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{qs}")


@router.get("/google/callback")
async def callback(request: Request):
    """Handle the OAuth callback from Google."""
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")

    if error:
        return HTMLResponse(
            content=f"<h1>Login failed</h1><p>Google returned: {error}</p>",
            status_code=400,
        )

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    # Verify state
    stored = _sessions.pop("oauth_state", None)
    if not stored or stored["state"] != state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        token_data = token_resp.json()

        if "id_token" not in token_data:
            raise HTTPException(status_code=400, detail="Failed to get ID token")

        # Get user info
        user_resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        user = user_resp.json()

    email = user.get("email", "")
    name = user.get("name", email.split("@")[0])
    picture = user.get("picture", "")
    role = _get_role(email)

    # Create session token
    session_token = secrets.token_urlsafe(32)
    _sessions[session_token] = {
        "email": email,
        "name": name,
        "picture": picture,
        "role": role,
        "created": time.time(),
    }

    # Set cookie and redirect
    redirect = _get_redirect(role)
    response = RedirectResponse(url=redirect)
    response.set_cookie(
        key="session",
        value=session_token,
        max_age=SESSION_DURATION,
        httponly=True,
        secure=True,
        samesite="lax",
    )
    return response


@router.get("/session")
async def get_session(request: Request):
    """Return current session info."""
    token = request.cookies.get("session")
    if not token or token not in _sessions:
        return {"authenticated": False}

    session = _sessions[token]
    return {
        "authenticated": True,
        "email": session["email"],
        "name": session["name"],
        "picture": session["picture"],
        "role": session["role"],
    }


@router.post("/logout")
async def logout():
    """Clear session."""
    response = RedirectResponse(url="/")
    response.delete_cookie("session")
    return response
