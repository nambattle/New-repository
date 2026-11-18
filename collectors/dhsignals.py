import re
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone

from collectors.base_collector import BaseCollector

class DHSignalsCollector(BaseCollector):
    URL = "https://www.dhsignals.com/briefing"

    def __init__(self):
        super().__init__("DH Signals")

    def collect(self):
        html = self.fetch_html(self.URL)
        soup = self.parse_html(html)
        article = soup.find("article")
        if article is None:
            article = soup.find(attrs={"style": re.compile("white-space\\s*:\\s*pre-wrap", re.I)})
        if article is None:
            raise ValueError("DH Signals 본문 영역을 찾지 못했습니다.")

        title_tag = article.find(["h1", "h2"]) or soup.find("h1") or soup.title
        title = title_tag.get_text(" ", strip=True) if title_tag else "DH Signals 브리핑"
        body = article.get_text("\\n", strip=True)
        body = re.sub(r"\\n{3,}", "\\n\\n", body)
        dates = re.findall(r"20\\d{2}[-./]\\d{1,2}[-./]\\d{1,2}", body)
        published_at = None
        if dates:
            published_at = dates[0].replace(".", "-").replace("/", "-")

        original_links = []
        for link in article.find_all("a", href=True):
            url = self.absolute_url(self.URL, link["href"])
            if url.startswith("http") and "dhsignals.com" not in urlparse(url).netloc:
                original_links.append(url)
        original_links = list(dict.fromkeys(original_links))

        reference_date = None
        for link in soup.find_all("a", href=True):
            query = parse_qs(urlparse(link["href"]).query)
            if query.get("dr"):
                reference_date = query["dr"][0]
                break

        item = self.make_item(
            title=title,
            body=body,
            link=self.URL,
            published_at=published_at,
            source_type="newsletter",
            reference_date=reference_date,
            original_links=original_links
        )
        return [item]
