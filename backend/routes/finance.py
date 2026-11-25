from fastapi import APIRouter, Response
from core.security import DB, Tenant
from database.models import Payment
from database.schemas import DocumentInput, PaymentInput, StatusInput
from database.crud.common import list_records, log_activity
from database.crud.finance import (
    get_documents,
    save_document,
    change_status,
    convert_quotation,
    record_payment,
    reverse_payment,
)
from services.pdf import document_pdf

router = APIRouter(prefix="/api/finance", tags=["Finance"])


@router.get("/documents")
def documents(db: DB, workspace: Tenant) -> list:
    """List all quotations and invoices."""

    return get_documents(db, workspace.id)


@router.post("/documents")
def create(data: DocumentInput, db: DB, workspace: Tenant) -> dict:
    """Create a priced document draft."""

    result = save_document(db, workspace.id, data)
    log_activity(db, workspace.id, "Created document")
    db.commit()

    return result


@router.put("/documents/{record_id}")
def update(record_id: int, data: DocumentInput, db: DB, workspace: Tenant) -> dict:
    """Edit an eligible document draft."""

    result = save_document(db, workspace.id, data, record_id)
    db.commit()

    return result


@router.post("/documents/{record_id}/status")
def status(record_id: int, data: StatusInput, db: DB, workspace: Tenant) -> dict:
    """Apply a valid document status transition."""

    result = change_status(db, workspace.id, record_id, data.status)
    log_activity(db, workspace.id, "Changed document status")
    db.commit()

    return result


@router.post("/documents/{record_id}/convert")
def convert(record_id: int, db: DB, workspace: Tenant) -> dict:
    """Convert an accepted quotation into an invoice draft."""

    result = convert_quotation(db, workspace.id, record_id)
    db.commit()

    return result


@router.get("/documents/{record_id}/pdf")
def pdf(record_id: int, db: DB, workspace: Tenant) -> Response:
    """Download an authorized document PDF."""

    return Response(
        document_pdf(db, workspace, record_id),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="dotlink-{record_id}.pdf"'},
    )


@router.get("/payments")
def payments(db: DB, workspace: Tenant) -> list:
    """List recorded payments."""

    return list_records(db, Payment, workspace.id)


@router.post("/payments")
def pay(data: PaymentInput, db: DB, workspace: Tenant) -> dict:
    """Record a confirmed received payment."""

    result = record_payment(db, workspace.id, data)
    log_activity(db, workspace.id, "Recorded payment")
    db.commit()

    return result


@router.post("/payments/{record_id}/reverse")
def reverse(record_id: int, db: DB, workspace: Tenant) -> dict:
    """Reverse a payment while retaining its audit record."""

    result = reverse_payment(db, workspace.id, record_id)
    log_activity(db, workspace.id, "Reversed payment")
    db.commit()

    return result


from database.schemas import QuoteProjectInput, QuoteLinkInput
from database.crud.projects import create_from_quote, link_quote

@router.post("/documents/{record_id}/create-project")
def quote_project(record_id: int, data: QuoteProjectInput, db: DB, workspace: Tenant) -> dict:
    result = create_from_quote(db, workspace.id, data, record_id)
    log_activity(db, workspace.id, "Created project from accepted quotation")
    db.commit()
    return result

@router.post("/documents/{record_id}/link-project")
def quote_link(record_id: int, data: QuoteLinkInput, db: DB, workspace: Tenant) -> dict:
    result = link_quote(db, workspace.id, data, record_id)
    log_activity(db, workspace.id, "Linked accepted quotation to project")
    db.commit()
    return result
