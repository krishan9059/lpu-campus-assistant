"""Time helpers, isolated so that date-dependent logic stays testable."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo


def today_in(timezone: str) -> date:
    return datetime.now(ZoneInfo(timezone)).date()
