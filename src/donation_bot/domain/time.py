"""Time & reporting-period helpers.

Timestamps are stored in UTC; report periods are bucketed in the **organization
time zone** (default ``Asia/Tashkent``). A "day" is a calendar day in that zone.
See ``docs/BUSINESS_RULES.md`` §5 (BR-R4/BR-R5) and
``docs/adr/0007-reports-derived-from-ledger.md``.

A :class:`Period` is a half-open UTC interval ``[start, end)`` suitable for
``event_at >= start AND event_at < end`` queries, so periods never overlap or
double-count at boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

DEFAULT_ORG_TIMEZONE = "Asia/Tashkent"


def _tz(org_timezone: str) -> ZoneInfo:
    return ZoneInfo(org_timezone)


@dataclass(frozen=True, slots=True)
class Period:
    """A half-open UTC interval ``[start, end)`` with a human label."""

    start: datetime
    end: datetime
    label: str

    def __post_init__(self) -> None:
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise ValueError("Period bounds must be timezone-aware (UTC)")
        if self.end <= self.start:
            raise ValueError("Period end must be after start")

    def contains(self, moment: datetime) -> bool:
        return self.start <= moment < self.end


def _to_utc(local_dt: datetime) -> datetime:
    return local_dt.astimezone(timezone.utc)


def day_period(day: date, org_timezone: str = DEFAULT_ORG_TIMEZONE) -> Period:
    """The calendar day ``day`` in the org time zone, as a UTC interval."""
    tz = _tz(org_timezone)
    start_local = datetime(day.year, day.month, day.day, tzinfo=tz)
    end_local = start_local + timedelta(days=1)
    return Period(_to_utc(start_local), _to_utc(end_local), day.isoformat())


def month_period(year: int, month: int, org_timezone: str = DEFAULT_ORG_TIMEZONE) -> Period:
    tz = _tz(org_timezone)
    start_local = datetime(year, month, 1, tzinfo=tz)
    if month == 12:
        end_local = datetime(year + 1, 1, 1, tzinfo=tz)
    else:
        end_local = datetime(year, month + 1, 1, tzinfo=tz)
    return Period(_to_utc(start_local), _to_utc(end_local), f"{year:04d}-{month:02d}")


def year_period(year: int, org_timezone: str = DEFAULT_ORG_TIMEZONE) -> Period:
    tz = _tz(org_timezone)
    start_local = datetime(year, 1, 1, tzinfo=tz)
    end_local = datetime(year + 1, 1, 1, tzinfo=tz)
    return Period(_to_utc(start_local), _to_utc(end_local), f"{year:04d}")


def custom_period(
    start_day: date, end_day_inclusive: date, org_timezone: str = DEFAULT_ORG_TIMEZONE
) -> Period:
    """A custom inclusive day range ``[start_day, end_day_inclusive]`` in org tz."""
    if end_day_inclusive < start_day:
        raise ValueError("end day must not be before start day")
    tz = _tz(org_timezone)
    start_local = datetime(start_day.year, start_day.month, start_day.day, tzinfo=tz)
    end_local = datetime(
        end_day_inclusive.year, end_day_inclusive.month, end_day_inclusive.day, tzinfo=tz
    ) + timedelta(days=1)
    return Period(
        _to_utc(start_local),
        _to_utc(end_local),
        f"{start_day.isoformat()}..{end_day_inclusive.isoformat()}",
    )
