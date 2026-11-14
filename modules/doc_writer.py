import os
from datetime import datetime, timezone, timedelta

class BriefingDocWriter:
    def __init__(self, output_dir="briefings"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.kst = timezone(timedelta(hours=9))

    def format_briefing(self, indices, mapped_news):
        now_kst = datetime.now(self.kst)
        date_str = now_kst.strftime("%Y-%m-%d")
        time_str = now_kst.strftime("%Y년 %m월 %d일 %H:%M KST")

        lines = []
        lines.append(f"# 📈 모닝 경제·증권 브리핑 ({date_str})")
        lines.append(f"생성 시각: {time_str}\n")
        
        lines.append("## 1. 글로벌 주요 증시 마감 현황")
        lines.append("| 지수명 | 종가 | 전일 대비 등락률 |")
        lines.append("| :--- | :---: | :---: |")
        
        for name, val in indices.items():
            if "error" in val:
                lines.append(f"| {name} | 수집 실패 | - |")
            else:
                price = f"{val['price']:,.2f}"
                pct = val['change_pct']
                sign = "▲" if pct > 0 else ("▼" if pct < 0 else "-")
                lines.append(f"| {name} | {price} | {sign} {abs(pct):.2f}% |")
        
        lines.append("\n## 2. 섹터별 주요 경제·증권 뉴스")
        for idx, item in enumerate(mapped_news, 1):
            sectors = ", ".join(item["sectors"])
            lines.append(f"{idx}. **[{sectors}]** [{item['title']}]({item['link']})")

        return "\n".join(lines)

    def save_to_file(self, content):
        now_kst = datetime.now(self.kst)
        filename = f"{now_kst.strftime('%Y-%m-%d')}_briefing.md"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
        return filepath
