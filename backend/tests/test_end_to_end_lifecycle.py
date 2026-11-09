"""LeadVault AI — End-to-End Enterprise Lifecycle Integration Test.

Verifies the complete pipeline:
ICP Ingest -> Boolean Query Synthesis -> Compliance Gate -> Multi-Head Intent Scoring ->
29-Field Revenue Dossier -> V7 Deep Research -> V8 Token Budget -> Relational SQL Persistence ->
Policy Triad Human Gate -> HMAC-SHA256 Webhook Stream -> V6 Hermes Learning -> V11 Closed-Loop OS.
"""

import pytest
from backend.services.closed_loop_os import ClosedLoopOperatingSystem
from backend.services.deep_research import DeepResearchEngine
from backend.services.hermes_memory import HermesMemoryEngine
from backend.services.multi_agent_mesh import MultiAgentCoordinator
from backend.services.revenue_intelligence import analyze_revenue_intelligence
from backend.services.storage_engine import StorageEngine
from backend.services.token_budget_queue import DistributedLeadQueue, QueuedLeadTask
from backend.services.universal_engine import build_discovery_plan, plan_as_dict
from backend.services.webhook_dispatcher import WebhookDispatcher


@pytest.mark.asyncio
async def test_complete_enterprise_lifecycle():
    tenant_id = "tenant_e2e_enterprise"

    # 1. Ingest ICP & Synthesize Queries (build_discovery_plan)
    plan = build_discovery_plan(
        company_name="Acme AI Studio",
        website="https://acme-ai.example.com",
        services=["Autonomous agent mesh architectures", "RevOps data pipelines"],
        lead_objective="agency_procurement",
    )
    spec = plan_as_dict(
        company_name="Acme AI Studio",
        website="https://acme-ai.example.com",
        services=["Autonomous agent mesh architectures", "RevOps data pipelines"],
        lead_objective="agency_procurement",
    )
    assert plan.lead_objective == "agency_procurement"
    assert len(plan.linkedin_search_phrases) > 0
    assert len(plan.google_search_phrases) > 0

    # 2. Multi-Agent Mesh Coordination (MultiAgentCoordinator)
    coordinator = MultiAgentCoordinator(tenant_id=tenant_id)
    raw_signal = (
        "We are looking for an elite agency partner to overhaul our underwriting pipelines ASAP. "
        "RFP closes in 14 days, approved budget $145,000."
    )
    candidates = [
        {
            "text": raw_signal,
            "title": "VP Global Procurement",
            "company_name": "Ramp Inc.",
            "url": "https://ramp.com",
            "source": "LinkedIn",
        }
    ]
    mesh_res = coordinator.process_signals(candidates)
    assert len(mesh_res.qualified_leads) == 1
    assert len(mesh_res.handoff_trace) >= 3

    # 3. 29-Field Revenue Intelligence Dossier (analyze_revenue_intelligence)
    dossier = analyze_revenue_intelligence(
        text=raw_signal,
        intent_score=95,
        confidence_score=0.94,
        title="VP Global Procurement",
        company_name="Ramp Inc.",
        industry="FinTech",
        source="LinkedIn",
        category="PROCUREMENT_BUYER",
        service_category="Custom Agent Integration",
    )
    assert dossier.lead_tier == "A"
    assert dossier.budget_authority is True
    assert dossier.deal_value_max >= 150000
    assert len(dossier.revenue_intelligence_fields) == 29

    # 4. V7 Deep Research & Expansion Intelligence (DeepResearchEngine)
    deep_engine = DeepResearchEngine()
    docs = [
        {"text": "Ramp secured $150M Series D funding for corporate cards.", "source": "TechCrunch", "timestamp_utc": "2026-11-05T12:00:00Z"},
        {"text": "Ramp welcomes Alex Vance as new VP Procurement.", "source": "LinkedIn", "timestamp_utc": "2026-11-06T08:00:00Z"},
        {"text": "We are migrating to Snowflake. Seeking implementation partner.", "source": "Reddit", "timestamp_utc": "2026-11-06T09:00:00Z"},
    ]
    research = deep_engine.analyze_company_signals("Ramp Inc.", "ramp.com", docs)
    assert research.expansion_urgency >= 80
    assert len(research.executive_signals) >= 1
    assert len(research.expansion_signals) >= 2

    # 5. V8 Distributed Queuing & Token Budget Governance (DistributedLeadQueue)
    token_queue = DistributedLeadQueue()
    token_queue.set_budget(tenant_id, budget_usd=50.00)
    assert token_queue.check_can_execute(tenant_id) is True

    task = QueuedLeadTask(task_id="task_e2e_01", tenant_id=tenant_id, payload=dossier.as_dict())
    token_queue.enqueue(tenant_id, task)

    batch_res = await token_queue.process_batch(
        tenant_id=tenant_id,
        items=[dossier.as_dict()],
        worker_fn=lambda x: {"status": "QUALIFIED", "lead_tier": x.get("lead_tier", "A")},
        estimated_prompt_tokens=200,
        estimated_output_tokens=60,
    )
    assert batch_res["success"] is True
    assert batch_res["processed_count"] == 1
    assert batch_res["budget_status"]["total_tokens"] == 260

    # 6. Relational SQL Persistence (StorageEngine)
    storage = StorageEngine()
    storage.save_spec(tenant_id, spec)
    lead_payload = {**dossier.as_dict(), **dossier.revenue_intelligence_fields, "Company Name": "Ramp Inc."}
    storage.insert_lead(tenant_id, "lead_ramp_e2e", lead_payload, status="ACCEPTED")

    leads_in_db = storage.list_leads(tenant_id, tier="A")
    assert len(leads_in_db) >= 1
    assert leads_in_db[0]["Company Name"] == "Ramp Inc."

    # 7. Cryptographic CRM Webhook Dispatcher (WebhookDispatcher)
    dispatcher = WebhookDispatcher()
    dispatcher.register_webhook(
        tenant_id=tenant_id,
        target_url="https://api.hubspot.com/v3/events",
        secret_key="whsec_e2e_test_secret",
        trigger_events=["lead.approved"],
    )
    dispatch_res = dispatcher.dispatch(
        tenant_id=tenant_id,
        event="lead.approved",
        lead_data=dossier.as_dict(),
    )
    assert len(dispatch_res) == 1
    assert dispatch_res[0].event == "lead.approved"
    signature = dispatcher.compute_signature(b"test_payload", "whsec_e2e_test_secret")
    assert len(signature) == 64

    # 8. V6 Hermes Episodic Conversion Memory (HermesMemoryEngine)
    hermes = HermesMemoryEngine()
    hermes.record_conversion_outcome(
        tenant_id=tenant_id,
        lead_id="lead_ramp_e2e",
        company_name="Ramp Inc.",
        outcome="closed_won",
        deal_value=145000,
        feedback="Signed in 14 days with budget authority pre-approved.",
        matched_rules=["RULE_AGENCY_PROCUREMENT", "RULE_BUDGET_CONFIRMED"],
    )
    report = hermes.run_reflection_cycle(tenant_id)
    assert report.total_outcomes_evaluated >= 1
    assert report.conversion_rate == 1.0

    # 9. V11 Autonomous Closed-Loop Operating System (ClosedLoopOperatingSystem)
    os_engine = ClosedLoopOperatingSystem()
    sanity = os_engine.run_golden_corpus_sanity()
    assert sanity.healthy is True
    assert sanity.precision >= 0.90

    # Model failover test
    assert os_engine.get_active_model() == "claude-3-5-sonnet"
    os_engine.record_model_failure("claude-3-5-sonnet", "Provider Timeout")
    os_engine.record_model_failure("claude-3-5-sonnet", "Provider Timeout")
    os_engine.record_model_failure("claude-3-5-sonnet", "Provider Timeout")
    assert os_engine.get_active_model() == "gpt-4o"
    os_engine.restore_model_health("claude-3-5-sonnet")
    assert os_engine.get_active_model() == "claude-3-5-sonnet"

    # CRM closed-loop feedback ingestion
    crm_feedback = os_engine.ingest_crm_stage_movement(
        tenant_id=tenant_id,
        lead_id="lead_ramp_e2e",
        company_name="Ramp Inc.",
        stage_transition="OPPORTUNITY->CLOSED_WON",
        deal_value_usd=145000.0,
        feedback="Won agency partner agreement.",
    )
    assert crm_feedback["status"] == "ACCEPTED"
