import feedparser
from urllib.parse import urlparse, parse_qs, urljoin

from .base_collector import BaseCollector


class KindCollector(BaseCollector):
    BASE_URL = "https://kind.krx.co.kr"
    RSS_URL = (
        BASE_URL
        + "/disclosure/rsstodaydistribute.do?method=searchRssTodayDistribute"
        + "&repIsuSrtCd=&mktTpCdo=0&searchCorpName=&currentPageSize=100"
    )
    KEYWORDS = (
        "계약", "수주", "공급", "매출", "영업이익", "실적", "잠정",
        "유상증자", "무상증자", "최대주주", "지분", "합병",
        "투자판단", "자기주식", "주식등의대량보유",
    )
    CORRECTION_NOTICES = ()

    def __init__(self, max_items=100):
        super().__init__("KIND_한국거래소")
        self.max_items = max_items

    def _document_url(self, viewer_url):
        """KIND 뷰어에서 본문 문서의 실제 주소를 찾는다."""
        page = self.parse_html(self.fetch_html(viewer_url))
        doc_no = ""

        for option in page.select("select[name='mainDoc'] option"):
            value = option.get("value", "").strip()
            if "|" in value:
                doc_no = value.split("|", 1)[0].strip()
                if doc_no:
                    break

        if not doc_no:
            return ""

        response = self.session.get(
            self.BASE_URL + "/common/disclsviewer.do",
            params={"method": "searchContents", "docNo": doc_no},
            timeout=self.timeout,
        )
        response.raise_for_status()

        raw = response.content.decode("utf-8", errors="replace")
        marker = "parent.setPath("
        start = raw.find(marker)
        if start < 0:
            return ""

        first_comma = raw.find(",", start)
        quote = chr(39)
        q1 = raw.find(quote, first_comma)
        q2 = raw.find(quote, q1 + 1)
        if first_comma < 0 or q1 < 0 or q2 < 0:
            return ""

        return urljoin(self.BASE_URL, raw[q1 + 1:q2])

    def _fetch_document(self, document_url):
        """실제 공시 HTML을 UTF-8 우선으로 읽어 텍스트를 반환한다."""
        response = self.session.get(document_url, timeout=self.timeout)
        response.raise_for_status()

        try:
            html_text = response.content.decode("utf-8-sig")
        except UnicodeDecodeError:
            encoding = response.apparent_encoding or "utf-8"
            html_text = response.content.decode(encoding, errors="replace")

        document = self.parse_html(html_text)
        for tag in document.select("script, style, noscript"):
            tag.decompose()

        return document.get_text("\n", strip=True)

    def collect(self):
        feed = feedparser.parse(self.fetch_html(self.RSS_URL))
        results = []

        for entry in feed.entries[:self.max_items]:
            title = entry.get("title", "").strip()
            if not any(word in title for word in self.KEYWORDS):
                continue

            url = entry.get("link", "").strip()
            summary = entry.get("summary", "")
            published = entry.get("published") or entry.get("updated")
            disclosure_id = parse_qs(
                urlparse(url).query
            ).get("acptNo", [""])[0]

            body = ""
            document_url = ""
            notice_text = ""
            detail_error = ""

            try:
                viewer = self.parse_html(self.fetch_html(url))
                notice_text = viewer.get_text(" ", strip=True)
                document_url = self._document_url(url)

                if document_url:
                    body = self._fetch_document(document_url)
            except Exception as exc:
                detail_error = str(exc)
                print(f"[KIND] 원문 수집 실패: {url} - {exc}")

            if len(body.strip()) >= 100:
                extraction_status = "article_body"
            else:
                body = summary
                extraction_status = (
                    "rss_summary_only" if body else "detail_unavailable"
                )

            item = self.make_item(
                title,
                body,
                url,
                published,
                summary=summary,
                source_type="official_disclosure",
                disclosure_id=disclosure_id,
                verification_status="official_source",
                rss_id=entry.get("id", ""),
                document_url=document_url,
                detail_error=detail_error,
            )
            item["extraction_status"] = extraction_status

            if any(text in notice_text for text in self.CORRECTION_NOTICES):
                item["disclosure_status"] = "correction_pending"
            elif "[정정]" in title:
                item["disclosure_status"] = "correction"
            else:
                item["disclosure_status"] = "original_or_regular"

            results.append(item)

        return results
