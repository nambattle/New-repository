
class NewsSummarizer:
    def __init__(self):
        self.sector_keywords = {
            "반도체/AI/스토리지": [
                "반도체", "AI", "인공지능", "엔비디아", "하이닉스",
                "삼성전자", "HBM", "마이크론", "샌디스크", "SOX",
                "Nvidia", "Micron", "Semiconductor", "Chip", "Memory"
            ],
            "지정학/전쟁/중동": [
                "이란", "우크라이나", "러시아", "전쟁", "호르무즈",
                "해협", "후티", "반군", "사우디", "이스라엘", "중동",
                "Iran", "Ukraine", "Russia", "War", "Hormuz",
                "Houthi", "Middle East", "Israel"
            ],
            "에너지/유가/원자재": [
                "유가", "원유", "WTI", "브렌트유", "경유", "OPEC",
                "석유", "가스", "Oil", "Crude", "Energy", "Gas"
            ],
            "의료/바이오/헬스케어": [
                "의료", "바이오", "제약", "신약", "비만", "릴리",
                "FDA", "임상", "헬스케어", "Pharma", "Biotech",
                "Healthcare", "Lilly", "Drug"
            ],
            "방산/조선/중공업": [
                "방산", "수주", "자율수상함", "HD현대", "한화",
                "조선", "Defense", "Military", "Shipbuilding"
            ],
            "거시경제/금리/환율": [
                "금리", "연준", "Fed", "환율", "달러", "물가",
                "CPI", "인플레이션", "국채", "Rate", "Inflation",
                "Treasury", "Dollar", "Economy"
            ]
        }

    def summarize_and_map_news(self, news_list):
        mapped_results = []

        for item in news_list or []:
            if not isinstance(item, dict):
                continue

            # 원본 항목을 복사해 새 수집기 메타데이터를 보존한다.
            result = dict(item)

            title = str(item.get("title") or item.get("raw_title") or "")
            body = str(
                item.get("body")
                or item.get("summary")
                or item.get("raw_body")
                or "본문 내용 없음"
            )

            # 분류에는 제목과 본문을 모두 사용한다.
            full_text = f"{title} {body}".casefold()

            matched_sectors = []

            for sector, keywords in self.sector_keywords.items():
                if any(str(keyword).casefold() in full_text
                       for keyword in keywords):
                    matched_sectors.append(sector)

            if not matched_sectors:
                matched_sectors = ["일반시황"]

            # 기존 main.py와 DocWriter가 사용하는 필드는 유지한다.
            result["title"] = title
            result["body"] = body
            result["link"] = item.get("link", "")
            result["source"] = item.get("source", "글로벌/국내뉴스")
            result["sectors"] = matched_sectors

            mapped_results.append(result)

        return mapped_results

    def classify_and_map(self, news_list):
        return self.summarize_and_map_news(news_list)
