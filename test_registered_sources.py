
import json
import tempfile
import shutil
from pathlib import Path
from collections import Counter

from modules.collector import MarketDataCollector
from modules.sources import RSS_SOURCES

temp_dir = tempfile.mkdtemp(prefix="registered_sources_test_")

try:
    collector = MarketDataCollector(
        cache_file=str(Path(temp_dir) / "cache.json"),
        exclusion_log=str(Path(temp_dir) / "excluded.jsonl"),
        max_articles_per_feed=5,
    )

    print("정식 등록 피드:", len(RSS_SOURCES))
    print("최근 48시간 / 피드당 최대 5건")
    print("기존 뉴스 JSON 변경 없음")
    print("\n실제 수집 시작\n")

    accepted = collector.fetch_economic_news()

    log_path = Path(temp_dir) / "excluded.jsonl"
    excluded = []

    if log_path.exists():
        excluded = [
            json.loads(line)
            for line in log_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    accepted_by_source = Counter(
        x.get("source", "unknown") for x in accepted
    )
    excluded_by_source = Counter(
        x.get("source", "unknown") for x in excluded
    )
    reason_counts = Counter(
        x.get("reason", "unknown") for x in excluded
    )

    print("\n===== 출처별 결과 =====")

    for source in RSS_SOURCES:
        name = source["name"]
        print(
            f"{name}: 채택 {accepted_by_source[name]}건 / "
            f"제외 {excluded_by_source[name]}건"
        )

    print("\n===== 전체 결과 =====")
    print("최종 채택:", len(accepted))
    print("제외:", len(excluded))
    print("본문 누락:", sum(
        not str(x.get("body") or "").strip()
        for x in accepted
    ))
    print("분류된 분야:", dict(Counter(
        sector
        for item in accepted
        for sector in item.get("sectors", [])
    )))
    print("제외 사유:", dict(reason_counts))

    print("\n===== 채택 기사 일부 =====")
    for item in accepted:
        print(
            f"[{item.get('source')}] "
            f"{item.get('title')} "
            f"| 본문 {len(item.get('body') or '')}자"
        )

    print("\n===== 시험 완료 =====")
    print("임시 저장소만 사용했습니다.")

finally:
    shutil.rmtree(temp_dir, ignore_errors=True)
