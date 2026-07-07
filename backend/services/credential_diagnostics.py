from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any

from config import settings


@dataclass
class ProviderStatus:
    provider: str
    configured: bool
    usable: bool
    detail: str


def _split(value: str) -> list[str]:
    return [item.strip() for item in (value or "").replace("\n", ",").replace(";", ",").split(",") if item.strip()]


def _validate_apify_tokens() -> ProviderStatus:
    tokens = _split(settings.APIFY_API_TOKENS)
    if not tokens:
        return ProviderStatus("apify", False, False, "missing_apify_tokens")
    ok = 0
    for token in tokens:
        try:
            url = "https://api.apify.com/v2/users/me?token=" + urllib.parse.quote(token)
            with urllib.request.urlopen(url, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8", errors="ignore"))
            if payload.get("data", {}).get("id"):
                ok += 1
        except Exception:
            continue
    return ProviderStatus("apify", True, ok > 0, f"{ok}/{len(tokens)} token(s) valid")


def provider_diagnostics() -> dict[str, Any]:
    statuses = [
        _validate_apify_tokens(),
        ProviderStatus("crm_webhook", bool(settings.CRM_WEBHOOK_URL), bool(settings.CRM_WEBHOOK_URL), "webhook configured" if settings.CRM_WEBHOOK_URL else "local_crm_audit_only"),
        ProviderStatus("hubspot", bool(settings.HUBSPOT_ACCESS_TOKEN), bool(settings.HUBSPOT_ACCESS_TOKEN), "token configured" if settings.HUBSPOT_ACCESS_TOKEN else "not_configured"),
        ProviderStatus("enrichment", settings.ENABLE_LIVE_ENRICHMENT, settings.ENABLE_LIVE_ENRICHMENT and any([settings.HUNTER_API_KEY, settings.CLEARBIT_API_KEY, settings.APOLLO_API_KEY]), "live enrichment keys available" if any([settings.HUNTER_API_KEY, settings.CLEARBIT_API_KEY, settings.APOLLO_API_KEY]) else "local_enrichment_only"),
    ]
    return {
        "status": "success",
        "providers": [asdict(item) for item in statuses],
        "can_live_scrape": any(item.provider == "apify" and item.usable for item in statuses),
        "can_live_enrich": any(item.provider == "enrichment" and item.usable for item in statuses),
        "crm_mode": "webhook" if settings.CRM_WEBHOOK_URL else "local_audit",
    }

