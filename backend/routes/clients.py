from fastapi import APIRouter
from core.security import DB, Tenant
from database.models import Client
from database.schemas import ClientInput
from database.crud.common import list_records, owned, log_activity, serialize
from database.crud.clients import save_client

router = APIRouter(prefix="/api/clients", tags=["Clients"])


@router.get("")
def get_all(db: DB, workspace: Tenant) -> list:
    """List workspace clients."""

    return list_records(db, Client, workspace.id)


@router.post("")
def create(data: ClientInput, db: DB, workspace: Tenant) -> dict:
    """Create a client."""

    result = save_client(db, workspace.id, data)
    log_activity(db, workspace.id, "Created client")
    db.commit()

    return result


@router.put("/{record_id}")
def update(record_id: int, data: ClientInput, db: DB, workspace: Tenant) -> dict:
    """Update an owned client."""

    result = save_client(db, workspace.id, data, record_id)
    log_activity(db, workspace.id, "Updated client")
    db.commit()

    return result


@router.post("/{record_id}/archive")
def archive(record_id: int, db: DB, workspace: Tenant) -> dict:
    """Toggle archive status without deleting historical records."""

    row = owned(db, Client, workspace.id, record_id, lock=True)
    row.archived = not row.archived
    log_activity(db, workspace.id, "Changed client archive status")
    db.commit()

    return serialize(row)
