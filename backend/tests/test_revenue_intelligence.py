"""
Unit and regression tests for LeadVault AI Revenue Intelligence & Deal Valuation Engine.
"""

from __future__ import annotations

import pytest

from services.revenue_intelligence import (
    analyze_revenue_intelligence,
    estimate_deal_value,
    extract_authority,
    extract_pain_point,
    extract_timeline,
)


class TestAuthorityExtraction:
    def test_c_suite_title_is_budget_holder(self):
        is_auth, role = extract_authority("Need an agency", title="CEO & Founder")
        assert is_auth is True
        assert role == "Budget Holder"

    def test_vp_title_is_budget_holder(self):
        is_auth, role = extract_authority("Looking for partners", title="VP of Growth")
        assert is_auth is True
        assert role == "Budget Holder"

    def test_manager_title_is_influencer(self):
        is_auth, role = extract_authority("Exploring options", title="Marketing Manager")
        assert is_auth is False
        assert role == "Influencer"

    def test_explicit_budget_in_text_is_budget_holder(self):
        is_auth, role = extract_authority("We have approved budget for external agency support", title="")
        assert is_auth is True
        assert role == "Budget Holder"


class TestTimelineExtraction:
    def test_asap_is_immediate(self):
        timeline = extract_timeline("Looking for an agency to start ASAP on urgent migration.")
        assert timeline == "immediate"

    def test_next_month_is_short_term(self):
        timeline = extract_timeline("Planning to hire external consultants within 60 days.")
        assert timeline == "1-3mo"

    def test_generic_is_nurture(self):
        timeline = extract_timeline("Interested in understanding SEO best practices.")
        assert timeline == "nurture"


class TestDealValuation:
    def test_enterprise_scope_valuation(self):
        label, d_min, d_max = estimate_deal_value("Enterprise multi-year transformation RFP", 85)
        assert "Enterprise" in label
        assert d_min >= 150000

    def test_strategic_scope_valuation(self):
        label, d_min, d_max = estimate_deal_value("Looking for ongoing fractional CMO agency partner", 80)
        assert "Strategic" in label
        assert d_min == 50000

    def test_tactical_scope_valuation(self):
        label, d_min, d_max = estimate_deal_value("Small audit need for our landing page", 55)
        assert "Tactical" in label
        assert d_max == 50000


class TestRevenueIntelligenceEndToEnd:
    def test_tier_a_sql_classification(self):
        result = analyze_revenue_intelligence(
            text="Looking for an AI implementation partner for our SaaS workflow ASAP. Budget allocated.",
            intent_score=85,
            confidence_score=0.88,
            title="CMO",
            company_name="CloudScale Corp",
            source="LinkedIn Post",
            category="PROCUREMENT_BUYER",
        )
        assert result.lead_tier == "A"
        assert result.budget_authority is True
        assert result.timeline == "immediate"
        assert result.urgency_score >= 80
        assert "Estimated_Deal_Value" in result.revenue_intelligence_fields
        assert result.revenue_intelligence_fields["Lead_Tier"] == "A"
        assert len(result.revenue_intelligence_fields) == 29

    def test_tier_b_mql_classification(self):
        result = analyze_revenue_intelligence(
            text="Exploring vendor options for next quarter.",
            intent_score=60,
            confidence_score=0.65,
            title="Marketing Lead",
            company_name="Acme Startup",
            source="LinkedIn Post",
            category="PROCUREMENT_BUYER",
        )
        assert result.lead_tier == "B"
        assert result.timeline == "1-3mo"
        assert len(result.revenue_intelligence_fields) == 29
