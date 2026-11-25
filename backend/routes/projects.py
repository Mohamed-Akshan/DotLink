from fastapi import APIRouter
from core.security import DB, Tenant
from database.models import Project
from database.schemas import ProjectInput
from database.crud.common import list_records, owned, log_activity, serialize
from database.crud.projects import save_project, get_projects

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.get("")
def get_all(db: DB, workspace: Tenant) -> list:
    """List workspace projects."""

    return get_projects(db, workspace.id)


@router.post("")
def create(data: ProjectInput, db: DB, workspace: Tenant) -> dict:
    """Create a project."""

    result = save_project(db, workspace.id, data)
    log_activity(db, workspace.id, "Created project")
    db.commit()

    return result


@router.put("/{record_id}")
def update(record_id: int, data: ProjectInput, db: DB, workspace: Tenant) -> dict:
    """Update an owned project."""

    result = save_project(db, workspace.id, data, record_id)
    log_activity(db, workspace.id, "Updated project")
    db.commit()

    return result


@router.post("/{record_id}/archive")
def archive(record_id: int, db: DB, workspace: Tenant) -> dict:
    """Toggle archive status without deleting historical records."""

    row = owned(db, Project, workspace.id, record_id, lock=True)
    row.archived = not row.archived
    log_activity(db, workspace.id, "Changed project archive status")
    db.commit()

    return serialize(row)


from database.models import Task
from database.schemas import TaskInput
from database.crud.projects import save_task


@router.get("/{record_id}/tasks")
def tasks(record_id: int, db: DB, workspace: Tenant) -> list:
    """List tasks for an owned project."""

    owned(db, Project, workspace.id, record_id)

    results = []

    for row in db.query(Task).filter_by(workspace_id=workspace.id, project_id=record_id).all():

        results.append(serialize(row))

    return results


@router.post("/tasks")
def create_task(data: TaskInput, db: DB, workspace: Tenant) -> dict:
    """Add a task to a project."""

    result = save_task(db, workspace.id, data)
    db.commit()

    return result


@router.put("/tasks/{record_id}")
def update_task(record_id: int, data: TaskInput, db: DB, workspace: Tenant) -> dict:
    """Update a task in the workspace."""

    result = save_task(db, workspace.id, data, record_id)
    db.commit()

    return result


@router.delete("/tasks/{record_id}")
def delete_task(record_id: int, db: DB, workspace: Tenant) -> dict:
    """Delete an authorized task explicitly selected by the owner."""

    db.delete(owned(db, Task, workspace.id, record_id))
    db.commit()

    return {"deleted": True}


@router.get("/tasks/all")
def all_tasks(db: DB, workspace: Tenant) -> list:
    """List all workspace tasks, including standalone work."""
    return list_records(db, Task, workspace.id)


@router.get("/{record_id}/details")
def details(record_id: int, db: DB, workspace: Tenant) -> dict:
    """Show related business records and a factual project timeline."""
    from database.models import Expense, Document, Payment
    from database.crud.finance import document_details
    from services.analytics import project_finances
    project = owned(db, Project, workspace.id, record_id)
    project_tasks = []
    documents = []
    expenses = []
    timeline = [{"label": "Project created", "date": project.created_at.date().isoformat()}]
    for row in db.query(Task).filter_by(workspace_id=workspace.id, project_id=record_id).all():
        project_tasks.append(serialize(row))
        timeline.append({"label": f"Task created: {row.title} ({row.status})", "date": row.created_at.date().isoformat()})
    for row in db.query(Document).filter_by(workspace_id=workspace.id, project_id=record_id).all():
        documents.append(document_details(db, row))
        timeline.append({"label": f"{row.document_type.title()} #{row.id:05d} ({row.status})", "date": row.created_at.date().isoformat()})
        if row.document_type == "invoice":
            for payment in db.query(Payment).filter_by(workspace_id=workspace.id, invoice_id=row.id).all():
                timeline.append({"label": f"Payment {payment.amount:,.2f}" + (" (reversed)" if payment.reversed else " received"), "date": payment.payment_date.isoformat()})
    for row in db.query(Expense).filter_by(workspace_id=workspace.id, project_id=record_id).all():
        expenses.append(serialize(row))
        timeline.append({"label": f"Expense: {row.title}", "date": row.expense_date.isoformat()})
    finances = None
    for row in project_finances(db, workspace.id):
        if row["id"] == record_id:
            finances = row
            break
    timeline.sort(key=lambda row: row["date"], reverse=True)
    return {"project": serialize(project), "tasks": project_tasks, "documents": documents,
            "expenses": expenses, "finances": finances, "timeline": timeline}
