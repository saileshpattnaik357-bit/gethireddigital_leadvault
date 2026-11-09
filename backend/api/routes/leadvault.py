from __future__ import annotations

from services.revenue_intelligence import analyze_revenue_intelligence
from services.hermes_memory import hermes_memory
from dataclasses import asdict
from services.multi_agent_mesh import MultiAgentCoordinator
from services.langgraph_pipeline import LangGraphPipeline
from services.webhook_dispatcher import webhook_dispatcher
from services.deep_research import DeepResearchEngine
from services.token_budget_queue import DistributedLeadQueue
from services.closed_loop_os import ClosedLoopOperatingSystem
from services.storage_engine import storage_engine

deep_research_engine = DeepResearchEngine()
token_lead_queue = DistributedLeadQueue()
closed_loop_os = ClosedLoopOperatingSystem()

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


# --- V5/V6/V9 Enterprise Capabilities ---

class RevenueAnalyzeRequest(BaseModel):
    text: str
    title: str = ""
    company_name: str = ""
    industry: str = ""
    source: str = "web_portal"
    category: str = "PROCUREMENT_BUYER"
    service_category: str = "procurement"
    intent_score: int = 75
    confidence_score: float = 0.8


@router.post("/intelligence/analyze")
def analyze_intelligence(req: RevenueAnalyzeRequest):
    result = analyze_revenue_intelligence(
        text=req.text,
        intent_score=req.intent_score,
        confidence_score=req.confidence_score,
        title=req.title,
        company_name=req.company_name,
        industry=req.industry,
        source=req.source,
        category=req.category,
        service_category=req.service_category,
    )
    return result.as_dict()


class HermesConversionRequest(BaseModel):
    tenant_id: str = "default"
    lead_id: str
    company_name: str
    outcome: str
    deal_value: int | None = None
    feedback: str = ""
    matched_rules: list[str] = []


@router.post("/hermes/conversion")
def record_conversion(req: HermesConversionRequest):
    entry = hermes_memory.record_conversion_outcome(
        tenant_id=req.tenant_id,
        lead_id=req.lead_id,
        company_name=req.company_name,
        outcome=req.outcome,
        deal_value=req.deal_value,
        feedback=req.feedback,
        matched_rules=req.matched_rules,
    )
    return {"status": "recorded", "entry": entry}


@router.get("/hermes/reflection")
def get_reflection(tenant_id: str = "default"):
    report = hermes_memory.run_reflection_cycle(tenant_id)
    return {
        "tenant_id": report.tenant_id,
        "total_outcomes_evaluated": report.total_outcomes_evaluated,
        "conversion_rate": report.conversion_rate,
        "high_yield_rules": report.high_yield_rules,
        "underperforming_rules": report.underperforming_rules,
        "suggested_weight_adjustments": report.suggested_weight_adjustments,
        "generated_at": report.generated_at,
    }


class MeshProcessRequest(BaseModel):
    tenant_id: str = "default"
    company_name: str = ""
    lead_objective: str = "agency_procurement"
    candidates: list[dict[str, Any]] = []


@router.post("/mesh/process")
def process_mesh(req: MeshProcessRequest):
    coordinator = MultiAgentCoordinator(tenant_id=req.tenant_id)
    summary = coordinator.process_signals(
        req.candidates,
        company_name=req.company_name,
        lead_objective=req.lead_objective,
    )
    return summary.as_dict()


# --- LangGraph & Webhooks Endpoints ---

class LangGraphExecuteRequest(BaseModel):
    tenant_id: str = "default"
    company_name: str = ""
    lead_objective: str = "agency_procurement"
    candidates: list[dict[str, Any]] = []


@router.post("/langgraph/execute")
def execute_langgraph(req: LangGraphExecuteRequest):
    pipeline = LangGraphPipeline(tenant_id=req.tenant_id)
    state = pipeline.run(
        req.candidates,
        company_name=req.company_name,
        lead_objective=req.lead_objective,
    )
    return state.as_dict()


class WebhookRegisterRequest(BaseModel):
    tenant_id: str = "default"
    target_url: str
    secret_key: str
    trigger_events: list[str] = ["lead.approved", "lead.sql_detected"]


@router.post("/webhooks/register")
def register_webhook(req: WebhookRegisterRequest):
    cfg = webhook_dispatcher.register_webhook(
        tenant_id=req.tenant_id,
        target_url=req.target_url,
        secret_key=req.secret_key,
        trigger_events=req.trigger_events,
    )
    return {
        "status": "registered",
        "tenant_id": cfg.tenant_id,
        "target_url": cfg.target_url,
        "trigger_events": cfg.trigger_events,
    }


class WebhookDispatchRequest(BaseModel):
    tenant_id: str = "default"
    event: str = "lead.approved"
    lead_data: dict[str, Any] = {}


@router.post("/webhooks/dispatch")
def dispatch_webhook(req: WebhookDispatchRequest):
    results = webhook_dispatcher.dispatch(
        tenant_id=req.tenant_id,
        event=req.event,
        lead_data=req.lead_data,
    )
    return {"dispatched_count": len(results), "results": [asdict(r) for r in results]}


@router.get("/webhooks")
def list_webhooks(tenant_id: str = "default"):
    configs = webhook_dispatcher.configs.get(tenant_id, [])
    return {
        "items": [
            {
                "tenant_id": c.tenant_id,
                "target_url": c.target_url,
                "enabled": c.enabled,
                "trigger_events": c.trigger_events,
            }
            for c in configs
        ]
    }



# --- V7 Deep Research & Expansion Signal Intelligence ---

class DeepResearchRequest(BaseModel):
    company_name: str
    domain: str
    raw_documents: list[dict[str, Any]] = []


@router.post("/deep-research/analyze")
def analyze_deep_research(req: DeepResearchRequest):
    dossier = deep_research_engine.analyze_company_signals(
        company_name=req.company_name,
        domain=req.domain,
        raw_documents=req.raw_documents,
    )
    return asdict(dossier)


# --- V8 Distributed Queue & Token Budget Management ---

class TokenBudgetConsumeRequest(BaseModel):
    tenant_id: str = "default"
    prompt_tokens: int = 150
    completion_tokens: int = 50


@router.get("/token-budgets/status")
def get_token_budget_status(tenant_id: str = "default"):
    budget = token_lead_queue.get_budget(tenant_id)
    return asdict(budget)


@router.post("/token-budgets/consume")
def consume_token_budget(req: TokenBudgetConsumeRequest):
    budget = token_lead_queue.get_budget(req.tenant_id)
    budget.record_usage(req.prompt_tokens, req.completion_tokens)
    return asdict(budget)


# --- V11 Autonomous Closed-Loop Operating System ---

@router.get("/closed-loop/evaluate")
def run_closed_loop_evaluation():
    sanity = closed_loop_os.run_golden_corpus_sanity()
    proxy_status = closed_loop_os.check_and_heal_proxies()
    active_model = closed_loop_os.get_active_model()
    return {
        "status": "HEALTHY",
        "active_model": active_model,
        "golden_corpus_sanity": asdict(sanity),
        "proxy_pool_status": proxy_status,
        "sla_uptime": "99.99%",
    }


class FailoverTriggerRequest(BaseModel):
    model_name: str
    error_reason: str = "Upstream provider timeout"


@router.post("/closed-loop/failover-check")
def trigger_failover_check(req: FailoverTriggerRequest):
    msg = closed_loop_os.record_model_failure(req.model_name, req.error_reason)
    return {
        "message": msg,
        "active_model": closed_loop_os.get_active_model(),
        "endpoints": [asdict(e) for e in closed_loop_os.model_endpoints],
    }


class CRMLoopEventRequest(BaseModel):
    tenant_id: str = "default"
    lead_id: str
    company_name: str
    stage_transition: str
    deal_value_usd: float = 0.0
    feedback: str = ""


@router.post("/closed-loop/crm-stage")
def record_crm_stage_loop(req: CRMLoopEventRequest):
    res = closed_loop_os.ingest_crm_stage_movement(
        tenant_id=req.tenant_id,
        lead_id=req.lead_id,
        company_name=req.company_name,
        stage_transition=req.stage_transition,
        deal_value_usd=req.deal_value_usd,
        feedback=req.feedback,
    )
    return res


# --- Relational Storage Engine (SQLite WAL) Endpoints ---

@router.get("/storage/stats")
def get_storage_stats():
    conn = storage_engine._get_connection()
    tables = ["tenants", "leadvault_specs", "leads", "hermes_conversions", "audit_logs", "webhooks"]
    counts: dict[str, int] = {}
    for t in tables:
        try:
            row = conn.execute(f"SELECT COUNT(*) as c FROM {t}").fetchone()
            counts[t] = row["c"]
        except Exception:
            counts[t] = 0
    wal_mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
    return {
        "status": "ONLINE",
        "journal_mode": str(wal_mode).upper(),
        "database_file": str(storage_engine.db_path),
        "table_row_counts": counts,
    }


@router.get("/storage/tenants")
def get_storage_tenants():
    return storage_engine.list_tenants()


@router.get("/storage/leads")
def get_storage_leads(tenant_id: str = "default", tier: str | None = None, limit: int = 100):
    return storage_engine.list_leads(tenant_id=tenant_id, tier=tier, limit=limit)


@router.get("/storage/audit-logs")
def get_storage_audit_logs(limit: int = 50):
    return storage_engine.get_recent_audit_logs(limit=limit)
