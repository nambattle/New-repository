
import json
import tempfile
import shutil
from pathlib import Path
from collections import Counter, defaultdict

from modules.collector import MarketDataCollector

probe_path = Path("data/rss_feed_probe.json")
probe = json.loads(probe_path.read_text(encoding="utf-8"))

sources = []

for item in probe:
    if item.get("status") != "OK":
        continue

    name = item["name"]
    language = "en" if name.startswith(("CNBC_", "WSJ_")) else "ko"

    sources.append({
        "name": name,
        "url": item["url"],
        "language": language,
    })

temp_dir = tempfile.mkdtemp(prefix="expanded_rss_test_")

try:
    collector = MarketDataCollector(
        cache_file=str(Path(temp_dir) / "cache.json"),
        exclusion_log=str(Path(temp_dir) / "excluded.jsonl"),
        max_articles_per_feed=5,
    )

    # Use all verified feeds only for this isolated test.
    collector.rss_urls = sources

    print("실제 본문 수집 시험:", len(sources), "개 피드")
    print("피드별 최대 채택:", 5, "건")
    print("기존 뉴스 JSON 및 sources.py 변경 없음")
    print()

    accepted = collector.fetch_economic_news()

    exclusion_path = Path(temp_dir) / "excluded.jsonl"
    excluded = []

    if exclusion_path.exists():
        excluded = [
            json.loads(line)
            for line in exclusion_path.read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip()
        ]

    accepted_by_source = Counter(
        x.get("source", "unknown") for x in accepted
    )
    excluded_by_source = Counter(
        x.get("source", "unknown") for x in excluded
    )
    excluded_by_reason = Counter(
        x.get("reason", "unknown") for x in excluded
    )

    print("\n===== 실제 본문 채택 결과 =====")
    print("채택:", len(accepted))
    print("제외:", len(excluded))
    print("출처별 채택:")

    for source in sorted(
        set(accepted_by_source) | set(excluded_by_source)
    ):
        print(
            f"{source}: 채택 {accepted_by_source[source]} / "
            f"제외 {excluded_by_source[source]}"
        )

    print("\n===== 제외 사유 =====")
    print(dict(excluded_by_reason))

    print("\n===== 채택된 기사 =====")
    for item in accepted:
        print(
            f"[{item.get('source')}] "
            f"{item.get('title')} "
            f"(본문 {len(item.get('body') or '')}자)"
        )

    print("\n===== 본문 수집 검증 종료 =====")

finally:
    shutil.rmtree(temp_dir, ignore_errors=True)
