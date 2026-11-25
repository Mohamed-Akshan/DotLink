from fastapi import APIRouter
from core.security import DB, Tenant
from database.models import Approval
from database.schemas import ReviewInput, ProposalEdit
from services.approvals import review_action, edit_action, present_approval

router = APIRouter(prefix="/api/approvals", tags=["Approvals"])


@router.get("")
def approvals(db: DB, workspace: Tenant) -> list:
    """List the owner's AI proposals with readable review details."""

    results = []

    for row in db.query(Approval).filter_by(workspace_id=workspace.id).order_by(Approval.id.desc()).all():

        results.append(present_approval(db, workspace.id, row))

    return results


@router.put("/{record_id}")
def edit(record_id: int, data: ProposalEdit, db: DB, workspace: Tenant) -> dict:
    """Update and re-preview a pending proposal without executing it."""

    return edit_action(db, workspace.id, record_id, data.payload)


@router.post("/{record_id}/review")
def review(record_id: int, data: ReviewInput, db: DB, workspace: Tenant) -> dict:
    """Approve or reject a persisted proposal."""

    return review_action(db, workspace.id, record_id, data.decision, data.payload)
