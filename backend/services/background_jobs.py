from __future__ import annotations

import json
import threading
import traceback
from uuid import uuid4
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


STORE_FILE = Path(__file__).resolve().parent.parent / "runtime" / "background_jobs.json"
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


def _update(job_id: str, **updates: Any) -> dict[str, Any]:
    with LOCK:
        items = _read()
        for item in items:
            if item.get("job_id") == job_id:
                item.update(updates)
                _write(items[:100])
                return item
    return {}


def create_job(tenant_id: str, job_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    job = {
        "job_id": f"job_{uuid4().hex[:12]}",
        "tenant_id": tenant_id or "default",
        "job_type": job_type,
        "status": "queued",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
        "result": None,
        "error": "",
    }
    with LOCK:
        items = _read()
        items.insert(0, job)
        _write(items[:100])
    return job


def run_job_async(job: dict[str, Any], runner: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    job_id = str(job["job_id"])

    def _target() -> None:
        _update(job_id, status="running", updated_at_utc=datetime.now(timezone.utc).isoformat())
        try:
            result = runner()
            _update(job_id, status="succeeded", result=result, updated_at_utc=datetime.now(timezone.utc).isoformat())
        except Exception as exc:  # noqa: BLE001
            _update(
                job_id,
                status="failed",
                error=f"{exc}\n{traceback.format_exc()[-1200:]}",
                updated_at_utc=datetime.now(timezone.utc).isoformat(),
            )

    thread = threading.Thread(target=_target, daemon=True)
    thread.start()
    return job


def list_jobs(tenant_id: str | None = None) -> list[dict[str, Any]]:
    items = _read()
    if not tenant_id:
        return items
    return [item for item in items if item.get("tenant_id") == tenant_id]


def get_job(job_id: str) -> dict[str, Any] | None:
    return next((item for item in _read() if item.get("job_id") == job_id), None)
