from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from core.config import settings
from database.connection import get_db
from database.models import User, Workspace

hasher = PasswordHasher()
oauth = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password) -> str:
    """Hash a password using Argon2."""

    return hasher.hash(password)


def verify_password(password, stored_hash) -> bool:
    """Verify a password without exposing the stored hash."""

    try:

        return hasher.verify(stored_hash, password)

    except (VerificationError, InvalidHashError):

        return False


def create_token(user_id) -> str:
    """Create a signed, short-lived access token."""

    return jwt.encode(
        {"sub": str(user_id), "exp": datetime.now(timezone.utc) + timedelta(hours=2)},
        settings.secret_key,
        algorithm="HS256",
    )


def current_workspace(token: Annotated[str, Depends(oauth)], db: Annotated[Session, Depends(get_db)]) -> Workspace:
    """Resolve the workspace from authenticated identity, never request data."""

    try:

        user_id = int(jwt.decode(token, settings.secret_key, algorithms=["HS256"])["sub"])

    except (jwt.PyJWTError, ValueError, KeyError):

        raise HTTPException(401, "Please sign in again")

    workspace = db.query(Workspace).filter_by(owner_id=user_id).first()

    if not workspace or not db.get(User, user_id):

        raise HTTPException(401, "Account unavailable")

    return workspace


DB = Annotated[Session, Depends(get_db)]
Tenant = Annotated[Workspace, Depends(current_workspace)]
