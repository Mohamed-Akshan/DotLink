from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from database.models import User, Workspace
from core.security import hash_password, verify_password, create_token


def register(db, data) -> dict:
    """Create an account and private workspace in one transaction."""

    user = User(full_name=data.full_name, email=data.email.lower(), password_hash=hash_password(data.password))

    try:

        db.add(user)
        db.flush()
        db.add(Workspace(owner_id=user.id, business_name=data.business_name, business_email=user.email))
        db.commit()

    except IntegrityError:

        db.rollback()
        raise HTTPException(409, "Unable to register with that email")

    return {"access_token": create_token(user.id)}


def login(db, data) -> dict:
    """Validate credentials and return an access token."""

    user = db.query(User).filter_by(email=data.email.lower()).first()

    if not user or not verify_password(data.password, user.password_hash):

        raise HTTPException(401, "Invalid email or password")

    return {"access_token": create_token(user.id)}
