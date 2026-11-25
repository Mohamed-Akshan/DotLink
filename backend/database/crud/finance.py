from decimal import Decimal, ROUND_HALF_UP
from datetime import date, timedelta
from core.dates import business_today
from fastapi import HTTPException
from database.models import Client, Project, Service, Document, DocumentItem, Payment
from database.crud.common import owned, save, serialize, list_records


def money(value) -> Decimal:
    """Round money to two decimal places using decimal arithmetic."""

    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def save_service(db, workspace_id, data, record_id=None) -> dict:
    """Save a service rate-card entry."""

    return save(db, Service, workspace_id, data.model_dump(), record_id)


def paid_amount(db, invoice) -> Decimal:
    """Calculate confirmed, non-reversed payments."""

    rows = db.query(Payment).filter_by(workspace_id=invoice.workspace_id, invoice_id=invoice.id, reversed=False).all()

    total = Decimal("0")

    for row in rows:

        total += row.amount

    return total


def document_details(db, document) -> dict:
    """Return a document with its line items and unpaid balance."""

    result = serialize(document)
    result["items"] = []

    for row in db.query(DocumentItem).filter_by(document_id=document.id).order_by(DocumentItem.id).all():

        result["items"].append(serialize(row))
    result["balance"] = float(document.total - paid_amount(db, document)) if document.document_type == "invoice" and document.status not in ("Draft", "Void") else 0

    return result


def get_documents(db, workspace_id) -> list:
    """List quotations and invoices in one workspace."""

    results = []

    for row in db.query(Document).filter_by(workspace_id=workspace_id).order_by(Document.id.desc()).all():

        results.append(document_details(db, row))

    return results


def save_document(db, workspace_id, data, record_id=None) -> dict:
    """Price a draft from the official rate card and save its line items."""

    client = owned(db, Client, workspace_id, data.client_id)
    if client.archived:
        raise HTTPException(400, "Choose an active client")

    if data.project_id is not None:

        project = owned(db, Project, workspace_id, data.project_id)

        if project.archived:
            raise HTTPException(400, "Choose an active project")

        if project.client_id != data.client_id:

            raise HTTPException(400, "Project belongs to a different client")

    if data.due_date < data.issue_date:

        raise HTTPException(400, "Invalid document dates")

    items = []
    subtotal = Decimal("0")

    for item in data.items:

        service = owned(db, Service, workspace_id, item.service_id)

        if service.archived:

            raise HTTPException(400, "Service is archived")

        subtotal += money(service.unit_price * item.quantity)
        items.append(DocumentItem(
            service_id=service.id,
            description=service.name,
            quantity=item.quantity,
            unit_price=service.unit_price,
        ))

    total = money(subtotal * (100 - data.discount) / 100)
    values = data.model_dump(exclude={"items"})
    values["total"] = total

    if record_id is not None:

        current = owned(db, Document, workspace_id, record_id, lock=True)

        if current.status != "Draft" or current.document_type != data.document_type or current.source_id:

            raise HTTPException(400, "Only ordinary drafts can be edited")

        db.query(DocumentItem).filter_by(document_id=record_id).delete()

    result = save(db, Document, workspace_id, values, record_id)

    for item in items:

        item.document_id = result["id"]
        db.add(item)

    db.flush()

    return document_details(db, db.get(Document, result["id"]))


def change_status(db, workspace_id, record_id, status: str) -> dict:
    """Enforce valid quotation and invoice status transitions."""

    document = owned(db, Document, workspace_id, record_id, lock=True)
    if document.document_type == "quotation":

        # Acceptance may be confirmed outside DotLink, before marking it sent.
        transitions = {
            "Draft": ["Sent", "Accepted", "Rejected"],
            "Sent": ["Accepted", "Rejected"],
        }

    else:

        transitions = {
            "Draft": ["Unpaid", "Void"],
            "Unpaid": ["Void"],
        }

    if status not in transitions.get(document.status, []):

        raise HTTPException(400, "Invalid status transition")

    if status == "Void" and paid_amount(db, document) > 0:

        raise HTTPException(400, "Reverse payments before voiding")

    document.status = "Paid" if status == "Unpaid" and document.total == 0 else status
    db.flush()

    return document_details(db, document)


def convert_quotation(
    db,
    workspace_id: int,
    record_id: int,
    issue_date: date | None = None,
    due_date: date | None = None
) -> dict:
    """Copy an accepted quotation into one invoice without repricing."""

    quote = owned(db, Document, workspace_id, record_id, lock=True)

    if quote.document_type != "quotation" or quote.status != "Accepted":

        raise HTTPException(400, "An accepted quotation is required")

    if db.query(Document).filter_by(source_id=quote.id).first():

        raise HTTPException(409, "Quotation already converted")

    if issue_date is None:

        issue_date = business_today()

    if due_date is None:

        due_date = issue_date + timedelta(days=14)

    if due_date < issue_date:

        raise HTTPException(400, "Payment due date must be on or after the issue date")

    invoice = Document(
        workspace_id=workspace_id,
        client_id=quote.client_id,
        project_id=quote.project_id,
        source_id=quote.id,
        document_type="invoice",
        issue_date=issue_date,
        due_date=due_date,
        discount=quote.discount,
        total=quote.total,
        notes=quote.notes,
        status="Draft",
    )
    db.add(invoice)
    db.flush()

    for item in db.query(DocumentItem).filter_by(document_id=quote.id).order_by(DocumentItem.id).all():

        db.add(DocumentItem(
            document_id=invoice.id,
            service_id=item.service_id,
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
        ))

    db.flush()

    return document_details(db, invoice)


def set_quotation_status(db, workspace_id: int, data, record_id: int) -> dict:
    """Apply an owner-approved quotation status change."""

    quote = owned(db, Document, workspace_id, record_id, lock=True)

    if quote.document_type != "quotation":

        raise HTTPException(400, "Choose a quotation")

    return change_status(db, workspace_id, record_id, data.status)


def convert_approved_quotation(db, workspace_id: int, data, record_id: int) -> dict:
    """Copy an accepted quotation using the approved invoice dates."""

    return convert_quotation(db, workspace_id, record_id, data.issue_date, data.due_date)


def issue_invoice(db, workspace_id: int, data, record_id: int) -> dict:
    """Issue a draft invoice after owner approval."""

    invoice = owned(db, Document, workspace_id, record_id, lock=True)

    if invoice.document_type != "invoice" or invoice.status != "Draft":

        raise HTTPException(400, "Choose a draft invoice to issue")

    return change_status(db, workspace_id, record_id, "Unpaid")


def record_payment(db, workspace_id, data) -> dict:
    """Record a payment without exceeding the invoice balance."""

    invoice = owned(db, Document, workspace_id, data.invoice_id, lock=True)

    if invoice.document_type != "invoice" or invoice.status not in ("Unpaid", "Partially paid"):

        raise HTTPException(400, "Choose an issued unpaid invoice")

    if data.payment_date > business_today():

        raise HTTPException(400, "A confirmed payment cannot have a future date")

    balance = invoice.total - paid_amount(db, invoice)

    if data.amount > balance:

        raise HTTPException(400, "Payment exceeds the unpaid balance")

    if data.reference:

        existing = db.query(Payment).filter_by(
            workspace_id=workspace_id,
            invoice_id=invoice.id,
            reference=data.reference,
            reversed=False
        ).first()

        if existing:

            raise HTTPException(409, "This transaction reference is already recorded for this invoice")

    result = save(db, Payment, workspace_id, data.model_dump())
    invoice.status = "Paid" if data.amount == balance else "Partially paid"
    db.flush()

    return result


def reverse_payment(db, workspace_id, record_id) -> dict:
    """Reverse a payment while preserving its original record."""

    payment = owned(db, Payment, workspace_id, record_id, lock=True)
    invoice = owned(db, Document, workspace_id, payment.invoice_id, lock=True)

    if payment.reversed:

        raise HTTPException(400, "Payment already reversed")

    payment.reversed = True
    db.flush()
    remaining_paid = paid_amount(db, invoice)
    invoice.status = "Unpaid" if remaining_paid == 0 else "Partially paid"

    return serialize(payment)
