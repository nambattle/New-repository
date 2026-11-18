import json
import tempfile
from pathlib import Path
from core.date_parser import parse_date
from core.text_cleaner import clean_text
from core.deduplicator import remove_duplicates
from storage.json_writer import save_json

assert parse_date("2026-11-17T09:00:00Z") is not None
assert clean_text("<p>Hello <b>world</b></p>") == "Hello world"

items = [
    {"title": "Test News", "link": "https://example.com/1"},
    {"title": " test   news ", "link": "https://example.com/2"},
    {"title": "Other News", "link": "https://example.com/3"},
]
unique = remove_duplicates(items)
assert len(unique) == 2

with tempfile.TemporaryDirectory() as folder:
    path = save_json(unique, Path(folder) / "test.json")
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert len(saved) == 2

print("날짜 변환: 성공")
print("HTML 정리: 성공")
print("중복 제거: 성공 (3건 -> 2건)")
print("JSON 저장 및 읽기: 성공")
print("전체 공통 모듈 테스트 통과")
