import feedparser
import yfinance as yf
import requests

class MarketDataCollector:
    def __init__(self):
        self.tickers = {
            "S&P 500": "^GSPC", 
            "Nasdaq": "^IXIC", 
            "EuroStoxx 50": "^STOXX50E", 
            "Nikkei 225": "^N225"
        }
        # 접속 안정성이 검증된 경제 뉴스 RSS 주소로 교체
        self.rss_urls = [
            "https://www.hankyung.com/feed/finance",
            "https://www.mk.co.kr/rss/30100041/"
        ]

    def fetch_global_indices(self):
        data = {}
        for name, ticker in self.tickers.items():
            try:
                t = yf.Ticker(ticker)
                hist = t.history(period="2d")
                if len(hist) >= 2:
                    close_price = hist['Close'].iloc[-1]
                    prev_close = hist['Close'].iloc[-2]
                    change_pct = ((close_price - prev_close) / prev_close) * 100
                    data[name] = {
                        "price": round(close_price, 2), 
                        "change_pct": round(change_pct, 2)
                    }
                else:
                    data[name] = {"price": 0.0, "change_pct": 0.0}
            except Exception as e:
                data[name] = {"error": str(e)}
        return data

    def fetch_economic_news(self):
        news_list = []
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        for url in self.rss_urls:
            try:
                response = requests.get(url, headers=headers, timeout=5)
                feed = feedparser.parse(response.content)
                for entry in feed.entries[:3]:
                    news_list.append({
                        "title": entry.title,
                        "link": entry.link
                    })
            except Exception as e:
                print(f"RSS 수집 에러 ({url}): {e}")
        return news_list
