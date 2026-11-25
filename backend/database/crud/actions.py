from fastapi import HTTPException
from database.models import Client, Project, Task, Service, Document, Payment
from database.crud.common import owned, serialize
from database.crud.finance import change_status, reverse_payment


def set_archive(db, workspace_id, data, record_id, model) -> dict:
    """Set an explicit archive state, never toggle unexpectedly."""
    row = owned(db, model, workspace_id, record_id, lock=True)
    if row.archived == data.archived:
        raise HTTPException(409, "This record already has the requested archive status")
    row.archived = data.archived
    db.flush()
    return serialize(row)


def archive_client(db, workspace_id, data, record_id) -> dict:
    """Archive or restore a client."""
    return set_archive(db, workspace_id, data, record_id, Client)


def archive_project(db, workspace_id, data, record_id) -> dict:
    """Archive or restore a project."""
    return set_archive(db, workspace_id, data, record_id, Project)


def archive_service(db, workspace_id, data, record_id) -> dict:
    """Archive or restore a service."""
    return set_archive(db, workspace_id, data, record_id, Service)


def delete_task(db, workspace_id, data, record_id) -> dict:
    """Permanently remove an explicitly selected task."""
    task = owned(db, Task, workspace_id, record_id, lock=True)
    result = {"title": task.title, "deleted": True}
    db.delete(task)
    db.flush()
    return result


def void_invoice(db, workspace_id, data, record_id) -> dict:
    """Void an eligible invoice, retaining its historical record."""
    document = owned(db, Document, workspace_id, record_id, lock=True)
    if document.document_type != "invoice":
        raise HTTPException(400, "Choose an invoice")
    return change_status(db, workspace_id, record_id, "Void")


def reverse_confirmed_payment(db, workspace_id, data, record_id) -> dict:
    """Reverse a confirmed payment via the existing financial workflow."""
    return reverse_payment(db, workspace_id, record_id)
