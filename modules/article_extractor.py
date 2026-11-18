"""Fetch publisher pages and extract actual article bodies."""
import logging
from urllib.parse import urlparse

import trafilatura

logger = logging.getLogger(__name__)


class ArticleExtractor:
    def __init__(self, timeout=15, max_chars=8000, session=None):
        self.timeout = timeout
        self.max_chars = max_chars
        self.session = session

    def extract(self, url):
        host = (urlparse(url).hostname or '').lower()

        try:
            headers = {}
            if host == "hankyung.com" or host.endswith(".hankyung.com"):
                headers = {
                    "User-Agent": "Mozilla/5.0 (compatible; MorningBriefing/1.0)",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                }

            response = self.session.get(
                url,
                timeout=self.timeout,
                headers=headers,
            )
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "").lower()

            if content_type and not any(
                x in content_type for x in ("html", "text/")
            ):
                logger.warning(
                    "Unsupported content: host=%s type=%s",
                    host, content_type
                )
                return "", "unsupported_content_type", False

            text = trafilatura.extract(
                response.text,
                include_comments=False,
                include_tables=False,
                include_links=False,
                favor_recall=True,
            ) or ""

            text = " ".join(text.split())

            if len(text) < 80:
                logger.warning(
                    "Extraction failed: host=%s final_url=%s html_length=%s extracted_length=%s",
                    host,
                    response.url,
                    len(response.text),
                    len(text),
                )
                return "", "extraction_failed", False

            truncated = len(text) > self.max_chars

            return text[:self.max_chars], (
                "article_body_truncated" if truncated else "article_body"
            ), truncated

        except Exception as exc:
            logger.warning(
                "Fetch failed: host=%s error=%s: %s",
                host,
                type(exc).__name__,
                exc,
            )
            return "", "fetch_failed", False
