"""Persistent URL cache. Existing version-2 cache files remain compatible."""
import json
import os


class CacheManager:
    def __init__(self, path="cache/scraped_urls.json", limit=5000):
        self.path = path
        self.limit = limit
        self.load_ok = True
        self.successful_urls = self._load()

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                data = json.load(file)
            if isinstance(data, list):
                values = data
            elif isinstance(data, dict):
                values = data.get("successful_urls", data.get("urls", []))
            else:
                values = []
            if not isinstance(values, list):
                raise ValueError("캐시의 URL 목록 형식이 올바르지 않습니다.")
            return {str(url) for url in values if url}
        except FileNotFoundError:
            return set()
        except Exception:
            # Preserve an unreadable existing cache; do not overwrite it on save.
            self.load_ok = False
            return set()

    def add_success(self, url):
        self.successful_urls.add(url)

    def save(self):
        if not self.load_ok:
            return
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        temp_path = self.path + ".tmp"
        urls = sorted(self.successful_urls)[-self.limit:]
        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(
                {"version": 2, "successful_urls": urls},
                file,
                ensure_ascii=False,
                indent=2,
            )
        os.replace(temp_path, self.path)
