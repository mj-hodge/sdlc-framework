"""
Authentication utilities: password hashing (pwdlib + argon2) and JWT tokens (PyJWT).

pwdlib replaces the abandoned passlib library.
PyJWT replaces the abandoned python-jose library.
argon2 is the OWASP-recommended hashing algorithm.
"""

from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

from app.core.config import settings
from app.core.exceptions import AuthenticationError

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.InvalidTokenError as e:
        raise AuthenticationError("Invalid or expired token") from e


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Dependency that extracts and validates the current user from a JWT token.

    TODO: Implement user lookup from database:
        payload = verify_token(token)
        user_id = payload.get("sub")
        user = await user_repo.get(user_id)
        if user is None:
            raise AuthenticationError("User not found")
        return user
    """
    payload = verify_token(token)
    return payload
