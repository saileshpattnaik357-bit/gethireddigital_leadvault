"""
API integration tests for new Revenue Intelligence, Hermes Memory, and Multi-Agent Mesh endpoints.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from main import app

client = TestClient(app)


class TestApiExtensions:
    def test_revenue_intelligence_analyze_endpoint(self):
        resp = client.post(
            "/api/leadvault/intelligence/analyze",
            json={
                "text": "Looking for an agency to build our Shopify Plus store ASAP. Budget allocated.",
                "title": "VP of E-commerce",
                "company_name": "Modern Retailers",
                "intent_score": 85,
                "confidence_score": 0.9,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["lead_tier"] == "A"
        assert data["budget_authority"] is True
        assert data["timeline"] == "immediate"
        assert "Estimated_Deal_Value" in data["revenue_intelligence_fields"]

    def test_hermes_conversion_and_reflection_endpoints(self):
        # 1. Record conversion
        conv_resp = client.post(
            "/api/leadvault/hermes/conversion",
            json={
                "tenant_id": "test_api_tenant",
                "lead_id": "lead_999",
                "company_name": "API Enterprise",
                "outcome": "closed_won",
                "deal_value": 75000,
                "feedback": "Signed annual contract",
                "matched_rules": ["explicit_vendor_search"],
            },
        )
        assert conv_resp.status_code == 200
        assert conv_resp.json()["status"] == "recorded"

        # 2. Query reflection
        ref_resp = client.get("/api/leadvault/hermes/reflection?tenant_id=test_api_tenant")
        assert ref_resp.status_code == 200
        ref_data = ref_resp.json()
        assert ref_data["tenant_id"] == "test_api_tenant"
        assert ref_data["total_outcomes_evaluated"] >= 1
        assert ref_data["conversion_rate"] > 0

    def test_mesh_process_endpoint(self):
        mesh_resp = client.post(
            "/api/leadvault/mesh/process",
            json={
                "tenant_id": "test_api_tenant",
                "company_name": "Test Client Agency",
                "candidates": [
                    {
                        "text": "Looking for an AI implementation partner for our sales workflow.",
                        "source": "LinkedIn Post",
                        "title": "Founder",
                    }
                ],
            },
        )
        assert mesh_resp.status_code == 200
        mesh_data = mesh_resp.json()
        assert mesh_data["total_candidates_processed"] == 1
        assert len(mesh_data["qualified_leads"]) == 1
        assert len(mesh_data["handoff_trace"]) >= 4

    def test_storage_stats_and_query_endpoints(self):
        resp = client.get("/api/leadvault/storage/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ONLINE"
        assert data["journal_mode"] == "WAL"
        assert "table_row_counts" in data
        assert "tenants" in data["table_row_counts"]

        tenants_resp = client.get("/api/leadvault/storage/tenants")
        assert tenants_resp.status_code == 200
        assert isinstance(tenants_resp.json(), list)

        leads_resp = client.get("/api/leadvault/storage/leads?tenant_id=default")
        assert leads_resp.status_code == 200
        assert isinstance(leads_resp.json(), list)
