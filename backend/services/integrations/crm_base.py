"""LeadVault AI — Phase 14 Shared CRM OAuth2, Governance & Bidirectional Feedback Base.

Implements shared OAuth2 token vaulting, Policy P-ACCEPT-02 enforcement before
outbound CRM sync, and closed-won/closed-lost feedback ingestion into Hermes Memory.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.services.hermes_memory import HermesMemoryEngine
from backend.services.storage_engine import storage_engine


@dataclass
class OAuthTokenRecord:
    provider: str
    tenant_id: str
    access_token: str
    refresh_token: str = ""
    expires_at: float = 0.0
    instance_url: str = ""

    def is_expired(self, now_ts: Optional[float] = None) -> bool:
        if self.expires_at <= 0:
            return False
        ts = now_ts if now_ts is not None else time.time()
        return ts >= (self.expires_at - 30.0)


@dataclass
class CRMSyncResult:
    provider: str
    tenant_id: str
    lead_id: str
    status: str  # SYNCED, DENIED_POLICY, FAILED
    remote_record_id: Optional[str] = None
    mapped_payload: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    synced_at_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BaseCRMConnector:
    """Shared base class for HubSpot and Salesforce bidirectional CRM connectors."""

    provider_name: str = "crm"

    def __init__(self, hermes_engine: Optional[HermesMemoryEngine] = None) -> None:
        self._tokens: Dict[str, OAuthTokenRecord] = {}
        self.hermes = hermes_engine or HermesMemoryEngine()

    def store_token(self, record: OAuthTokenRecord) -> None:
        self._tokens[record.tenant_id] = record

    def get_token(self, tenant_id: str) -> Optional[OAuthTokenRecord]:
        return self._tokens.get(tenant_id)

    def refresh_access_token(self, token_record: OAuthTokenRecord) -> OAuthTokenRecord:
        """Override in subclass to call provider OAuth2 refresh endpoint."""
        raise NotImplementedError

    def ensure_valid_token(self, tenant_id: str) -> Optional[OAuthTokenRecord]:
        rec = self._tokens.get(tenant_id)
        if rec and rec.is_expired() and rec.refresh_token:
            rec = self.refresh_access_token(rec)
            self._tokens[tenant_id] = rec
        return rec

    def check_policy_p_accept_02(self, lead_dossier: Dict[str, Any], lead_status: str) -> bool:
        """Policy P-ACCEPT-02: Tier-A leads require explicit approval before export/CRM sync."""
        tier = str(lead_dossier.get("lead_tier", lead_dossier.get("Priority", "B"))).upper()
        if tier == "A" and lead_status.upper() not in {"ACCEPTED", "APPROVED"}:
            return False
        return True

    def ingest_deal_stage_feedback(
        self,
        *,
        tenant_id: str,
        lead_id: str,
        company_name: str,
        crm_stage: str,
        deal_value_usd: float = 0.0,
        matched_rules: Optional[List[str]] = None,
        notes: str = "",
    ) -> Dict[str, Any]:
        """Convert CRM deal stage updates into Hermes episodic conversion feedback."""
        stage_norm = crm_stage.strip().lower().replace("_", "").replace(" ", "")
        if "won" in stage_norm:
            hermes_outcome = "closed_won"
            db_outcome = "CLOSED_WON"
        elif "lost" in stage_norm:
            hermes_outcome = "closed_lost"
            db_outcome = "CLOSED_LOST"
        else:
            hermes_outcome = "meeting_booked"
            db_outcome = "PIPELINE_ACTIVE"

        rules = matched_rules or ["CRM_STAGE_SYNC"]
        self.hermes.record_conversion_outcome(
            tenant_id=tenant_id,
            lead_id=lead_id,
            company_name=company_name,
            outcome=hermes_outcome,
            deal_value=int(deal_value_usd) if deal_value_usd else None,
            feedback=notes or f"{self.provider_name} stage synced: {crm_stage}",
            matched_rules=rules,
        )

        conversion_id = f"conv_{self.provider_name}_{uuid.uuid4().hex[:10]}"
        storage_engine.insert_conversion(
            tenant_id=tenant_id,
            conversion_id=conversion_id,
            lead_id=lead_id,
            company_name=company_name,
            outcome=db_outcome,
            deal_value_usd=float(deal_value_usd),
            feedback=notes or f"{self.provider_name} stage: {crm_stage}",
            matched_rules=rules,
        )
        storage_engine.log_audit(
            tenant_id=tenant_id,
            agent_id="MESH_007",
            action=f"{self.provider_name.upper()}_FEEDBACK_INGESTED",
            status="SUCCESS",
            details={"lead_id": lead_id, "crm_stage": crm_stage, "hermes_outcome": hermes_outcome},
        )
        return {
            "conversion_id": conversion_id,
            "hermes_outcome": hermes_outcome,
            "db_outcome": db_outcome,
        }
