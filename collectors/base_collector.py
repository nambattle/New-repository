from datetime import datetime, timezone
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

class BaseCollector:
    def __init__(self, source_name, timeout=20):
        self.source_name = source_name
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})

    def fetch_html(self, url):
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        return response.text

    def parse_html(self, html):
        return BeautifulSoup(html, "html.parser")

    def absolute_url(self, base_url, link):
        return urljoin(base_url, link or "")

    def make_item(self, title, body, link, published_at=None, **extra):
        body = (body or "").strip()
        item = {
            "title": (title or "").strip(),
            "body": body,
            "summary": "",
            "source": self.source_name,
            "language": "ko",
            "link": link,
            "published_at": published_at,
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "date_status": "available" if published_at else "unknown",
            "extraction_status": "article_body" if body else "extraction_failed",
            "body_length": len(body),
            "body_truncated": False,
            "sectors": [],
            "source_type": "news"
        }
        item.update(extra)
        return item
