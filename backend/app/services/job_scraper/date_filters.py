from datetime import datetime, timedelta, timezone

DATE_POSTED_DAYS = {"24h": 1, "3d": 3, "7d": 7, "30d": 30}


def days_for(date_posted: str | None) -> int | None:
    if date_posted is None:
        return None
    return DATE_POSTED_DAYS.get(date_posted)


def cutoff_for(date_posted: str | None) -> datetime | None:
    days = days_for(date_posted)
    if days is None:
        return None
    return datetime.now(timezone.utc) - timedelta(days=days)