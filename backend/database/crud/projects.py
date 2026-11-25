from fastapi import HTTPException
from database.models import Client, Project, Task, Document
from database.crud.common import owned, save, list_records


def get_projects(db, workspace_id) -> list:
    """List projects with their calculated task progress."""

    projects = list_records(db, Project, workspace_id)
    tasks = list_records(db, Task, workspace_id)

    for project in projects:

        count = 0
        completed = 0

        for task in tasks:

            if task["project_id"] == project["id"]:

                count += 1

                if task["status"] == "Completed":

                    completed += 1

        project["progress"] = round(completed / count * 100) if count else (100 if project["status"] == "Completed" else 0)

    return projects


def save_project(db, workspace_id, data, record_id=None) -> dict:
    """Save a project after verifying its client."""

    client = owned(db, Client, workspace_id, data.client_id)

    if client.archived:

        raise HTTPException(400, "Client is archived")

    if record_id is not None:
        project = owned(db, Project, workspace_id, record_id, lock=True)
        if project.client_id != data.client_id:
            if db.query(Document).filter_by(workspace_id=workspace_id, project_id=record_id).first():
                raise HTTPException(409, "A project linked to financial documents cannot change clients")
        for task in db.query(Task).filter_by(workspace_id=workspace_id, project_id=record_id).all():
            if not data.start_date <= task.due_date <= data.deadline:
                raise HTTPException(400, "Adjust linked task deadlines before changing the project dates")

    return save(db, Project, workspace_id, data.model_dump(), record_id)


def save_task(db, workspace_id, data, record_id=None) -> dict:
    """Save a task within the authorized project's date range."""

    if data.project_id is not None:

        project = owned(db, Project, workspace_id, data.project_id)

        if project.archived or not project.start_date <= data.due_date <= project.deadline:

            raise HTTPException(400, "Choose a task date inside the active project dates")

    return save(db, Task, workspace_id, data.model_dump(), record_id)


def accepted_quote(db, workspace_id, record_id):
    """Lock and validate the source quotation."""
    from database.models import Document
    quote = owned(db, Document, workspace_id, record_id, lock=True)
    if quote.document_type != "quotation" or quote.status != "Accepted":
        raise HTTPException(400, "Choose an accepted quotation")
    if quote.project_id is not None:
        raise HTTPException(409, "This quotation is already linked to a project")
    return quote


def attach_quote(db, workspace_id, quote, project_id) -> dict:
    """Link the quote and any derived invoice without changing prices."""
    from database.models import Document
    quote.project_id = project_id
    for invoice in db.query(Document).filter_by(workspace_id=workspace_id, source_id=quote.id).all():
        if invoice.project_id not in (None, project_id):
            raise HTTPException(409, "The derived invoice belongs to another project")
        invoice.project_id = project_id
    db.flush()
    return {"quotation_id": quote.id, "project_id": project_id, "value": float(quote.total)}


def create_from_quote(db, workspace_id, data, record_id) -> dict:
    """Create a project from an accepted quotation, preserving agreed value."""
    from database.schemas import ProjectInput
    from database.crud.finance import document_details
    quote = accepted_quote(db, workspace_id, record_id)
    scope = []
    for item in document_details(db, quote)["items"]:
        scope.append(f"{item['description']} × {item['quantity']}")
    project = save_project(db, workspace_id, ProjectInput(client_id=quote.client_id,
        title=data.title, description="; ".join(scope), start_date=data.start_date,
        deadline=data.deadline, priority=data.priority))
    attach_quote(db, workspace_id, quote, project["id"])
    # Generated IDs must not invalidate a preview created in a rolled-back savepoint.
    return {"title": project["title"], "client_id": quote.client_id, "value": float(quote.total),
            "start_date": project["start_date"], "deadline": project["deadline"]}


def link_quote(db, workspace_id, data, record_id) -> dict:
    """Link an accepted quotation to a project owned by the same client."""
    quote = accepted_quote(db, workspace_id, record_id)
    project = owned(db, Project, workspace_id, data.project_id, lock=True)
    if project.archived or project.client_id != quote.client_id:
        raise HTTPException(400, "Choose an active project for the same client")
    return attach_quote(db, workspace_id, quote, project.id)
