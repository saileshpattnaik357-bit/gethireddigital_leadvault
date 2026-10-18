"""
Agent registry.

Canonical description of the components that actually exist in LeadVault,
with honest classification. Per the harness rule "no fake agents":

    kind = "agent"    has an objective, makes decisions, calls tools or produces
                      recommendations with evidence, and updates workflow state.
    kind = "service"  deterministic function; listed here because agents depend
                      on it, but it is not an agent and is not described as one.

Autonomy levels follow harness.policy.Autonomy (0-5). No agent is above 3; the
deterministic export service is 4 (execute within policy); nothing is 5.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from harness.policy import Autonomy


@dataclass
class Contract:
    inputs: list[str]
    outputs: list[str]
    allowed_actions: list[str]
    forbidden_actions: list[str]
    approval: str
    evidence: str
    state_updates: list[str]
    memory: str
    failure: str
    escalation: str


@dataclass
class Component:
    agent_id: str
    name: str
    kind: str                       # agent | service
    category: str
    responsibility: str
    location: str                   # repository path
    version: str
    status: str                     # IMPLEMENTED | IMPLEMENTED_NOT_LIVE_VALIDATED | PLANNED
    model: str                      # "none (deterministic)" or model policy
    allowed_tools: list[str]
    forbidden_tools: list[str]
    autonomy: Autonomy
    tenant_scope: str
    timeout_seconds: int
    retry_policy: str
    contract: Contract
    capabilities: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["autonomy_level"] = int(self.autonomy)
        data["autonomy_label"] = self.autonomy.name.lower()
        data.pop("autonomy", None)
        return data


REGISTRY: list[Component] = [
    Component(
        agent_id="spec_planner",
        name="Mining Brain Planner",
        kind="service",
        category="targeting",
        responsibility="Turn a client ICP (services, positioning, audience, geography, objective) into buyer clusters, "
                       "search phrases, negative filters and a query bank. Deterministic templates; no model.",
        location="backend/services/leadvault_agent.py, backend/services/universal_engine.py",
        version="1.0",
        status="IMPLEMENTED",
        model="none (deterministic)",
        allowed_tools=[],
        forbidden_tools=["*"],
        autonomy=Autonomy.RECOMMENDATION,
        tenant_scope="single tenant per call (tenant_id parameter)",
        timeout_seconds=5,
        retry_policy="none (pure function)",
        capabilities=["objective normalisation", "service-alias expansion", "phrase generation", "query scoring"],
        contract=Contract(
            inputs=["company_name", "website", "services[]", "icp", "positioning", "customer_examples[]", "lead_objective", "tenant_id"],
            outputs=["LeadVaultSpec: buyer_clusters, linkedin_queries, google_queries, buyer_phrases, negative_filters, query_scores"],
            allowed_actions=["generate_spec"],
            forbidden_actions=["mine_candidates", "any tool call", "any outbound action"],
            approval="none — output is a recommendation the operator confirms before spend",
            evidence="query_scores carry the rule hits behind each phrase",
            state_updates=["workflow: PLANNED"],
            memory="none; spec is persisted by leadvault_spec_store (last 25)",
            failure="raises; no partial output",
            escalation="n/a",
        ),
    ),
    Component(
        agent_id="mining_orchestrator",
        name="Mining Orchestrator",
        kind="agent",
        category="discovery",
        responsibility="Given a confirmed spec, choose sources by mode, sequence tool calls within budget, gather "
                       "candidates, hand each to the qualifier, route accepted rows to export or approval, persist "
                       "results and advance workflow state.",
        location="backend/services/leadvault_mining_runner.py (run_leadvault_mining, run_linkedin_capture_mining)",
        version="1.1",
        status="IMPLEMENTED",
        model="none (deterministic control flow)",
        allowed_tools=["apify_linkedin_search", "duckduckgo_search", "fetch_public_page"],
        forbidden_tools=["llm_validate", "send_email", "crm_write", "any tool not in the registry"],
        autonomy=Autonomy.EXECUTE_WITH_APPROVAL,
        tenant_scope="single tenant per run",
        timeout_seconds=600,
        retry_policy="per-tool: Apify tries up to 4 payload shapes x N actors then reports empty; web: single attempt",
        capabilities=["source selection", "budget-bounded tool sequencing", "dedup within run", "persistence", "workflow transitions"],
        contract=Contract(
            inputs=["LeadVaultSpec", "confirmed=true", "mining_mode", "max_results", "max_apify_queries", "max_posts_per_query"],
            outputs=["accepted[]", "rejected[]", "pending_approval[]", "apify_report[]", "workflow_id", "metrics"],
            allowed_actions=["mine_candidates", "tool.* (registered tools only)", "accept_lead (tier_2)", "export_accepted"],
            forbidden_actions=["send_email", "send_linkedin_message", "crm_write", "bulk_outreach", "accept tier_1 without approval"],
            approval="operator confirm before any run; tier_1 rows parked for human review",
            evidence="every accepted row carries the qualifier's explainability_trace; every tool call is audited",
            state_updates=["CONFIRMED", "MINING", "CLASSIFIED", "REVIEW|EXPORTED", "FAILED"],
            memory="within-run dedup only; no cross-run memory (known gap)",
            failure="tool errors are recorded and skipped; unhandled error -> workflow FAILED with message",
            escalation="tier_1 rows -> approval queue; zero candidates -> summary flags it",
        ),
    ),
    Component(
        agent_id="intent_qualifier",
        name="Buying-Intent Qualifier",
        kind="agent",
        category="qualification",
        responsibility="Decide whether a candidate post is a real buyer of the client's services. Produces a category, "
                       "a 0-100 score, evidence (matched rules), negative signals, confidence, a recommended play and "
                       "whether human approval is required. Optionally asks the LLM validator for a second opinion on "
                       "borderline rows.",
        location="backend/services/final_verifier.py, backend/services/buying_intent_agent.py, backend/harness/llm.py",
        version="2.1",
        status="IMPLEMENTED",
        model="deterministic rules; optional advisory model call via llm_validate (disabled by default)",
        allowed_tools=["llm_validate"],
        forbidden_tools=["apify_linkedin_search", "duckduckgo_search", "fetch_public_page", "any outbound tool"],
        autonomy=Autonomy.RECOMMENDATION,
        tenant_scope="stateless per call",
        timeout_seconds=20,
        retry_policy="LLM: single attempt, fall back to deterministic verdict on any error",
        capabilities=["category verification", "rule-based scoring", "confidence", "explainability trace", "borderline LLM second opinion"],
        contract=Contract(
            inputs=["candidate text", "lead_objective", "account context (company, url, source)"],
            outputs=["VerificationResult", "BuyingIntentResult (score, stage, priority, evidence, negative_signals, confidence, approval_required)", "llm_verdict (optional)"],
            allowed_actions=["classify_candidate", "tool.llm_validate"],
            forbidden_actions=["accept_lead", "export_accepted", "any outbound action", "overriding policy"],
            approval="n/a — it recommends; approval_required=True for tier_1 is enforced by the orchestrator + policy",
            evidence="explainability_trace lists every rule and weight that fired; LLM verdict includes a reason string",
            state_updates=["none directly; orchestrator uses its output"],
            memory="none",
            failure="deterministic path cannot fail; LLM path degrades to deterministic verdict",
            escalation="approval_required=True on tier_1",
        ),
    ),
    Component(
        agent_id="llm_validator",
        name="LLM Validation Layer",
        kind="agent",
        category="qualification",
        responsibility="Second opinion on borderline classifications using a language model. Receives a bounded context "
                       "packet where the post is tagged as untrusted external data. Returns buyer / not_buyer / unsure "
                       "with a reason. Advisory only: it can move a row between tiers, it cannot bypass policy, tenant "
                       "scope, or the approval gate.",
        location="backend/harness/llm.py, backend/harness/context.py",
        version="0.1",
        status="IMPLEMENTED_NOT_LIVE_VALIDATED",
        model="LEADVAULT_LLM_PROVIDER: ollama (local, e.g. mistral) | openai (gpt-4o-mini) | anthropic; Null provider unless LEADVAULT_LLM_VALIDATION=1",
        allowed_tools=[],
        forbidden_tools=["*"],
        autonomy=Autonomy.RECOMMENDATION,
        tenant_scope="stateless per call; no tenant data beyond the packet",
        timeout_seconds=20,
        retry_policy="none; any failure -> 'unsure' with reason",
        capabilities=["borderline arbitration", "reason generation"],
        contract=Contract(
            inputs=["ContextPacket (objective, ICP summary, deterministic verdict, untrusted post text)"],
            outputs=["LLMVerdict: verdict, confidence, reason, model, tokens"],
            allowed_actions=["tool.llm_validate"],
            forbidden_actions=["any tool call", "any state change", "any policy decision"],
            approval="none — output is advisory",
            evidence="reason string; provider + model + token counts recorded in audit",
            state_updates=["none"],
            memory="none",
            failure="returns unsure; deterministic verdict stands",
            escalation="unsure -> row stays at deterministic tier",
        ),
    ),
    Component(
        agent_id="export_service",
        name="Export & Persistence",
        kind="service",
        category="workflow",
        responsibility="Persist accepted / rejected rows and produce CSV/XLSX in the frozen legacy schema.",
        location="backend/services/accepted_export_store.py, rejected_audit_store.py, api/routes/leadvault.py",
        version="1.0",
        status="IMPLEMENTED",
        model="none",
        allowed_tools=[],
        forbidden_tools=["*"],
        autonomy=Autonomy.EXECUTE_WITHIN_POLICY,
        tenant_scope="filtered by tenant_id string (no auth)",
        timeout_seconds=5,
        retry_policy="none",
        contract=Contract(
            inputs=["rows[]", "tenant_id"],
            outputs=["export_id", "xlsx/csv stream"],
            allowed_actions=["export_accepted"],
            forbidden_actions=["schema changes (frozen by DECISIONS.md)"],
            approval="none",
            evidence="rows carry intent_score, category, explainability_trace",
            state_updates=["workflow: EXPORTED"],
            memory="JSON stores: 100 exports / 100 rejected runs / 25 specs",
            failure="write error propagates",
            escalation="n/a",
        ),
    ),
]


def list_components(kind: str | None = None) -> list[dict[str, Any]]:
    items = REGISTRY if not kind else [c for c in REGISTRY if c.kind == kind]
    return [c.as_dict() for c in items]


def get_component(agent_id: str) -> Component | None:
    return next((c for c in REGISTRY if c.agent_id == agent_id), None)
