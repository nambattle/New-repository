import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.collector import MarketDataCollector
from modules.summarizer import NewsSummarizer
from modules.doc_writer import BriefingDocWriter

def run_morning_briefing():
    print("1. 글로벌 증시 및 경제 뉴스 수집 중...")
    collector = MarketDataCollector()
    indices = collector.fetch_global_indices()
    raw_news = collector.fetch_economic_news()

    print("2. 뉴스 키워드 분석 및 섹터 매핑 중...")
    summarizer = NewsSummarizer()
    mapped_news = summarizer.summarize_and_map_news(raw_news)

    print("3. 아침 브리핑 리포트 문서 생성 중...")
    writer = BriefingDocWriter()
    report_content = writer.format_briefing(indices, mapped_news)
    saved_path = writer.save_to_file(report_content)

    print(f"\n✅ 브리핑 생성 완료! 저장 위치: {saved_path}")
    print("-" * 50)
    print(report_content)

if __name__ == "__main__":
    run_morning_briefing()
