from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any


class JsonFileCache:
    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path
        self._lock = Lock()
        self._content: dict[str, Any] = self._load()

    def get(self, key: str) -> Any | None:
        return self._content.get(key)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._content[key] = value
            self._persist()

    def _load(self) -> dict[str, Any]:
        if not self._file_path.exists():
            return {}

        try:
            raw = self._file_path.read_text(encoding="utf-8")
            return json.loads(raw) if raw.strip() else {}
        except (json.JSONDecodeError, OSError):
            return {}

    def _persist(self) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        self._file_path.write_text(
            json.dumps(self._content, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
