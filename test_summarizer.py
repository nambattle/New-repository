import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.collector import MarketDataCollector
from modules.summarizer import NewsSummarizer

collector = MarketDataCollector()
summarizer = NewsSummarizer()

print("--- [3] 뉴스 요약 및 섹터 매핑 테스트 ---")
raw_news = collector.fetch_economic_news()
mapped_news = summarizer.summarize_and_map_news(raw_news)

for idx, item in enumerate(mapped_news, 1):
    print(f"{idx}. [{', '.join(item['sectors'])}] {item['title']}")
