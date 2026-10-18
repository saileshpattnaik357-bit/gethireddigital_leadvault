"""
Mining-run workflow state machine.

Only the states LeadVault actually supports are modelled. There is no OUTREACH,
RESPONSE or FOLLOW_UP state because the product has no outbound capability.

    PLANNED     spec generated (mining brain built from ICP)
    CONFIRMED   operator confirmed the brain (cost gate passed)
    MINING      tools running (Apify / web)
    CLASSIFIED  candidates scored; accepted / rejected / pending-approval split
    REVIEW      one or more rows are waiting for a human decision
    EXPORTED    accepted rows persisted to the export store
    FAILED      terminal failure (recorded with error)

Transitions are validated; an illegal transition raises and is audited.
Records persist to runtime/workflows.json (same convention as the other stores).
"""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from harness import audit

STORE_FILE = Path(__file__).resolve().parent.parent / "runtime" / "workflows.json"
STORE_FILE.parent.mkdir(parents=True, exist_ok=True)
_LOCK = threading.Lock()
_MAX_RECORDS = 200


class State(str, Enum):
    PLANNED = "PLANNED"
    CONFIRMED = "CONFIRMED"
    MINING = "MINING"
    CLASSIFIED = "CLASSIFIED"
    REVIEW = "REVIEW"
    EXPORTED = "EXPORTED"
    FAILED = "FAILED"


TRANSITIONS: dict[State, set[State]] = {
    State.PLANNED: {State.CONFIRMED, State.FAILED},
    State.CONFIRMED: {State.MINING, State.FAILED},
    State.MINING: {State.CLASSIFIED, State.FAILED},
    State.CLASSIFIED: {State.REVIEW, State.EXPORTED, State.FAILED},
    State.REVIEW: {State.EXPORTED, State.FAILED},
    State.EXPORTED: set(),
    State.FAILED: set(),
}

STATE_CONTRACTS: dict[str, dict[str, Any]] = {
    "PLANNED": {"purpose": "Mining brain generated from ICP", "owner": "spec_planner", "approval": "none",
                "outputs": ["buyer_clusters", "linkedin_queries", "google_queries", "negative_filters"]},
    "CONFIRMED": {"purpose": "Operator reviewed the brain and approved spend", "owner": "human", "approval": "operator_confirm",
                  "outputs": ["confirmed=true"]},
    "MINING": {"purpose": "Tools gather candidates", "owner": "mining_orchestrator", "approval": "none (policy-bounded)",
               "outputs": ["candidates"]},
    "CLASSIFIED": {"purpose": "Each candidate scored with evidence", "owner": "intent_qualifier", "approval": "none",
                   "outputs": ["accepted", "rejected", "pending_approval"]},
    "REVIEW": {"purpose": "Human decides on hot-tier rows", "owner": "human", "approval": "human_review",
               "outputs": ["approved", "rejected_by_reviewer"]},
    "EXPORTED": {"purpose": "Accepted rows persisted in export schema", "owner": "system", "approval": "none",
                 "outputs": ["export_id"]},
    "FAILED": {"purpose": "Terminal failure with recorded error", "owner": "system", "approval": "none", "outputs": ["error"]},
}


class IllegalTransition(RuntimeError):
    pass


@dataclass
class WorkflowRecord:
    workflow_id: str
    tenant_id: str
    objective: str
    state: str
    created_at_utc: str
    updated_at_utc: str
    history: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read() -> list[dict[str, Any]]:
    if not STORE_FILE.exists():
        return []
    try:
        return json.loads(STORE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _write(items: list[dict[str, Any]]) -> None:
    STORE_FILE.write_text(json.dumps(items[:_MAX_RECORDS], indent=2, default=str), encoding="utf-8")


def create(*, tenant_id: str, objective: str, actor: str = "system", summary: dict[str, Any] | None = None) -> WorkflowRecord:
    now = _now()
    record = WorkflowRecord(
        workflow_id=f"wf_{uuid.uuid4().hex[:12]}",
        tenant_id=tenant_id,
        objective=objective,
        state=State.PLANNED.value,
        created_at_utc=now,
        updated_at_utc=now,
        history=[{"ts": now, "from": None, "to": State.PLANNED.value, "actor": actor}],
        summary=dict(summary or {}),
    )
    with _LOCK:
        items = _read()
        items.insert(0, record.as_dict())
        _write(items)
    audit.record(who=actor, what="workflow.create", tenant=tenant_id, workflow=record.workflow_id,
                 evidence={"objective": objective, "state": record.state})
    return record


def get(workflow_id: str) -> WorkflowRecord | None:
    for item in _read():
        if item.get("workflow_id") == workflow_id:
            return WorkflowRecord(**item)
    return None


def list_workflows(tenant_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    items = _read()
    if tenant_id:
        items = [item for item in items if item.get("tenant_id") == tenant_id]
    return items[:limit]


def transition(
    workflow_id: str,
    to: State,
    *,
    actor: str = "system",
    note: str = "",
    summary: dict[str, Any] | None = None,
    metrics: dict[str, Any] | None = None,
    error: str | None = None,
) -> WorkflowRecord:
    with _LOCK:
        items = _read()
        index = next((i for i, item in enumerate(items) if item.get("workflow_id") == workflow_id), None)
        if index is None:
            raise KeyError(f"unknown workflow: {workflow_id}")
        record = WorkflowRecord(**items[index])
        current = State(record.state)
        if to not in TRANSITIONS[current]:
            audit.record(who=actor, what="workflow.transition", tenant=record.tenant_id, workflow=workflow_id,
                         result="denied", error=f"illegal {current.value}->{to.value}")
            raise IllegalTransition(f"{current.value} -> {to.value} is not allowed")
        now = _now()
        record.history.append({"ts": now, "from": current.value, "to": to.value, "actor": actor, "note": note[:300]})
        record.state = to.value
        record.updated_at_utc = now
        if summary:
            record.summary.update(summary)
        if metrics:
            record.metrics = metrics
        if error:
            record.error = error[:500]
        items[index] = record.as_dict()
        _write(items)
    audit.record(who=actor, what="workflow.transition", tenant=record.tenant_id, workflow=workflow_id,
                 evidence={"from": current.value, "to": to.value, "note": note[:120]},
                 result="ok" if to != State.FAILED else "failed", error=error)
    return record
