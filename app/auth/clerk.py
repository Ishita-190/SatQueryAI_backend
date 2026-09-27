from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from app.config import Settings, get_settings

_bearer = HTTPBearer(auto_error=False)
_jwk_clients: dict[str, PyJWKClient] = {}


@dataclass(frozen=True)
class AuthUser:
    clerk_user_id: str


def _jwk_client(jwks_url: str) -> PyJWKClient:
    if jwks_url not in _jwk_clients:
        _jwk_clients[jwks_url] = PyJWKClient(jwks_url, cache_keys=True)
    return _jwk_clients[jwks_url]


def verify_clerk_token(token: str, settings: Settings) -> AuthUser:
    if not settings.clerk_jwks_url or not settings.clerk_issuer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Clerk auth is not configured on the server.",
        )
    issuer = settings.clerk_issuer.rstrip("/")
    try:
        key = _jwk_client(settings.clerk_jwks_url).get_signing_key_from_jwt(token)
        decode_kwargs: dict = {
            "algorithms": ["RS256"],
            "issuer": issuer,
            "leeway": 30,
            "options": {"verify_aud": bool(settings.clerk_audience.strip())},
        }
        if settings.clerk_audience.strip():
            decode_kwargs["audience"] = settings.clerk_audience.strip()
        payload = jwt.decode(token, key.key, **decode_kwargs)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        ) from exc

    sub = payload.get("sub")
    if not sub or not isinstance(sub, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject.",
        )
    return AuthUser(clerk_user_id=sub)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
        )
    return verify_clerk_token(credentials.credentials, settings)
