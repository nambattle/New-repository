
"""News-only collection coordinator."""
import json
from pathlib import Path
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

from modules.article_extractor import ArticleExtractor
from modules.cache_manager import CacheManager
from modules.feed_reader import FeedReader
from modules.news_classifier import classify_news, is_promotional
from modules.sources import RSS_SOURCES
from modules.text_utils import clean_text, parse_date

logger = logging.getLogger(__name__)


class MarketDataCollector:
    def __init__(
        self,
        cache_file="cache/scraped_urls.json",
        news_max_age_hours=168,
        article_timeout=15,
        feed_timeout=15,
        max_articles_per_feed=10,
        max_body_chars=8000,
        exclusion_log="logs/news_filter_exclusions.jsonl",
    ):
        self.news_max_age_hours = max(1, int(news_max_age_hours))
        self.max_articles_per_feed = max(1, int(max_articles_per_feed))
        self.cache = CacheManager(cache_file)
        self.session = requests.Session()
        self.feed_reader = FeedReader(timeout=feed_timeout, session=self.session)
        self.article_extractor = ArticleExtractor(
            timeout=article_timeout,
            max_chars=max_body_chars,
            session=self.session,
        )
        self.rss_urls = RSS_SOURCES
        self.exclusion_log = Path(exclusion_log)

    def _record_exclusion(
        self, title, link, source, reason, status="", body_length=0
    ):
        record = {
            "excluded_at": datetime.now(timezone.utc).isoformat(),
            "title": title,
            "link": link,
            "source": source,
            "reason": reason,
            "extraction_status": status,
            "body_length": body_length,
        }
        try:
            self.exclusion_log.parent.mkdir(parents=True, exist_ok=True)
            with self.exclusion_log.open("a", encoding="utf-8") as file:
                file.write(json.dumps(record, ensure_ascii=False) + "\n")
        except OSError as exc:
            logger.warning("Could not write exclusion log: %s", exc)

    @staticmethod
    def _is_blocked_link(link):
        host = (urlparse(link).hostname or "").lower()
        blocked_domains = ("fool.com", "theascent.com")
        return any(
            host == domain or host.endswith("." + domain)
            for domain in blocked_domains
        )

    def fetch_economic_news(self):
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=self.news_max_age_hours)
        future_limit = now + timedelta(hours=12)

        seen_urls = set()
        news = []

        for source in self.rss_urls:
            accepted = 0
            seen_titles = set()

            try:
                entries = self.feed_reader.read(source)
            except Exception as exc:
                logger.warning(
                    "RSS collection failed (%s): %s", source["name"], exc
                )
                continue

            for entry in entries:
                title = clean_text(getattr(entry, "title", ""))
                link = str(getattr(entry, "link", "") or "").strip()

                if not title or urlparse(link).scheme not in {"http", "https"}:
                    continue

                if self._is_blocked_link(link):
                    continue

                published = parse_date(entry)
                if published is None:
                    continue

                if published < cutoff or published > future_limit:
                    continue

                normalized_title = "".join(
                    ch.casefold() for ch in title if ch.isalnum()
                )

                if link in seen_urls or normalized_title in seen_titles:
                    continue

                seen_urls.add(link)
                seen_titles.add(normalized_title)

                summary = clean_text(
                    getattr(entry, "summary", "")
                    or getattr(entry, "description", "")
                )

                if source["name"].startswith("Google_News_"):
                    body = ""
                    extraction_status = "metadata_only"
                    truncated = False
                else:
                    body, extraction_status, truncated = (
                        self.article_extractor.extract(link)
                    )

                body = clean_text(body)
                body_length = len(body)

                if (
                    not extraction_status.startswith("article_body")
                    or body_length < 80
                ):
                    self._record_exclusion(
                        title, link, source["name"],
                        "본문 추출 실패 또는 본문 부족",
                        extraction_status, body_length,
                    )
                    continue

                if is_promotional(title, body):
                    self._record_exclusion(
                        title, link, source["name"],
                        "홍보·행사·수상성 기사",
                        extraction_status, body_length,
                    )
                    continue

                sectors = classify_news(title, body)

                if not sectors:
                    self._record_exclusion(
                        title, link, source["name"],
                        "투자 관련 분야 및 주요 이슈 미확인",
                        extraction_status, body_length,
                    )
                    continue

                collected_at = datetime.now(timezone.utc)

                self.cache.add_success(link)

                news.append({
                    "title": title,
                    "body": body,
                    "summary": summary,
                    "source": source["name"],
                    "language": source["language"],
                    "link": link,
                    "published_at": published.isoformat(),
                    "collected_at": collected_at.isoformat(),
                    "date_status": "known",
                    "extraction_status": extraction_status,
                    "body_length": body_length,
                    "body_truncated": truncated,
                    "sectors": sectors,
                })

                accepted += 1

                if accepted >= self.max_articles_per_feed:
                    break

        self.cache.save()
        news.sort(key=lambda item: item["published_at"], reverse=True)
        logger.info("Investment news collection completed: %d articles", len(news))
        return news
