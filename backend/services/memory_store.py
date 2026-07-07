from __future__ import annotations

import json
import math
import re
import threading
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


STORE_FILE = Path(__file__).resolve().parent.parent / "runtime" / "memory_store.json"
STORE_FILE.parent.mkdir(parents=True, exist_ok=True)
TOKEN_RE = re.compile(r"[a-zA-Z0-9]{3,}")
LOCK = threading.Lock()


def _read() -> list[dict[str, Any]]:
    if not STORE_FILE.exists():
        return []
    try:
        return json.loads(STORE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _write(items: list[dict[str, Any]]) -> None:
    STORE_FILE.write_text(json.dumps(items, indent=2), encoding="utf-8")


def _tokens(text: str) -> Counter[str]:
    return Counter(token.lower() for token in TOKEN_RE.findall(text or ""))


def _similarity(a: Counter[str], b: Counter[str]) -> float:
    if not a or not b:
        return 0.0
    overlap = sum(min(a[key], b[key]) for key in a.keys() & b.keys())
    return overlap / math.sqrt(sum(a.values()) * sum(b.values()))


def index_memory(tenant_id: str, kind: str, rows: list[dict[str, Any]], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    inserted = 0
    with LOCK:
        items = _read()
        for row in rows:
            text = " ".join(str(row.get(key, "")) for key in ["Client Intent Signal", "Client Exact Query", "Company Name", "Service Category", "rejection_reason", "text", "query"])
            if not text.strip():
                continue
            items.insert(0, {
                "memory_id": f"mem_{uuid4().hex[:12]}",
                "tenant_id": tenant_id,
                "kind": kind,
                "text": text[:1600],
                "metadata": metadata or {},
                "created_at_utc": now,
            })
            inserted += 1
        _write(items[:1000])
    return {"status": "success", "inserted": inserted}


def search_memory(tenant_id: str, query: str, limit: int = 10) -> list[dict[str, Any]]:
    query_tokens = _tokens(query)
    scored = []
    for item in _read():
        if tenant_id and item.get("tenant_id") != tenant_id:
            continue
        score = _similarity(query_tokens, _tokens(str(item.get("text", ""))))
        if score > 0:
            scored.append({**item, "score": round(score, 4)})
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[: max(1, min(limit, 50))]
