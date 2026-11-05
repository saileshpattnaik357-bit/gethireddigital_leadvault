"""
Unit tests for LeadVault AI WebMCP Bridge & Token Bucket Rate Limiting.
"""

from __future__ import annotations

import pytest

from harness.webmcp_bridge import CircuitBreaker, CircuitBreakerOpen, TokenBucket, WebMCPBridge


class TestTokenBucketAndCircuitBreaker:
    def test_token_bucket_rate_limiting(self):
        bucket = TokenBucket(capacity=2.0, refill_rate_per_sec=0.1)
        assert bucket.consume(1.0) is True
        assert bucket.consume(1.0) is True
        # Bucket exhausted
        assert bucket.consume(1.0) is False

    def test_circuit_breaker_trips_on_failures(self):
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout_sec=0.5)
        assert breaker.can_execute() is True

        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == "CLOSED"

        breaker.record_failure()
        assert breaker.state == "OPEN"
        assert breaker.can_execute() is False


class TestWebMCPBridge:
    def test_linkedin_search_and_audit(self):
        bridge = WebMCPBridge()
        result = bridge.search_linkedin_signals("e-commerce agency", tenant_id="tenant_mcp")
        assert result["status"] == "success"
        data = result["data"]
        assert len(data) > 0
        assert "Looking for an agency" in data[0]["text"]

    def test_crunchbase_lookup(self):
        bridge = WebMCPBridge()
        result = bridge.lookup_crunchbase_firmographics("Notion", tenant_id="tenant_mcp")
        assert result["status"] == "success"
        firm = result["data"]
        assert firm["company_name"] == "Notion"
        assert firm["funding_stage"] == "Series A"
        assert firm["total_funding_usd"] > 0
