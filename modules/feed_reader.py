"""RSS download and parsing."""
import feedparser
import requests
from urllib.parse import urlparse


class FeedReader:
    def __init__(self, timeout=15, session=None):
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        })

    def read(self, source):
        url = source["url"]
        host = (urlparse(url).hostname or "").lower()

        headers = {}
        if host == "hankyung.com" or host.endswith(".hankyung.com"):
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; MorningBriefing/1.0)",
                "Accept": "application/rss+xml, application/xml, text/xml, */*",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            }

        response = self.session.get(
            url,
            timeout=self.timeout,
            headers=headers,
        )
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
        if not parsed.entries:
            detail = getattr(parsed, "bozo_exception", "RSS에 기사가 없습니다.")
            raise ValueError(str(detail))
        return parsed.entries
