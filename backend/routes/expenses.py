from fastapi import APIRouter
from core.security import DB, Tenant
from database.models import Expense
from database.schemas import ExpenseInput
from database.crud.common import list_records, log_activity
from database.crud.expenses import save_expense, delete_expense

router = APIRouter(prefix="/api/expenses", tags=["Expenses"])

@router.get("")
def all_expenses(db: DB, workspace: Tenant) -> list:
    """Return authorized expense records."""
    return list_records(db, Expense, workspace.id)

@router.post("")
def create(data: ExpenseInput, db: DB, workspace: Tenant) -> dict:
    result = save_expense(db, workspace.id, data)
    log_activity(db, workspace.id, "Recorded expense: " + data.title)
    db.commit()
    return result

@router.put("/{record_id}")
def update(record_id: int, data: ExpenseInput, db: DB, workspace: Tenant) -> dict:
    result = save_expense(db, workspace.id, data, record_id)
    log_activity(db, workspace.id, "Updated expense: " + data.title)
    db.commit()
    return result

@router.delete("/{record_id}")
def delete(record_id: int, db: DB, workspace: Tenant) -> dict:
    result = delete_expense(db, workspace.id, None, record_id)
    log_activity(db, workspace.id, "Deleted expense: " + result["title"])
    db.commit()
    return result
