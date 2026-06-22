from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STORE_FILE = Path(__file__).resolve().parent.parent / "runtime" / "leadvault_specs.json"
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


def save_leadvault_spec(payload: dict[str, Any]) -> dict[str, Any]:
    items = _read()
    record = {
        "spec_id": payload.get("spec_id") or f"leadvault_{len(items)+1}",
        "tenant_id": payload.get("tenant_id") or "default",
        "saved_at_utc": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }
    items.insert(0, record)
    _write(items[:25])
    return record


def list_leadvault_specs(tenant_id: str | None = None) -> list[dict[str, Any]]:
    items = _read()

    def _flatten(item: dict[str, Any]) -> dict[str, Any]:
        payload = item.get("payload", {})
        return {**payload, **item}

    filtered = items
    if tenant_id:
        filtered = [
            item
            for item in items
            if item.get("tenant_id") == tenant_id or item.get("payload", {}).get("tenant_id") == tenant_id
        ]
    return [_flatten(item) for item in filtered]
