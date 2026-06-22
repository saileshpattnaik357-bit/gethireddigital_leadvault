from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STORE_FILE = Path(__file__).resolve().parent.parent / "runtime" / "rejected_audits.json"
STORE_FILE.parent.mkdir(parents=True, exist_ok=True)


def _read() -> list[dict[str, Any]]:
    if not STORE_FILE.exists():
        return []
    try:
        return json.loads(STORE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _write(items: list[dict[str, Any]]) -> None:
    STORE_FILE.write_text(json.dumps(items, indent=2), encoding="utf-8")


def save_rejected_audit(payload: dict[str, Any]) -> dict[str, Any]:
    items = _read()
    record = {
        "audit_id": payload.get("audit_id") or f"audit_{len(items)+1}",
        "tenant_id": payload.get("tenant_id") or "default",
        "saved_at_utc": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }
    items.insert(0, record)
    _write(items[:50])
    return record


def list_rejected_audits(tenant_id: str | None = None) -> list[dict[str, Any]]:
    items = _read()
    def _flatten(item: dict[str, Any]) -> dict[str, Any]:
        payload = item.get("payload", {})
        classification = payload.get("classification", {})
        return {
            **payload,
            **item,
            **classification,
        }

    filtered = items
    if tenant_id:
        filtered = [
            item
            for item in items
            if item.get("tenant_id") == tenant_id or item.get("payload", {}).get("tenant_id") == tenant_id
        ]
    return [_flatten(item) for item in filtered]


def latest_rejected_audit(tenant_id: str | None = None) -> dict[str, Any] | None:
    items = list_rejected_audits(tenant_id)
    return items[0] if items else None
