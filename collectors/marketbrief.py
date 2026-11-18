from urllib.parse import urlparse
from .base_collector import BaseCollector

class MarketBriefCollector(BaseCollector):
    ARCHIVE_URL = "https://marketbrief.io.kr/brief"

    def __init__(self, max_pages=5):
        super().__init__("MarketBrief")
        self.max_pages = max_pages

    def collect(self):
        archive = self.parse_html(self.fetch_html(self.ARCHIVE_URL))
        briefs = {}
        for link in archive.select("a[href]"):
            href = link.get("href", "")
            path = urlparse(href).path.rstrip("/")
            parts = path.split("/")
            if len(parts) == 3 and parts[1] == "brief" and len(parts[2]) == 10:
                date_text = parts[2]
                if date_text[4:5] == "-" and date_text[7:8] == "-":
                    briefs[date_text] = self.absolute_url(self.ARCHIVE_URL, href)

        results = []
        for issue_date, url in sorted(briefs.items(), reverse=True)[:self.max_pages]:
            try:
                soup = self.parse_html(self.fetch_html(url))
                title_tag = soup.find("h1") or soup.find("title")
                title = title_tag.get_text(" ", strip=True) if title_tag else "MarketBrief 브리핑"
                content = soup.find("article") or soup.find("main") or soup.body
                body = content.get_text("\\n", strip=True) if content else ""
                if not body:
                    print(f"[MarketBrief] 본문 없음: {url}")
                    continue
                original_links = []
                for tag in content.select("a[href]"):
                    target = self.absolute_url(url, tag.get("href"))
                    domain = urlparse(target).netloc.lower()
                    if domain and "marketbrief.io.kr" not in domain and target not in original_links:
                        original_links.append(target)
                results.append(self.make_item(
                    title, body, url, issue_date,
                    reference_date=issue_date,
                    original_links=original_links,
                    source_type="market_briefing"
                ))
            except Exception as exc:
                print(f"[MarketBrief] 수집 실패: {url} - {exc}")
        return results
