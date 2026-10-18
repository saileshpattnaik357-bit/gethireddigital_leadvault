"""
Optional LLM validation layer.

Disabled unless BOTH are true:
    settings.LEADVAULT_LLM_VALIDATION == "1"
    settings.ANTHROPIC_API_KEY is set

When disabled, `validate()` returns an `unsure` verdict tagged provider="null"
and the deterministic verdict stands. This keeps the application fully
functional with zero model spend, which is its default state.

The model is only consulted for rows in the BORDERLINE band (see `is_borderline`):
verifier and scorer disagree, or the score sits in 45..79. Clear accepts and
clear rejects never cost a model call.

The model's verdict is ADVISORY. It may move a row between tiers inside the
orchestrator's rules; it cannot approve, export, bypass the approval gate, or
touch policy. Output is parsed as strict JSON; anything else -> unsure.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass
from typing import Any, Protocol

from harness import audit
from harness.context import ContextPacket
from harness.metrics import metrics

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
BORDERLINE_LOW = 45
BORDERLINE_HIGH = 79
MAX_LLM_CALLS_PER_RUN = 40


@dataclass
class LLMVerdict:
    verdict: str            # buyer | not_buyer | unsure
    confidence: float
    reason: str
    provider: str
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class Provider(Protocol):
    name: str

    def complete(self, *, system: str, user: str, model: str, max_tokens: int, timeout: int) -> tuple[str, int, int]:
        """Return (text, tokens_in, tokens_out)."""


class NullProvider:
    name = "null"

    def complete(self, *, system: str, user: str, model: str, max_tokens: int, timeout: int) -> tuple[str, int, int]:
        raise RuntimeError("llm_disabled")


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str) -> None:
        import anthropic  # imported lazily so the app never needs the SDK unless enabled

        self._client = anthropic.Anthropic(api_key=api_key)

    def complete(self, *, system: str, user: str, model: str, max_tokens: int, timeout: int) -> tuple[str, int, int]:
        response = self._client.with_options(timeout=timeout).messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=0,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(getattr(block, "text", "") for block in response.content)
        usage = getattr(response, "usage", None)
        return text, int(getattr(usage, "input_tokens", 0) or 0), int(getattr(usage, "output_tokens", 0) or 0)


class OpenAICompatProvider:
    """
    Any server that speaks the OpenAI chat-completions API:
      - Ollama locally      base_url=http://localhost:11434/v1   api_key unused
      - OpenAI in the cloud base_url=https://api.openai.com/v1  api_key required
    Uses urllib only, so there is no SDK dependency.
    """

    def __init__(self, base_url: str, api_key: str = "", name: str = "openai_compat") -> None:
        self.name = name
        self._base = base_url.rstrip("/")
        self._key = api_key

    def complete(self, *, system: str, user: str, model: str, max_tokens: int, timeout: int) -> tuple[str, int, int]:
        import urllib.request

        payload = {
            "model": model,
            "temperature": 0,
            "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        headers = {"Content-Type": "application/json"}
        if self._key:
            headers["Authorization"] = f"Bearer {self._key}"
        request = urllib.request.Request(
            f"{self._base}/chat/completions", data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8", errors="ignore"))
        text = ((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
        usage = data.get("usage") or {}
        return text, int(usage.get("prompt_tokens") or 0), int(usage.get("completion_tokens") or 0)


def _provider_name(settings: Any) -> str:
    return str(getattr(settings, "LEADVAULT_LLM_PROVIDER", "") or "").strip().lower()


def is_enabled(settings: Any) -> bool:
    """
    Enabled when LEADVAULT_LLM_VALIDATION=1 and the chosen provider has what it needs:
      ollama     nothing (local, no key)
      openai     OPENAI_API_KEY
      anthropic  ANTHROPIC_API_KEY
    """
    if str(getattr(settings, "LEADVAULT_LLM_VALIDATION", "") or "").strip() != "1":
        return False
    name = _provider_name(settings)
    if name == "ollama":
        return True
    if name == "openai":
        return bool((getattr(settings, "OPENAI_API_KEY", "") or "").strip())
    if name == "anthropic":
        return bool((getattr(settings, "ANTHROPIC_API_KEY", "") or "").strip())
    return False


def build_provider(settings: Any) -> Provider:
    if not is_enabled(settings):
        return NullProvider()
    name = _provider_name(settings)
    try:
        if name == "ollama":
            return OpenAICompatProvider(getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434/v1"), name="ollama")
        if name == "openai":
            return OpenAICompatProvider("https://api.openai.com/v1", settings.OPENAI_API_KEY, name="openai")
        if name == "anthropic":
            return AnthropicProvider(settings.ANTHROPIC_API_KEY)
    except Exception:  # noqa: BLE001 — SDK missing or misconfigured: degrade to disabled
        pass
    return NullProvider()


def is_borderline(*, should_export: bool, score: int) -> bool:
    """Verifier and scorer disagree, or the score is in the ambiguous band."""
    if should_export and score < 60:
        return True
    if (not should_export) and score >= 60:
        return True
    return BORDERLINE_LOW <= score <= BORDERLINE_HIGH


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse(text: str) -> tuple[str, float, str] | None:
    match = _JSON_RE.search(text or "")
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    verdict = str(data.get("verdict", "")).strip().lower()
    if verdict not in {"buyer", "not_buyer", "unsure"}:
        return None
    try:
        confidence = float(data.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))
    reason = str(data.get("reason", "")).strip()[:400]
    return verdict, confidence, reason


def validate(
    packet: ContextPacket,
    *,
    provider: Provider,
    model: str = DEFAULT_MODEL,
    tenant: str = "default",
    workflow: str | None = None,
    timeout: int = 20,
) -> LLMVerdict:
    if provider.name == "null":
        return LLMVerdict("unsure", 0.0, "llm validation disabled", provider.name, model, error="llm_disabled")

    started = time.perf_counter()
    try:
        text, tin, tout = provider.complete(
            system=packet.system_policy,
            user=packet.render_user_message(),
            model=model,
            max_tokens=200,
            timeout=timeout,
        )
    except Exception as exc:  # noqa: BLE001 — degrade, never raise into the pipeline
        latency = int((time.perf_counter() - started) * 1000)
        audit.record(who="llm_validator", what="tool.llm_validate", tenant=tenant, workflow=workflow,
                     policy="P-TOOL-LLM-01", result="error", error=str(exc), latency_ms=latency)
        return LLMVerdict("unsure", 0.0, "llm call failed; deterministic verdict stands", provider.name, model,
                          latency_ms=latency, error=str(exc)[:200])

    latency = int((time.perf_counter() - started) * 1000)
    metrics.llm_call(workflow, tokens_in=tin, tokens_out=tout)
    parsed = _parse(text)
    if parsed is None:
        audit.record(who="llm_validator", what="tool.llm_validate", tenant=tenant, workflow=workflow,
                     policy="P-TOOL-LLM-01", result="unparseable", evidence={"raw": text[:200]}, latency_ms=latency)
        return LLMVerdict("unsure", 0.0, "model returned non-JSON; ignored", provider.name, model, tin, tout, latency,
                          error="unparseable_output")

    verdict, confidence, reason = parsed
    audit.record(who="llm_validator", what="tool.llm_validate", tenant=tenant, workflow=workflow,
                 policy="P-TOOL-LLM-01", result="ok",
                 evidence={"verdict": verdict, "confidence": confidence, "reason": reason[:160]},
                 model=model, tokens_in=tin, tokens_out=tout, latency_ms=latency)
    return LLMVerdict(verdict, confidence, reason, provider.name, model, tin, tout, latency)
