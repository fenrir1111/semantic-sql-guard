"""全链路审计日志：每一次查询都留痕（JSONL 落盘 + 内存环形缓冲）。"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path


class AuditLogger:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._buffer: list[dict] = []
        self._lock = threading.Lock()
        self._seq = 0

    def record(self, **fields) -> int:
        with self._lock:
            self._seq += 1
            rec = {"id": self._seq, "ts": datetime.now(timezone.utc).isoformat(), **fields}
            self._buffer.append(rec)
            if len(self._buffer) > 500:
                self._buffer = self._buffer[-500:]
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            return rec["id"]

    def recent(self, limit: int = 50) -> list[dict]:
        with self._lock:
            return list(self._buffer[-limit:])
