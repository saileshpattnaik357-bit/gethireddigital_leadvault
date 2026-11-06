from backend.services.closed_loop_os import ClosedLoopOperatingSystem


def test_closed_loop_failover_and_sanity():
    os_engine = ClosedLoopOperatingSystem()

    # 1. Golden corpus sanity test
    check = os_engine.run_golden_corpus_sanity()
    assert check.healthy is True
    assert check.precision >= 0.90
    assert check.anti_hallucination_guaranteed is True

    # 2. Model failover cascade
    assert os_engine.get_active_model() == "claude-3-5-sonnet"

    # Simulate 3 failures on primary
    os_engine.record_model_failure("claude-3-5-sonnet", "504 Gateway Timeout")
    os_engine.record_model_failure("claude-3-5-sonnet", "504 Gateway Timeout")
    msg = os_engine.record_model_failure("claude-3-5-sonnet", "504 Gateway Timeout")

    assert "Failover triggered" in msg
    # Secondary model is now active
    assert os_engine.get_active_model() == "gpt-4o"

    # Restore primary
    os_engine.restore_model_health("claude-3-5-sonnet")
    assert os_engine.get_active_model() == "claude-3-5-sonnet"

    # 3. CRM stage movement feedback loop
    crm_res = os_engine.ingest_crm_stage_movement(
        tenant_id="tenant-acme",
        lead_id="lead-777",
        company_name="Snowflake",
        stage_transition="OPPORTUNITY->CLOSED_WON",
        deal_value_usd=220000.0,
        feedback="Closed due to high-urgency billing migration signals.",
    )
    assert crm_res["status"] == "ACCEPTED"
    assert "intent_threshold" in crm_res["closed_loop_adjustments"]

    # 4. Proxy self-healing
    proxy_res = os_engine.check_and_heal_proxies()
    assert "healthy_pools" in proxy_res
