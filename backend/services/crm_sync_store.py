from __future__ import annotations

import json
import threading
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from config import settings


STORE_FILE = Path(__file__).resolve().parent.parent / "runtime" / "crm_syncs.json"
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


def sync_leads_to_crm(tenant_id: str, rows: list[dict[str, Any]], provider: str = "local") -> dict[str, Any]:
    mode = "webhook" if settings.CRM_WEBHOOK_URL else "local_audit"
    status = "success"
    error = ""
    if settings.CRM_WEBHOOK_URL and rows:
        try:
            request = urllib.request.Request(
                settings.CRM_WEBHOOK_URL,
                data=json.dumps({"tenant_id": tenant_id, "rows": rows}, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                response.read(1000)
        except Exception as exc:  # noqa: BLE001
            status = "failed"
            error = str(exc)[:240]
    record = {
        "sync_id": f"crm_{uuid4().hex[:12]}",
        "tenant_id": tenant_id,
        "provider": provider,
        "mode": mode,
        "status": status,
        "error": error,
        "row_count": len(rows),
        "synced_at_utc": datetime.now(timezone.utc).isoformat(),
        "rows": rows[:100],
    }
    with LOCK:
        items = _read()
        items.insert(0, record)
        _write(items[:100])
    return record


def list_crm_syncs(tenant_id: str | None = None) -> list[dict[str, Any]]:
    items = _read()
    if not tenant_id:
        return items
    return [item for item in items if item.get("tenant_id") == tenant_id]
