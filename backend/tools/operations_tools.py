from fastapi import HTTPException
from pydantic import ValidationError
from database.connection import SessionLocal
from database.models import Task
from database.crud.clients import get_clients as clients, get_client
from database.crud.projects import get_projects as projects
from database.crud.common import list_records
from services.approvals import prepare_action


def build_operations_tools(workspace_id, conversation_id) -> list:
    """Expose workspace-bound read tools and write proposals."""

    def propose(action, payload) -> dict:
        """Save a proposal for owner review."""

        with SessionLocal() as db:

            try:

                return prepare_action(db, workspace_id, conversation_id, action, payload, "Prepared for your review")

            except ValidationError as error:

                fields = []

                for item in error.errors():

                    fields.append(str(item["loc"][-1]).replace("_", " "))

                return {"status": "Needs clarification", "fields": fields}

            except HTTPException as error:

                return {"status": "Needs clarification", "message": str(error.detail)}

    def get_clients() -> list:
        """List clients and IDs in the current workspace."""

        with SessionLocal() as db:

            return clients(db, workspace_id)

    def get_client_details(client_id: int) -> dict:
        """Retrieve a client by its verified ID."""

        with SessionLocal() as db:

            return get_client(db, workspace_id, client_id)

    def create_client(
        name: str,
        email: str,
        phone: str,
        company: str = "",
        address: str = "",
        notes: str = "",
    ) -> dict:
        """Propose a new client only after the owner provides name, real email and phone. Ask for missing fields; never guess."""

        return propose(
            "create_client",
            dict(name=name, company=company, email=email, phone=phone, address=address, notes=notes),
        )

    def update_client(
        record_id: int,
        name: str,
        email: str,
        phone: str,
        company: str = "",
        address: str = "",
        notes: str = "",
    ) -> dict:
        """Propose a client update; preserve all unchanged fields."""

        return propose(
            "update_client",
            dict(
                record_id=record_id,
                name=name,
                company=company,
                email=email,
                phone=phone,
                address=address,
                notes=notes,
            ),
        )

    def get_projects() -> list:
        """Retrieve projects and calculated task progress."""

        with SessionLocal() as db:

            return projects(db, workspace_id)

    def create_project(
        client_id: int,
        title: str,
        start_date: str,
        deadline: str,
        description: str,
        priority: str = "Medium",
        status: str = "Pending",
    ) -> dict:
        """Propose a project only with owner-provided title, scope, start date and deadline, and verified client."""

        return propose(
            "create_project",
            dict(
                client_id=client_id,
                title=title,
                start_date=start_date,
                deadline=deadline,
                description=description,
                priority=priority,
                status=status,
            ),
        )

    def update_project(
        record_id: int,
        client_id: int,
        title: str,
        start_date: str,
        deadline: str,
        description: str,
        priority: str = "Medium",
        status: str = "Pending",
    ) -> dict:
        """Propose a project update, preserving unchanged fields."""

        return propose(
            "update_project",
            dict(
                record_id=record_id,
                client_id=client_id,
                title=title,
                start_date=start_date,
                deadline=deadline,
                description=description,
                priority=priority,
                status=status,
            ),
        )

    def get_tasks(project_id: int | None = None) -> list:
        """List tasks belonging to a selected project."""

        with SessionLocal() as db:

            tasks = []

            for row in list_records(db, Task, workspace_id):

                if project_id is None or row["project_id"] == project_id:

                    tasks.append(row)

            return tasks

    def create_task(
        title: str,
        due_date: str,
        project_id: int | None = None,
        description: str = "",
        status: str = "Pending",
        priority: str = "Medium",
    ) -> dict:
        """Propose a task using an existing project ID and ISO date."""

        return propose(
            "create_task",
            dict(project_id=project_id, title=title, due_date=due_date, description=description, status=status, priority=priority),
        )

    def update_task(
        record_id: int,
        title: str,
        due_date: str,
        project_id: int | None = None,
        description: str = "",
        status: str = "Pending",
        priority: str = "Medium",
    ) -> dict:
        """Propose a task update, preserving unchanged fields."""

        return propose(
            "update_task",
            dict(
                record_id=record_id,
                project_id=project_id,
                title=title,
                due_date=due_date,
                description=description,
                status=status, priority=priority,
            ),
        )

    def set_client_archive(record_id: int, archived: bool) -> dict:
        """Propose archiving or restoring an identified client; preserve history."""
        return propose("archive_client", dict(record_id=record_id, archived=archived))

    def set_project_archive(record_id: int, archived: bool) -> dict:
        """Propose archiving or restoring an identified project."""
        return propose("archive_project", dict(record_id=record_id, archived=archived))

    def delete_task(record_id: int) -> dict:
        """Propose deletion only when the user explicitly requests it."""
        return propose("delete_task", dict(record_id=record_id))

    return [
        set_client_archive, set_project_archive, delete_task,
        get_clients,
        get_client_details,
        create_client,
        update_client,
        get_projects,
        create_project,
        update_project,
        get_tasks,
        create_task,
        update_task,
    ]
