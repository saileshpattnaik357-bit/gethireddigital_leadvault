"""
Harness API — read the control plane, decide approvals, run the evaluation.

All routes are tenant-scoped by the `tenant_id` string the caller supplies. That
is the same trust model the rest of the API has today (no authentication); the
harness does not pretend otherwise. See docs/AGENTIC_HARNESS.md §Security.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from harness import approvals, audit, workflow
from harness import llm as llm_layer
from harness.metrics import metrics
from harness.policy import policy_engine
from harness.registry import get_component, list_components
from harness.tools import gateway
from harness.workflow import STATE_CONTRACTS, TRANSITIONS
from config import settings

router = APIRouter(prefix="/api/leadvault/harness", tags=["harness"])


@router.get("/status")
def status() -> dict[str, Any]:
    return {
        "status": "ok",
        "llm_validation_enabled": llm_layer.is_enabled(settings),
        "llm_model": settings.LEADVAULT_LLM_MODEL,
        "agents": [c["agent_id"] for c in list_components(kind="agent")],
        "services": [c["agent_id"] for c in list_components(kind="service")],
        "tools": [t["tool_id"] for t in gateway.list_tools()],
        "policies": len(policy_engine.list_policies()),
    }


@router.get("/registry")
def registry(kind: str | None = Query(None, pattern="^(agent|service)$")) -> dict[str, Any]:
    return {"status": "success", "items": list_components(kind=kind)}


@router.get("/registry/{agent_id}")
def registry_item(agent_id: str) -> dict[str, Any]:
    component = get_component(agent_id)
    if component is None:
        raise HTTPException(status_code=404, detail="unknown agent_id")
    return {"status": "success", "item": component.as_dict()}


@router.get("/tools")
def tools() -> dict[str, Any]:
    return {"status": "success", "items": gateway.list_tools()}


@router.get("/policies")
def policies() -> dict[str, Any]:
    return {"status": "success", "items": policy_engine.list_policies()}


@router.get("/workflow-states")
def workflow_states() -> dict[str, Any]:
    return {
        "status": "success",
        "states": STATE_CONTRACTS,
        "transitions": {k.value: sorted(s.value for s in v) for k, v in TRANSITIONS.items()},
    }


@router.get("/workflows")
def workflows(tenant_id: str | None = None, limit: int = Query(50, ge=1, le=200)) -> dict[str, Any]:
    return {"status": "success", "items": workflow.list_workflows(tenant_id, limit=limit)}


@router.get("/workflows/{workflow_id}")
def workflow_item(workflow_id: str) -> dict[str, Any]:
    record = workflow.get(workflow_id)
    if record is None:
        raise HTTPException(status_code=404, detail="unknown workflow_id")
    return {
        "status": "success",
        "item": record.as_dict(),
        "audit": audit.read(workflow=workflow_id, limit=200),
    }


@router.get("/audit")
def audit_log(tenant_id: str | None = None, workflow_id: str | None = None, limit: int = Query(100, ge=1, le=500)) -> dict[str, Any]:
    return {"status": "success", "items": audit.read(tenant=tenant_id, workflow=workflow_id, limit=limit)}


@router.get("/metrics")
def run_metrics(limit: int = Query(20, ge=1, le=100)) -> dict[str, Any]:
    return {"status": "success", "items": metrics.recent(limit=limit)}


@router.get("/approvals")
def list_approvals(tenant_id: str = Query("default"), state: str | None = Query("READY_FOR_REVIEW")) -> dict[str, Any]:
    return {"status": "success", "items": approvals.list_pending(tenant_id, state=state or None)}


class ApprovalDecision(BaseModel):
    tenant_id: str = "default"
    decision: str = Field(pattern="^(?i)(approved|rejected)$")
    actor: str = Field(min_length=1, max_length=120)
    comment: str = Field(default="", max_length=1000)


@router.post("/approvals/{approval_id}/decide")
def decide_approval(approval_id: str, body: ApprovalDecision) -> dict[str, Any]:
    try:
        item = approvals.decide(
            approval_id=approval_id, tenant_id=body.tenant_id, decision=body.decision,
            actor=body.actor, comment=body.comment,
        )
    except approvals.ApprovalError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    # If nothing else is pending for this workflow, advance it out of REVIEW.
    wf_id = item.get("workflow_id")
    if wf_id:
        still_pending = [i for i in approvals.list_pending(body.tenant_id) if i.get("workflow_id") == wf_id]
        record = workflow.get(wf_id)
        if record and record.state == "REVIEW" and not still_pending:
            workflow.transition(wf_id, workflow.State.EXPORTED, actor=body.actor, note="all approvals decided")
    return {"status": "success", "item": item}


@router.post("/evaluate")
def evaluate() -> dict[str, Any]:
    """Run the classifier evaluation harness against gold + silver corpora (no API spend)."""
    from evaluation.harness import run_all

    out = run_all(write_report=True)
    return {"status": "success", "reports": out["reports"], "label_distribution": out["label_distribution"]}
