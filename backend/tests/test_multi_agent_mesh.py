"""
Unit tests for LeadVault AI Multi-Agent Collaboration Mesh & Coordinator (V5).
"""

from __future__ import annotations

import pytest

from services.multi_agent_mesh import MultiAgentCoordinator


class TestMultiAgentMesh:
    def test_process_signals_end_to_end(self):
        coordinator = MultiAgentCoordinator(tenant_id="tenant_mesh_test")
        candidates = [
            {
                "text": "Looking for an agency partner to rebuild our Shopify Plus store ASAP.",
                "source": "LinkedIn Post",
                "url": "https://linkedin.com/posts/test1",
                "title": "VP of E-commerce",
            },
            {
                "text": "We are hiring a full-time Senior Python Backend Engineer. Apply here.",
                "source": "LinkedIn Job",
                "url": "https://linkedin.com/jobs/test2",
                "title": "Talent Acquisition",
            },
        ]

        summary = coordinator.process_signals(
            candidates,
            company_name="ShopCorp",
            lead_objective="agency_procurement",
        )

        assert summary.tenant_id == "tenant_mesh_test"
        assert summary.total_candidates_processed == 2
        assert len(summary.qualified_leads) == 1
        assert len(summary.disqualified_candidates) == 1

        # Check qualified lead
        lead = summary.qualified_leads[0]
        assert lead["lead_tier"] in {"A", "B"}
        assert lead["budget_authority"] is True
        assert "Estimated_Deal_Value" in lead["revenue_intelligence_fields"]

        # Check disqualified lead
        rej = summary.disqualified_candidates[0]
        assert rej["rejection_category"] == "RECRUITMENT"

        # Check multi-agent handoff trace
        trace = summary.handoff_trace
        assert len(trace) >= 4
        participating = summary.participating_agents
        assert "MiningCoordinator" in participating
        assert "SignalScoutAgent" in participating
        assert "ComplianceGateAgent" in participating
        assert "IntentScorerAgent" in participating
        assert "RevenueEnricherAgent" in participating
