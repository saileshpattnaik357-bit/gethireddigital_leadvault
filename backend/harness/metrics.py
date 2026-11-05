"""
Per-run observability.

Collects, for each workflow id: wall-clock latency, tool calls (count / errors /
seconds / items), candidates reviewed, accepted, rejected, parked for approval,
LLM calls and estimated cost. Written into the workflow record at completion and
readable via the /harness/metrics endpoint.

Cost model is deliberately simple and labelled as an estimate:
    apify actor run  ~ $0.01 per query attempt (varies by actor; see Apify billing)
    llm validation   ~ $0.001 per call (Haiku-class, short prompt)
Set the real figures in `COST_ESTIMATES` once billing data exists.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any

COST_ESTIMATES_USD = {
    "apify_linkedin_search": 0.01,
    "llm_validate": 0.001,
    "duckduckgo_search": 0.0,
    "fetch_public_page": 0.0,
}


@dataclass
class RunMetrics:
    workflow_id: str
    started_at: float = field(default_factory=time.perf_counter)
    finished_at: float | None = None
    tool_calls: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    tool_errors: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    tool_seconds: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tool_items: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    candidates_reviewed: int = 0
    accepted: int = 0
    rejected: int = 0
    pending_approval: int = 0
    llm_calls: int = 0
    llm_tokens_in: int = 0
    llm_tokens_out: int = 0

    def finish(self) -> None:
        self.finished_at = time.perf_counter()

    @property
    def latency_seconds(self) -> float:
        end = self.finished_at or time.perf_counter()
        return round(end - self.started_at, 3)

    @property
    def estimated_cost_usd(self) -> float:
        total = 0.0
        for tool, count in self.tool_calls.items():
            total += COST_ESTIMATES_USD.get(tool, 0.0) * count
        return round(total, 4)

    def as_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "tool_calls": dict(self.tool_calls),
            "tool_errors": dict(self.tool_errors),
            "tool_seconds": {k: round(v, 3) for k, v in self.tool_seconds.items()},
            "tool_items": dict(self.tool_items),
            "candidates_reviewed": self.candidates_reviewed,
            "accepted": self.accepted,
            "rejected": self.rejected,
            "pending_approval": self.pending_approval,
            "llm_calls": self.llm_calls,
            "llm_tokens_in": self.llm_tokens_in,
            "llm_tokens_out": self.llm_tokens_out,
            "latency_seconds": self.latency_seconds,
            "estimated_cost_usd": self.estimated_cost_usd,
            "accept_rate": round(self.accepted / self.candidates_reviewed, 4) if self.candidates_reviewed else 0.0,
            "tool_error_rate": round(
                sum(self.tool_errors.values()) / max(1, sum(self.tool_calls.values())), 4
            ),
        }


class MetricsCollector:
    def __init__(self) -> None:
        self._runs: dict[str, RunMetrics] = {}
        self._lock = threading.Lock()

    def start(self, workflow_id: str) -> RunMetrics:
        with self._lock:
            run = RunMetrics(workflow_id=workflow_id)
            self._runs[workflow_id] = run
            return run

    def get(self, workflow_id: str | None) -> RunMetrics | None:
        if not workflow_id:
            return None
        return self._runs.get(workflow_id)

    def tool_call(self, workflow_id: str | None, tool_id: str, *, ok: bool, seconds: float, items: int = 0) -> None:
        run = self.get(workflow_id)
        if run is None:
            return
        with self._lock:
            run.tool_calls[tool_id] += 1
            run.tool_seconds[tool_id] += seconds
            run.tool_items[tool_id] += items
            if not ok:
                run.tool_errors[tool_id] += 1

    def llm_call(self, workflow_id: str | None, *, tokens_in: int = 0, tokens_out: int = 0) -> None:
        run = self.get(workflow_id)
        if run is None:
            return
        with self._lock:
            run.llm_calls += 1
            run.llm_tokens_in += tokens_in
            run.llm_tokens_out += tokens_out
            run.tool_calls["llm_validate"] += 1

    def finish(self, workflow_id: str) -> dict[str, Any] | None:
        run = self.get(workflow_id)
        if run is None:
            return None
        run.finish()
        return run.as_dict()

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._lock:
            runs = list(self._runs.values())[-limit:]
        return [run.as_dict() for run in reversed(runs)]


metrics = MetricsCollector()
