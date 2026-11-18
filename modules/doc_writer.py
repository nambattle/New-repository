
import os
from datetime import datetime, timezone, timedelta


class BriefingDocWriter:
    def __init__(self, output_dir="briefings"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.kst = timezone(timedelta(hours=9))

    @staticmethod
    def _format_price(value):
        try:
            return f"{float(value):,.2f}"
        except (TypeError, ValueError):
            return "자료 없음"

    @staticmethod
    def _format_pct(value):
        try:
            pct = float(value)
            sign = "▲" if pct > 0 else ("▼" if pct < 0 else "-")
            return f"{sign} {abs(pct):.2f}%"
        except (TypeError, ValueError):
            return "자료 없음"

    def _render_table(self, data_dict):
        lines = [
            "| 종목 / 지표명 | 현재가 (종가) | 전일 대비 등락률 | 데이터 기준일 |",
            "| :--- | :---: | :---: | :---: |"
        ]

        if not isinstance(data_dict, dict) or not data_dict:
            lines.append("| 데이터 없음 | - | - | - |")
            return lines

        for name, val in data_dict.items():
            if not isinstance(val, dict):
                lines.append(f"| {name} | 자료 형식 오류 | - | - |")
                continue

            if val.get("error"):
                lines.append(f"| {name} | 수집 실패 | - | - |")
                continue

            price = self._format_price(val.get("price"))
            pct = self._format_pct(val.get("change_pct"))
            market_date = val.get("market_date") or "-"

            lines.append(
                f"| {name} | {price} | {pct} | {market_date} |"
            )

        return lines

    @staticmethod
    def _quote_body(body):
        """본문의 줄바꿈을 Markdown 인용문 형식으로 안전하게 변환."""
        if not body:
            return "> 본문 내용 없음"

        body = str(body).strip()
        if not body:
            return "> 본문 내용 없음"

        return "\n".join(
            f"> {line}" if line.strip() else ">"
            for line in body.splitlines()
        )

    def format_briefing(self, market_data, mapped_news):
        now_kst = datetime.now(self.kst)
        date_str = now_kst.strftime("%Y-%m-%d")
        time_str = now_kst.strftime("%Y년 %m월 %d일 %H:%M KST")

        # 이전 버전의 market_data 구조도 지원한다.
        if isinstance(market_data, dict) and "indices" in market_data:
            indices = market_data.get("indices") or {}
            stocks = market_data.get("stocks") or {}
        else:
            indices = market_data if isinstance(market_data, dict) else {}
            stocks = {}

        lines = [
            f"# 📈 모닝 경제·증권·지정학 심층 브리핑 ({date_str})",
            f"생성 시각: {time_str}",
            "",
            "## 1. 글로벌 주요 증시 및 매크로 지표",
        ]

        lines.extend(self._render_table(indices))

        if stocks:
            lines.extend([
                "",
                "## 2. 미국 핵심 섹터 대장주 동향",
            ])
            lines.extend(self._render_table(stocks))

        lines.extend([
            "",
            "## 3. 경제·증권·국제/지정학 뉴스 원문 및 섹터 분석",
            ""
        ])

        if not mapped_news:
            lines.append("현재 수집된 뉴스가 없습니다.")
        else:
            for idx, item in enumerate(mapped_news, 1):
                title = str(item.get("title") or "제목 없음")
                link = str(item.get("link") or "")
                source = str(item.get("source") or "출처 미상")
                sectors = item.get("sectors") or ["일반시황"]
                body = item.get("body") or "본문 내용 없음"

                lines.append(f"### {idx}. {title}")

                if link:
                    lines.append(f"- **원문 링크**: {link}")

                lines.append(
                    f"- **매체 / 핵심 테마**: {source} / "
                    f"**`{', '.join(map(str, sectors))}`**"
                )

                # 새 collector.py가 제공하는 메타데이터 표시
                published_at = item.get("published_at")
                date_status = item.get("date_status")
                extraction_status = item.get("extraction_status")
                verification_status = item.get("verification_status")

                if published_at:
                    lines.append(f"- **발행 시각**: {published_at}")

                if date_status:
                    lines.append(f"- **날짜 상태**: {date_status}")

                if extraction_status:
                    lines.append(f"- **본문 추출 상태**: {extraction_status}")

                if verification_status:
                    lines.append(f"- **검증 상태**: {verification_status}")

                lines.append("- **원문 본문**:")
                lines.append(self._quote_body(body))
                lines.append("")

        return "\n".join(lines)

    def save_to_file(self, content):
        now_kst = datetime.now(self.kst)
        filename = f"{now_kst.strftime('%Y-%m-%d')}_briefing.md"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath
