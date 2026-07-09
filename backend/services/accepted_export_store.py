from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from services.sqlite_store import save_record


STORE_FILE = Path(__file__).resolve().parent.parent / "runtime" / "accepted_exports.json"
STORE_FILE.parent.mkdir(parents=True, exist_ok=True)
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


def save_accepted_export(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload.get("rows") or []
    tenant_id = payload.get("tenant_id") or "default"
    record = {
        "export_id": payload.get("export_id") or f"accepted_{uuid4().hex[:12]}",
        "tenant_id": tenant_id,
        "saved_at_utc": datetime.now(timezone.utc).isoformat(),
        "row_count": len(rows),
        "rows": rows,
    }
    with LOCK:
        items = _read()
        items.insert(0, record)
        _write(items[:100])
    save_record("accepted_export", tenant_id, record, record["export_id"])
    return record


def list_accepted_exports(tenant_id: str | None = None) -> list[dict[str, Any]]:
    items = _read()
    if not tenant_id:
        return items
    return [item for item in items if item.get("tenant_id") == tenant_id]


def latest_accepted_export(tenant_id: str | None = None) -> dict[str, Any] | None:
    items = list_accepted_exports(tenant_id)
    return items[0] if items else None
