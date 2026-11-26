import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from backend.services.hermes_memory import HermesMemoryEngine
from backend.services.integrations.crm_base import OAuthTokenRecord
from backend.services.integrations.hubspot_client import HubSpotConnector
from backend.services.integrations.salesforce_client import SalesforceConnector


def test_hubspot_policy_p_accept_02_and_sync():
    with tempfile.TemporaryDirectory() as tmpdir:
        hermes = HermesMemoryEngine(storage_path=Path(tmpdir) / "hermes.json")
        hs = HubSpotConnector(client_id="cid", client_secret="csec", hermes_engine=hermes)

        dossier = {
            "Company Name": "Acme Cloud",
            "Company Website": "https://acmecloud.io",
            "Client Name": "Elena Vance",
            "Contact Email": "elena@acmecloud.io",
            "lead_tier": "A",
            "match_score": 94,
            "revenue_deal_value": "$180,000",
            "Client Intent Signal": "Active RFP for multi-agent procurement analytics.",
        }

        denied = hs.sync_lead("tenant_crm", "lead_hs_1", dossier, lead_status="PENDING_REVIEW")
        assert denied.status == "DENIED_POLICY"

        synced = hs.sync_lead("tenant_crm", "lead_hs_1", dossier, lead_status="ACCEPTED")
        assert synced.status == "SYNCED"
        assert synced.mapped_payload["contact"]["properties"]["leadvault_tier"] == "A"
        assert synced.mapped_payload["deal"]["properties"]["amount"] == "180000"


def test_hubspot_oauth_token_refresh_when_expired():
    hs = HubSpotConnector(client_id="cid", client_secret="csec")
    hs.store_token(
        OAuthTokenRecord(
            provider="hubspot",
            tenant_id="t_oauth",
            access_token="old_tok",
            refresh_token="ref_tok",
            expires_at=time.time() - 60,
        )
    )
    mock_resp = MagicMock()
    mock_resp.__enter__.return_value.read.return_value = b'{"access_token": "new_tok", "expires_in": 1800}'
    with patch("urllib.request.urlopen", return_value=mock_resp):
        valid = hs.ensure_valid_token("t_oauth")
    assert valid is not None
    assert valid.access_token == "new_tok"


def test_salesforce_bulk_sync_and_hermes_feedback_ingestion():
    with tempfile.TemporaryDirectory() as tmpdir:
        hermes = HermesMemoryEngine(storage_path=Path(tmpdir) / "hermes.json")
        sf = SalesforceConnector(hermes_engine=hermes)

        leads = [
            {"lead_id": "sf_1", "Company Name": "Beta Systems", "lead_tier": "A", "match_score": 91},
            {"lead_id": "sf_2", "Company Name": "Gamma Labs", "lead_tier": "B", "match_score": 78},
        ]
        results = sf.bulk_sync_leads("tenant_sf", leads, lead_status="ACCEPTED")
        assert len(results) == 2
        assert all(r.status == "SYNCED" for r in results)
        assert results[0].mapped_payload["Rating"] == "Hot"
        assert results[1].mapped_payload["Rating"] == "Warm"

        fb = sf.ingest_deal_stage_feedback(
            tenant_id="tenant_sf",
            lead_id="sf_1",
            company_name="Beta Systems",
            crm_stage="Closed Won",
            deal_value_usd=150000.0,
            matched_rules=["RULE_RFP_ACTIVE"],
        )
        assert fb["hermes_outcome"] == "closed_won"
        assert fb["db_outcome"] == "CLOSED_WON"
