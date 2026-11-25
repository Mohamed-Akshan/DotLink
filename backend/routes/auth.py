from fastapi import APIRouter, Request
from core.rate_limit import limit_auth
from core.security import DB, Tenant
from database.schemas import Signup, Login
from database.crud.users import register, login
from database.crud.common import serialize
from database.models import User

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/signup")
def signup(data: Signup, db: DB, request: Request) -> dict:
    """Register a new business owner."""

    limit_auth(request)

    return register(db, data)


@router.post("/login")
def sign_in(data: Login, db: DB, request: Request) -> dict:
    """Authenticate an existing business owner."""

    limit_auth(request)

    return login(db, data)


@router.get("/me")
def me(db: DB, workspace: Tenant) -> dict:
    """Return the signed-in owner's profile and workspace."""

    return {"user": serialize(db.get(User, workspace.owner_id)), "workspace": serialize(workspace)}
