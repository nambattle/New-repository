





















"""Merge collected materials and enforce retention policies."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from email.utils import parsedate_to_datetime


LONG_TERM_TYPES = {
    "newsletter",
    "market_briefing",
    "independent_commentary",
}

SHORT_TERM_TYPES = {
    "news",
    "official_disclosure",
}

LONG_TERM_DAYS = 30
SHORT_TERM_DAYS = 7


def parse_datetime(value):
    if not value:
        return None

    try:
        if isinstance(value, datetime):
            parsed = value
        else:
            text = str(value).strip()

            try:
                parsed = datetime.fromisoformat(
                    text.replace("Z", "+00:00")
                )
            except ValueError:
                parsed = parsedate_to_datetime(text)

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc)

    except (ValueError, TypeError, OverflowError):
        return None


def normalize_url(url):
    if not url:
        return ""

    try:
        parts = urlsplit(str(url).strip())
        return urlunsplit((
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path.rstrip("/"),
            parts.query,
            "",
        ))
    except ValueError:
        return str(url).strip()


def retention_anchor(item):
    source_type = item.get("source_type") or "news"

    if source_type in LONG_TERM_TYPES:
        return parse_datetime(item.get("collected_at")), LONG_TERM_DAYS

    if source_type in SHORT_TERM_TYPES:
        return parse_datetime(item.get("published_at")), SHORT_TERM_DAYS

    return None, None


def item_keys(item):
    source_type = item.get("source_type") or "news"

    if source_type == "official_disclosure":
        disclosure_id = str(item.get("disclosure_id") or "").strip()
        if disclosure_id:
            return [("disclosure", disclosure_id)]

    keys = []

    url = normalize_url(item.get("link"))
    if url:
        keys.append(("url", url))

    source = str(item.get("source") or "unknown").strip().casefold()
    title = " ".join(str(item.get("title") or "").casefold().split())

    if title:
        keys.append(("source_title", source, title))

    return keys


def load_existing(path):
    if not path.exists():
        return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        raise RuntimeError(f"기존 뉴스 파일을 읽을 수 없습니다: {path}")


def merge_and_prune(new_items, output_path, now=None):
    path = Path(output_path)
    current_time = parse_datetime(now) if now else datetime.now(timezone.utc)

    if current_time is None:
        raise ValueError("기준 시각이 올바르지 않습니다.")

    existing_items = load_existing(path)
    merged = existing_items + list(new_items)

    unique_items = []
    seen_keys = set()
    expired_count = 0
    invalid_date_count = 0
    duplicate_count = 0

    for item in merged:
        if not isinstance(item, dict):
            continue

        anchor, retention_days = retention_anchor(item)

        if anchor is None or retention_days is None:
            invalid_date_count += 1
            continue

        cutoff = current_time - timedelta(days=retention_days)

        if anchor < cutoff:
            expired_count += 1
            continue

        keys = item_keys(item)

        if any(key in seen_keys for key in keys):
            duplicate_count += 1
            continue

        seen_keys.update(keys)
        unique_items.append(item)

    unique_items.sort(
        key=lambda item: retention_anchor(item)[0],
        reverse=True,
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")

    temp_path.write_text(
        json.dumps(unique_items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temp_path.replace(path)

    return {
        "previous_count": len(existing_items),
        "incoming_count": len(new_items),
        "saved_count": len(unique_items),
        "expired_count": expired_count,
        "invalid_date_count": invalid_date_count,
        "duplicate_count": duplicate_count,
        "saved_path": str(path.resolve()),
    }