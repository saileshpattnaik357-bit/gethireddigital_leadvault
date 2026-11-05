"""
Tool registry and gateway.

Agents do not call external systems directly. They call `gateway.invoke(tool_id, ...)`,
which:

  1. looks the tool up in the registry (unknown tool -> refused),
  2. asks the policy engine whether the tool's action is permitted in this context,
  3. applies tool-specific guards (URL scheme/host checks for fetches),
  4. runs the tool with a wall-clock budget,
  5. records an audit event and a metrics sample regardless of outcome.

Only tools that actually exist in LeadVault are registered. There is no email,
CRM, or messaging tool because the product has none.
"""

from __future__ import annotations

import ipaddress
import socket
import time
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Callable

from harness import audit
from harness.metrics import metrics
from harness.policy import Action, Decision, PolicyDenied, policy_engine


@dataclass
class ToolSpec:
    tool_id: str
    purpose: str
    action: Action                     # policy action this tool maps to
    allowed_agents: list[str]
    input_schema: dict[str, str]
    output_schema: dict[str, str]
    risk: str                          # low | medium | high
    approval: str                      # none | operator_confirm | human_review
    timeout_seconds: int
    rate_limit_note: str
    external_spend: bool
    status: str = "IMPLEMENTED"

    def as_dict(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "purpose": self.purpose,
            "policy_action": self.action.value,
            "allowed_agents": list(self.allowed_agents),
            "input_schema": dict(self.input_schema),
            "output_schema": dict(self.output_schema),
            "risk": self.risk,
            "approval": self.approval,
            "timeout_seconds": self.timeout_seconds,
            "rate_limit": self.rate_limit_note,
            "external_spend": self.external_spend,
            "status": self.status,
        }


TOOL_SPECS: dict[str, ToolSpec] = {
    "apify_linkedin_search": ToolSpec(
        tool_id="apify_linkedin_search",
        purpose="Run a LinkedIn post-search actor on Apify for one query and return raw post candidates.",
        action=Action.TOOL_APIFY_SEARCH,
        allowed_agents=["mining_orchestrator"],
        input_schema={"query": "str", "max_posts": "int<=25"},
        output_schema={"candidates": "list[MiningCandidate]", "error": "str|None"},
        risk="medium",
        approval="operator_confirm",
        timeout_seconds=150,
        rate_limit_note="bounded by max_apify_queries (<=25) x actors (3) per run",
        external_spend=True,
    ),
    "duckduckgo_search": ToolSpec(
        tool_id="duckduckgo_search",
        purpose="HTML search on DuckDuckGo for one query; returns result titles and URLs.",
        action=Action.TOOL_WEB_SEARCH,
        allowed_agents=["mining_orchestrator"],
        input_schema={"query": "str", "limit": "int<=8"},
        output_schema={"candidates": "list[MiningCandidate]"},
        risk="low",
        approval="none",
        timeout_seconds=8,
        rate_limit_note="<=8 queries per run",
        external_spend=False,
    ),
    "fetch_public_page": ToolSpec(
        tool_id="fetch_public_page",
        purpose="Fetch one public http(s) page and extract buyer-intent sentences. Content is treated as untrusted data.",
        action=Action.TOOL_FETCH_PAGE,
        allowed_agents=["mining_orchestrator"],
        input_schema={"url": "str (http/https, public host only)", "limit": "int<=4"},
        output_schema={"candidates": "list[MiningCandidate]"},
        risk="low",
        approval="none",
        timeout_seconds=8,
        rate_limit_note="<=2 pages per search seed, <=16 per run",
        external_spend=False,
    ),
    "llm_validate": ToolSpec(
        tool_id="llm_validate",
        purpose="Ask a model for a second opinion on a borderline classification. Advisory only; disabled unless configured.",
        action=Action.TOOL_LLM_VALIDATE,
        allowed_agents=["intent_qualifier"],
        input_schema={"context_packet": "ContextPacket"},
        output_schema={"verdict": "buyer|not_buyer|unsure", "confidence": "0-1", "reason": "str"},
        risk="low",
        approval="none",
        timeout_seconds=20,
        rate_limit_note="only for candidates in the borderline band; capped per run",
        external_spend=True,
        status="IMPLEMENTED_NOT_LIVE_VALIDATED",
    ),
}


class ToolRefused(PermissionError):
    pass


_PRIVATE_HOSTNAMES = {"localhost", "metadata.google.internal"}


def _is_public_http_url(url: str) -> tuple[bool, str]:
    """Return (ok, reason). Refuses non-http schemes and private/loopback/link-local hosts."""
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return False, "unparseable_url"
    if parsed.scheme not in {"http", "https"}:
        return False, f"scheme_not_allowed:{parsed.scheme or 'none'}"
    host = (parsed.hostname or "").strip().lower()
    if not host:
        return False, "missing_host"
    if host in _PRIVATE_HOSTNAMES or host.endswith(".local") or host.endswith(".internal"):
        return False, "private_hostname"
    # Literal IP?
    try:
        ip = ipaddress.ip_address(host)
        if not ip.is_global:
            return False, "non_public_ip"
        return True, "ok"
    except ValueError:
        pass
    # Resolve and check every address.
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False, "dns_resolution_failed"
    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            continue
        if not ip.is_global:
            return False, f"resolves_to_non_public:{addr}"
    return True, "ok"


@dataclass
class ToolGateway:
    specs: dict[str, ToolSpec] = field(default_factory=lambda: dict(TOOL_SPECS))
    impls: dict[str, Callable[..., Any]] = field(default_factory=dict)

    def register_impl(self, tool_id: str, fn: Callable[..., Any]) -> None:
        if tool_id not in self.specs:
            raise KeyError(f"unknown tool: {tool_id}")
        self.impls[tool_id] = fn

    def list_tools(self) -> list[dict[str, Any]]:
        return [spec.as_dict() for spec in self.specs.values()]

    def is_url_allowed(self, url: str) -> bool:
        ok, _ = _is_public_http_url(url)
        return ok

    def invoke(
        self,
        tool_id: str,
        *,
        agent_id: str,
        tenant: str,
        workflow: str | None,
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        spec = self.specs.get(tool_id)
        if spec is None:
            audit.record(who=agent_id, what=f"tool.{tool_id}", tenant=tenant, workflow=workflow, result="refused", error="unknown_tool")
            raise ToolRefused(f"unknown tool: {tool_id}")
        if agent_id not in spec.allowed_agents:
            audit.record(who=agent_id, what=f"tool.{tool_id}", tenant=tenant, workflow=workflow, result="refused", error="agent_not_allowed")
            raise ToolRefused(f"{agent_id} may not call {tool_id}")

        decision = policy_engine.decide(spec.action, context or {})
        if decision.decision != Decision.ALLOW:
            audit.record(who=agent_id, what=f"tool.{tool_id}", tenant=tenant, workflow=workflow,
                         policy=decision.policy_id, result="denied", error=decision.reason)
            raise PolicyDenied(decision)

        if tool_id == "fetch_public_page":
            ok, reason = _is_public_http_url(str(kwargs.get("url", "")))
            if not ok:
                audit.record(who=agent_id, what=f"tool.{tool_id}", tenant=tenant, workflow=workflow,
                             policy=decision.policy_id, result="refused", error=reason,
                             evidence={"url": str(kwargs.get("url", ""))[:200]})
                metrics.tool_call(workflow, tool_id, ok=False, seconds=0.0)
                raise ToolRefused(f"fetch refused: {reason}")

        impl = self.impls.get(tool_id)
        if impl is None:
            audit.record(who=agent_id, what=f"tool.{tool_id}", tenant=tenant, workflow=workflow,
                         policy=decision.policy_id, result="error", error="no_implementation_registered")
            raise ToolRefused(f"{tool_id} has no implementation registered")

        started = time.perf_counter()
        try:
            result = impl(**kwargs)
        except Exception as exc:  # noqa: BLE001 — the gateway must record every failure
            elapsed = time.perf_counter() - started
            metrics.tool_call(workflow, tool_id, ok=False, seconds=elapsed)
            audit.record(who=agent_id, what=f"tool.{tool_id}", tenant=tenant, workflow=workflow,
                         policy=decision.policy_id, result="error", error=str(exc),
                         evidence={k: (str(v)[:120] if not isinstance(v, (int, float)) else v) for k, v in kwargs.items()})
            raise
        elapsed = time.perf_counter() - started
        size = len(result) if hasattr(result, "__len__") else 1
        metrics.tool_call(workflow, tool_id, ok=True, seconds=elapsed, items=size)
        audit.record(who=agent_id, what=f"tool.{tool_id}", tenant=tenant, workflow=workflow,
                     policy=decision.policy_id, result="ok",
                     evidence={k: (str(v)[:120] if not isinstance(v, (int, float)) else v) for k, v in kwargs.items()},
                     items=size, seconds=round(elapsed, 3))
        return result


gateway = ToolGateway()
