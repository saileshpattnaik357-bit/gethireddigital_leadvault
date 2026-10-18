"""
AIService — the provider adapter `leadvault_agent.build_leadvault_spec_with_llm` expects.

Before this file existed the import in leadvault_agent.py failed silently and the
"AI Refine" path was a no-op. It now delegates to the harness LLM provider and is
gated by the same switch: LEADVAULT_LLM_VALIDATION=1 + ANTHROPIC_API_KEY. When
disabled, `complete()` raises and the caller keeps the deterministic spec, so the
UI's generation_mode stays "deterministic" rather than pretending.
"""

from __future__ import annotations

import asyncio
from typing import Any

from config import settings
from harness import audit
from harness import llm as llm_layer


class AIService:
    def __init__(self) -> None:
        self._provider = llm_layer.build_provider(settings)

    @property
    def enabled(self) -> bool:
        return self._provider.name != "null"

    async def complete(
        self,
        *,
        messages: list[dict[str, Any]],
        model: str | None = None,
        max_tokens: int = 1000,
        temperature: float = 0.0,  # accepted for signature compatibility; provider pins 0
        system: str = "You refine B2B lead-mining query banks. Return strict JSON only.",
    ) -> str:
        if not self.enabled:
            raise RuntimeError("llm_disabled")
        user = "\n\n".join(str(m.get("content", "")) for m in messages if m.get("role") == "user")
        chosen_model = model or settings.LEADVAULT_LLM_MODEL

        def _call() -> tuple[str, int, int]:
            return self._provider.complete(system=system, user=user, model=chosen_model, max_tokens=max_tokens, timeout=30)

        text, tin, tout = await asyncio.to_thread(_call)
        audit.record(who="spec_planner", what="tool.llm_refine_spec", policy="P-TOOL-LLM-01", result="ok",
                     model=chosen_model, tokens_in=tin, tokens_out=tout)
        return text
