from fastapi import HTTPException
from pydantic import ValidationError
from database.connection import SessionLocal
from database.models import Service, Payment, Document, Client, Project
from database.schemas import PaymentInput
from database.crud.common import list_records, owned
from database.crud.finance import get_documents
from services.approvals import prepare_action


def build_finance_tools(workspace_id, conversation_id, downloads) -> list:
    """Expose finance reads and approval-backed write tools."""

    def propose(action, payload) -> dict:
        """Store a finance proposal without changing records."""

        with SessionLocal() as db:

            try:

                if action == "record_payment":

                    payment = PaymentInput.model_validate(payload)
                    from core.dates import business_today
                    if payment.payment_date > business_today():
                        raise HTTPException(400, "A confirmed payment cannot have a future date")
                    invoice = owned(db, Document, workspace_id, payment.invoice_id)

                    if invoice.document_type == "invoice" and invoice.status == "Draft":

                        if payment.amount > invoice.total:

                            raise HTTPException(400, "Payment exceeds the invoice total")

                        proposal = prepare_action(
                            db,
                            workspace_id,
                            conversation_id,
                            "issue_invoice",
                            {"record_id": invoice.id},
                            "The draft invoice must be issued before recording payment"
                        )

                        proposal["message"] = (
                            "This proposal issues the draft invoice only. "
                            "No payment has been recorded. After the owner approves issuance, "
                            "continue with the payment using the details already supplied."
                        )

                        return proposal

                return prepare_action(db, workspace_id, conversation_id, action, payload, "Prepared for your review")

            except ValidationError as error:

                fields = []

                for item in error.errors():

                    location = item.get("loc", ())
                    field = str(location[-1]).replace("_", " ") if location else "Details"
                    fields.append(field + ": " + item["msg"])

                return {"status": "Needs clarification", "fields": fields}

            except ValueError as error:

                return {"status": "Needs clarification", "message": str(error)}

            except HTTPException as error:

                return {"status": "Needs clarification", "message": str(error.detail)}

    def documents_by_type(kind: str) -> list:
        """Return documents with recognizable client, project and reference names."""

        with SessionLocal() as db:

            results = []

            for row in get_documents(db, workspace_id):

                if row["document_type"] != kind:

                    continue

                client = owned(db, Client, workspace_id, row["client_id"])
                row["client_name"] = client.name
                row["company"] = client.company
                row["project_title"] = None

                if row["project_id"] is not None:

                    project = owned(db, Project, workspace_id, row["project_id"])
                    row["project_title"] = project.title

                prefix = "QUO" if kind == "quotation" else "INV"
                row["reference"] = f"{prefix}-{row['id']:05d}"
                results.append(row)

            return results


    def get_services() -> list:
        """Retrieve rate-card services, prices and IDs."""

        with SessionLocal() as db:

            return list_records(db, Service, workspace_id)

    def create_service(
        name: str,
        unit_price: float,
        pricing_unit: str,
        category: str = "Design",
        description: str = "",
    ) -> dict:
        """Propose a service with a confirmed name, price and unit.

        Pricing units are design, hour, package or item. Natural phrases
        such as per design and per package are normalized automatically.
        """

        payload = {
            "name": name,
            "unit_price": unit_price,
            "pricing_unit": pricing_unit,
            "category": category,
            "description": description,
        }

        return propose("create_service", payload)

    def update_service(
        record_id: int,
        name: str | None = None,
        unit_price: float | None = None,
        category: str | None = None,
        description: str | None = None,
        pricing_unit: str | None = None
    ) -> dict:
        """Propose only requested service changes and preserve other values."""

        with SessionLocal() as db:

            service = owned(db, Service, workspace_id, record_id)

            payload = {
                "record_id": record_id,
                "name": service.name if name is None else name,
                "unit_price": str(service.unit_price) if unit_price is None else unit_price,
                "category": service.category if category is None else category,
                "description": service.description if description is None else description,
                "pricing_unit": service.pricing_unit if pricing_unit is None else pricing_unit,
            }

        return propose("update_service", payload)


    def create_quotation(
        client_id: int,
        issue_date: str,
        due_date: str,
        items: list[dict],
        project_id: int | None = None,
        discount: float = 0,
        notes: str = "",
    ) -> dict:
        """Propose a quotation; each item has service_id and quantity."""

        return propose(
            "create_quotation",
            dict(
                client_id=client_id,
                issue_date=issue_date,
                due_date=due_date,
                items=items,
                project_id=project_id,
                discount=discount,
                notes=notes,
                document_type="quotation",
            ),
        )

    def get_quotations() -> list:
        """Find quotations by client, project, reference, items and status."""

        return documents_by_type("quotation")


    def update_quotation(
        record_id: int,
        client_id: int,
        issue_date: str,
        due_date: str,
        items: list[dict],
        project_id: int | None = None,
        discount: float = 0,
        notes: str = "",
    ) -> dict:
        """Propose edits to an existing quotation draft."""

        return propose(
            "update_quotation",
            dict(
                record_id=record_id,
                client_id=client_id,
                issue_date=issue_date,
                due_date=due_date,
                items=items,
                project_id=project_id,
                discount=discount,
                notes=notes,
                document_type="quotation",
            ),
        )

    def create_invoice(
        client_id: int,
        issue_date: str,
        due_date: str,
        items: list[dict],
        project_id: int | None = None,
        discount: float = 0,
        notes: str = "",
    ) -> dict:
        """Propose an invoice draft with rate-card service IDs and quantities."""

        return propose(
            "create_invoice",
            dict(
                client_id=client_id,
                issue_date=issue_date,
                due_date=due_date,
                items=items,
                project_id=project_id,
                discount=discount,
                notes=notes,
                document_type="invoice",
            ),
        )

    def get_invoices() -> list:
        """Find invoices by client, project, reference, balance and status."""

        return documents_by_type("invoice")


    def set_quotation_status(record_id: int, status: str) -> dict:
        """Propose Sent, Accepted or Rejected for a quotation after owner confirmation."""

        return propose(
            "set_quotation_status",
            {"record_id": record_id, "status": status}
        )


    def convert_quotation_to_invoice(
        record_id: int,
        issue_date: str,
        due_date: str
    ) -> dict:
        """Propose conversion of an accepted quote, preserving all agreed prices."""

        return propose(
            "convert_quotation_to_invoice",
            {
                "record_id": record_id,
                "issue_date": issue_date,
                "due_date": due_date,
            }
        )


    def issue_invoice(record_id: int) -> dict:
        """Propose issuance of an existing draft invoice, without sending it externally."""

        return propose("issue_invoice", {"record_id": record_id})


    def update_invoice(
        record_id: int,
        client_id: int,
        issue_date: str,
        due_date: str,
        items: list[dict],
        project_id: int | None = None,
        discount: float = 0,
        notes: str = ""
    ) -> dict:
        """Propose changes to an ordinary invoice draft, preserving unchanged fields."""

        return propose(
            "update_invoice",
            {
                "record_id": record_id,
                "client_id": client_id,
                "issue_date": issue_date,
                "due_date": due_date,
                "items": items,
                "project_id": project_id,
                "discount": discount,
                "notes": notes,
                "document_type": "invoice",
            }
        )


    def record_payment(
        invoice_id: int,
        amount: float,
        payment_date: str,
        method: str,
        reference: str = "",
        notes: str = "",
    ) -> dict:
        """Propose a payment explicitly confirmed as received by the owner."""

        return propose(
            "record_payment",
            dict(
                invoice_id=invoice_id,
                amount=amount,
                payment_date=payment_date,
                method=method,
                reference=reference,
                notes=notes,
            ),
        )

    def get_payments() -> list:
        """Retrieve recorded payments and reversal status."""

        with SessionLocal() as db:

            return list_records(db, Payment, workspace_id)

    def generate_document_pdf(record_id: int) -> dict:
        """Prepare a download for an existing authorized document."""

        with SessionLocal() as db:

            document = owned(db, Document, workspace_id, record_id)
            link = {
                "path": f"/finance/documents/{record_id}/pdf",
                "label": f"{document.document_type.title()} #{record_id}.pdf",
            }
            downloads.append(link)

            return link

    def get_expenses() -> list:
        """Read workspace expenses."""
        from database.models import Expense
        with SessionLocal() as db:
            return list_records(db, Expense, workspace_id)

    def record_expense(title: str, category: str, amount: float, expense_date: str, method: str, project_id: int | None = None, notes: str = "") -> dict:
        """Propose a paid expense after confirming essential details."""
        return propose("create_expense", dict(title=title, category=category, amount=amount, expense_date=expense_date, method=method, project_id=project_id, notes=notes))

    def update_expense(record_id: int, title: str, category: str, amount: float, expense_date: str, method: str, project_id: int | None = None, notes: str = "") -> dict:
        """Propose an expense edit, preserving all unchanged fields."""
        return propose("update_expense", dict(record_id=record_id, title=title, category=category, amount=amount, expense_date=expense_date, method=method, project_id=project_id, notes=notes))

    def delete_expense(record_id: int) -> dict:
        """Propose deletion of an explicitly identified expense."""
        return propose("delete_expense", {"record_id": record_id})

    def create_project_from_quotation(record_id: int, title: str, start_date: str, deadline: str, priority: str = "Medium") -> dict:
        """Propose creating a project from an accepted unlinked quotation."""
        return propose("create_project_from_quotation", dict(record_id=record_id, title=title, start_date=start_date, deadline=deadline, priority=priority))

    def link_quotation_to_project(record_id: int, project_id: int) -> dict:
        """Propose linking an accepted quote to an active same-client project."""
        return propose("link_quotation_to_project", dict(record_id=record_id, project_id=project_id))

    def set_service_archive(record_id: int, archived: bool) -> dict:
        """Propose archiving or restoring a rate-card service."""
        return propose("archive_service", dict(record_id=record_id, archived=archived))

    def void_invoice(record_id: int) -> dict:
        """Propose voiding an eligible draft or unpaid invoice, never a paid invoice."""
        return propose("void_invoice", dict(record_id=record_id))

    def reverse_payment(record_id: int) -> dict:
        """Propose reversing an identified payment, retaining its audit history."""
        return propose("reverse_payment", dict(record_id=record_id))

    return [
        set_service_archive, void_invoice, reverse_payment,
        get_expenses, record_expense, update_expense, delete_expense, create_project_from_quotation, link_quotation_to_project,
        get_services,
        create_service,
        update_service,
        create_quotation,
        get_quotations,
        update_quotation,
        create_invoice,
        get_invoices,
        set_quotation_status,
        convert_quotation_to_invoice,
        issue_invoice,
        update_invoice,
        record_payment,
        get_payments,
        generate_document_pdf,
    ]
