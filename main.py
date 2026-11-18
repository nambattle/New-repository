"""Run unified news and reference-material collection."""

from collections import Counter
from pathlib import Path

from core.collector_manager import CollectorManager
from storage.retention_manager import merge_and_prune


OUTPUT_PATH = Path("data/news_latest.json")
MIN_BODY_LENGTH = 80


def main():
    manager = CollectorManager()

    collected = manager.collect_all(include_legacy_rss=True)

    valid_items = []
    excluded_count = 0

    for item in collected:
        if not item.get("source_type"):
            item["source_type"] = "news"

        body = str(item.get("body") or "").strip()
        status = str(item.get("extraction_status") or "")

        if status.startswith("article_body") and len(body) >= MIN_BODY_LENGTH:
            item["body_length"] = len(body)
            valid_items.append(item)
        else:
            excluded_count += 1

    result = merge_and_prune(valid_items, OUTPUT_PATH)

    source_counts = Counter(
        item.get("source", "unknown")
        for item in valid_items
    )

    type_counts = Counter(
        item.get("source_type", "unknown")
        for item in valid_items
    )

    print("Unified collection completed")
    print("Newly collected:", len(collected))
    print("New items with original body:", len(valid_items))
    print("Excluded without sufficient original body:", excluded_count)

    print("\nRetention and storage results")
    print("Previous items:", result["previous_count"])
    print("Incoming items:", result["incoming_count"])
    print("Saved active items:", result["saved_count"])
    print("Expired items removed:", result["expired_count"])
    print("Invalid or missing dates removed:", result["invalid_date_count"])
    print("Duplicates removed:", result["duplicate_count"])

    print("\nNew collection by source:")
    for source, count in sorted(source_counts.items()):
        print(f"  {source}: {count}")

    print("New collection by type:", dict(type_counts))
    print("Saved file:", result["saved_path"])


if __name__ == "__main__":
    main()