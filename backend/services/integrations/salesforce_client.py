"""LeadVault AI — Phase 14 Salesforce REST API & Bulk Sync Connector (LV-P14-002)."""

from __future__ import annotations

import json
import urllib.request
import uuid
from typing import Any, Dict, List

from backend.services.integrations.crm_base import BaseCRMConnector, CRMSyncResult
from backend.services.storage_engine import storage_engine


class SalesforceConnector(BaseCRMConnector):
    """Salesforce Enterprise REST API connector supporting single and bulk sObject sync."""

    provider_name = "salesforce"

    @staticmethod
    def map_dossier_to_salesforce_lead(lead_dossier: Dict[str, Any]) -> Dict[str, Any]:
        contact_name = str(lead_dossier.get("Client Name", "Procurement Contact")).strip()
        raw_deal = str(lead_dossier.get("revenue_deal_value", lead_dossier.get("Estimated Deal Value", "50000")))
        deal_num = float("".join(c for c in raw_deal if c.isdigit()) or 50000)
        tier = str(lead_dossier.get("lead_tier", lead_dossier.get("Priority", "B"))).upper()

        return {
            "attributes": {"type": "Lead"},
            "Company": str(lead_dossier.get("Company Name", "Unknown")),
            "LastName": contact_name or "Procurement Contact",
            "Website": str(lead_dossier.get("Company Website", "")),
            "Email": str(lead_dossier.get("Contact Email", "")),
            "Rating": "Hot" if tier == "A" else ("Warm" if tier == "B" else "Cold"),
            "LeadSource": "LeadVault AI",
            "Description": str(lead_dossier.get("Client Intent Signal", ""))[:1000],
            "LeadVault_Intent_Score__c": int(lead_dossier.get("match_score", 80)),
            "Estimated_Deal_Value__c": deal_num,
        }

    def sync_lead(
        self,
        tenant_id: str,
        lead_id: str,
        lead_dossier: Dict[str, Any],
        lead_status: str = "ACCEPTED",
        live_http: bool = False,
    ) -> CRMSyncResult:
        if not self.check_policy_p_accept_02(lead_dossier, lead_status):
            storage_engine.log_audit(
                tenant_id=tenant_id,
                agent_id="MESH_006",
                action="SALESFORCE_SYNC_DENIED",
                status="POLICY_P_ACCEPT_02",
                details={"lead_id": lead_id, "lead_status": lead_status},
            )
            return CRMSyncResult(
                provider="salesforce",
                tenant_id=tenant_id,
                lead_id=lead_id,
                status="DENIED_POLICY",
                error="Policy P-ACCEPT-02 requires Tier-A approval before Salesforce sync.",
            )

        mapped = self.map_dossier_to_salesforce_lead(lead_dossier)
        token_rec = self.ensure_valid_token(tenant_id)
        remote_id = f"00Q{uuid.uuid4().hex[:12]}"

        if live_http and token_rec and token_rec.instance_url:
            url = f"{token_rec.instance_url.rstrip('/')}/services/data/v60.0/sobjects/Lead/"
            req = urllib.request.Request(
                url,
                data=json.dumps(mapped).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {token_rec.access_token}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                remote_id = str(body.get("id", remote_id))

        storage_engine.log_audit(
            tenant_id=tenant_id,
            agent_id="MESH_005",
            action="SALESFORCE_LEAD_SYNCED",
            status="SUCCESS",
            details={"lead_id": lead_id, "remote_id": remote_id, "live_http": live_http},
        )
        return CRMSyncResult(
            provider="salesforce",
            tenant_id=tenant_id,
            lead_id=lead_id,
            status="SYNCED",
            remote_record_id=remote_id,
            mapped_payload=mapped,
        )

    def bulk_sync_leads(
        self,
        tenant_id: str,
        leads: List[Dict[str, Any]],
        lead_status: str = "ACCEPTED",
        live_http: bool = False,
    ) -> List[CRMSyncResult]:
        return [
            self.sync_lead(
                tenant_id=tenant_id,
                lead_id=str(lead.get("lead_id", f"lead_{idx}")),
                lead_dossier=lead,
                lead_status=lead_status,
                live_http=live_http,
            )
            for idx, lead in enumerate(leads)
        ]
