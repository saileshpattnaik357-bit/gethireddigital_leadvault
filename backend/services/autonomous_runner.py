from __future__ import annotations

from typing import Any

from services.background_jobs import create_job, run_job_async
from services.credential_diagnostics import provider_diagnostics
from services.crm_sync_store import sync_leads_to_crm
from services.leadvault_mining_runner import run_leadvault_mining


def run_autonomous_pipeline(payload: dict[str, Any]) -> dict[str, Any]:
    tenant_id = payload.get("tenant_id") or "default"
    diagnostics = provider_diagnostics()
    mining_mode = payload.get("mining_mode") or ("hybrid" if diagnostics.get("can_live_scrape") else "public_web")
    mining = run_leadvault_mining(
        tenant_id=tenant_id,
        company_name=payload.get("company_name", ""),
        website=payload.get("website", ""),
        services=payload.get("services") or [],
        geography=payload.get("geography", ""),
        icp=payload.get("icp", ""),
        positioning=payload.get("positioning", ""),
        customer_examples=payload.get("customer_examples") or [],
        founder_profile=payload.get("founder_profile", ""),
        max_results=max(1, min(int(payload.get("max_results") or 25), 100)),
        live_web=bool(payload.get("live_web", True)),
        mining_mode=mining_mode,
        max_apify_queries=max(1, min(int(payload.get("max_apify_queries") or 10), 25)),
        max_posts_per_query=max(1, min(int(payload.get("max_posts_per_query") or 10), 25)),
        lead_objective=payload.get("lead_objective") or "agency_procurement",
    )
    crm_sync = sync_leads_to_crm(tenant_id, mining.get("accepted") or [], provider=payload.get("crm_provider") or "local")
    mining["crm_sync"] = crm_sync
    mining["diagnostics"] = diagnostics
    mining["summary"]["crm_sync_status"] = crm_sync.get("status")
    mining["summary"]["crm_sync_mode"] = crm_sync.get("mode")
    return mining


def start_autonomous_job(payload: dict[str, Any]) -> dict[str, Any]:
    tenant_id = payload.get("tenant_id") or "default"
    job = create_job(tenant_id, "autonomous_lead_mining", payload)
    return run_job_async(job, lambda: run_autonomous_pipeline(payload))
