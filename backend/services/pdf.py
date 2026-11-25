from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from database.models import Client, Document
from database.crud.common import owned
from database.crud.finance import document_details, money
from decimal import Decimal
from services.analytics import summary


def make_pdf(title, business, rows, notes="") -> bytes:
    """Generate a simple branded PDF in memory."""

    buffer = BytesIO()
    styles = getSampleStyleSheet()
    logo = Path(__file__).resolve().parents[2] / "frontend/public/assets/dotlink-logo.png"
    story = []

    if logo.exists():

        brand = Image(str(logo), width=115, height=35)
        brand.hAlign = "LEFT"
        story.append(brand)

    story.extend([
        Paragraph(escape(business), styles["Title"]),
        Paragraph(escape(title), styles["Heading2"]),
        Spacer(1, 18),
    ])
    formatted_rows = []

    for row in rows:

        cells = []

        for value in row:

            cells.append(Paragraph(escape(str(value)), styles["BodyText"]))

        formatted_rows.append(cells)

    table = Table(formatted_rows, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF0FF")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    story.extend([table, Spacer(1, 14), Paragraph(escape(notes), styles["BodyText"])])
    SimpleDocTemplate(buffer).build(story)

    return buffer.getvalue()


def document_pdf(db, workspace, record_id) -> bytes:
    """Render a quotation or invoice owned by the current workspace."""

    document = owned(db, Document, workspace.id, record_id)
    data = document_details(db, document)
    client = owned(db, Client, workspace.id, document.client_id)
    rows = [["Service", "Quantity", "Unit price", "Amount"]]

    for item in data["items"]:

        line_total = money(Decimal(str(item["quantity"])) * Decimal(str(item["unit_price"])))
        rows.append([item["description"], item["quantity"], f'{item["unit_price"]:,.2f}', f'{line_total:,.2f}'])

    rows.extend([
        ["Discount", "", "", f'{document.discount}%'],
        ["Total", "", "", f'{workspace.currency} {document.total:,.2f}'],
    ])
    notes = (
        f"Client: {client.name} ({client.company}) | {client.email} | {client.phone}. "
        f"Business contact: {workspace.business_email} | {workspace.phone} | {workspace.address}. "
        f"Issued: {document.issue_date} | Due: {document.due_date} | "
        f"Status: {document.status}. {document.notes}"
    )

    return make_pdf(f"{document.document_type.title()} #{document.id:05d}", workspace.business_name, rows, notes)


def report_pdf(db, workspace) -> bytes:
    """Generate a business summary report from database totals."""

    data = summary(db, workspace.id)
    rows = [["Metric", "Value"]]

    for key in ["revenue", "expenses", "cash_surplus", "outstanding", "invoiced", "overdue", "active_projects", "clients"]:

        rows.append([key.replace("_", " ").title(), data[key]])

    for item in data["trend"]:

        rows.append([item["month"], item["revenue"]])

    return make_pdf(
        "Business performance report",
        workspace.business_name,
        rows,
        f"Currency: {workspace.currency}. Revenue and expenses reflect recorded cash transactions this month. Cash surplus is not accrual accounting profit.",
    )
