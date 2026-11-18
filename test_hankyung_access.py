
import requests
import feedparser

FEEDS = {
    "경제": "https://www.hankyung.com/feed/economy",
    "금융": "https://www.hankyung.com/feed/finance",
    "IT": "https://www.hankyung.com/feed/it",
    "국제": "https://www.hankyung.com/feed/international",
}

HEADERS = {
    "현재 프로그램": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    },
    "RSS 검사 성공 방식": {
        "User-Agent": "Mozilla/5.0 (compatible; MorningBriefing/1.0)",
    },
    "표준 RSS 요청": {
        "User-Agent": "Mozilla/5.0 (compatible; MorningBriefing/1.0)",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
    },
}

for feed_name, url in FEEDS.items():
    print(f"\n===== {feed_name} =====")

    for method, headers in HEADERS.items():
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=15,
            )
            parsed = feedparser.parse(response.content)

            print(
                method,
                "| HTTP:", response.status_code,
                "| 기사:", len(parsed.entries),
            )

            if response.status_code == 200 and parsed.entries:
                entry = parsed.entries[0]
                print("첫 기사:", entry.get("title", ""))

                # Test whether the article page itself is accessible.
                article_url = entry.get("link", "")
                if article_url:
                    article = requests.get(
                        article_url,
                        headers=headers,
                        timeout=15,
                    )
                    print("본문 페이지 HTTP:", article.status_code)

        except Exception as exc:
            print(method, "| 오류:", str(exc)[:160])

print("\n접속 비교 시험 종료. 기존 프로젝트 파일 변경 없음.")
