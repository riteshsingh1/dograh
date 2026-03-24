from typing import Any, Optional

import httpx


GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


async def resolve_google_access_token(
    source_auth: Optional[dict[str, Any]] = None,
) -> Optional[str]:
    """Resolve a usable Google access token from campaign/source auth config.

    Supported modes:
    - access_token (direct token)
    - oauth_refresh_token (refresh token exchange)
    """
    source_auth = source_auth or {}

    auth_type = (source_auth.get("auth_type") or "").strip().lower()
    access_token = (source_auth.get("access_token") or "").strip()
    if auth_type in ("", "access_token") and access_token:
        return access_token

    if auth_type == "oauth_refresh_token":
        refresh_token = (source_auth.get("refresh_token") or "").strip()
        client_id = (source_auth.get("client_id") or "").strip()
        client_secret = (source_auth.get("client_secret") or "").strip()
        token_url = (source_auth.get("token_uri") or GOOGLE_TOKEN_URL).strip()

        if not refresh_token or not client_id or not client_secret:
            return None

        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(token_url, data=data)
            response.raise_for_status()
            payload = response.json()
            token = (payload.get("access_token") or "").strip()
            return token or None

    return access_token or None
