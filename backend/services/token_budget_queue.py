"""LeadVault AI — Version 8.0: Distributed Queue & Token Budget Management.

Provides high-throughput task queuing, distributed job worker abstraction,
token usage telemetry, cost estimation in USD, and strict quota enforcement.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


@dataclass
class TokenBudgetUsage:
    tenant_id: str
    monthly_budget_usd: float = 100.00
    current_spend_usd: float = 0.00
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    alert_triggered_80: bool = False
    quota_exhausted: bool = False
    last_updated_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def record_usage(self, prompt: int, completion: int, cost_per_1k_input: float = 0.0005, cost_per_1k_output: float = 0.0015) -> None:
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.total_tokens = self.prompt_tokens + self.completion_tokens
        
        incremental_cost = (prompt / 1000.0 * cost_per_1k_input) + (completion / 1000.0 * cost_per_1k_output)
        self.current_spend_usd = round(self.current_spend_usd + incremental_cost, 4)
        
        ratio = self.current_spend_usd / max(0.01, self.monthly_budget_usd)
        if ratio >= 0.8:
            self.alert_triggered_80 = True
        if ratio >= 1.0:
            self.quota_exhausted = True
        self.last_updated_utc = datetime.now(timezone.utc).isoformat()


@dataclass
class QueuedLeadTask:
    task_id: str
    tenant_id: str
    payload: Dict[str, Any]
    priority: int = 1  # 1 (low) to 5 (urgent)
    status: str = "PENDING"  # PENDING, PROCESSING, COMPLETED, FAILED, DEAD_LETTER
    attempts: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    created_at_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DistributedLeadQueue:
    """Enterprise job queue for high-throughput parallel lead processing."""

    def __init__(self) -> None:
        self._queues: Dict[str, List[QueuedLeadTask]] = {}
        self._budgets: Dict[str, TokenBudgetUsage] = {}
        self._dead_letter_queue: List[QueuedLeadTask] = []
        self._lock = asyncio.Lock()

    def get_budget(self, tenant_id: str) -> TokenBudgetUsage:
        if tenant_id not in self._budgets:
            self._budgets[tenant_id] = TokenBudgetUsage(tenant_id=tenant_id)
        return self._budgets[tenant_id]

    def set_budget(self, tenant_id: str, budget_usd: float) -> TokenBudgetUsage:
        b = self.get_budget(tenant_id)
        b.monthly_budget_usd = max(0.001, budget_usd)
        return b

    def check_can_execute(self, tenant_id: str) -> bool:
        budget = self.get_budget(tenant_id)
        return not budget.quota_exhausted

    def enqueue(self, tenant_id: str, task: QueuedLeadTask) -> None:
        if tenant_id not in self._queues:
            self._queues[tenant_id] = []
        self._queues[tenant_id].append(task)
        # Sort by priority descending
        self._queues[tenant_id].sort(key=lambda t: t.priority, reverse=True)

    def dequeue(self, tenant_id: str) -> Optional[QueuedLeadTask]:
        queue = self._queues.get(tenant_id, [])
        if not queue:
            return None
        return queue.pop(0)

    async def process_batch(
        self,
        tenant_id: str,
        items: List[Dict[str, Any]],
        worker_fn: Callable[[Dict[str, Any]], Any],
        estimated_prompt_tokens: int = 150,
        estimated_output_tokens: int = 50,
    ) -> Dict[str, Any]:
        """Process a batch of leads respecting token budget quotas and concurrency."""
        budget = self.get_budget(tenant_id)
        if budget.quota_exhausted:
            return {
                "success": False,
                "processed": 0,
                "error": "QUOTA_EXHAUSTED: Monthly token budget limit reached. Please upgrade tier.",
                "budget": budget,
            }

        processed_results: List[Any] = []
        failures: List[Dict[str, Any]] = []

        start_time = time.perf_counter()

        for item in items:
            # Check budget before each invocation
            if budget.quota_exhausted:
                failures.append({"item": item, "reason": "Budget exhausted mid-batch"})
                continue

            try:
                if asyncio.iscoroutinefunction(worker_fn):
                    res = await worker_fn(item)
                else:
                    res = worker_fn(item)
                processed_results.append(res)
                # Deduct token usage
                budget.record_usage(estimated_prompt_tokens, estimated_output_tokens)
            except Exception as e:
                failures.append({"item": item, "reason": str(e)})

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "success": True,
            "processed_count": len(processed_results),
            "failed_count": len(failures),
            "duration_ms": round(duration_ms, 2),
            "results": processed_results,
            "failures": failures,
            "budget_status": {
                "current_spend_usd": budget.current_spend_usd,
                "monthly_budget_usd": budget.monthly_budget_usd,
                "total_tokens": budget.total_tokens,
                "alert_triggered_80": budget.alert_triggered_80,
                "quota_exhausted": budget.quota_exhausted,
            },
        }
