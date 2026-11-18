
import json
from collections import defaultdict
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "news_latest.json"
BRIEFINGS_DIR = BASE_DIR / "briefings"

TYPE_LABELS = {
    "news": "국내외 뉴스",
    "independent_commentary": "독립 투자 논평",
    "market_briefing": "투자시장 브리핑",
    "newsletter": "투자 뉴스레터",
    "official_disclosure": "거래소 공식 공시",
}

st.set_page_config(
    page_title="모닝 경제·증권 통합 투자자료관",
    page_icon="📈",
    layout="wide",
)

if not DATA_PATH.exists():
    st.error("통합 뉴스 데이터 파일을 찾을 수 없습니다.")
    st.stop()

try:
    items = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if not isinstance(items, list):
        raise ValueError("JSON 데이터 형식이 올바르지 않습니다.")
except Exception as exc:
    st.error(f"데이터 읽기 오류: {exc}")
    st.stop()

# ---------------------------
# Sidebar navigation
# ---------------------------
st.sidebar.title("📚 통합 자료관")

category_options = ["all"] + list(TYPE_LABELS.keys())

selected_type = st.sidebar.radio(
    "\uc790\ub8cc \uc720\ud615",
    category_options,
    index=0,
    format_func=lambda value: (
        "\uc804\uccb4 \uc790\ub8cc" if value == "all" else TYPE_LABELS[value]
    ),
    key="source_type_filter",
)

selected_category = (
    "\uc804\uccb4 \uc790\ub8cc" if selected_type == "all"
    else TYPE_LABELS[selected_type]
)

if selected_type == "all":
    category_items = list(items)
else:
    category_items = [
        item for item in items
        if str(item.get("source_type") or "").strip() == selected_type
    ]

available_sources = sorted({
    str(item.get("source") or "출처 미상")
    for item in category_items
})

selected_source = st.sidebar.selectbox(
    "수집 출처",
    ["전체 출처"] + available_sources,
)

title_search = st.sidebar.text_input(
    "제목 검색",
    placeholder="기업명 또는 기사 제목 입력",
).strip().casefold()

view_mode = st.sidebar.radio(
    "자료 보기 방식",
    ["사건별 보기", "기사별 보기"],
    index=0,
)

sort_order = st.sidebar.radio(
    "정렬 순서",
    ["최신순", "오래된 순"],
    horizontal=True,
)

page_size_choice = st.sidebar.selectbox(
    "Page size",
    [10, 20, 50, 100, "All"],
    index=1,
)


# ---------------------------
# Filter articles
# ---------------------------
filtered = []

for item in category_items:
    source = str(item.get("source") or "출처 미상")
    title = str(item.get("title") or "")

    if selected_source != "전체 출처" and source != selected_source:
        continue

    if title_search and title_search not in title.casefold():
        continue

    filtered.append(item)


def article_date(item):
    return str(
        item.get("published_at")
        or item.get("collected_at")
        or ""
    )


def sort_key(item):
    return article_date(item)


filtered.sort(
    key=sort_key,
    reverse=(sort_order == "최신순"),
)

# ---------------------------
# Header and metrics
# ---------------------------
st.title("📈 모닝 경제·증권 통합 투자자료관")
st.caption(
    "국내외 뉴스 · 해외 투자 블로그 · 시장 브리핑 · 공식 공시"
)

groups = defaultdict(list)

for index, item in enumerate(filtered):
    group_id = item.get("event_group_id") or f"fallback-{index}"
    groups[group_id].append(item)

multi_groups = [
    members for members in groups.values()
    if len(members) > 1
]

body_count = sum(
    bool(str(item.get("body") or "").strip())
    for item in filtered
)

source_count = len({
    item.get("source")
    for item in filtered
    if item.get("source")
})

metric_cols = st.columns(4)

metric_cols[0].metric("표시 자료", f"{len(filtered)}건")
metric_cols[1].metric("사건 그룹", f"{len(groups)}개")
metric_cols[2].metric("복수 기사 사건", f"{len(multi_groups)}개")
metric_cols[3].metric("원문 본문 확보", f"{body_count}건")

st.divider()

if selected_category == "전체 자료":
    heading = "전체 수집 자료"
else:
    heading = selected_category

if selected_source != "전체 출처":
    heading += f" · {selected_source}"

st.subheader(heading)

st.caption(
    f"검색 결과 {len(filtered)}건 · "
    f"자료 출처 {source_count}곳 · "
    f"보기 방식: {view_mode}"
)

# ---------------------------
# Article detail renderer
# ---------------------------
def render_article(item, number=None):
    title = str(item.get("title") or "제목 없음")
    source = str(item.get("source") or "출처 미상")
    source_type = str(item.get("source_type") or "unknown")
    type_label = TYPE_LABELS.get(source_type, source_type)

    body = str(item.get("body") or "")
    summary = str(item.get("summary") or "")
    link = str(item.get("link") or "")
    published = article_date(item)

    if number is not None:
        st.markdown(f"**{number}. {title}**")
    else:
        st.markdown(f"**{title}**")

    st.caption(
        f"출처: {source} · 유형: {type_label} · 게시일: {published}"
    )

    sectors = item.get("sectors") or []
    if sectors:
        st.write("관련 분야: " + ", ".join(map(str, sectors)))

    st.caption(
        f"본문 길이: {len(body):,}자 · "
        f"추출 상태: {item.get('extraction_status', 'unknown')}"
    )

    if summary:
        with st.expander("요약 및 소개", expanded=False):
            st.write(summary)

    if body:
        with st.expander("원문 전문 보기", expanded=False):
            st.text(body)
    else:
        st.warning("원문 본문이 없습니다.")

    if item.get("body_truncated"):
        st.warning("본문 일부가 설정된 최대 길이에 따라 잘렸습니다.")

    if link.startswith(("https://", "http://")):
        st.markdown(f"[원문 페이지 열기]({link})")

    if source_type == "official_disclosure":
        st.caption(
            f"공시 접수번호: {item.get('disclosure_id') or '정보 없음'}"
        )
        st.caption(
            f"공시 상태: {item.get('disclosure_status') or '정보 없음'}"
        )


# ---------------------------
# Group sorting
# ---------------------------
def group_sort_key(members):
    return max(
        (article_date(item) for item in members),
        default="",
    )


sorted_groups = sorted(
    groups.values(),
    key=group_sort_key,
    reverse=(sort_order == "최신순"),
)

# Pagination
active_count = len(sorted_groups) if view_mode == "\uc0ac\uac74\ubcc4 \ubcf4\uae30" else len(filtered)
page_size = max(active_count, 1) if page_size_choice == "All" else int(page_size_choice)
page_count = max(1, (active_count + page_size - 1) // page_size)

page_signature = (
    selected_type, selected_source, title_search,
    view_mode, sort_order, page_size_choice,
)

if st.session_state.get("_library_page_signature") != page_signature:
    st.session_state["_library_page_signature"] = page_signature
    st.session_state["_library_page"] = 1

if "_library_page" not in st.session_state:
    st.session_state["_library_page"] = 1

if st.session_state["_library_page"] > page_count:
    st.session_state["_library_page"] = page_count

page_number = st.sidebar.number_input(
    "Page", min_value=1, max_value=page_count,
    step=1, key="_library_page",
)

page_start = (page_number - 1) * page_size
page_end = min(page_start + page_size, active_count)
page_groups = sorted_groups[page_start:page_end]
page_items = filtered[page_start:page_end]

st.caption(
    f"Page {page_number}/{page_count} ? "
    f"Showing {page_start + 1 if active_count else 0}-{page_end} "
    f"of {active_count}"
)


# ---------------------------
# Event view
# ---------------------------
if view_mode == "사건별 보기":

    if not sorted_groups:
        st.info("선택한 조건에 해당하는 사건이 없습니다.")

    else:
        for group_number, members in enumerate(page_groups, start=page_start + 1):
            members.sort(
                key=sort_key,
                reverse=(sort_order == "최신순"),
            )

            first = members[0]
            group_label = (
                first.get("event_group_label")
                or "개별 자료"
            )

            original_count = max(
                int(item.get("related_article_count") or 1)
                for item in members
            )

            group_status = first.get("event_group_status", "unknown")

            if group_status == "grouped":
                status_label = "관련 사건 기사"
            elif group_status == "single":
                status_label = "독립 자료"
            else:
                status_label = "미분류 자료"

            preview_title = first.get("title") or "제목 없음"

            header = (
                f"{group_number:02d}. {group_label} "
                f"· 현재 {len(members)}건"
            )

            with st.expander(header, expanded=False):
                st.caption(
                    f"그룹 상태: {status_label} · "
                    f"현재 검색 결과: {len(members)}건 · "
                    f"사건 전체 연결 자료: {original_count}건"
                )

                all_sources = sorted({
                    str(source)
                    for item in members
                    for source in (
                        item.get("related_sources")
                        or [item.get("source") or "출처 미상"]
                    )
                })

                st.caption("연관 출처: " + ", ".join(all_sources))

                for article_number, item in enumerate(members, start=1):
                    render_article(item, article_number)

                    if article_number < len(members):
                        st.divider()

# ---------------------------
# Article view
# ---------------------------
else:

    if not filtered:
        st.info("검색 조건에 맞는 자료가 없습니다.")

    else:
        for index, item in enumerate(page_items, start=page_start + 1):
            title = str(item.get("title") or "제목 없음")
            source = str(item.get("source") or "출처 미상")
            group_label = item.get("event_group_label") or "개별 자료"
            related_count = item.get("related_article_count") or 1

            with st.expander(
                f"{index:02d}. {title} · {source}",
                expanded=False,
            ):
                st.caption(
                    f"사건 그룹: {group_label} · "
                    f"관련 기사: {related_count}건"
                )
                render_article(item)


# ---------------------------
# Compact Markdown report menu
# ---------------------------
BRIEFINGS_DIR.mkdir(parents=True, exist_ok=True)

report_files = sorted(
    BRIEFINGS_DIR.glob("*_briefing.md"),
    key=lambda path: path.name,
    reverse=True,
)

with st.sidebar.expander("📅 날짜별 브리핑 리포트", expanded=False):
    if report_files:
        report_names = ["선택 안 함"] + [
            path.name for path in report_files
        ]

        selected_report = st.selectbox(
            "리포트 선택",
            report_names,
        )

        if selected_report != "선택 안 함":
            report_path = BRIEFINGS_DIR / selected_report
            st.session_state["selected_report"] = str(report_path)
    else:
        st.caption("아직 생성된 마크다운 리포트가 없습니다.")

report_path_value = st.session_state.get("selected_report")

if report_path_value:
    report_path = Path(report_path_value)

    if report_path.exists():
        with st.expander(
            f"📝 브리핑 리포트: {report_path.name}",
            expanded=False,
        ):
            st.markdown(report_path.read_text(encoding="utf-8"))

st.sidebar.divider()
st.sidebar.caption(f"통합 저장 자료: {len(items)}건")
st.sidebar.caption("자료 갱신: PowerShell에서 python main.py 실행")
