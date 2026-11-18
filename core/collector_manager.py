
from collections import Counter

from modules.collector import MarketDataCollector
from collectors.dhsignals import DHSignalsCollector
from collectors.mooconomy import MooConomyCollector
from collectors.marketbrief import MarketBriefCollector
from collectors.kind import KindCollector
from collectors.owenanalytics import OwenAnalyticsCollector
from core.deduplicator import remove_duplicates
from core.event_grouper import add_event_groups


class CollectorManager:
    def __init__(self):
        self.collectors = [
            DHSignalsCollector(),
            MooConomyCollector(),
            MarketBriefCollector(),
            KindCollector(),
            OwenAnalyticsCollector(),
        ]

    def collect_all(self, include_legacy_rss=True):
        all_items = []

        if include_legacy_rss:
            try:
                legacy = MarketDataCollector()
                items = legacy.fetch_economic_news()
                all_items.extend(items)
                print(f"[Legacy RSS] collected: {len(items)}")
            except Exception as exc:
                print(f"[Legacy RSS] collection failed: {exc}")

        for collector in self.collectors:
            try:
                items = collector.collect()
                all_items.extend(items)
                print(f"[{collector.source_name}] collected: {len(items)}")
            except Exception as exc:
                print(f"[{collector.source_name}] collection failed: {exc}")

        # Remove only exact duplicates, preserving same-event coverage
        # published independently by different sources.
        unique_items = remove_duplicates(all_items)

        # Add event metadata; no article is removed here.
        grouped_items = add_event_groups(unique_items)

        grouped_items.sort(
            key=lambda item: item.get("published_at") or "",
            reverse=True,
        )

        groups = {}
        for item in grouped_items:
            group_id = item.get("event_group_id")
            groups.setdefault(group_id, []).append(item)

        multi_article_groups = [
            members for members in groups.values()
            if len(members) > 1
        ]

        print(
            f"[Combined collection] total {len(all_items)} / "
            f"after exact deduplication {len(unique_items)}"
        )
        print(
            f"[Event grouping] groups {len(groups)} / "
            f"multi-article events {len(multi_article_groups)}"
        )

        return grouped_items
