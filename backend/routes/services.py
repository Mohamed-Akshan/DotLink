from fastapi import APIRouter
from core.security import DB, Tenant
from database.models import Service
from database.schemas import ServiceInput
from database.crud.common import list_records, owned, log_activity, serialize
from database.crud.finance import save_service

router = APIRouter(prefix="/api/services", tags=["Services"])


@router.get("")
def get_all(db: DB, workspace: Tenant) -> list:
    """List workspace services."""

    return list_records(db, Service, workspace.id)


@router.post("")
def create(data: ServiceInput, db: DB, workspace: Tenant) -> dict:
    """Create a service."""

    result = save_service(db, workspace.id, data)
    log_activity(db, workspace.id, "Created service")
    db.commit()

    return result


@router.put("/{record_id}")
def update(record_id: int, data: ServiceInput, db: DB, workspace: Tenant) -> dict:
    """Update an owned service."""

    result = save_service(db, workspace.id, data, record_id)
    log_activity(db, workspace.id, "Updated service")
    db.commit()

    return result


@router.post("/{record_id}/archive")
def archive(record_id: int, db: DB, workspace: Tenant) -> dict:
    """Toggle archive status without deleting historical records."""

    row = owned(db, Service, workspace.id, record_id, lock=True)
    row.archived = not row.archived
    log_activity(db, workspace.id, "Changed service archive status")
    db.commit()

    return serialize(row)
