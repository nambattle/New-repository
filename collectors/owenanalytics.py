
import re
from datetime import datetime
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
from .base_collector import BaseCollector


class OwenAnalyticsCollector(BaseCollector):
    SITEMAP_URL = "https://www.owenanalytics.com.au/sitemap.xml"
    BASE_URL = "https://www.owenanalytics.com.au"
    EXCLUDED_KEYWORDS = (
        "chemo", "post-chemo", "health", "medical",
        "inch bag", "bug out", "personal update"
    )

    def __init__(self, max_pages=20):
        super().__init__("OwenAnalytics")
        self.max_pages = max_pages

    def _get_sitemap_posts(self):
        xml = self.fetch_html(self.SITEMAP_URL)
        root = ET.fromstring(xml)
        posts = []

        for node in root.iter():
            if node.tag.rsplit(chr(125), 1)[-1] != "url":
                continue
            loc = next((child for child in node if child.tag.rsplit(chr(125), 1)[-1] == "loc"), None)
            if loc is None:
                continue

            url = (loc.text or "").strip()
            path = urlparse(url).path.rstrip("/")

            if not path or path == "":
                continue
            if path.startswith("/edition/"):
                continue
            if path in ("/archive", "/about", "/books", "/testimonials"):
                continue

            lastmod_tag = next((child for child in node if child.tag.rsplit(chr(125), 1)[-1] == "lastmod"), None)
            lastmod = (lastmod_tag.text or "").strip() if lastmod_tag is not None else ""

            posts.append({
                "url": url,
                "lastmod": lastmod
            })

        posts.sort(
            key=lambda item: item["lastmod"],
            reverse=True
        )
        return posts

    def _parse_published_date(self, soup, body):
        time_tag = soup.find("time")
        if time_tag:
            value = time_tag.get("datetime") or time_tag.get_text(" ", strip=True)
            if value:
                try:
                    return datetime.fromisoformat(
                        value.replace("Z", "+00:00")
                    ).date().isoformat()
                except ValueError:
                    pass

        patterns = (
            r"\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\b",
            r"\b[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}\b"
        )

        for pattern in patterns:
            match = re.search(pattern, body)
            if match:
                value = match.group(0)
                for fmt in ("%d %b %Y", "%d %B %Y",
                            "%B %d, %Y", "%B %d %Y",
                            "%b %d, %Y", "%b %d %Y"):
                    try:
                        return datetime.strptime(value, fmt).date().isoformat()
                    except ValueError:
                        continue
        return None

    def _is_irrelevant(self, title, categories):
        text = f"{title} {' '.join(categories)}".casefold()
        return any(word in text for word in self.EXCLUDED_KEYWORDS)

    def _extract_article(self, url):
        soup = self.parse_html(self.fetch_html(url))

        title_tag = soup.find("h1") or soup.find("title")
        title = title_tag.get_text(" ", strip=True) if title_tag else ""

        content = soup.find("article") or soup.find("main")
        if content is None:
            content = soup.body

        if content is None:
            return None

        for tag in content.select("script, style, nav, footer, header"):
            tag.decompose()

        body = content.get_text("\n", strip=True)
        body = re.sub(r"\n{3,}", "\n\n", body).strip()

        categories = []
        for tag in content.select("a[href]"):
            href = tag.get("href", "")
            label = tag.get_text(" ", strip=True)
            if "/category/" in href and label and label not in categories:
                categories.append(label)

        original_links = []
        for tag in content.select("a[href]"):
            href = tag.get("href", "").strip()
            if not href:
                continue
            target = self.absolute_url(url, href)
            domain = urlparse(target).netloc.lower()
            if domain and "owenanalytics.com.au" not in domain:
                if target not in original_links:
                    original_links.append(target)

        published_at = self._parse_published_date(soup, body)

        if not title or not body:
            return None

        if self._is_irrelevant(title, categories):
            print(f"[OwenAnalytics] 투자 비관련 글 제외: {title}")
            return None

        item = self.make_item(
            title,
            body,
            url,
            published_at,
            language="en",
            categories=categories,
            original_links=original_links,
            source_type="independent_commentary",
            sitemap_lastmod=None,
            author="Ashley Owen"
        )

        return item

    def collect(self):
        results = []

        posts = self._get_sitemap_posts()
        print(f"[OwenAnalytics] 사이트맵 게시물: {len(posts)}개")

        for post in posts[:self.max_pages]:
            url = post["url"]
            try:
                item = self._extract_article(url)
                if item:
                    item["sitemap_lastmod"] = post["lastmod"] or None
                    results.append(item)
                    print(f"[OwenAnalytics] 수집 성공: {item['title']}")
            except Exception as exc:
                print(f"[OwenAnalytics] 수집 실패: {url} - {exc}")

        return results
