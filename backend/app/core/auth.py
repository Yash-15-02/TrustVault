"""
Optional API-key authentication.

When REQUIRE_AUTH=true, every request must include a valid
``X-API-Key`` header whose value is one of the keys listed in API_KEYS.

When REQUIRE_AUTH=false (default), auth is skipped and
the caller is labelled ``anonymous``.
"""

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import API_KEYS, REQUIRE_AUTH

_header_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: str | None = Security(_header_scheme),
) -> str:
    """
    FastAPI dependency.

    Returns the *name* associated with the key (e.g. ``"admin"``),
    or ``"anonymous"`` when auth is disabled.
    """
    if not REQUIRE_AUTH:
        return API_KEYS.get(api_key, "anonymous") if api_key else "anonymous"

    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )
    name = API_KEYS.get(api_key)
    if name is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    return name
