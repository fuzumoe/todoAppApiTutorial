from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import bcrypt
import jwt

from app.core.config import settings


def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt()
    hashed: bytes = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        result: bool = bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
        return result
    except Exception:
        return False


def create_access_token(
    subject: str,
    *,
    roles: Sequence[str] | None = None,
    expires_delta: timedelta | None = None,
    extra_claims: Mapping[str, Any] | None = None,
) -> str:
    now = datetime.now(UTC)
    expire = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.security_access_token_expire_minutes)
    )

    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if roles:
        payload["roles"] = list(roles)
    if extra_claims:
        payload.update(dict(extra_claims))

    token: str = jwt.encode(
        payload,
        settings.security_secret_key,
        algorithm=settings.security_jwt_algorithm,
    )
    # In PyJWT>=2, encode returns a str
    return token


def decode_access_token(token: str) -> dict[str, Any]:
    decoded = jwt.decode(
        token,
        settings.security_secret_key,
        algorithms=[settings.security_jwt_algorithm],
        options={"verify_signature": True, "verify_exp": True},
    )
    # Ensure expected types
    if "roles" in decoded and not isinstance(decoded["roles"], list):
        decoded["roles"] = [decoded["roles"]]
    return cast(dict[str, Any], decoded)
