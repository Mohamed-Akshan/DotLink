from typing import Any
import hashlib
import json
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from database.models import Approval, Client, Project, Task, Service, Document, Message, Expense, Payment
from database.schemas import (
    ClientInput, ProjectInput, TaskInput, ServiceInput, DocumentInput,
    PaymentInput, QuotationStatusInput, ConversionInput, InvoiceIssueInput, ExpenseInput, QuoteProjectInput, QuoteLinkInput, ArchiveInput
)
from database.crud.clients import save_client
from database.crud.projects import save_project, save_task, create_from_quote, link_quote
from database.crud.expenses import save_expense, delete_expense
from database.crud.finance import (
    save_service, save_document, record_payment, set_quotation_status,
    convert_approved_quotation, issue_invoice, document_details
)
from database.crud.common import owned, serialize, log_activity
from guardrails.tool_guard import allowed_write
from database.crud.actions import archive_client, archive_project, archive_service, delete_task, void_invoice, reverse_confirmed_payment

ACTIONS = {
    "archive_client": (ArchiveInput, archive_client, Client),
    "archive_project": (ArchiveInput, archive_project, Project),
    "archive_service": (ArchiveInput, archive_service, Service),
    "delete_task": (InvoiceIssueInput, delete_task, Task),
    "void_invoice": (InvoiceIssueInput, void_invoice, Document),
    "reverse_payment": (InvoiceIssueInput, reverse_confirmed_payment, Payment),
    "create_expense": (ExpenseInput, save_expense, None),
    "update_expense": (ExpenseInput, save_expense, Expense),
    "delete_expense": (InvoiceIssueInput, delete_expense, Expense),
    "create_project_from_quotation": (QuoteProjectInput, create_from_quote, Document),
    "link_quotation_to_project": (QuoteLinkInput, link_quote, Document),
    "create_client": (ClientInput, save_client, None),
    "update_client": (ClientInput, save_client, Client),
    "create_project": (ProjectInput, save_project, None),
    "update_project": (ProjectInput, save_project, Project),
    "create_task": (TaskInput, save_task, None),
    "update_task": (TaskInput, save_task, Task),
    "create_service": (ServiceInput, save_service, None),
    "update_service": (ServiceInput, save_service, Service),
    "create_quotation": (DocumentInput, save_document, None),
    "update_quotation": (DocumentInput, save_document, Document),
    "create_invoice": (DocumentInput, save_document, None),
    "update_invoice": (DocumentInput, save_document, Document),
    "set_quotation_status": (QuotationStatusInput, set_quotation_status, Document),
    "convert_quotation_to_invoice": (ConversionInput, convert_approved_quotation, Document),
    "issue_invoice": (InvoiceIssueInput, issue_invoice, Document),
    "record_payment": (PaymentInput, record_payment, None),
}


def validate_action(db, workspace_id, action, payload) -> tuple:
    """Validate only explicitly supported AI write operations."""

    if not allowed_write(action, ACTIONS):

        raise HTTPException(400, "Unsupported AI action")

    schema, function, model = ACTIONS[action]
    values = dict(payload)
    record_id = values.pop("record_id", None)

    if model is not None:

        if not isinstance(record_id, int):

            raise HTTPException(400, "Record ID is required")

        owned(db, model, workspace_id, record_id)

    elif record_id is not None:

        raise HTTPException(400, "Unexpected record ID")

    data = schema.model_validate(values)

    if action in ("create_quotation", "update_quotation") and data.document_type != "quotation":

        raise HTTPException(400, "Expected quotation")

    if action in ("create_invoice", "update_invoice") and data.document_type != "invoice":

        raise HTTPException(400, "Expected invoice")

    return function, data, record_id


def canonical_payload(db, workspace_id: int, action: str, payload: dict) -> dict:
    """Store the exact validated values instead of raw model wording."""

    _, data, record_id = validate_action(db, workspace_id, action, payload)
    values = data.model_dump(mode="json")

    if record_id is not None:

        values["record_id"] = record_id

    return values


def run_action(db, workspace_id, action, payload) -> dict:
    """Call the same validated write function used by the manual interface."""

    function, data, target = validate_action(db, workspace_id, action, payload)

    if target is not None:

        return function(db, workspace_id, data, target)

    return function(db, workspace_id, data)


def comparable(value) -> Any:
    """Remove generated identifiers and timestamps from a proposed result."""

    if isinstance(value, list):

        items = []

        for item in value:

            items.append(comparable(item))

        return items

    if isinstance(value, dict):

        result = {}

        for key, item in value.items():

            if key not in ("id", "created_at", "document_id"):

                result[key] = comparable(item)

        return result

    return value


def current_record(db, workspace_id, action, payload) -> dict | None:
    """Capture the current record for stale approval protection."""

    model = ACTIONS[action][2]

    if model is not None:

        record = owned(db, model, workspace_id, payload["record_id"], lock=True)
        db.refresh(record, with_for_update=True)

        if model is Document:

            return document_details(db, record)

        if model is Payment:

            invoice = owned(db, Document, workspace_id, record.invoice_id, lock=True)
            return {**serialize(record), "invoice": document_details(db, invoice)}

        return serialize(record)

    if action == "record_payment":

        invoice = owned(db, Document, workspace_id, payload["invoice_id"], lock=True)
        db.refresh(invoice, with_for_update=True)

        return document_details(db, invoice)

    return None


def preview_action(db, workspace_id: int, action: str, payload: dict) -> dict:
    """Validate an operation in a temporary transaction, without saving it."""

    validate_action(db, workspace_id, action, payload)
    transaction = db.begin_nested()

    try:

        return comparable(run_action(db, workspace_id, action, payload))

    finally:

        transaction.rollback()


def proposal_key(workspace_id: int, conversation_id: int | None, action: str, payload: dict, preview: dict, before: dict | None) -> str:
    """Create a unique fingerprint to prevent identical pending proposals."""

    details = [workspace_id, conversation_id, action, payload, preview, before]
    fingerprint = json.dumps(details, sort_keys=True)

    # The hash is only a compact duplicate-prevention key, not AI logic.
    return hashlib.sha256(fingerprint.encode()).hexdigest()


def prepare_action(db, workspace_id: int, conversation_id: int | None, action: str, payload: dict, reason: str) -> dict:
    """Store a proposal without changing any business record."""

    payload = canonical_payload(db, workspace_id, action, payload)
    before = current_record(db, workspace_id, action, payload)
    preview = preview_action(db, workspace_id, action, payload)
    key = proposal_key(workspace_id, conversation_id, action, payload, preview, before)
    existing = db.query(Approval).filter_by(dedupe_key=key).first()

    if existing:

        return serialize(existing)

    row = Approval(
        workspace_id=workspace_id,
        conversation_id=conversation_id,
        action=action,
        payload=payload,
        reason=reason,
        preview=preview,
        before=before,
        dedupe_key=key,
    )

    try:

        db.add(row)
        db.commit()

    except IntegrityError:

        db.rollback()
        row = db.query(Approval).filter_by(dedupe_key=key).first()

        if not row:

            raise

    return serialize(row)


def edit_action(db, workspace_id: int, record_id: int, payload: dict) -> dict:
    """Save edited proposal details and a fresh preview, but never execute them."""

    row = owned(db, Approval, workspace_id, record_id, lock=True)

    if row.status != "Pending":

        raise HTTPException(409, "This proposal has already been reviewed")

    if payload.get("record_id") != row.payload.get("record_id"):

        raise HTTPException(400, "The original record cannot be changed during review")

    if row.action == "record_payment" and payload.get("invoice_id") != row.payload.get("invoice_id"):

        raise HTTPException(400, "Request a new proposal to change the invoice")

    payload = canonical_payload(db, workspace_id, row.action, payload)
    before = current_record(db, workspace_id, row.action, payload)

    if before != row.before:

        raise HTTPException(409, "The original record changed. Please reject this proposal and request a new one.")

    preview = preview_action(db, workspace_id, row.action, payload)
    key = proposal_key(workspace_id, row.conversation_id, row.action, payload, preview, before)
    duplicate = db.query(Approval).filter_by(dedupe_key=key).first()

    if duplicate and duplicate.id != row.id:

        raise HTTPException(409, "An identical proposal is already awaiting approval")

    row.payload = payload
    row.preview = preview
    row.dedupe_key = key

    try:

        db.commit()

    except IntegrityError:

        db.rollback()
        raise HTTPException(409, "An identical proposal is already awaiting approval")

    return present_approval(db, workspace_id, row)


def review_action(db, workspace_id: int, record_id: int, decision: str, edited_payload: dict | None = None) -> dict:
    """Execute a pending proposal once, only after owner confirmation."""

    row = owned(db, Approval, workspace_id, record_id, lock=True)

    if row.status != "Pending":

        raise HTTPException(409, "Approval already reviewed")

    if decision == "reject":

        row.status = "Rejected"

    else:

        if edited_payload is not None and edited_payload != row.payload:

            raise HTTPException(400, "Save the edited proposal and review its updated preview before approving")

        payload = row.payload

        validate_action(db, workspace_id, row.action, payload)
        before = current_record(db, workspace_id, row.action, payload)

        if before != row.before:

            raise HTTPException(409, "The underlying record changed. Reject this proposal and ask Dottie again.")

        result = run_action(db, workspace_id, row.action, payload)

        if comparable(result) != row.preview:

            db.rollback()
            raise HTTPException(
                409,
                "Prices or business data changed. Edit the proposal to refresh its preview, or request a new one.",
            )

        row.payload = payload
        row.result = result
        row.status = "Executed"
        log_activity(db, workspace_id, f"Approved AI action: {row.action}")

    row.dedupe_key = None

    if row.conversation_id is not None:

        title = action_title(row.action).lower()

        if row.status == "Executed":

            content = f"Done! Your approval for '{title}' has been processed successfully. The changes are now saved in your workspace."

        else:

            content = f"I've cancelled the '{title}' proposal. No business records were changed."

        db.add(Message(conversation_id=row.conversation_id, role="assistant", content=content))

    db.commit()

    return present_approval(db, workspace_id, row)


ACTION_TITLES = {
    "archive_client": "Change client archive status",
    "archive_project": "Change project archive status",
    "archive_service": "Change service archive status",
    "delete_task": "Delete task",
    "void_invoice": "Void invoice",
    "reverse_payment": "Reverse payment",
    "create_expense": 'Create Expense',
    "update_expense": 'Update Expense',
    "delete_expense": 'Delete Expense',
    "create_project_from_quotation": 'Create Project From Quotation',
    "link_quotation_to_project": 'Link Quotation To Project',
    "create_client": "Add client",
    "update_client": "Update client",
    "create_project": "Create project",
    "update_project": "Update project",
    "create_task": "Add task",
    "update_task": "Update task",
    "create_service": "Add service",
    "update_service": "Update service",
    "create_quotation": "Prepare quotation",
    "update_quotation": "Update quotation",
    "create_invoice": "Prepare invoice",
    "update_invoice": "Update invoice draft",
    "set_quotation_status": "Change quotation status",
    "convert_quotation_to_invoice": "Convert quotation to invoice",
    "issue_invoice": "Issue invoice",
    "record_payment": "Record payment",
}


def action_title(action: str) -> str:
    """Convert an internal action name into a friendly display title."""

    return ACTION_TITLES.get(action, "Business change")


def present_approval(db, workspace_id: int, row: Approval) -> dict:
    """Attach named, human-readable details to the proposal for the interface."""

    result = serialize(row)
    result["title"] = action_title(row.action)
    details = []
    labels = {
        "name": "Name", "company": "Company", "email": "Email", "phone": "Phone",
        "address": "Address", "notes": "Notes", "title": "Title", "description": "Scope / description",
        "start_date": "Start date", "deadline": "Deadline", "due_date": "Due / validity date",
        "priority": "Priority", "status": "Status", "category": "Category", "unit_price": "Unit price (LKR)",
        "pricing_unit": "Pricing unit", "issue_date": "Issue date", "discount": "Discount (%)",
        "amount": "Amount received (LKR)", "payment_date": "Payment date", "method": "Payment method",
        "reference": "Payment reference", "expense_date": "Expense date", "archived": "Archive record",
    }

    for key, value in row.payload.items():

        if value is None or value == "":

            continue

        if key in labels:

            details.append({"label": labels[key], "value": str(value)})

        elif key == "client_id":

            client = db.query(Client).filter_by(id=value, workspace_id=workspace_id).first()
            details.append({"label": "Client", "value": client.name if client else "Unavailable client"})

        elif key == "project_id":

            project = db.query(Project).filter_by(id=value, workspace_id=workspace_id).first()
            details.append({"label": "Project", "value": project.title if project else "Unavailable project"})

        elif key == "invoice_id":

            details.append({"label": "Invoice", "value": f"INV-{int(value):05d}"})

        elif key == "record_id" and isinstance(row.before, dict):

            kind = row.before.get("document_type")

            if row.before.get("title") or row.before.get("name"):
                details.append({"label": "Record", "value": row.before.get("title") or row.before.get("name")})
            if row.action == "reverse_payment":
                details.append({"label": "Payment", "value": f"PAY-{int(value):05d}"})
            if "amount" in row.before:
                details.append({"label": "Original amount (LKR)", "value": str(row.before["amount"])})
            if kind in ("quotation", "invoice"):

                prefix = "QUO" if kind == "quotation" else "INV"
                details.append({"label": "Document", "value": f"{prefix}-{int(value):05d}"})

    if row.action in ("set_quotation_status", "convert_quotation_to_invoice", "issue_invoice"):

        before = row.before or {}
        client_id = before.get("client_id")
        project_id = before.get("project_id")

        if client_id is not None:

            client = db.query(Client).filter_by(id=client_id, workspace_id=workspace_id).first()

            if client:

                details.append({"label": "Client", "value": client.company or client.name})

        if project_id is not None:

            project = db.query(Project).filter_by(id=project_id, workspace_id=workspace_id).first()

            if project:

                details.append({"label": "Project", "value": project.title})

        details.append({"label": "Current status", "value": before.get("status", "Unknown")})
        details.append({"label": "Status after approval", "value": row.preview.get("status", "Unknown")})

    result["details"] = details

    return result
