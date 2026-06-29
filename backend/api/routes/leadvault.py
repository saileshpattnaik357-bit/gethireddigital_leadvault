from __future__ import annotations

import json
from io import BytesIO
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from pydantic import BaseModel

from services.accepted_export_store import latest_accepted_export, list_accepted_exports
from services.rejected_audit_store import latest_rejected_audit, list_rejected_audits
from services.leadvault_agent import (
    aggregate_icp_profile,
    build_leadvault_spec,
    build_leadvault_spec_with_llm,
    leadvault_spec_as_dict,
    parse_icp_rows,
)
from services.leadvault_mining_runner import (
    aggregate_mining_context,
    parse_generic_icp_file,
    run_leadvault_mining,
    run_linkedin_capture_mining,
)
from services.leadvault_spec_store import list_leadvault_specs, save_leadvault_spec


router = APIRouter(prefix="/api/leadvault", tags=["leadvault"])

EXACT_EXPORT_COLUMNS = [
    "Date Added",
    "Estimated Deal Value",
    "Client Name",
    "Client LinkedIn Profile URL",
    "Title",
    "Company Name",
    "Company Website",
    "Industry",
    "Region",
    "Client Email",
    "Client Phone",
    "Number of Employees",
    "Lead Source",
    "Client Intent Signal",
    "Client Exact Query",
    "Client Query Post URL",
    "Priority",
    "Service Category",
    "Outreach Status",
    "Ajroni Offer",
    "Notes",
]


def _excel_value(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(value, ensure_ascii=True, default=str)
    return value


class LeadVaultPlanRequest(BaseModel):
    company_name: str = ""
    website: str = ""
    services: list[str] = []
    geography: str = ""
    icp: str = ""
    positioning: str = ""
    customer_examples: list[str] = []
    founder_profile: str = ""
    target_audience: str = ""
    lead_objective: str = ""
    notes: str = ""
    tenant_id: str = "default"
    use_llm: bool = False
    save: bool = False


class LeadVaultMineRequest(LeadVaultPlanRequest):
    max_results: int = 25
    live_web: bool = True
    confirmed: bool = False
    mining_mode: str = "hybrid"
    max_apify_queries: int = 10
    max_posts_per_query: int = 10


class LinkedInCaptureRequest(BaseModel):
    posts_text: str = ""
    rows: list[dict[str, Any]] = []
    query: str = "linkedin_capture"
    tenant_id: str = "default"
    max_results: int = 50
    lead_objective: str = "agency_procurement"


@router.get("/health")
def health():
    return {"status": "ok", "engine": "leadvault"}


@router.post("/plan")
async def plan(req: LeadVaultPlanRequest):
    spec = build_leadvault_spec(
        company_name=req.company_name,
        website=req.website,
        services=req.services,
        geography=req.geography,
        icp=req.icp,
        positioning=req.positioning,
        customer_examples=req.customer_examples,
        founder_profile=req.founder_profile,
        target_audience=req.target_audience,
        lead_objective=req.lead_objective,
        notes=req.notes,
        tenant_id=req.tenant_id,
    )
    if req.use_llm:
        spec = await build_leadvault_spec_with_llm(spec)
    payload = leadvault_spec_as_dict(spec)
    record = save_leadvault_spec(payload) if req.save else None
    return {
        "status": "success",
        "spec": payload,
        "record": record,
        "summary": {
            "buyer_clusters": len(spec.buyer_clusters),
            "linkedin_queries": len(spec.linkedin_queries),
            "google_queries": len(spec.google_queries),
            "buyer_phrases": len(spec.buyer_phrases),
            "negative_filters": len(spec.negative_filters),
            "generation_mode": spec.generation_mode,
        },
    }


@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    tenant_id: str = Form("default"),
    lead_objective: str = Form(""),
    use_llm: bool = Form(False),
    save: bool = Form(True),
):
    raw = await file.read()
    try:
        rows = parse_icp_rows(raw, file.filename or "icp_upload")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not rows:
        raise HTTPException(status_code=400, detail="No usable ICP rows found in the uploaded file")

    profile = aggregate_icp_profile(rows)
    spec = build_leadvault_spec(
        company_name=profile.get("company_name", ""),
        website=profile.get("website", ""),
        services=profile.get("services", []),
        geography=profile.get("geography", ""),
        icp=profile.get("icp", ""),
        positioning=profile.get("positioning", ""),
        customer_examples=profile.get("customer_examples", []),
        founder_profile=profile.get("founder_profile", ""),
        lead_objective=lead_objective or profile.get("lead_objective", ""),
        notes=profile.get("notes", ""),
        tenant_id=tenant_id,
    )
    if use_llm:
        spec = await build_leadvault_spec_with_llm(spec)
    payload = leadvault_spec_as_dict(spec)
    record = save_leadvault_spec({**payload, "source_filename": file.filename}) if save else None
    return {
        "status": "success",
        "source_profile": profile,
        "spec": payload,
        "record": record,
        "summary": {
            "uploaded_rows": len(rows),
            "buyer_clusters": len(spec.buyer_clusters),
            "linkedin_queries": len(spec.linkedin_queries),
            "google_queries": len(spec.google_queries),
            "buyer_phrases": len(spec.buyer_phrases),
            "negative_filters": len(spec.negative_filters),
            "generation_mode": spec.generation_mode,
        },
    }


@router.get("/specs")
def specs(tenant_id: str | None = None):
    return {"status": "success", "items": list_leadvault_specs(tenant_id)}


@router.get("/runs")
def runs(tenant_id: str | None = None):
    return {
        "status": "success",
        "accepted_exports": list_accepted_exports(tenant_id),
        "rejected_audits": list_rejected_audits(tenant_id),
    }


@router.get("/tenants")
def tenants():
    specs = list_leadvault_specs()
    accepted = list_accepted_exports()
    rejected = list_rejected_audits()
    tenant_ids = {
        str(item.get("tenant_id") or "default")
        for item in [*specs, *accepted, *rejected]
    }
    tenant_ids.add("default")

    items = []
    for tenant_id in sorted(tenant_ids):
        tenant_specs = [item for item in specs if item.get("tenant_id") == tenant_id]
        tenant_accepted = [item for item in accepted if item.get("tenant_id") == tenant_id]
        tenant_rejected = [item for item in rejected if item.get("tenant_id") == tenant_id]
        items.append(
            {
                "tenant_id": tenant_id,
                "company_name": (tenant_specs[0].get("company_name") if tenant_specs else "") or tenant_id,
                "spec_count": len(tenant_specs),
                "accepted_runs": len(tenant_accepted),
                "rejected_rows": len(tenant_rejected),
                "latest_spec": tenant_specs[0] if tenant_specs else None,
            }
        )
    return {"status": "success", "items": items}


@router.get("/export/{kind}")
def export_latest(kind: str, tenant_id: str = Query("default")):
    kind = kind.lower().strip()
    if kind not in {"accepted", "rejected"}:
        raise HTTPException(status_code=400, detail="Export kind must be accepted or rejected")

    if kind == "accepted":
        record = latest_accepted_export(tenant_id)
        rows = (record or {}).get("rows") or []
        filename = f"leadvault_accepted_{tenant_id}.xlsx"
        sheet_name = "Accepted"
        columns = EXACT_EXPORT_COLUMNS
    else:
        record = latest_rejected_audit(tenant_id)
        rows = [record] if record else []
        filename = f"leadvault_rejected_{tenant_id}.xlsx"
        sheet_name = "Rejected"
        columns = sorted({key for row in rows for key in row.keys()}) if rows else ["tenant_id", "saved_at_utc"]

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = sheet_name
    worksheet.append(columns)
    for row in rows:
        worksheet.append([_excel_value(row.get(column, "")) for column in columns])

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/mine")
def mine(req: LeadVaultMineRequest):
    if not req.confirmed:
        raise HTTPException(
            status_code=409,
            detail="Review and confirm the generated LeadVault mining brain before running mining.",
        )
    return run_leadvault_mining(
        tenant_id=req.tenant_id,
        company_name=req.company_name,
        website=req.website,
        services=req.services,
        geography=req.geography,
        icp=req.icp,
        positioning=req.positioning,
        customer_examples=req.customer_examples,
        founder_profile=req.founder_profile,
        max_results=max(1, min(req.max_results, 100)),
        live_web=req.live_web,
        mining_mode=req.mining_mode,
        max_apify_queries=max(1, min(req.max_apify_queries, 25)),
        max_posts_per_query=max(1, min(req.max_posts_per_query, 25)),
        lead_objective=req.lead_objective,
    )


@router.post("/mine-upload")
async def mine_upload(
    file: UploadFile = File(...),
    tenant_id: str = Form("default"),
    max_results: int = Form(25),
    live_web: bool = Form(True),
    confirmed: bool = Form(False),
    mining_mode: str = Form("hybrid"),
    max_apify_queries: int = Form(10),
    max_posts_per_query: int = Form(10),
    lead_objective: str = Form(""),
):
    if not confirmed:
        raise HTTPException(
            status_code=409,
            detail="Review and confirm the generated LeadVault mining brain before running upload mining.",
        )
    raw = await file.read()
    try:
        rows = parse_generic_icp_file(raw, file.filename or "icp_upload")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse ICP upload: {exc}") from exc
    if not rows:
        raise HTTPException(status_code=400, detail="No usable rows found in ICP upload")

    profile = aggregate_mining_context(rows)
    result = run_leadvault_mining(
        tenant_id=tenant_id,
        company_name=profile.get("company_name", ""),
        website=profile.get("website", ""),
        services=profile.get("services", []),
        geography=profile.get("geography", ""),
        icp=profile.get("icp", ""),
        positioning=profile.get("positioning", ""),
        customer_examples=profile.get("customer_examples", []),
        founder_profile=profile.get("founder_profile", ""),
        max_results=max(1, min(max_results, 100)),
        live_web=live_web,
        mining_mode=mining_mode,
        max_apify_queries=max(1, min(max_apify_queries, 25)),
        max_posts_per_query=max(1, min(max_posts_per_query, 25)),
        lead_objective=lead_objective or profile.get("lead_objective", ""),
    )
    result["summary"]["uploaded_rows"] = len(rows)
    result["summary"]["source_filename"] = file.filename
    return result


@router.post("/linkedin-capture")
def linkedin_capture(req: LinkedInCaptureRequest):
    return run_linkedin_capture_mining(
        tenant_id=req.tenant_id,
        posts_text=req.posts_text,
        rows=req.rows,
        query=req.query,
        max_results=max(1, min(req.max_results, 100)),
        lead_objective=req.lead_objective,
    )


@router.post("/linkedin-capture-upload")
async def linkedin_capture_upload(
    file: UploadFile = File(...),
    tenant_id: str = Form("default"),
    query: str = Form("linkedin_capture"),
    max_results: int = Form(50),
    lead_objective: str = Form("agency_procurement"),
):
    raw = await file.read()
    try:
        rows = parse_generic_icp_file(raw, file.filename or "linkedin_capture")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse LinkedIn capture upload: {exc}") from exc
    result = run_linkedin_capture_mining(
        tenant_id=tenant_id,
        rows=rows,
        query=query,
        max_results=max(1, min(max_results, 100)),
        lead_objective=lead_objective,
    )
    result["summary"]["uploaded_rows"] = len(rows)
    result["summary"]["source_filename"] = file.filename
    return result
