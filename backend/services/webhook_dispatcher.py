"""
LeadVault AI: Webhook Streaming & CRM Dispatcher (V10 / V11)

Implements:
1. Real-time webhook delivery for verified SQL / MQL leads.
2. HMAC-SHA256 cryptographic payload signing for authenticity verification.
3. SSRF-safe URL validation via ToolGateway.
4. Retry logic with exponential backoff.
5. Delivery audit logging with execution timestamps and HTTP response codes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import hmac
import json
import time
from typing import Any
import urllib.error
import urllib.request

from harness import audit
from harness.tools import gateway


@dataclass
class WebhookConfig:
    tenant_id: str
    target_url: str
    secret_key: str
    enabled: bool = True
    trigger_events: list[str] = field(default_factory=lambda: ["lead.approved", "lead.sql_detected"])


@dataclass
class WebhookDeliveryResult:
    delivery_id: str
    tenant_id: str
    target_url: str
    event: str
    status_code: int
    success: bool
    attempt_count: int
    error: str | None = None
    delivered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class WebhookDispatcher:
    """
    Dispatches cryptographic HMAC-signed webhooks to client CRM endpoints.
    """

    def __init__(self):
        self.configs: dict[str, list[WebhookConfig]] = {}

    def register_webhook(
        self,
        tenant_id: str,
        target_url: str,
        secret_key: str,
        trigger_events: list[str] | None = None,
    ) -> WebhookConfig:
        cfg = WebhookConfig(
            tenant_id=tenant_id,
            target_url=target_url,
            secret_key=secret_key,
            enabled=True,
            trigger_events=trigger_events or ["lead.approved", "lead.sql_detected"],
        )
        self.configs.setdefault(tenant_id, []).append(cfg)
        audit.record(
            who="WebhookDispatcher",
            what="webhook.register",
            tenant=tenant_id,
            workflow=None,
            policy="POL-CRM-01",
            evidence={"target_url": target_url, "events": cfg.trigger_events},
        )
        return cfg

    def compute_signature(self, payload_bytes: bytes, secret: str) -> str:
        """Compute HMAC-SHA256 signature for payload verification."""
        return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

    def dispatch(
        self,
        tenant_id: str,
        event: str,
        lead_data: dict[str, Any],
        *,
        max_retries: int = 3,
    ) -> list[WebhookDeliveryResult]:
        tenant_configs = [c for c in self.configs.get(tenant_id, []) if c.enabled and event in c.trigger_events]
        results: list[WebhookDeliveryResult] = []

        for cfg in tenant_configs:
            delivery_id = f"wh_{int(datetime.now(timezone.utc).timestamp())}_{tenant_id}"
            payload = {
                "event": event,
                "tenant_id": tenant_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": lead_data,
            }
            body = json.dumps(payload, indent=2).encode("utf-8")
            sig = self.compute_signature(body, cfg.secret_key)

            # SSRF pre-check
            if not gateway.is_url_allowed(cfg.target_url):
                res = WebhookDeliveryResult(
                    delivery_id=delivery_id,
                    tenant_id=tenant_id,
                    target_url=cfg.target_url,
                    event=event,
                    status_code=403,
                    success=False,
                    attempt_count=1,
                    error="SSRF guard refused webhook target URL",
                )
                results.append(res)
                continue

            # Attempt delivery with exponential backoff
            attempt = 0
            delivered = False
            last_status = 0
            err_msg = None

            while attempt < max_retries and not delivered:
                attempt += 1
                req = urllib.request.Request(
                    cfg.target_url,
                    data=body,
                    headers={
                        "Content-Type": "application/json",
                        "X-LeadVault-Signature": sig,
                        "X-LeadVault-Event": event,
                        "User-Agent": "LeadVault-Webhook-Dispatcher/2.0",
                    },
                    method="POST",
                )
                try:
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        last_status = resp.status
                        if 200 <= last_status < 300:
                            delivered = True
                except urllib.error.HTTPError as he:
                    last_status = he.code
                    err_msg = str(he)
                    if last_status < 500:
                        break  # Do not retry 4xx errors
                except Exception as ex:
                    last_status = 599
                    err_msg = str(ex)

                if not delivered and attempt < max_retries:
                    time.sleep(0.1 * (2 ** (attempt - 1)))

            delivery_res = WebhookDeliveryResult(
                delivery_id=delivery_id,
                tenant_id=tenant_id,
                target_url=cfg.target_url,
                event=event,
                status_code=last_status,
                success=delivered,
                attempt_count=attempt,
                error=err_msg if not delivered else None,
            )
            results.append(delivery_res)

            audit.record(
                who="WebhookDispatcher",
                what="webhook.dispatch",
                tenant=tenant_id,
                workflow=None,
                policy="POL-CRM-01",
                evidence={
                    "event": event,
                    "target_url": cfg.target_url,
                    "status_code": last_status,
                    "success": delivered,
                    "attempts": attempt,
                },
            )

        return results


webhook_dispatcher = WebhookDispatcher()
