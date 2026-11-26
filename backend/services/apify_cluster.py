"""LeadVault AI — Phase 13 Production Apify Token Cluster & Proxy Self-Healing.

Implements LV-P13-003: Multi-token rotation, HTTP 429 rate-limit cooldown,
and graceful sandbox fallback when APIFY_API_TOKENS is unconfigured.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ApifyTokenState:
    token_id: str
    token_secret: str
    requests_served: int = 0
    rate_limit_hits: int = 0
    cooldown_until: float = 0.0

    def is_available(self, now_ts: Optional[float] = None) -> bool:
        ts = now_ts if now_ts is not None else time.time()
        return ts >= self.cooldown_until


class ApifyTokenCluster:
    """Round-robin Apify token pool with automatic 429 cooldown and sandbox fallback."""

    def __init__(
        self,
        tokens: Optional[List[str]] = None,
        cooldown_seconds: float = 60.0,
    ) -> None:
        raw_tokens = tokens if tokens is not None else [
            t.strip() for t in os.getenv("APIFY_API_TOKENS", "").split(",") if t.strip()
        ]
        self._pool: List[ApifyTokenState] = [
            ApifyTokenState(token_id=f"apify_tok_{idx + 1}", token_secret=tok)
            for idx, tok in enumerate(raw_tokens)
        ]
        self._cursor = 0
        self.cooldown_seconds = cooldown_seconds

    @property
    def mode(self) -> str:
        return "paid_cluster" if self._pool else "sandbox_fallback"

    def acquire_token(self, now_ts: Optional[float] = None) -> Optional[ApifyTokenState]:
        """Select the next healthy token using round-robin rotation."""
        if not self._pool:
            return None
        ts = now_ts if now_ts is not None else time.time()
        total = len(self._pool)
        for offset in range(total):
            idx = (self._cursor + offset) % total
            candidate = self._pool[idx]
            if candidate.is_available(ts):
                self._cursor = (idx + 1) % total
                candidate.requests_served += 1
                return candidate
        return None

    def report_rate_limit(self, token_id: str, now_ts: Optional[float] = None) -> None:
        ts = now_ts if now_ts is not None else time.time()
        for entry in self._pool:
            if entry.token_id == token_id:
                entry.rate_limit_hits += 1
                entry.cooldown_until = ts + self.cooldown_seconds
                break

    def execute_with_failover(
        self,
        actor_fn: Callable[[Optional[str]], Dict[str, Any]],
        max_attempts: int = 3,
    ) -> Dict[str, Any]:
        """Run an Apify actor call with automatic token rotation on 429 rate limits."""
        if not self._pool:
            result = actor_fn(None)
            return {**result, "cluster_mode": "sandbox_fallback", "token_id": None}

        last_error: Optional[Exception] = None
        for _ in range(max_attempts):
            tok = self.acquire_token()
            if tok is None:
                break
            try:
                result = actor_fn(tok.token_secret)
                return {**result, "cluster_mode": "paid_cluster", "token_id": tok.token_id}
            except RuntimeError as exc:
                last_error = exc
                if "429" in str(exc):
                    self.report_rate_limit(tok.token_id)
                    continue
                raise

        return {
            "status": "FALLBACK",
            "cluster_mode": "sandbox_fallback",
            "error": str(last_error) if last_error else "all_tokens_cooling_down",
        }

    def get_cluster_health(self, now_ts: Optional[float] = None) -> Dict[str, Any]:
        ts = now_ts if now_ts is not None else time.time()
        available = sum(1 for t in self._pool if t.is_available(ts))
        return {
            "mode": self.mode,
            "total_tokens": len(self._pool),
            "available_tokens": available,
            "cooling_down_tokens": len(self._pool) - available,
            "total_requests_served": sum(t.requests_served for t in self._pool),
            "total_rate_limits": sum(t.rate_limit_hits for t in self._pool),
            "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        }
