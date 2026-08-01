"""Verifies Supabase-issued session tokens for protected endpoints.

Rather than re-implementing Supabase's JWT verification (which differs by
project — HS256 shared secret on older projects, JWKS/asymmetric on newer
ones), this delegates verification to Supabase itself by calling its own
GoTrue ``/auth/v1/user`` endpoint with the caller's bearer token. That's one
extra network round trip per request, which is an acceptable trade for
correctness and zero new secrets to manage — fine for this stage of the
project; a future optimization could cache/verify locally if latency ever
matters.
"""

from __future__ import annotations

import uuid

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.config import settings

_bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    """The identity Supabase reports for a verified session token."""

    id: uuid.UUID
    email: str | None = None
    full_name: str | None = None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> CurrentUser:
    """FastAPI dependency: raises 401 unless the request carries a valid
    Supabase session token, otherwise returns the identity it belongs to."""
    if credentials is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Missing bearer token."
        )
    project_url = settings.supabase_project_url
    if not project_url or not settings.SUPABASE_ANON_KEY:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Supabase auth is not configured on the server "
            "(SUPABASE_URL / SUPABASE_ANON_KEY missing).",
        )

    url = f"{project_url}/auth/v1/user"
    headers = {
        "Authorization": f"Bearer {credentials.credentials}",
        "apikey": settings.SUPABASE_ANON_KEY,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Could not reach Supabase to verify the session.",
        ) from exc

    if response.status_code != 200:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Invalid or expired session."
        )

    data = response.json()
    metadata = data.get("user_metadata") or {}
    return CurrentUser(
        id=uuid.UUID(data["id"]),
        email=data.get("email"),
        full_name=metadata.get("full_name") or metadata.get("name"),
    )
