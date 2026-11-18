
"""Exact duplicate handling while preserving independent publisher coverage."""

import re
from urllib.parse import urlsplit, urlunsplit


def normalize_url(url):
    if not url:
        return ""

    try:
        parts = urlsplit(url.strip())
        return urlunsplit((
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path.rstrip("/"),
            parts.query,
            "",
        ))
    except ValueError:
        return url.strip()


def normalize_title(title):
    return re.sub(r"\s+", " ", (title or "").strip()).casefold()


def remove_duplicates(items):
    results = []
    seen_urls = set()
    seen_source_titles = set()
    seen_disclosures = set()

    for item in items:
        if item.get("source_type") == "official_disclosure":
            disclosure_id = str(
                item.get("disclosure_id") or ""
            ).strip()

            if disclosure_id:
                if disclosure_id in seen_disclosures:
                    continue

                seen_disclosures.add(disclosure_id)
                results.append(item)
                continue

        url = normalize_url(item.get("link", ""))
        title = normalize_title(item.get("title", ""))
        source = str(item.get("source") or "unknown").strip().casefold()

        source_title = (source, title)

        # Same URL is an exact duplicate.
        # Same title is a duplicate only within the same publisher/feed.
        if (url and url in seen_urls) or (
            title and source_title in seen_source_titles
        ):
            continue

        if url:
            seen_urls.add(url)

        if title:
            seen_source_titles.add(source_title)

        results.append(item)

    return results
