from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


def parse_date(value):
    """날짜 문자열을 UTC datetime으로 변환한다."""
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = parsedate_to_datetime(str(value))
        except (TypeError, ValueError):
            try:
                dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            except ValueError:
                return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def utc_now():
    return datetime.now(timezone.utc)


def iso_now():
    return utc_now().isoformat()
