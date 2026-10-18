"""
Policy engine.

Decides, in plain code and outside any model, whether an action may proceed:

    ALLOW               safe automation — proceed and audit
    REQUIRE_APPROVAL    prepare, then park for a human decision
    DENY                never, regardless of what any agent or model says

Policies are keyed by action. Actions are the real things LeadVault can do
today plus the outbound actions it explicitly cannot (so that if someone wires
an email tool in later, it starts DENIED rather than silently allowed).

Autonomy levels (Phase 23 of the harness spec):
    0  information        1  recommendation      2  action preparation
    3  execute w/ approval 4  execute within policy 5  monitored high autonomy
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Decision(str, Enum):
    ALLOW = "ALLOW"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    DENY = "DENY"


class Autonomy(int, Enum):
    INFORMATION = 0
    RECOMMENDATION = 1
    PREPARATION = 2
    EXECUTE_WITH_APPROVAL = 3
    EXECUTE_WITHIN_POLICY = 4
    MONITORED_HIGH = 5


# Canonical action names. Anything not listed is DENIED by default.
class Action(str, Enum):
    GENERATE_SPEC = "generate_spec"                 # build mining brain from ICP
    MINE_CANDIDATES = "mine_candidates"             # spend budget on Apify / web fetch
    TOOL_APIFY_SEARCH = "tool.apify_linkedin_search"
    TOOL_WEB_SEARCH = "tool.duckduckgo_search"
    TOOL_FETCH_PAGE = "tool.fetch_public_page"
    TOOL_LLM_VALIDATE = "tool.llm_validate"
    CLASSIFY_CANDIDATE = "classify_candidate"       # deterministic scoring
    ACCEPT_LEAD = "accept_lead"                     # move a row to the accepted export
    EXPORT_ACCEPTED = "export_accepted"             # download xlsx/csv
    APPROVE_LEAD = "approve_lead"                   # human decision on a queued row
    # Outbound / mutating actions LeadVault does NOT implement. Listed so they are
    # denied explicitly rather than by omission.
    SEND_EMAIL = "send_email"
    SEND_LINKEDIN_MESSAGE = "send_linkedin_message"
    CRM_WRITE = "crm_write"
    BULK_OUTREACH = "bulk_outreach"


@dataclass
class PolicyDecision:
    action: str
    decision: Decision
    policy_id: str
    reason: str
    requires: list[str] = field(default_factory=list)

    @property
    def allowed(self) -> bool:
        return self.decision == Decision.ALLOW

    def as_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "decision": self.decision.value,
            "policy_id": self.policy_id,
            "reason": self.reason,
            "requires": list(self.requires),
        }


@dataclass
class Policy:
    policy_id: str
    action: Action
    decision: Decision
    reason: str
    autonomy: Autonomy
    requires: list[str] = field(default_factory=list)   # context keys that must be truthy
    risk: str = "low"                                    # low | medium | high

    def as_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "action": self.action.value,
            "decision": self.decision.value,
            "reason": self.reason,
            "autonomy_level": int(self.autonomy),
            "requires": list(self.requires),
            "risk": self.risk,
        }


POLICIES: list[Policy] = [
    Policy("P-SPEC-01", Action.GENERATE_SPEC, Decision.ALLOW,
           "Deterministic, no external spend, no external side effects.", Autonomy.RECOMMENDATION),
    Policy("P-MINE-01", Action.MINE_CANDIDATES, Decision.ALLOW,
           "Permitted only after the operator confirms the generated brain (cost gate).",
           Autonomy.EXECUTE_WITH_APPROVAL, requires=["confirmed"], risk="medium"),
    Policy("P-TOOL-APIFY-01", Action.TOOL_APIFY_SEARCH, Decision.ALLOW,
           "Paid external tool; bounded by max_queries/max_posts and a per-call timeout.",
           Autonomy.EXECUTE_WITHIN_POLICY, requires=["confirmed"], risk="medium"),
    Policy("P-TOOL-WEB-01", Action.TOOL_WEB_SEARCH, Decision.ALLOW,
           "Free public search; read-only.", Autonomy.EXECUTE_WITHIN_POLICY),
    Policy("P-TOOL-FETCH-01", Action.TOOL_FETCH_PAGE, Decision.ALLOW,
           "Read-only fetch of a public http(s) page; private/loopback hosts are refused by the gateway.",
           Autonomy.EXECUTE_WITHIN_POLICY),
    Policy("P-TOOL-LLM-01", Action.TOOL_LLM_VALIDATE, Decision.ALLOW,
           "Optional model call for borderline classifications; disabled unless configured; advisory only.",
           Autonomy.RECOMMENDATION, requires=["llm_enabled"], risk="low"),
    Policy("P-CLASS-01", Action.CLASSIFY_CANDIDATE, Decision.ALLOW,
           "Deterministic scoring; produces recommendation and evidence, no side effects.", Autonomy.RECOMMENDATION),
    Policy("P-ACCEPT-01", Action.ACCEPT_LEAD, Decision.ALLOW,
           "Tier-2 rows are accepted automatically into the export set.", Autonomy.EXECUTE_WITHIN_POLICY),
    Policy("P-ACCEPT-02", Action.ACCEPT_LEAD, Decision.REQUIRE_APPROVAL,
           "Tier-1 (hot) rows are parked for human review before they appear in the accepted export.",
           Autonomy.EXECUTE_WITH_APPROVAL, requires=["hot_tier"], risk="medium"),
    Policy("P-EXPORT-01", Action.EXPORT_ACCEPTED, Decision.ALLOW,
           "Export is tenant-scoped and read-only.", Autonomy.EXECUTE_WITHIN_POLICY),
    Policy("P-APPROVE-01", Action.APPROVE_LEAD, Decision.ALLOW,
           "Human decision; recorded with actor, timestamp, evidence and comment.", Autonomy.INFORMATION),
    Policy("P-OUT-EMAIL", Action.SEND_EMAIL, Decision.DENY,
           "No email integration exists. Denied until one is implemented behind approval.", Autonomy.INFORMATION, risk="high"),
    Policy("P-OUT-LI", Action.SEND_LINKEDIN_MESSAGE, Decision.DENY,
           "No LinkedIn messaging integration exists. Denied.", Autonomy.INFORMATION, risk="high"),
    Policy("P-OUT-CRM", Action.CRM_WRITE, Decision.DENY,
           "No CRM integration exists. Denied.", Autonomy.INFORMATION, risk="high"),
    Policy("P-OUT-BULK", Action.BULK_OUTREACH, Decision.DENY,
           "Bulk outbound actions are never automated.", Autonomy.INFORMATION, risk="high"),
]


class PolicyEngine:
    def __init__(self, policies: list[Policy] | None = None) -> None:
        self._policies = list(policies or POLICIES)

    def list_policies(self) -> list[dict[str, Any]]:
        return [p.as_dict() for p in self._policies]

    def decide(self, action: Action | str, context: dict[str, Any] | None = None) -> PolicyDecision:
        """
        Evaluate policies for an action, most restrictive applicable policy wins.

        A policy applies when all its `requires` keys are truthy in context. Among
        applicable policies: DENY > REQUIRE_APPROVAL > ALLOW. If no policy applies
        (e.g. a required context key is missing) the action is DENIED with the
        unmet requirement named.
        """
        ctx = context or {}
        name = action.value if isinstance(action, Action) else str(action)
        candidates = [p for p in self._policies if p.action.value == name]
        if not candidates:
            return PolicyDecision(name, Decision.DENY, "P-DEFAULT-DENY", "No policy defined for this action.")

        applicable: list[Policy] = []
        unmet: list[str] = []
        for policy in candidates:
            missing = [key for key in policy.requires if not ctx.get(key)]
            if missing:
                unmet.extend(missing)
                continue
            applicable.append(policy)

        # Approval policies with unmet requirements simply don't apply (the row is
        # not hot, so the hot-tier approval rule is irrelevant). Only fail when
        # *nothing* applies.
        if not applicable:
            return PolicyDecision(
                name, Decision.DENY, candidates[0].policy_id,
                f"Requirement not met: {', '.join(sorted(set(unmet)))}",
                requires=sorted(set(unmet)),
            )

        rank = {Decision.DENY: 2, Decision.REQUIRE_APPROVAL: 1, Decision.ALLOW: 0}
        chosen = max(applicable, key=lambda p: rank[p.decision])
        return PolicyDecision(name, chosen.decision, chosen.policy_id, chosen.reason, requires=list(chosen.requires))

    def assert_allowed(self, action: Action | str, context: dict[str, Any] | None = None) -> PolicyDecision:
        decision = self.decide(action, context)
        if decision.decision == Decision.DENY:
            raise PolicyDenied(decision)
        return decision


class PolicyDenied(PermissionError):
    def __init__(self, decision: PolicyDecision) -> None:
        super().__init__(f"{decision.action}: {decision.reason} [{decision.policy_id}]")
        self.decision = decision


policy_engine = PolicyEngine()
