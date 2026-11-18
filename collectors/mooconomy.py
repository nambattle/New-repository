import re
from urllib.parse import urlparse
from .base_collector import BaseCollector

class MooConomyCollector(BaseCollector):
    ARCHIVE_URL = "https://mooconomy.co.kr/archive/"
    ISSUE_PATTERN = re.compile(r"/issues/(\d{4}-\d{2}-\d{2})\.html")

    def __init__(self, max_pages=5):
        super().__init__("MOO:conomy")
        self.max_pages = max_pages

    def collect(self):
        archive = self.parse_html(self.fetch_html(self.ARCHIVE_URL))
        issues = {}
        for link in archive.select("a[href]"):
            href = link.get("href", "")
            match = self.ISSUE_PATTERN.search(href)
            if match:
                url = self.absolute_url(self.ARCHIVE_URL, href)
                issues[match.group(1)] = url

        results = []
        for issue_date, url in sorted(issues.items(), reverse=True)[:self.max_pages]:
            try:
                soup = self.parse_html(self.fetch_html(url))
                title_tag = soup.find("h1") or soup.find("title")
                title = title_tag.get_text(" ", strip=True) if title_tag else "MOO:conomy 브리핑"
                content = soup.find("article") or soup.find("main") or soup.body
                body = content.get_text("\\n", strip=True) if content else ""
                original_links = []
                if content:
                    for tag in content.select("a[href]"):
                        target = self.absolute_url(url, tag.get("href"))
                        domain = urlparse(target).netloc.lower()
                        if domain and "mooconomy.co.kr" not in domain and target not in original_links:
                            original_links.append(target)
                if body:
                    results.append(self.make_item(
                        title, body, url, issue_date,
                        reference_date=issue_date,
                        original_links=original_links,
                        source_type="market_briefing"
                    ))
            except Exception as exc:
                print(f"[MOO:conomy] 수집 실패: {url} - {exc}")
        return results
