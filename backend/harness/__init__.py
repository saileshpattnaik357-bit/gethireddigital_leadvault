"""
LeadVault Agentic Harness — the control plane between the application and its
intelligence components.

Modules:
    audit      append-only audit log (who / what / when / under which policy / result)
    policy     action policy engine — ALLOW / REQUIRE_APPROVAL / DENY, enforced outside any model
    tools      tool registry + gateway: every external call goes through here (allowlist, timeouts, audit)
    registry   canonical registry of the components that actually exist, with honest autonomy levels
    workflow   explicit mining-run state machine with persisted transitions
    approvals  human-in-the-loop queue for high-impact rows
    context    bounded context packets; external content is always tagged untrusted
    llm        optional LLM validation layer (disabled unless configured), never authoritative on policy
    metrics    per-run observability (latency, tool calls, errors, accept rate, cost estimate)

Design rule: the LLM is never the final authority on permissions, tenant scope,
tool access, or export. Those are decided by `policy` and `tools`, in code.
"""
