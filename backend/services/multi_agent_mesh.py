"""
LeadVault AI: Multi-Agent Collaboration Mesh & Orchestrator (V5)

Implements:
1. Multi-Agent Coordinator-Worker hierarchy:
   - MiningCoordinator: Top-level task planner and state orchestrator.
   - SignalScoutAgent: Tool-governed crawling across public portals.
   - IntentScorerAgent: Two-tier heuristic and confidence calibration.
   - RevenueEnricherAgent: 29-field revenue intelligence and deal valuation.
   - ComplianceGateAgent: FinalVerifier, SSRF, PII, and policy enforcement.
2. Structured inter-agent handoff traces.
3. Integration with Harness AuditLogger and ComponentRegistry.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from harness import audit
from services.buying_intent_agent import analyze_buying_intent
from services.final_verifier import verify_post
from services.revenue_intelligence import analyze_revenue_intelligence


@dataclass
class AgentTaskHandoff:
    step_number: int
    from_agent: str
    to_agent: str
    action: str
    payload_summary: dict[str, Any]
    status: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class MultiAgentRunSummary:
    workflow_id: str
    tenant_id: str
    coordinator: str
    participating_agents: list[str]
    handoff_trace: list[AgentTaskHandoff]
    total_candidates_processed: int
    qualified_leads: list[dict[str, Any]]
    disqualified_candidates: list[dict[str, Any]]
    execution_time_ms: float
    completed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class MultiAgentCoordinator:
    """
    Coordinates execution across the specialized agent mesh.
    Ensures strict handoff boundaries, explainability, and policy compliance.
    """

    def __init__(self, tenant_id: str = "default", workflow_id: str | None = None):
        self.tenant_id = tenant_id
        self.workflow_id = workflow_id or f"wf_mesh_{int(datetime.now(timezone.utc).timestamp())}"
        self.handoff_trace: list[AgentTaskHandoff] = []

    def _record_handoff(
        self,
        from_agent: str,
        to_agent: str,
        action: str,
        summary: dict[str, Any],
        status: str = "SUCCESS",
    ) -> None:
        step = len(self.handoff_trace) + 1
        handoff = AgentTaskHandoff(
            step_number=step,
            from_agent=from_agent,
            to_agent=to_agent,
            action=action,
            payload_summary=summary,
            status=status,
        )
        self.handoff_trace.append(handoff)
        audit.record(
            who=from_agent,
            what=action,
            tenant=self.tenant_id,
            workflow=self.workflow_id,
            policy="POL-MESH-01",
            evidence={"step": step, "target_agent": to_agent, **summary},
        )

    def process_signals(
        self,
        raw_candidates: list[dict[str, Any]],
        *,
        company_name: str = "",
        lead_objective: str = "",
    ) -> MultiAgentRunSummary:
        start_time = datetime.now(timezone.utc)
        self._record_handoff(
            from_agent="MiningCoordinator",
            to_agent="SignalScoutAgent",
            action="receive_raw_candidates",
            summary={"count": len(raw_candidates), "objective": lead_objective},
        )

        qualified_leads: list[dict[str, Any]] = []
        disqualified: list[dict[str, Any]] = []

        for candidate in raw_candidates:
            text = candidate.get("text", "")
            source = candidate.get("source", "web_portal")
            url = candidate.get("url", "")
            title = candidate.get("title", "")

            # Handoff 1: Compliance & Noise Filtering
            self._record_handoff(
                from_agent="SignalScoutAgent",
                to_agent="ComplianceGateAgent",
                action="verify_anti_noise",
                summary={"text_sample": text[:60]},
            )
            classification = verify_post(text, lead_objective=lead_objective)

            if not classification.should_export:
                disqualified.append({
                    "text": text,
                    "url": url,
                    "source": source,
                    "rejection_category": classification.category,
                    "rationale": classification.rationale,
                })
                continue

            # Handoff 2: Intent Classification & Scoring
            self._record_handoff(
                from_agent="ComplianceGateAgent",
                to_agent="IntentScorerAgent",
                action="score_buying_intent",
                summary={"category": classification.category},
            )
            intent = analyze_buying_intent(
                text,
                account={"company": title, "website": url, "source": source},
                verification_category=classification.category,
            )

            # Handoff 3: Revenue Intelligence Enrichment
            self._record_handoff(
                from_agent="IntentScorerAgent",
                to_agent="RevenueEnricherAgent",
                action="generate_revenue_dossier",
                summary={"intent_score": intent.intent_score, "priority": intent.priority},
            )
            revenue_intel = analyze_revenue_intelligence(
                text=text,
                intent_score=intent.intent_score,
                confidence_score=intent.confidence_score,
                title=title,
                company_name=company_name or title or "Prospect Company",
                source=source,
                category=classification.category,
                service_category=intent.signal_type,
            )

            lead_dossier = {
                "tenant_id": self.tenant_id,
                "workflow_id": self.workflow_id,
                "text": text,
                "url": url,
                "source": source,
                "lead_tier": revenue_intel.lead_tier,
                "estimated_deal_value": revenue_intel.estimated_deal_value,
                "budget_authority": revenue_intel.budget_authority,
                "timeline": revenue_intel.timeline,
                "intent_score": intent.intent_score,
                "confidence_score": intent.confidence_score,
                "pain_point_summary": revenue_intel.pain_point_summary,
                "recommended_angle": revenue_intel.recommended_outreach_angle,
                "revenue_intelligence_fields": revenue_intel.revenue_intelligence_fields,
            }
            qualified_leads.append(lead_dossier)

        duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        self._record_handoff(
            from_agent="RevenueEnricherAgent",
            to_agent="MiningCoordinator",
            action="finalize_multi_agent_run",
            summary={"qualified": len(qualified_leads), "disqualified": len(disqualified)},
        )

        return MultiAgentRunSummary(
            workflow_id=self.workflow_id,
            tenant_id=self.tenant_id,
            coordinator="MultiAgentCoordinator",
            participating_agents=[
                "MiningCoordinator",
                "SignalScoutAgent",
                "ComplianceGateAgent",
                "IntentScorerAgent",
                "RevenueEnricherAgent",
            ],
            handoff_trace=self.handoff_trace,
            total_candidates_processed=len(raw_candidates),
            qualified_leads=qualified_leads,
            disqualified_candidates=disqualified,
            execution_time_ms=round(duration_ms, 2),
        )
