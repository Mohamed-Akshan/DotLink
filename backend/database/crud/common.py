from typing import Any
from datetime import datetime, timezone
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from database.models import ActivityLog


def serialize(row) -> dict:
    """Convert a database record to safe JSON data."""

    values = {}

    for column in row.__table__.columns:

        if column.name == "password_hash":

            continue

        value = getattr(row, column.name)

        if isinstance(value, datetime) and value.tzinfo is None:

            value = value.replace(tzinfo=timezone.utc)

        values[column.name] = value

    return jsonable_encoder(values)


def owned(db, model, workspace_id, record_id, lock=False) -> Any:
    """Find a record belonging to the authenticated workspace."""

    query = db.query(model).filter_by(id=record_id, workspace_id=workspace_id)

    if lock:

        query = query.with_for_update()

    row = query.first()

    if not row:

        raise HTTPException(404, "Record not found")

    return row


def list_records(db, model, workspace_id) -> list:
    """Return records belonging to one workspace."""

    results = []

    for row in db.query(model).filter_by(workspace_id=workspace_id).order_by(model.id.desc()).all():

        results.append(serialize(row))

    return results


def save(db, model, workspace_id, data, record_id=None) -> dict:
    """Create or update an authorized record without committing yet."""

    if record_id is None:

        row = model(workspace_id=workspace_id, **data)
        db.add(row)

    else:

        row = owned(db, model, workspace_id, record_id, lock=True)

        for key, value in data.items():

            setattr(row, key, value)

    db.flush()

    return serialize(row)


def log_activity(db, workspace_id, description) -> None:
    """Record an auditable business operation in the current transaction."""

    db.add(ActivityLog(workspace_id=workspace_id, description=description))

    return None
