"""
Unit tests for LeadVault AI LangGraph Stateful Pipeline.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from services.langgraph_pipeline import CheckpointStore, LangGraphPipeline


@pytest.fixture
def temp_checkpoint_store(tmp_path: Path) -> CheckpointStore:
    return CheckpointStore(base_dir=tmp_path / "checkpoints")


class TestLangGraphPipeline:
    def test_pipeline_execution_end_to_end(self, temp_checkpoint_store: CheckpointStore):
        pipeline = LangGraphPipeline(
            tenant_id="tenant_lg_test",
            workflow_id="wf_test_100",
            checkpoint_store=temp_checkpoint_store,
        )

        candidates = [
            {
                "text": "Looking for an agency partner for our HubSpot migration ASAP. Budget approved.",
                "title": "VP of Revenue Operations",
                "source": "LinkedIn Post",
                "url": "https://linkedin.com/posts/sample-1",
            },
            {
                "text": "We are hiring a Senior React Developer. Send resume to jobs@example.com.",
                "title": "Recruiter",
                "source": "LinkedIn Job",
                "url": "https://linkedin.com/jobs/sample-2",
            },
        ]

        state = pipeline.run(candidates, company_name="RevTech Inc")

        assert state.status == "COMPLETED"
        assert state.checkpoint_step >= 5
        assert len(state.final_rejected) == 1
        assert len(state.enriched_leads) == 1

        lead = state.enriched_leads[0]
        assert lead["lead_tier"] == "A"
        assert lead["budget_authority"] is True
        assert lead["timeline"] == "immediate"

        # Check that checkpoint file was persisted
        loaded = temp_checkpoint_store.load("wf_test_100")
        assert loaded is not None
        assert loaded.workflow_id == "wf_test_100"
        assert loaded.status == "COMPLETED"

    def test_pipeline_resume_from_checkpoint(self, temp_checkpoint_store: CheckpointStore):
        pipeline = LangGraphPipeline(
            tenant_id="tenant_lg_test",
            workflow_id="wf_resume_200",
            checkpoint_store=temp_checkpoint_store,
        )

        candidates = [
            {
                "text": "Looking for an agency to build our e-commerce app.",
                "title": "Founder",
            }
        ]

        # Initial run
        state1 = pipeline.run(candidates)
        assert state1.checkpoint_step >= 5

        # Resume run should not crash and load saved state
        state2 = pipeline.run([], resume_from_checkpoint=True)
        assert state2.workflow_id == "wf_resume_200"
        assert len(state2.enriched_leads) == 1
