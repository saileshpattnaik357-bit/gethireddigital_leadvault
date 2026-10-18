"""
Append-only audit log.

Every meaningful harness action writes one JSON line to runtime/audit.jsonl:

    who         actor (user id / "system" / agent id)
    what        action name
    when        UTC timestamp
    tenant      tenant scope
    workflow    workflow id, when the action belongs to a run
    policy      policy decision that permitted the action, if any
    evidence    short structured evidence the action was based on
    result      outcome (ok / denied / error / ...)

The log is append-only by construction: there is no update or delete API.
Rotation is the operator's job (the file is plain JSONL).
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUDIT_FILE = Path(__file__).resolve().parent.parent / "runtime" / "audit.jsonl"
AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

_LOCK = threading.Lock()
_MAX_EVIDENCE_CHARS = 600


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _bounded(value: Any) -> Any:
    """Keep evidence payloads small; the audit log is a ledger, not a data store."""
    if value is None:
        return None
    text = json.dumps(value, default=str, ensure_ascii=False)
    if len(text) <= _MAX_EVIDENCE_CHARS:
        return value
    return {"_truncated": True, "preview": text[:_MAX_EVIDENCE_CHARS]}


def record(
    *,
    who: str,
    what: str,
    tenant: str = "default",
    workflow: str | None = None,
    policy: str | None = None,
    evidence: Any = None,
    result: str = "ok",
    error: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    event = {
        "ts": _utc_now(),
        "who": who,
        "what": what,
        "tenant": tenant,
        "workflow": workflow,
        "policy": policy,
        "evidence": _bounded(evidence),
        "result": result,
        "error": (error or "")[:300] or None,
    }
    for key, value in extra.items():
        event[key] = _bounded(value)
    line = json.dumps(event, ensure_ascii=False, default=str)
    with _LOCK:
        with AUDIT_FILE.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    return event


def read(
    *,
    tenant: str | None = None,
    workflow: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """Read the most recent events, newest first. Filters are exact-match."""
    if not AUDIT_FILE.exists():
        return []
    events: list[dict[str, Any]] = []
    with _LOCK:
        lines = AUDIT_FILE.read_text(encoding="utf-8").splitlines()
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if tenant and event.get("tenant") != tenant:
            continue
        if workflow and event.get("workflow") != workflow:
            continue
        events.append(event)
        if len(events) >= limit:
            break
    return events
