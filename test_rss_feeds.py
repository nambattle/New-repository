
import json
import requests
import feedparser
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from modules.sources import RSS_SOURCES

EXTRA_SOURCES = [
    # CNBC: investment and market sections
    ("CNBC_MarketInsider", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20409666", "en"),
    ("CNBC_Investing", "https://www.cnbc.com/id/15839069/device/rss/rss.html", "en"),
    ("CNBC_Earnings", "https://www.cnbc.com/id/15839135/device/rss/rss.html", "en"),
    ("CNBC_Economy", "https://www.cnbc.com/id/20910258/device/rss/rss.html", "en"),
    ("CNBC_Finance", "https://www.cnbc.com/id/10000664/device/rss/rss.html", "en"),
    ("CNBC_Technology", "https://www.cnbc.com/id/19854910/device/rss/rss.html", "en"),
    ("CNBC_Energy", "https://www.cnbc.com/id/19836768/device/rss/rss.html", "en"),
    ("CNBC_AsiaNews", "https://www.cnbc.com/id/19832390/device/rss/rss.html", "en"),

    # Maeil Business News Korea
    ("Maeil_Economy", "https://www.mk.co.kr/rss/30100041/", "ko"),
    ("Maeil_Corporate", "https://www.mk.co.kr/rss/50100032/", "ko"),
    ("Maeil_International", "https://www.mk.co.kr/rss/30300018/", "ko"),
    ("Maeil_Politics", "https://www.mk.co.kr/rss/30200030/", "ko"),
    ("Maeil_RealEstate", "https://www.mk.co.kr/rss/50300009/", "ko"),

    # Hankyung
    ("Hankyung_Finance", "https://www.hankyung.com/feed/finance", "ko"),
    ("Hankyung_Economy", "https://www.hankyung.com/feed/economy", "ko"),
    ("Hankyung_IT", "https://www.hankyung.com/feed/it", "ko"),
    ("Hankyung_International", "https://www.hankyung.com/feed/international", "ko"),

    # Wall Street Journal / Dow Jones
    ("WSJ_Markets", "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain", "en"),
    ("WSJ_Economy", "https://feeds.content.dowjones.io/public/rss/socialeconomyfeed", "en"),
    ("WSJ_USBusiness", "https://feeds.content.dowjones.io/public/rss/WSJcomUSBusiness", "en"),
    ("WSJ_Technology", "https://feeds.content.dowjones.io/public/rss/RSSWSJD", "en"),
]

candidates = list(RSS_SOURCES)
existing = {x["name"] for x in candidates}

for name, url, language in EXTRA_SOURCES:
    if name not in existing:
        candidates.append({
            "name": name,
            "url": url,
            "language": language,
        })

def check_feed(source):
    name = source["name"]
    url = source["url"]

    try:
        response = requests.get(
            url,
            timeout=12,
            headers={"User-Agent": "Mozilla/5.0 (compatible; MorningBriefing/1.0)"},
        )
        response.raise_for_status()

        parsed = feedparser.parse(response.content)
        entries = parsed.entries
        feed_title = parsed.feed.get("title", "")
        
        if not entries:
            return {
                "name": name,
                "url": url,
                "status": "EMPTY",
                "count": 0,
                "feed_title": feed_title,
                "sample_title": "",
                "error": str(getattr(parsed, "bozo_exception", "")),
            }

        return {
            "name": name,
            "url": url,
            "status": "OK",
            "count": len(entries),
            "feed_title": feed_title,
            "sample_title": entries[0].get("title", ""),
            "error": "",
        }

    except Exception as exc:
        return {
            "name": name,
            "url": url,
            "status": "FAIL",
            "count": 0,
            "feed_title": "",
            "sample_title": "",
            "error": str(exc),
        }

print("RSS 피드 검사 시작:", len(candidates), "개")

results = []

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(check_feed, x) for x in candidates]

    for future in as_completed(futures):
        result = future.result()
        results.append(result)

results.sort(key=lambda x: x["name"])

print("\n===== 피드별 검사 결과 =====")

for x in results:
    print(
        f"[{x['status']}] {x['name']} | "
        f"기사 {x['count']}건 | {x['sample_title'][:65]}"
    )
    if x["error"]:
        print("   오류:", x["error"][:180])

ok = [x for x in results if x["status"] == "OK"]
empty = [x for x in results if x["status"] == "EMPTY"]
failed = [x for x in results if x["status"] == "FAIL"]

report_path = Path("data/rss_feed_probe.json")
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(
    json.dumps(results, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print("\n===== 최종 검사 결과 =====")
print("전체:", len(results))
print("정상:", len(ok))
print("빈 피드:", len(empty))
print("접속 실패:", len(failed))
print("검사 보고서:", report_path.resolve())
print("기존 sources.py 및 뉴스 데이터 변경 없음")
