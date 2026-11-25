from datetime import timedelta
from decimal import Decimal
from core.dates import business_today
from database.models import Client, Project, Payment, ActivityLog, Expense, Task
from database.crud.common import list_records
from database.crud.finance import get_documents


def total(values) -> float:
    """Add currency values using decimal arithmetic."""

    result = Decimal("0")

    for value in values:

        result += Decimal(str(value))

    return float(result)


def project_finances(db, workspace_id: int) -> list:
    """Compute project cash metrics without counting quotations as income."""
    documents = get_documents(db, workspace_id)
    payments = list_records(db, Payment, workspace_id)
    expenses = list_records(db, Expense, workspace_id)
    result = []
    for project in list_records(db, Project, workspace_id):
        invoices = []
        quoted = Decimal("0")
        for doc in documents:
            if doc["project_id"] != project["id"]:
                continue
            if doc["document_type"] == "invoice" and doc["status"] not in ("Draft", "Void"):
                invoices.append(doc)
            if doc["document_type"] == "quotation" and doc["status"] == "Accepted":
                quoted += Decimal(str(doc["total"]))
        ids = []
        for doc in invoices:
            ids.append(doc["id"])
        received_values = []
        for payment in payments:
            if not payment["reversed"] and payment["invoice_id"] in ids:
                received_values.append(payment["amount"])
        expense_values = []
        for expense in expenses:
            if expense["project_id"] == project["id"]:
                expense_values.append(expense["amount"])
        received = total(received_values)
        spent = total(expense_values)
        result.append({"id": project["id"], "title": project["title"], "quoted": float(quoted),
            "invoiced": total(doc["total"] for doc in invoices), "outstanding": total(doc["balance"] for doc in invoices),
            "received": received, "expenses": spent, "cash_margin": round((received-spent)/received*100,2) if received else None, "cash_surplus": float(Decimal(str(received))-Decimal(str(spent)))})
    return result


def summary(db, workspace_id: int, month: str | None = None) -> dict:
    """Calculate actual business totals and the six-month revenue trend."""

    today = business_today()
    current_month = month or today.isoformat()[:7]
    monthly_expenses = {}
    for expense in list_records(db, Expense, workspace_id):
        key = expense["expense_date"][:7]
        monthly_expenses[key] = monthly_expenses.get(key, Decimal("0")) + Decimal(str(expense["amount"]))
    spent = monthly_expenses.get(current_month, Decimal("0"))
    revenue = Decimal("0")
    outstanding = Decimal("0")
    invoiced = Decimal("0")
    overdue = Decimal("0")
    clients = 0
    active_projects = 0
    deadlines = []
    trend = []
    statuses = {"Pending": 0, "In progress": 0, "Completed": 0, "On hold": 0}
    monthly_payments = {}

    for client in list_records(db, Client, workspace_id):

        if not client["archived"]:

            clients += 1

    for project in list_records(db, Project, workspace_id):

        if project["archived"]:

            continue

        status = project["status"]
        statuses[status] += 1

        if status == "In progress":

            active_projects += 1

        if status != "Completed" and project["deadline"] <= (today + timedelta(days=7)).isoformat():

            deadlines.append(project)

    for payment in list_records(db, Payment, workspace_id):

        if payment["reversed"]:

            continue

        month = payment["payment_date"][:7]
        amount = Decimal(str(payment["amount"]))
        monthly_payments[month] = monthly_payments.get(month, Decimal("0")) + amount

        if month == current_month:

            revenue += amount

    for document in get_documents(db, workspace_id):

        if document["document_type"] != "invoice" or document["status"] in ("Draft", "Void"):

            continue

        balance = Decimal(str(document["balance"]))
        invoiced += Decimal(str(document["total"]))
        outstanding += balance

        if document["due_date"] < today.isoformat():

            overdue += balance

    for offset in range(5, -1, -1):

        month_index = today.year * 12 + today.month - 1 - offset
        month = f"{month_index // 12}-{month_index % 12 + 1:02d}"
        trend.append({"month": month, "revenue": float(monthly_payments.get(month, 0)), "expenses": float(monthly_expenses.get(month, 0))})

    distribution = []

    for status, count in statuses.items():

        distribution.append({"name": status, "value": count})

    activity = []

    for row in list_records(db, ActivityLog, workspace_id):

        # Ignore legacy notifications from the earlier MVP version.
        if not row["is_notification"]:

            activity.append(row)

        if len(activity) == 8:

            break

    return {
        "revenue": float(revenue),
        "month": current_month,
        "expenses": float(spent),
        "cash_surplus": float(revenue - spent),
        "cash_margin": float((revenue - spent) / revenue * 100) if revenue else None,
        "tasks": list_records(db, Task, workspace_id),
        "project_finances": project_finances(db, workspace_id),
        "outstanding": float(outstanding),
        "active_projects": active_projects,
        "clients": clients,
        "invoiced": float(invoiced),
        "overdue": float(overdue),
        "trend": trend,
        "distribution": distribution,
        "deadlines": deadlines,
        "activity": activity,
    }
