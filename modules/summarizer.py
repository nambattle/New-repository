class NewsSummarizer:
    def __init__(self):
        # 실제 경제 뉴스 트렌드에 맞춘 확장된 키워드 사전
        self.sector_keywords = {
            "반도체/테크": ["반도체", "SK하이닉스", "삼성전자", "DB하이텍", "HBM", "메모리", "AI", "테크", "미국"],
            "방산/중공업": ["한화에어로스페이스", "현대로템", "효성중공업", "방산", "수주", "중공업", "조선"],
            "거시경제/증시": ["금리", "연준", "환율", "물가", "채권", "국채", "변동장", "증시", "월가", "IB"],
            "부동산/대출/금융": ["주담대", "모기지", "대출", "부동산", "보험", "국민연금", "ETF", "잭팟"]
        }

    def summarize_and_map_news(self, news_list):
        """수집된 뉴스를 분석하여 주요 키워드 및 연관 섹터 매핑"""
        processed_news = []
        
        for item in news_list:
            title = item["title"]
            matched_sectors = []
            
            for sector, keywords in self.sector_keywords.items():
                if any(kw in title for kw in keywords):
                    if sector not in matched_sectors:
                        matched_sectors.append(sector)
            
            if not matched_sectors:
                matched_sectors.append("일반시황")
                
            processed_news.append({
                "title": title,
                "link": item["link"],
                "sectors": matched_sectors
            })
            
        return processed_news
