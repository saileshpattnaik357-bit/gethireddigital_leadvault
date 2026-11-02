"""
Unit tests for LeadVault AI Hermes Learning Memory Engine.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from services.hermes_memory import HermesMemoryEngine


@pytest.fixture
def temp_memory(tmp_path: Path) -> HermesMemoryEngine:
    file_path = tmp_path / "test_hermes.json"
    return HermesMemoryEngine(storage_path=file_path)


class TestHermesMemoryEngine:
    def test_record_conversion_outcome(self, temp_memory: HermesMemoryEngine):
        entry = temp_memory.record_conversion_outcome(
            tenant_id="tenant_alpha",
            lead_id="lead_101",
            company_name="Acme SaaS",
            outcome="closed_won",
            deal_value=65000,
            feedback="Customer signed 12-month agency contract",
            matched_rules=["explicit_vendor_search", "budget_allocation"],
        )
        assert entry.outcome == "closed_won"
        assert entry.deal_value_actual == 65000

        # Verify tenant isolation
        bucket = temp_memory._get_tenant_bucket("tenant_alpha")
        assert len(bucket["episodic_outcomes"]) == 1
        assert bucket["rule_performance"]["explicit_vendor_search"]["positive"] == 1

        # Tenant beta must be clean
        beta_bucket = temp_memory._get_tenant_bucket("tenant_beta")
        assert len(beta_bucket["episodic_outcomes"]) == 0

    def test_record_operator_decision(self, temp_memory: HermesMemoryEngine):
        temp_memory.record_operator_decision(
            tenant_id="tenant_alpha",
            approval_id="appr_001",
            decision="approve",
            actor="senior_sdr",
            reason="Confirmed high-intent post from Founder",
            matched_rules=["explicit_vendor_search"],
        )
        bucket = temp_memory._get_tenant_bucket("tenant_alpha")
        assert len(bucket["operator_decisions"]) == 1
        assert bucket["operator_decisions"][0]["decision"] == "approve"

    def test_reflection_cycle_adjusts_weights(self, temp_memory: HermesMemoryEngine):
        # Record 4 positive outcomes for explicit_vendor_search
        for i in range(4):
            temp_memory.record_conversion_outcome(
                tenant_id="tenant_gamma",
                lead_id=f"lead_{i}",
                company_name=f"Company_{i}",
                outcome="closed_won",
                deal_value=50000,
                matched_rules=["explicit_vendor_search"],
            )

        # Record 4 negative outcomes for underperforming rule
        for i in range(4):
            temp_memory.record_conversion_outcome(
                tenant_id="tenant_gamma",
                lead_id=f"lead_bad_{i}",
                company_name=f"BadCompany_{i}",
                outcome="disqualified",
                matched_rules=["weak_signal_rule"],
            )

        report = temp_memory.run_reflection_cycle("tenant_gamma")
        assert report.total_outcomes_evaluated == 8
        assert report.conversion_rate == 0.5
        assert any(r["rule"] == "explicit_vendor_search" for r in report.high_yield_rules)
        assert any(r["rule"] == "weak_signal_rule" for r in report.underperforming_rules)

        weights = temp_memory.get_active_weight_adjustments("tenant_gamma")
        assert weights.get("explicit_vendor_search", 0) > 0
        assert weights.get("weak_signal_rule", 0) < 0
