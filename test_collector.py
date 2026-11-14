import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.collector import MarketDataCollector

collector = MarketDataCollector()

print("--- [1] 글로벌 주요 지수 수집 테스트 ---")
indices = collector.fetch_global_indices()
for name, val in indices.items():
    print(f"{name}: {val}")

print("\n--- [2] 경제 뉴스 수집 테스트 ---")
news = collector.fetch_economic_news()
for idx, item in enumerate(news[:5], 1):
    print(f"{idx}. {item['title']}")
