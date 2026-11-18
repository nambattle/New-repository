
"""Conservative rule-based event grouping. Original articles are preserved."""

from collections import defaultdict
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from hashlib import sha1
import re


EVENT_WINDOW_HOURS = 36

ENTITY_ALIASES = [
    ("NVIDIA", "엔비디아", ("nvidia", "엔비디아", "젠슨 황", "젠슨황")),
    ("ANTHROPIC", "앤트로픽", ("anthropic", "앤트로픽")),
    ("OPENAI", "오픈AI", ("openai", "오픈ai")),
    ("SAMSUNG_ELECTRONICS", "삼성전자", ("삼성전자", "samsung electronics")),
    ("SAMSUNG_ELECTRO", "삼성전기", ("삼성전기", "samsung electro-mechanics")),
    ("SK_HYNIX", "SK하이닉스", ("sk hynix", "sk하이닉스", "하이닉스")),
    ("MICRON", "마이크론", ("micron", "마이크론")),
    ("AMD", "AMD", ("amd",)),
    ("HOME_DEPOT", "홈디포", ("home depot",)),
    ("DISNEY", "디즈니", ("disney", "디즈니")),
    ("BERKSHIRE", "버크셔 해서웨이", ("berkshire hathaway", "버크셔")),
    ("APPLE", "애플", ("apple", "애플")),
    ("GOOGLE", "구글", ("google", "구글", "알파벳")),
    ("MICROSOFT", "마이크로소프트", ("microsoft", "마이크로소프트")),
    ("TESLA", "테슬라", ("tesla", "테슬라")),
    ("HYUNDAI_MOTOR", "현대자동차", ("hyundai motor", "현대차", "현대자동차")),
    ("KAI", "한국항공우주", ("korea aerospace", "한국항공우주", "kai")),
    ("HANWHA_AEROSPACE", "한화에어로스페이스", ("hanwha aerospace", "한화에어로스페이스")),
    ("LIG_NEX1", "LIG넥스원", ("lig nex1", "lig넥스원", "lig넥스")),
    ("SHINHAN", "신한금융", ("신한은행", "신한카드", "신한금융", "shinhan")),
    ("KDB_LIFE", "KDB생명", ("kdb life", "kdb생명", "케이디비생명")),
    ("JPMORGAN", "JP모건", ("jpmorgan", "jp모건")),
    ("FED", "미국 연방준비제도", ("federal reserve", "연방준비제도", "연준", "뉴욕 연은")),
    ("KOSPI", "코스피", ("코스피", "kospi")),
    ("KOSDAQ", "코스닥", ("코스닥", "kosdaq")),
]


TOPIC_RULES = [
    (
        "leadership",
        "경영진·지배구조",
        r"\bceo\b|사임|복귀|재선임|이사회|후계|succession|successor|resignation|resign|ousted|board of directors",
    ),
    (
        "earnings",
        "실적·실적전망",
        r"earnings|실적|매출|영업이익|순이익|revenue|profit|guidance|컨퍼런스콜|어닝|실적 전망|sales outlook",
    ),
    (
        "ipo_funding",
        "IPO·자금조달",
        r"\bipo\b|기업공개|상장|투자유치|투자 유치|자금조달|valuation|funding|공모",
    ),
    (
        "ownership_deal",
        "지분·인수·매각",
        r"지분|매각|인수|합병|매수|acquisition|acquire|merger|stake|buyout|takeover|sell.*stake",
    ),
    (
        "trade_regulation",
        "무역·규제·정책",
        r"수출통제|수출 규제|관세|제재|무역|export control|tariff|sanction|trade war|규제",
    ),
    (
        "monetary_policy",
        "금리·물가·통화정책",
        r"\bfed\b|interest rate|rate cut|rate hike|bond yield|inflation|cpi|연준|금리|물가|국채금리|국채 수익률",
    ),
    (
        "infrastructure_capex",
        "AI·전력·인프라 투자",
        r"data cent(er|re)s?|데이터센터|전력망|변압기|송전망|power grid|ai infrastructure|인프라 투자|서버 투자",
    ),
    (
        "geopolitics",
        "지정학·국제정세",
        r"정상회담|회담|apec|summit|중동|이란|iran|전쟁|\bwar\b|군사|military|북중|미중",
    ),
    (
        "contracts_production",
        "수주·공급·생산",
        r"공급계약|수주|계약 체결|가동률|공장 증설|contract|orders|shipments|production capacity",
    ),
    (
        "investment_strategy",
        "투자전략·자산배분",
        r"투자전략|자산배분|portfolio strategy|investment strategy|투자 포지션|fund manager|options traders",
    ),
    (
        "market_moves",
        "주가·시장 움직임",
        r"주가|급등|급락|상승|하락|증시|shares? fall|shares? rise|stock rally|selloff|plunge|surges?",
    ),
]


TOPIC_LABELS = dict(
    (key, label) for key, label, pattern in TOPIC_RULES
)


def _contains(text, phrase):
    phrase = phrase.casefold()

    if phrase.isascii() and phrase.replace(" ", "").isalnum():
        pattern = r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])"
        return re.search(pattern, text) is not None

    return phrase in text


def _find_position(text, phrase):
    phrase = phrase.casefold()

    if phrase.isascii() and phrase.replace(" ", "").isalnum():
        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(phrase)
            + r"(?![a-z0-9])"
        )
        match = re.search(pattern, text)
        return match.start() if match else -1

    return text.find(phrase)


def _detect_entity(title):
    text = (title or "").casefold()
    matches = []

    # Select the first-mentioned named company/entity in the headline.
    for key, label, aliases in ENTITY_ALIASES:
        positions = [
            _find_position(text, alias)
            for alias in aliases
        ]
        positions = [p for p in positions if p >= 0]

        if positions:
            matches.append((
                min(positions),
                key,
                label,
            ))

    if matches:
        matches.sort(key=lambda x: x[0])
        _, key, label = matches[0]
        return key, label

    # General market themes are used only when no named entity exists.
    if (
        ("china" in text or "중국" in text)
        and ("trump" in text or "미국" in text or "u.s." in text)
    ):
        return "US_CHINA", "미국·중국"


    if any(x in text for x in ("원유", "유가", "crude oil", "oil prices")):
        return "OIL_MARKET", "국제 원유시장"

    return None, None


def _detect_topic(title):
    text = (title or "").casefold()

    # Explicit leadership events take priority over earnings mentions.
    leadership_rule = next(
        (pattern for key, label, pattern in TOPIC_RULES
         if key == "leadership"),
        None,
    )

    if leadership_rule:
        leadership_rule += (
            r"|who and what comes next|what comes next|investor uncertainty|"
            r"leadership transition|succession planning"
            + "|" + "\uBE48 \uC790\uB9AC|\uD6C4\uC784"
        )

    if leadership_rule and re.search(leadership_rule, text, re.IGNORECASE):
        return "leadership", TOPIC_LABELS["leadership"]

    # A Fed mention alone is not enough to classify monetary policy.
    monetary_signal = (
        r"interest rate|rate cut|rate hike|bond yield|inflation|cpi|"
        r"\uAE08\uB9AC|\uBB3C\uAC00|\uAD6D\uCC44\uAE08\uB9AC|"
        r"\uAD6D\uCC44\s*\uC218\uC775\uB960"
    )

    if not re.search(monetary_signal, text, re.IGNORECASE):
        skip_monetary = True
    else:
        skip_monetary = False

    matches = []

    for key, label, pattern in TOPIC_RULES:
        if key == "leadership":
            continue
        if key == "monetary_policy" and skip_monetary:
            continue

        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            matches.append((match.start(), key, label))

    if not matches:
        return None, None

    matches.sort(key=lambda x: x[0])
    _, key, label = matches[0]
    return key, label

def _parse_date(value):
    if not value:
        return None

    value = str(value).strip()

    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            result = parsedate_to_datetime(value)
        except (ValueError, TypeError, OverflowError):
            return None

    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)

    return result.astimezone(timezone.utc)


def _article_id(item, index):
    seed = str(item.get("link") or item.get("title") or index)
    return "single-" + sha1(seed.encode("utf-8")).hexdigest()[:12]


def add_event_groups(items, window_hours=EVENT_WINDOW_HOURS):
    """Add event metadata without deleting or rewriting article content."""

    output = [dict(item) for item in items]
    candidates = defaultdict(list)

    for index, item in enumerate(output):
        # Only general news participates in event grouping.
        # Disclosures and reference materials remain standalone.
        source_type = item.get("source_type")
        if source_type not in (None, "", "news"):
            continue

        title = str(item.get("title") or "")
        entity_key, entity_label = _detect_entity(title)
        topic_key, topic_label = _detect_topic(title)
        published = _parse_date(item.get("published_at"))

        if entity_key and topic_key and published:
            candidates[(entity_key, topic_key)].append(
                (published, index, entity_label, topic_label)
            )

    assigned = set()
    window = timedelta(hours=max(1, int(window_hours)))

    for event_key, records in candidates.items():
        records.sort(key=lambda x: x[0])
        clusters = []
        current = []

        for record in records:
            if current and record[0] - current[-1][0] > window:
                clusters.append(current)
                current = []

            current.append(record)

        if current:
            clusters.append(current)

        for cluster in clusters:
            entity_label = cluster[0][2]
            topic_label = cluster[0][3]
            indexes = [record[1] for record in cluster]
            sources = sorted({
                str(output[i].get("source") or "출처 미상")
                for i in indexes
            })

            if len(cluster) >= 2:
                first_date = cluster[0][0].strftime("%Y%m%d")
                seed = (
                    event_key[0] + "|" +
                    event_key[1] + "|" +
                    first_date
                )
                group_id = "event-" + sha1(
                    seed.encode("utf-8")
                ).hexdigest()[:12]
                status = "grouped"
            else:
                group_id = _article_id(output[indexes[0]], indexes[0])
                status = "single"

            label = f"{entity_label} · {topic_label}"

            for index in indexes:
                output[index].update({
                    "event_group_id": group_id,
                    "event_group_label": label,
                    "event_group_status": status,
                    "event_group_key": event_key[0] + "|" + event_key[1],
                    "related_article_count": len(indexes),
                    "related_sources": sources,
                    "event_match_method": "title_entity_topic_rule",
                })
                assigned.add(index)

    # Articles without a confident event signature remain independent.
    for index, item in enumerate(output):
        if index in assigned:
            continue

        item.update({
            "event_group_id": _article_id(item, index),
            "event_group_label": "개별 자료",
            "event_group_status": "unclassified",
            "event_group_key": None,
            "related_article_count": 1,
            "related_sources": [
                str(item.get("source") or "출처 미상")
            ],
            "event_match_method": "standalone",
        })

    return output
