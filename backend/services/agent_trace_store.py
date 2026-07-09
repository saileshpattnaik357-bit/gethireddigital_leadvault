from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.sqlite_store import list_records, save_record, storage_stats


def save_agent_trace(
    tenant_id: str,
    run_id: str,
    stage: str,
    status: str,
    detail: str = "",
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "run_id": run_id,
        "tenant_id": tenant_id or "default",
        "stage": stage,
        "status": status,
        "detail": detail,
        "metrics": metrics or {},
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    save_record("agent_trace", tenant_id or "default", payload)
    return payload


def list_agent_traces(tenant_id: str | None = None, run_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    records = list_records("agent_trace", tenant_id, limit=max(1, min(limit, 500)))
    traces = [record.get("payload", {}) for record in records]
    if run_id:
        traces = [trace for trace in traces if trace.get("run_id") == run_id]
    return traces


def agent_storage_stats(tenant_id: str | None = None) -> dict[str, Any]:
    return storage_stats(tenant_id)
