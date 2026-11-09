import tempfile
from pathlib import Path
from backend.services.storage_engine import StorageEngine


def test_storage_engine_crud():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_leadvault.db"
        engine = StorageEngine(db_path=db_path)

        # 1. Tenant & Spec CRUD
        tenant_id = "test_acme_corp"
        spec_data = {
            "company_name": "Acme Corp",
            "website": "https://acme.com",
            "lead_objective": "agency_procurement",
            "services": ["AI Orchestration", "RevOps"],
        }
        engine.save_spec(tenant_id, spec_data)

        retrieved_spec = engine.get_spec(tenant_id)
        assert retrieved_spec is not None
        assert retrieved_spec["company_name"] == "Acme Corp"

        tenants = engine.list_tenants()
        assert any(t["tenant_id"] == tenant_id for t in tenants)

        # 2. Lead Insertion & Querying
        lead_dossier = {
            "Company Name": "Snowflake Inc.",
            "Company Website": "https://snowflake.com",
            "Client Name": "Marcus Thorne",
            "lead_tier": "A",
            "revenue_deal_value": "$220,000",
            "match_score": 95,
            "budget_authority": True,
            "procurement_timeline": "immediate",
            "Client Intent Signal": "Looking for external consultancy to overhaul billing.",
        }
        engine.insert_lead(tenant_id, "lead_snow_001", lead_dossier, status="ACCEPTED")

        leads = engine.list_leads(tenant_id, tier="A")
        assert len(leads) == 1
        assert leads[0]["Company Name"] == "Snowflake Inc."

        # 3. Hermes Conversion Logging & Stats
        engine.insert_conversion(
            tenant_id=tenant_id,
            conversion_id="conv_001",
            lead_id="lead_snow_001",
            company_name="Snowflake Inc.",
            outcome="CLOSED_WON",
            deal_value_usd=220000.0,
            feedback="Closed contract in 14 days",
            matched_rules=["RULE_AGENCY_PROCUREMENT", "RULE_BUDGET_CONFIRMED"],
        )

        stats = engine.get_conversion_stats(tenant_id)
        assert stats["total_conversions"] == 1
        assert stats["won_conversions"] == 1
        assert stats["total_won_revenue_usd"] == 220000.0
        assert stats["win_rate"] == 1.0

        # 4. Audit Logging
        engine.log_audit(
            tenant_id=tenant_id,
            agent_id="IntentScorerAgent",
            action="CLASSIFY_INTENT",
            status="SUCCESS",
            details={"score": 95, "tier": "A"},
        )
        logs = engine.get_recent_audit_logs(limit=5)
        assert len(logs) >= 1
        assert logs[0]["action"] == "CLASSIFY_INTENT"
