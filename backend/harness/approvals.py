"""
Human approval queue.

Rows that policy marks REQUIRE_APPROVAL (today: hot-tier / tier_1 leads) are
parked here instead of going straight into the accepted export. A human then
approves or rejects each one. Every decision records actor, timestamp, the
evidence the recommendation was based on, and a free-text comment.

States:  READY_FOR_REVIEW -> APPROVED | REJECTED

On APPROVED the row is appended to the tenant's accepted export store so it
appears in the normal export path. On REJECTED it is written to the rejected
audit store with reason "rejected_by_reviewer".

Tenant scope is enforced in code: a decision request must carry the same
tenant_id the item was created under, or it is refused.
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from harness import audit
from harness.policy import Action, policy_engine

STORE_FILE = Path(__file__).resolve().parent.parent / "runtime" / "approvals.json"
STORE_FILE.parent.mkdir(parents=True, exist_ok=True)
_LOCK = threading.Lock()
_MAX = 500

READY = "READY_FOR_REVIEW"
APPROVED = "APPROVED"
REJECTED = "REJECTED"


class ApprovalError(ValueError):
    pass


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
    STORE_FILE.write_text(json.dumps(items[:_MAX], indent=2, default=str), encoding="utf-8")


def enqueue(
    *,
    tenant_id: str,
    workflow_id: str | None,
    lead: dict[str, Any],
    evidence: dict[str, Any],
    recommended_action: str,
    reason: str,
    agent_id: str = "intent_qualifier",
) -> dict[str, Any]:
    item = {
        "approval_id": f"apr_{uuid.uuid4().hex[:12]}",
        "tenant_id": tenant_id,
        "workflow_id": workflow_id,
        "state": READY,
        "created_at_utc": _now(),
        "decided_at_utc": None,
        "decided_by": None,
        "decision_comment": "",
        "agent_id": agent_id,
        "recommended_action": recommended_action,
        "reason": reason,
        "evidence": evidence,
        "lead": lead,
    }
    with _LOCK:
        items = _read()
        items.insert(0, item)
        _write(items)
    audit.record(who=agent_id, what="approval.enqueue", tenant=tenant_id, workflow=workflow_id,
                 policy="P-ACCEPT-02", evidence={"approval_id": item["approval_id"], "reason": reason[:120]})
    return item


def list_pending(tenant_id: str | None = None, state: str | None = READY, limit: int = 100) -> list[dict[str, Any]]:
    items = _read()
    if tenant_id:
        items = [i for i in items if i.get("tenant_id") == tenant_id]
    if state:
        items = [i for i in items if i.get("state") == state]
    return items[:limit]


def get(approval_id: str) -> dict[str, Any] | None:
    for item in _read():
        if item.get("approval_id") == approval_id:
            return item
    return None


def decide(
    *,
    approval_id: str,
    tenant_id: str,
    decision: str,
    actor: str,
    comment: str = "",
) -> dict[str, Any]:
    """Apply a human decision. Enforces tenant scope and single-decision semantics."""
    decision = decision.upper().strip()
    if decision not in {APPROVED, REJECTED}:
        raise ApprovalError("decision must be APPROVED or REJECTED")
    if not actor or not actor.strip():
        raise ApprovalError("actor is required")

    policy = policy_engine.assert_allowed(Action.APPROVE_LEAD, {"actor": actor})

    with _LOCK:
        items = _read()
        index = next((i for i, item in enumerate(items) if item.get("approval_id") == approval_id), None)
        if index is None:
            raise ApprovalError("unknown approval_id")
        item = items[index]
        if item.get("tenant_id") != tenant_id:
            audit.record(who=actor, what="approval.decide", tenant=tenant_id, workflow=item.get("workflow_id"),
                         policy=policy.policy_id, result="denied", error="tenant_mismatch",
                         evidence={"approval_id": approval_id})
            raise ApprovalError("approval belongs to a different tenant")
        if item.get("state") != READY:
            raise ApprovalError(f"approval already decided: {item.get('state')}")
        item["state"] = decision
        item["decided_at_utc"] = _now()
        item["decided_by"] = actor.strip()[:120]
        item["decision_comment"] = (comment or "").strip()[:1000]
        items[index] = item
        _write(items)

    # Side effects happen after the record is durable.
    if decision == APPROVED:
        from services.accepted_export_store import save_accepted_export
        save_accepted_export({
            "tenant_id": tenant_id,
            "rows": [item["lead"]],
            "export_id": f"approved_{approval_id}",
        })
    else:
        from services.rejected_audit_store import save_rejected_audit
        save_rejected_audit({
            "tenant_id": tenant_id,
            "lead_objective": item["lead"].get("lead_objective", ""),
            "text": item["lead"].get("Client Intent Signal", ""),
            "query": item["lead"].get("Client Exact Query", ""),
            "source": item["lead"].get("Lead Source", ""),
            "url": item["lead"].get("Client Query Post URL", ""),
            "classification": {"category": item["lead"].get("category", ""), "rationale": "rejected_by_reviewer"},
            "buying_intent": {"intent_score": item["lead"].get("intent_score")},
            "rejection_reason": "rejected_by_reviewer",
            "reviewer_comment": item["decision_comment"],
        })

    audit.record(who=actor, what="approval.decide", tenant=tenant_id, workflow=item.get("workflow_id"),
                 policy=policy.policy_id, result=decision.lower(),
                 evidence={"approval_id": approval_id, "comment": item["decision_comment"][:120],
                           "intent_score": item["lead"].get("intent_score")})
    return item
