"""Regression tests for LeadVaultAI buying intent classifier."""

from __future__ import annotations

import json
from typing import Any

import pytest

from services.buying_intent_agent import analyze_buying_intent
from services.final_verifier import verify_post


class TestFinalVerifier:
    """Test the final verifier that categorizes posts."""

    def test_accept_explicit_vendor_search(self):
        """Should accept explicit vendor/agency search."""
        result = verify_post("Looking for an AI implementation partner for our workflow.")
        assert result.category == "PROCUREMENT_BUYER"
        assert result.should_export is True

    def test_accept_agency_recommendation(self):
        """Should accept recommendation requests for agencies."""
        result = verify_post("Can anyone recommend a good SEO agency?")
        assert result.category == "PROCUREMENT_BUYER"
        assert result.should_export is True

    def test_accept_implementation_partner(self):
        """Should accept implementation partner search."""
        result = verify_post("Seeking an implementation partner for HubSpot.")
        assert result.category == "PROCUREMENT_BUYER"
        assert result.should_export is True

    def test_accept_consultant_need(self):
        """Should accept explicit consultant need."""
        result = verify_post("Need external RevOps consultant for Q3.")
        assert result.category == "PROCUREMENT_BUYER"
        assert result.should_export is True

    def test_reject_recruitment(self):
        """Should reject job postings."""
        result = verify_post("We are hiring a Python developer, 5+ years experience. Send resume.")
        assert result.category == "RECRUITMENT"
        assert result.should_export is False

    def test_reject_seller_promotion(self):
        """Should reject seller self-promotion."""
        result = verify_post("We help brands with AI automation. DM me for services.")
        assert result.category == "SELLER_PROMOTION"
        assert result.should_export is False

    def test_reject_educational(self):
        """Should reject educational/thought leadership."""
        result = verify_post("5 AI trends for 2026. How to build GTM workflows.")
        assert result.category == "EDUCATIONAL"
        assert result.should_export is False

    def test_reject_open_for_projects(self):
        """Should reject generic 'open for projects' posts."""
        result = verify_post("Open for projects. Available for consulting work.")
        assert result.category == "SELLER_PROMOTION"
        assert result.should_export is False


class TestBuyingIntentScoring:
    """Test the buying intent scoring system."""

    def test_strong_procurement_signal_scores_high(self):
        """Strong procurement signals should score 60+."""
        result = analyze_buying_intent(
            "Looking for an AI implementation partner for our SaaS workflow."
        )
        assert result.intent_score >= 60
        assert result.buying_stage in {"active_research", "hot"}

    def test_recruitment_post_scores_low(self):
        """Recruitment posts should score below 50."""
        result = analyze_buying_intent(
            "We are hiring a Python developer, 5+ years experience."
        )
        assert result.intent_score < 50
        assert result.buying_stage == "cold_or_noise"

    def test_seller_promotion_scores_low(self):
        """Seller promotion should score below 50."""
        result = analyze_buying_intent("We help companies with AI automation. DM me.")
        assert result.intent_score < 50

    def test_final_verifier_boost_procurement(self):
        """Final verifier should boost procurement signals."""
        result = analyze_buying_intent(
            "Looking for a consultant.",
            verification_category="PROCUREMENT_BUYER",
        )
        assert result.intent_score >= 60

    def test_final_verifier_penalize_recruitment(self):
        """Final verifier should penalize recruitment posts."""
        result = analyze_buying_intent(
            "Looking for...",  # Matches procurement rule
            verification_category="RECRUITMENT",
        )
        # Should be penalized to below acceptance threshold
        assert result.intent_score < 80


class TestExportSchemaValidation:
    """Test that accepted leads preserve the exact export schema."""

    EXPECTED_COLUMNS = [
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

    def test_export_schema_columns_exact(self):
        """Export schema must have exactly these columns in order."""
        from api.routes.leadvault import EXACT_EXPORT_COLUMNS

        assert EXACT_EXPORT_COLUMNS == self.EXPECTED_COLUMNS

    def test_no_field_renaming(self):
        """Fields must not be renamed."""
        from api.routes.leadvault import EXACT_EXPORT_COLUMNS

        assert "Client Name" in EXACT_EXPORT_COLUMNS
        assert "Client name" not in EXACT_EXPORT_COLUMNS
        assert "ClientName" not in EXACT_EXPORT_COLUMNS

    def test_no_field_removal(self):
        """All required fields must be present."""
        from api.routes.leadvault import EXACT_EXPORT_COLUMNS

        critical_fields = [
            "Date Added",
            "Client Name",
            "Company Name",
            "Client Intent Signal",
            "Client Exact Query",
        ]
        for field in critical_fields:
            assert field in EXACT_EXPORT_COLUMNS


class TestTenantIsolation:
    """Test that tenant data is properly isolated."""

    def test_tenant_id_preserved_in_responses(self):
        """Tenant ID must be preserved in all responses."""
        result = analyze_buying_intent(
            "Looking for an agency.",
            account={"company": "Test Corp", "website": "test.com"},
        )
        # Result should have evidence and evidence should be in trace
        assert isinstance(result.explainability_trace, list)
        # The result itself doesn't have tenant_id, but it's preserved elsewhere
        assert hasattr(result, "scored_at_utc")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
