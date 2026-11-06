import asyncio
import pytest
from backend.services.token_budget_queue import DistributedLeadQueue, QueuedLeadTask


@pytest.mark.asyncio
async def test_token_budget_tracking_and_blocking():
    queue = DistributedLeadQueue()
    tenant = "tenant_enterprise_test"

    # Set modest budget
    queue.set_budget(tenant, budget_usd=0.01)
    budget = queue.get_budget(tenant)

    # Initial state
    assert budget.current_spend_usd == 0.0
    assert budget.quota_exhausted is False

    # Consume tokens
    budget.record_usage(prompt=10000, completion=4000)
    # cost = (10000/1000 * 0.0005) + (4000/1000 * 0.0015) = 0.005 + 0.006 = 0.011 USD (> 0.01)
    assert budget.current_spend_usd >= 0.01
    assert budget.quota_exhausted is True
    assert queue.check_can_execute(tenant) is False

    # Enqueue a task
    task = QueuedLeadTask(task_id="t1", tenant_id=tenant, payload={"lead": "Acme"})
    queue.enqueue(tenant, task)
    assert queue.dequeue(tenant) == task

    # Batch processing with exhausted budget should be refused
    batch_result = await queue.process_batch(
        tenant_id=tenant,
        items=[{"company": "Blocked Inc"}],
        worker_fn=lambda x: x,
    )
    assert batch_result["success"] is False
    assert "QUOTA_EXHAUSTED" in batch_result["error"]
