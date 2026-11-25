from database.connection import SessionLocal
from services.analytics import summary


def build_analytics_tools(workspace_id, downloads) -> list:
    """Expose deterministic business analytics and report downloads."""

    def get_business_summary() -> dict:
        """Retrieve actual business KPIs and recent activity."""

        with SessionLocal() as db:

            return summary(db, workspace_id)

    def get_revenue_summary() -> dict:
        """Retrieve current month collections and six-month trend."""

        data = get_business_summary()

        return {"revenue": data["revenue"], "trend": data["trend"]}

    def get_outstanding_payments() -> dict:
        """Retrieve issued invoice outstanding and overdue totals."""

        data = get_business_summary()

        return {"outstanding": data["outstanding"], "overdue": data["overdue"]}

    def get_project_summary() -> dict:
        """Retrieve project status distribution and approaching deadlines."""

        data = get_business_summary()

        return {"distribution": data["distribution"], "deadlines": data["deadlines"]}

    def generate_business_report() -> dict:
        """Prepare the current business performance PDF download."""

        link = {"path": "/overview/report", "label": "Business performance report.pdf"}
        downloads.append(link)

        return link

    def get_financial_performance(month: str | None = None) -> dict:
        """Get cash receipts, expenses and surplus for the specified YYYY-MM month."""
        from datetime import datetime
        if month is not None:
            try:
                if datetime.strptime(month, "%Y-%m").strftime("%Y-%m") != month:
                    raise ValueError()
            except ValueError:
                return {"error": "Use YYYY-MM for the month"}
        with SessionLocal() as db:
            return summary(db, workspace_id, month)

    def get_project_finances(project_id: int | None = None) -> list:
        """Get cash receipts, expenses, surplus and balances by project."""
        from services.analytics import project_finances
        with SessionLocal() as db:
            rows = []
            for row in project_finances(db, workspace_id):
                if project_id is None or row["id"] == project_id:
                    rows.append(row)
            return rows

    return [
        get_financial_performance, get_project_finances,
        get_business_summary,
        get_revenue_summary,
        get_outstanding_payments,
        get_project_summary,
        generate_business_report,
    ]
