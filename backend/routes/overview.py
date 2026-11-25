from fastapi import APIRouter, Response
from core.security import DB, Tenant
from services.analytics import summary
from services.pdf import report_pdf

router = APIRouter(prefix="/api/overview", tags=["Overview"])


@router.get("")
def overview(db: DB, workspace: Tenant, month: str | None = None) -> dict:
    """Return business dashboard metrics."""

    from datetime import datetime
    from fastapi import HTTPException
    if month is not None:
        try:
            if datetime.strptime(month, "%Y-%m").strftime("%Y-%m") != month:
                raise ValueError()
        except ValueError:
            raise HTTPException(422, "Choose a valid month")
    return summary(db, workspace.id, month)


@router.get("/report")
def report(db: DB, workspace: Tenant) -> Response:
    """Download a business performance PDF."""

    return Response(
        report_pdf(db, workspace),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="business-report.pdf"'},
    )


