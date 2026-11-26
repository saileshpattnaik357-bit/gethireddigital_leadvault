from unittest.mock import patch

from backend.services.apify_cluster import ApifyTokenCluster
from backend.tasks.celery_app import celery_app
from backend.tasks.mining_tasks import (
    _budget_guard,
    dispatch_mining_job,
    scheduled_icp_mining_heartbeat,
)


def test_celery_beat_schedule_configured():
    schedule = celery_app.conf.beat_schedule
    assert "scheduled-icp-mining-heartbeat" in schedule
    assert schedule["scheduled-icp-mining-heartbeat"]["task"] == "leadvault.tasks.scheduled_icp_mining_heartbeat"


def test_dispatch_mining_job_eager_execution_and_quota_guard():
    res = dispatch_mining_job("tenant_p13_ok", {"lead_objective": "rfp_mining"}, priority=5)
    assert res["queue"] == "p0_tier_a"
    assert res["result"]["status"] == "COMPLETED"

    budget = _budget_guard.get_budget("tenant_p13_exhausted")
    budget.quota_exhausted = True
    blocked = dispatch_mining_job("tenant_p13_exhausted", {"lead_objective": "rfp_mining"}, priority=1)
    assert blocked["queue"] == "p1_mining"
    assert blocked["result"]["status"] == "BLOCKED"
    assert blocked["result"]["reason"] == "quota_exhausted"


def test_scheduled_icp_mining_heartbeat_dispatches_active_tenants():
    fake_tenants = [
        {"tenant_id": "t_active", "has_spec": True, "latest_spec": {"lead_objective": "saas"}},
        {"tenant_id": "t_inactive", "has_spec": False, "latest_spec": None},
    ]
    with patch("backend.tasks.mining_tasks.storage_engine.list_tenants", return_value=fake_tenants):
        summary = scheduled_icp_mining_heartbeat()
    assert summary["status"] == "HEARTBEAT_OK"
    assert summary["dispatched_count"] == 1
    assert summary["tenant_ids"] == ["t_active"]


def test_apify_token_cluster_rotation_429_failover_and_fallback():
    sandbox = ApifyTokenCluster(tokens=[])
    assert sandbox.mode == "sandbox_fallback"
    sb_res = sandbox.execute_with_failover(lambda tok: {"items": 3, "used_token": tok})
    assert sb_res["cluster_mode"] == "sandbox_fallback"
    assert sb_res["used_token"] is None

    cluster = ApifyTokenCluster(tokens=["tok_a", "tok_b"], cooldown_seconds=120.0)
    assert cluster.mode == "paid_cluster"

    def flaky_actor(tok: str):
        if tok == "tok_a":
            raise RuntimeError("HTTP 429 Too Many Requests")
        return {"items": 25, "used_token": tok}

    res = cluster.execute_with_failover(flaky_actor, max_attempts=3)
    assert res["cluster_mode"] == "paid_cluster"
    assert res["used_token"] == "tok_b"

    health = cluster.get_cluster_health()
    assert health["total_tokens"] == 2
    assert health["available_tokens"] == 1
    assert health["cooling_down_tokens"] == 1
    assert health["total_rate_limits"] == 1
