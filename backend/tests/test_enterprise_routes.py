"""
Tests for LeadVault Enterprise REST API routes:
- /api/leadvault/intelligence/analyze
- /api/leadvault/hermes/conversion
- /api/leadvault/hermes/reflection
- /api/leadvault/mesh/process
- /api/leadvault/langgraph/execute
- /api/leadvault/webhooks/register
- /api/leadvault/webhooks/dispatch
- /api/leadvault/webhooks
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_analyze_intelligence_endpoint():
    res = client.post(
        "/api/leadvault/intelligence/analyze",
        json={
            "text": "Seeking an external agency for enterprise HubSpot migration ASAP. Approved budget ready.",
            "title": "VP RevOps",
            "company_name": "CloudCorp",
            "source": "LinkedIn",
            "category": "PROCUREMENT_BUYER",
            "intent_score": 88,
            "confidence_score": 0.85,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["lead_tier"] == "A"
    assert data["budget_authority"] is True
    assert data["timeline"] == "immediate"
    assert "$50K–$150K" in data["estimated_deal_value"] or "$150K–$250K" in data["estimated_deal_value"]


def test_hermes_conversion_and_reflection_endpoints():
    conv_res = client.post(
        "/api/leadvault/hermes/conversion",
        json={
            "tenant_id": "test_enterprise_tenant",
            "lead_id": "lead_123",
            "company_name": "ApexSaaS",
            "outcome": "CLOSED_WON",
            "deal_value": 75000,
            "feedback": "Signed contract within 14 days",
            "matched_rules": ["RULE_AGENCY_PROCUREMENT"],
        },
    )
    assert conv_res.status_code == 200
    assert conv_res.json()["status"] == "recorded"

    refl_res = client.get("/api/leadvault/hermes/reflection?tenant_id=test_enterprise_tenant")
    assert refl_res.status_code == 200
    refl_data = refl_res.json()
    assert refl_data["tenant_id"] == "test_enterprise_tenant"
    assert refl_data["total_outcomes_evaluated"] >= 1
    assert refl_data["conversion_rate"] == 1.0


def test_mesh_process_endpoint():
    res = client.post(
        "/api/leadvault/mesh/process",
        json={
            "tenant_id": "test_mesh_tenant",
            "company_name": "GrowthFlow",
            "lead_objective": "agency_procurement",
            "candidates": [
                {
                    "text": "Looking for an agency partner to rebuild our Shopify Plus store ASAP.",
                    "title": "Head of Growth",
                    "source": "LinkedIn",
                }
            ],
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_candidates_processed"] == 1
    assert len(data["qualified_leads"]) == 1
    assert data["qualified_leads"][0]["lead_tier"] in ["A", "B"]


def test_langgraph_execute_endpoint():
    res = client.post(
        "/api/leadvault/langgraph/execute",
        json={
            "tenant_id": "test_lg_tenant",
            "company_name": "TargetCorp",
            "lead_objective": "agency_procurement",
            "candidates": [
                {
                    "text": "We need a certified AWS partner to migrate our infrastructure.",
                    "title": "CTO",
                    "source": "LinkedIn Post",
                }
            ],
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "COMPLETED"
    assert data["checkpoint_step"] >= 5
    assert len(data["enriched_leads"]) == 1


def test_webhooks_register_and_list_endpoint():
    reg_res = client.post(
        "/api/leadvault/webhooks/register",
        json={
            "tenant_id": "test_wh_tenant",
            "target_url": "https://api.hubspot.com/v3/events",
            "secret_key": "sec_key_12345",
            "trigger_events": ["lead.approved"],
        },
    )
    assert reg_res.status_code == 200
    assert reg_res.json()["status"] == "registered"

    list_res = client.get("/api/leadvault/webhooks?tenant_id=test_wh_tenant")
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert any(item["target_url"] == "https://api.hubspot.com/v3/events" for item in items)
