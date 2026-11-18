
"""Rule-based investment news classification. No AI analysis."""
import re

SECTOR_KEYWORDS = {
    "반도체/AI": [
        "반도체", "엔비디아", "삼성전자", "하이닉스", "마이크론",
        "HBM", "semiconductor", "nvidia", "micron", "memory", "chip",
        "data center", "artificial intelligence", "AI", "인공지능",
        "데이터센터", "neocloud"
    ],
    "전력/인프라": [
        "전력망", "전력", "변압기", "전력기기", "송전망", "원전",
        "power grid", "transformer", "nuclear power", "infrastructure", "인프라 투자", "인프라", "전력 인프라", "미국 인프라",
        "fiber optic", "broadband"
    ],
    "방산/우주": [
        "방산", "방위산업", "미사일", "우주항공", "위성",
        "defense", "missile", "satellite", "aerospace"
    ],
    "바이오/헬스케어": [
        "제약", "임상", "신약", "바이오", "헬스케어",
        "pharma", "clinical trial", "biotech", "healthcare"
    ],
    "2차전지/전기차": [
        "2차전지", "배터리", "전기차", "양극재", "음극재", "리튬",
        "battery", "electric vehicle", "lithium", "cathode"
    ],
    "화장품/소비재": [
        "화장품", "K뷰티", "뷰티", "면세점", "소비재", "유통",
        "cosmetics", "beauty industry", "consumer goods", "retail sales"
    ],
    "금융": [
        "은행", "금융", "증권사", "보험사", "대출",
        "banking", "financial sector", "credit risk", "insurance"
    ],
    "에너지/원자재": [
        "유가", "원유", "브렌트유", "천연가스", "에너지", "구리", "원자재",
        "crude oil", "oil price", "natural gas", "commodities"
    ],
    "거시경제/금리/환율": [
        "금리", "연준", "환율", "달러", "물가", "국채", "인플레이션",
        "interest rate", "federal reserve", "treasury", "inflation",
        "exchange rate", "dollar", "CPI", "GDP", "의무공개매수", "공개매수법", "자본시장법", "증시 규제", "주식시장 규제"
    ],
    "지정학/무역": [
        "전쟁", "제재", "중동", "이란", "우크라이나", "이스라엘",
        "관세", "수출 통제", "무역 규제", "war", "sanction",
        "tariff", "export controls", "trade restrictions"
    ],
    "기업/증시": [
        "실적", "매출", "영업이익", "순이익", "상장", "인수", "합병",
        "배당", "수주", "공급 계약", "자사주", "주주환원",
        "earnings", "revenue", "profit", "contract", "acquisition",
        "merger", "dividend", "buyback", "IPO", "주가", "주식",
        "주주", "시가총액", "stock", "shares", "share price",
        "stock market", "valuation"
    ],
}

PROMOTION_TERMS = [
    "수상", "우수상", "대상 수상", "시상식", "한국PR대상",
    "어워드", "행사 개최", "참가자 모집", "세미나 개최",
    "컨퍼런스 개최", "홍보 영상", "유튜브 영상", "이벤트 진행",
    "무료 초청", "협찬", "광고", "교육 영상", "노하우",
    "wins award", "award ceremony", "webinar",
    "sponsored content", "promotional video"
]

NON_INVESTMENT_TITLE_TERMS = [
    "[포토]", "[사진]", "[영상]", "포토뉴스", "사진뉴스",
    "오늘의 증시", "증시 시황", "마감 시황", "장 마감",
    "일일 시황", "시황 정리", "증시 마감",
    "stock market today", "market wrap", "market recap",
    "daily market update", "market roundup", "live updates"
]

MATERIAL_TERMS = [
    'CEO', 'CFO', 'executive', 'leadership', 'resignation', 'steps down', 'returns as CEO', 'appointed CEO', 'management change', 'chief executive', 'board of directors', 'corporate governance', 'restructuring', 'capital raising', 'shareholder', '경영진', '최고경영자', '대표이사', '사임', '복귀', '선임', '취임', '경영권', '지배구조', '유상증자', '사업 재편',
    "실적", "매출", "영업이익", "순이익", "수주", "공급 계약",
    "계약 체결", "투자", "인수", "합병", "상장", "배당",
    "자사주", "공장 증설", "생산 확대", "사업 철수",
    "구조조정", "승인", "임상 결과", "수출 통제", "관세",
    "금리 인상", "금리 인하", "주가", "주식", "주주",
    "시가총액", "기업 가치", "투자자", "경기방어주",
    "슈퍼사이클", "시장 점유율", "수익성", "부채", "의무공개매수", "코스피 하락", "하락 가능", "반도체 다 팔", "미리 반도체", "투자 포지션", "portfolio shift", "fund manager", "billionaire investor", "인프라 투자", "인프라", "전력망 투자",
    "차입", "자금 조달", "earnings", "revenue", "profit",
    "contract", "order", "acquisition", "merger", "IPO",
    "dividend", "buyback", "investment", "approval",
    "export controls", "investors", "stock", "shares",
    "share price", "valuation", "debt", "financing",
    "supercycle", "market share", "profitability"
]

def _contains(text, keyword):
    key = keyword.casefold()
    if re.fullmatch(r"[a-z0-9 ]+", key):
        return bool(re.search(
            r"(?<![a-z0-9])" + re.escape(key) + r"(?![a-z0-9])",
            text
        ))
    return key in text

def is_promotional(title, body=""):
    title_text = str(title or "").casefold()
    return any(_contains(title_text, word) for word in PROMOTION_TERMS)

def classify_news(title, body=""):
    title_text = str(title or "").casefold()
    full_text = (title_text + " " + str(body or "")).casefold()
    reject = ["measles", "홍역", "kalshi", "mention markets", "esg 우수 기업", "esg공시 원해", "mk시그널", "상승률 1위", "stocks making the biggest moves", "biggest moves", "lisa cook lawyer", "주식 초고수는 지금", "주식고수는 지금", "5000피 붕괴", "5000피’ 붕괴", "5000선 아래로", "카모 분쟁", "율촌 선임"]
    if any(x in title_text for x in reject):
        return []

    if any(_contains(title_text, word)
           for word in NON_INVESTMENT_TITLE_TERMS):
        return []

    if any(_contains(title_text, word)
           for word in PROMOTION_TERMS):
        return []

    material = any(_contains(full_text, word)
                   for word in MATERIAL_TERMS)

    if not material:
        return []

    matched = []
    for sector, keywords in SECTOR_KEYWORDS.items():
        if any(_contains(full_text, word) for word in keywords):
            matched.append(sector)

    return matched[:4]






