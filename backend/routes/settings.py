from fastapi import APIRouter
from core.security import DB, Tenant
from database.schemas import WorkspaceInput
from database.crud.common import serialize

router = APIRouter(prefix="/api/settings", tags=["Settings"])


@router.get("")
def get_settings(workspace: Tenant) -> dict:
    """Read business preferences."""

    return serialize(workspace)


@router.put("")
def update_settings(data: WorkspaceInput, db: DB, workspace: Tenant) -> dict:
    """Update the owner's business contact information."""

    for key, value in data.model_dump().items():

        setattr(workspace, key, value)

    db.commit()

    return serialize(workspace)


from database.schemas import ProfileInput, PasswordChange
from database.models import User
from core.security import verify_password, hash_password
from fastapi import HTTPException


@router.put("/profile")
def update_profile(data: ProfileInput, db: DB, workspace: Tenant) -> dict:
    """Update the authenticated owner's display name."""

    user = db.get(User, workspace.owner_id)
    user.full_name = data.full_name
    db.commit()

    return serialize(user)


@router.put("/password")
def change_password(data: PasswordChange, db: DB, workspace: Tenant) -> dict:
    """Change the password after verifying the current one."""

    user = db.get(User, workspace.owner_id)

    if not verify_password(data.current_password, user.password_hash):

        raise HTTPException(400, "Current password is incorrect")

    user.password_hash = hash_password(data.password)
    db.commit()

    return {"updated": True}
