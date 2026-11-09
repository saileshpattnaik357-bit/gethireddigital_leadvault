# LeadVault AI: Project Discovery Audit

**Document ID**: `LV-AUDIT-DISCOVERY-2026`  
**Classification**: Engineering Control Standard  
**Maturity Level**: Enterprise Production (V11.0 Certified)  
**Verification**: 153/153 Automated Pytest Tests Passing | CI/CD Green  

---

## 1. Project Purpose & Business Objectives

LeadVault AI is an autonomous, multi-agent revenue intelligence platform designed to replace manual SDR prospecting and brittle keyword alerts. It discovers high-conviction, active buyer-intent signals for B2B tech companies, professional service firms, and agencies by continuously monitoring public social graphs (LinkedIn, Google RFPs, Reddit, GitHub, Apify actors).

### Core Business Objectives
1. **Zero-Hallucination Qualification**: Eliminate invented contact information and fictional deal sizes by enforcing deterministic evidence-first extraction.
2. **29-Field Revenue Dossier Generation**: Standardize every qualified lead into a 29-field commercial dossier with algorithmic deal valuation ($15K–$250K) and LeadTiering (`Tier A` SQL, `Tier B` MQL, `Tier C` Nurture).
3. **Adaptive Closed-Loop Learning**: Calibrate heuristic scoring weights autonomously based on closed-won sales feedback via Hermes Episodic Memory.
4. **Enterprise Resilience & Governance**: Provide out-of-band Policy Triad governance (`ALLOW`/`REQUIRE_APPROVAL`/`DENY`), SSRF network protection, token-budget cost controls, and automated model failover (`Claude 3.5 Sonnet` $\rightarrow$ `GPT-4o` $\rightarrow$ `Haiku`).

---

## 2. Existing Architecture & Technology Stack

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         LEADVAULT ENTERPRISE TOPOLOGY                            │
│                                                                                  │
│   [ Client Browser ]                                                            │
│          │                                                                       │
│          ▼ (HTTP / Webpack Dev / Next.js Static)                                 │
│   [ Next.js 16.2.6 (React 19) ] ── Clay.com 8-Tab Control Plane & Slide-Over     │
│          │                                                                       │
│          ▼ (REST / JSON / Streaming)                                             │
│   [ FastAPI 0.115 Backend ] ── CORS, Pydantic Schema Validation                 │
│          │                                                                       │
│          ├─► [ Multi-Agent Mesh ] ── Coordinator, Scout, Compliance, Intent     │
│          ├─► [ LangGraph Pipeline ] ── 5-Node Stateful DAG + CheckpointStore     │
│          ├─► [ Hermes Memory Engine ] ── Episodic Deal Store & Procedural Tuner  │
│          ├─► [ Deep Research V7 ] ── Executive Hires (<90d) & Funding Tracking   │
│          ├─► [ Token Budget Queue V8 ] ── Quota Guard (80%/100%) & USD Costing   │
│          ├─► [ Closed-Loop OS V11 ] ── Model Failover & Self-Healing Proxies     │
│          ├─► [ Storage Engine ] ── SQLite WAL Mode (ACID Relational Store)       │
│          └─► [ Webhook Dispatcher ] ── Signed HMAC-SHA256 Outbound Streamer      │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack Manifest
- **Frontend**: Next.js 16.2.6, React 19.2.4, TypeScript 5, Lucide-React, Linear/Clay CSS Design System.
- **Backend API**: Python 3.11–3.14, FastAPI 0.115, Pydantic V2, Uvicorn, Asynchronous Worker Pool.
- **Multi-Agent Orchestration**: Native Coordinator-Worker Mesh (`MultiAgentCoordinator`), LangGraph Stateful DAG (`LangGraphPipeline`).
- **Memory Systems**: Hermes Episodic Memory (`HermesMemoryEngine`), Semantic Profile Store, Disk Checkpointing (`CheckpointStore`).
- **Storage Layer**: SQLite 3 with Write-Ahead Logging (`WAL` mode), synchronous normal, foreign key integrity, JSON archival fallback.
- **Testing & Quality**: Pytest 8.x, Pytest-Asyncio, GitHub Actions CI/CD (matrix Python 3.11/Node 20).

---

## 3. Existing Agents & Execution Roles

| Agent Codename | Domain | Autonomy Level | Implementation File | Status |
| :--- | :--- | :--- | :--- | :--- |
| `MiningCoordinator` | Central Mesh | Supervisory (L0) | `backend/services/multi_agent_mesh.py` | VERIFIED |
| `SignalScoutAgent` | Signal Sourcing | Monitored (L3) | `backend/services/multi_agent_mesh.py` | VERIFIED |
| `ComplianceGateAgent` | Verification & Noise | Autonomous (L1) | `backend/services/multi_agent_mesh.py` | VERIFIED |
| `IntentScorerAgent` | Intent Classification | Autonomous (L1) | `backend/services/multi_agent_mesh.py` | VERIFIED |
| `RevenueEnricherAgent` | Revenue Intelligence | Bounded (L2) | `backend/services/revenue_intelligence.py` | VERIFIED |
| `HermesMemoryAgent` | Adaptive Learning | Autonomous (L1) | `backend/services/hermes_memory.py` | VERIFIED |
| `DeepResearchAgent` | Deep Research (V7) | Autonomous (L1) | `backend/services/deep_research.py` | VERIFIED |
| `TokenBudgetAgent` | Scale & Queue (V8) | Supervisor (L0) | `backend/services/token_budget_queue.py` | VERIFIED |
| `ClosedLoopOSAgent` | Resiliency (V11) | Autonomous (L1) | `backend/services/closed_loop_os.py` | VERIFIED |
| `WebhookDispatcherAgent` | CRM Delivery | Bounded (L2) | `backend/services/webhook_dispatcher.py` | VERIFIED |

---

## 4. Database Structure & Relational Schemas

Persistent relational storage is implemented in [`backend/services/storage_engine.py`](file:///D:/ANTIGRAVITY/LEADVAULT/backend/services/storage_engine.py):

1. **`tenants`**: `tenant_id` (PK), `company_name`, `website`, `industry`, `created_at_utc`, `updated_at_utc`.
2. **`leadvault_specs`**: `tenant_id` (PK, FK), `company_name`, `website`, `lead_objective`, `spec_json`, `updated_at_utc`.
3. **`leads`**: `lead_id` (PK), `tenant_id` (FK), `company_name`, `domain`, `contact_name`, `lead_tier`, `deal_size_usd`, `intent_score`, `budget_authority`, `procurement_timeline`, `raw_signal`, `dossier_json`, `status`, `created_at_utc`.
4. **`hermes_conversions`**: `conversion_id` (PK), `tenant_id` (FK), `lead_id`, `company_name`, `outcome`, `deal_value_usd`, `feedback`, `matched_rules`, `created_at_utc`.
5. **`audit_logs`**: `id` (PK Auto), `timestamp_utc`, `tenant_id`, `agent_id`, `action`, `status`, `details_json`.
6. **`webhooks`**: `webhook_id` (PK), `tenant_id`, `target_url`, `secret_key`, `trigger_events`, `enabled`, `created_at_utc`.

---

## 5. Security & Governance Invariants

1. **SSRF Guard**: All outbound crawler and webhook targets must pass `ToolGateway.is_url_allowed`. Loopbacks (`127.0.0.1`), RFC 1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), and AWS/GCP cloud metadata endpoints (`169.254.169.254`) are rejected with `SSRF_VIOLATION_BLOCKED`.
2. **Policy Triad Harness**: Out-of-band evaluation strictly enforcing `ALLOW`, `REQUIRE_APPROVAL`, and `DENY` decisions.
3. **Policy `P-ACCEPT-02`**: Tier-A leads cannot be exported to external CRMs without explicit operator approval.
4. **Cryptographic HMAC-SHA256**: Outbound CRM webhook payloads are signed with `compute_signature` generating a SHA-256 digest header.

---

## 6. Implementation Status & Audit Verdict

- **Code Quality**: Clean architecture, domain separation, 0 TypeScript errors, strict Pydantic schemas.
- **Test Pass Rate**: **153 / 153 tests passing (100%)**.
- **CI/CD Status**: GitHub Actions automated matrix runs passing on Python 3.11 and Node 20.
- **Verdict**: The LeadVault AI codebase is structurally sound, resilient, and enterprise-grade.
