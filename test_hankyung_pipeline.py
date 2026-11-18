
import json
import tempfile
import shutil
from pathlib import Path
from collections import Counter

from modules.collector import MarketDataCollector

sources = [
    {
        "name": "Hankyung_Economy",
        "url": "https://www.hankyung.com/feed/economy",
        "language": "ko",
    },
    {
        "name": "Hankyung_Finance",
        "url": "https://www.hankyung.com/feed/finance",
        "language": "ko",
    },
    {
        "name": "Hankyung_IT",
        "url": "https://www.hankyung.com/feed/it",
        "language": "ko",
    },
    {
        "name": "Hankyung_International",
        "url": "https://www.hankyung.com/feed/international",
        "language": "ko",
    },
]

temp_dir = tempfile.mkdtemp(prefix="hankyung_pipeline_test_")

try:
    collector = MarketDataCollector(
        cache_file=str(Path(temp_dir) / "cache.json"),
        exclusion_log=str(Path(temp_dir) / "excluded.jsonl"),
        max_articles_per_feed=5,
    )

    collector.rss_urls = sources

    print("한국경제 4개 분야 실제 수집 시험 시작")

    accepted = collector.fetch_economic_news()

    log_path = Path(temp_dir) / "excluded.jsonl"
    excluded = []

    if log_path.exists():
        excluded = [
            json.loads(line)
            for line in log_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    accepted_counts = Counter(x.get("source") for x in accepted)
    excluded_counts = Counter(x.get("source") for x in excluded)

    print("\n===== 분야별 결과 =====")

    for source in sources:
        name = source["name"]
        print(
            f"{name}: 채택 {accepted_counts[name]}건 / "
            f"제외 {excluded_counts[name]}건"
        )

    print("\n===== 본문 추출 상태 =====")
    print(Counter(x.get("extraction_status") for x in accepted))

    print("\n===== 제외 사유 =====")
    print(Counter(x.get("reason") for x in excluded))

    print("\n===== 실제 채택 기사 =====")
    for item in accepted:
        print(
            f"[{item.get('source')}] "
            f"{item.get('title')} "
            f"| 본문 {len(item.get('body') or '')}자"
        )

    print("\n시험 종료")
    print("기존 뉴스 JSON 및 정식 RSS 설정 변경 없음")

finally:
    shutil.rmtree(temp_dir, ignore_errors=True)
