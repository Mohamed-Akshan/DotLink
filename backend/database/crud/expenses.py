from fastapi import HTTPException
from core.dates import business_today
from database.models import Expense, Project
from database.crud.common import owned, save, list_records


def save_expense(db, workspace_id, data, record_id=None) -> dict:
    """Record a paid expense in the authenticated workspace."""
    if data.project_id is not None:
        owned(db, Project, workspace_id, data.project_id)

    if data.expense_date > business_today():
        raise HTTPException(400, "A paid expense cannot have a future date")

    return save(db, Expense, workspace_id, data.model_dump(), record_id)


def delete_expense(db, workspace_id, data, record_id) -> dict:
    """Delete a confirmed expense after owner authorization."""
    row = owned(db, Expense, workspace_id, record_id, lock=True)
    result = {"title": row.title, "amount": float(row.amount), "deleted": True}
    db.delete(row)
    db.flush()
    return result
