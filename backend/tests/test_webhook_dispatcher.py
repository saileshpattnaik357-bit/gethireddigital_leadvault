"""
Unit tests for LeadVault AI Webhook Streaming & CRM Dispatcher.
"""

from __future__ import annotations

import pytest

from services.webhook_dispatcher import WebhookDispatcher


class TestWebhookDispatcher:
    def test_signature_computation(self):
        dispatcher = WebhookDispatcher()
        payload = b'{"test": "data"}'
        secret = "secret_key_123"
        sig1 = dispatcher.compute_signature(payload, secret)
        sig2 = dispatcher.compute_signature(payload, secret)
        assert sig1 == sig2
        assert len(sig1) == 64  # SHA256 hex length

    def test_ssrf_blocks_private_webhook_target(self):
        dispatcher = WebhookDispatcher()
        dispatcher.register_webhook(
            tenant_id="tenant_wh_test",
            target_url="http://127.0.0.1:8000/internal-crm",
            secret_key="key",
            trigger_events=["lead.approved"],
        )

        results = dispatcher.dispatch(
            tenant_id="tenant_wh_test",
            event="lead.approved",
            lead_data={"company": "Acme", "intent_score": 90},
        )
        assert len(results) == 1
        assert results[0].success is False
        assert results[0].status_code == 403
        assert "SSRF" in (results[0].error or "")
