from datetime import datetime, date
from zoneinfo import ZoneInfo
from core.config import settings


def business_today() -> date:
    """Return today's date in the configured business timezone."""

    return datetime.now(ZoneInfo(settings.timezone)).date()
