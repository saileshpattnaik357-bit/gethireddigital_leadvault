# LeadVault AI: Enterprise Agentic Lead Intelligence Platform

[![CI/CD](https://github.com/saileshpattnaik357/LEADVAULT_AGENT_TEST_REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/saileshpattnaik357/LEADVAULT_AGENT_TEST_REPO/actions)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Next.js 16](https://img.shields.io/badge/Next.js-16.2.6-black.svg)](https://nextjs.org/)
[![Tests](https://img.shields.io/badge/Tests-147%20Passing-success.svg)](#test-suite-verification)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](#license)

**LeadVault AI** is an autonomous, multi-agent procurement intelligence platform engineered to mine high-intent B2B buyer leads, extract commercial deal sizing ($15K–$250K), calibrate heuristic scoring through sales outcome memory, and stream verified SQLs directly into client CRMs.

Built to the **SEORocket V1–V11 Enterprise Engineering Standard**, LeadVault combines deterministic policy harnesses, a 5-node stateful LangGraph pipeline, coordinator-worker multi-agent collaboration, and cryptographic webhook delivery.

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              LEADVAULT AI ENTERPRISE MESH                              │
│                                                                                        │
│   [ Client ICP / CSV ] ──▶ [ Mining Brain ] ──▶ [ Multi-Agent Mesh Coordinator ]      │
│                                                            │                           │
│     ┌──────────────────────────────────────────────────────┴──────────────────────┐    │
│     ▼                                                                             ▼    │
│  [ SignalScout ] ──▶ [ ComplianceGate ] ──▶ [ IntentScorer ] ──▶ [ RevenueEnricher ]   │
│   (WebMCP + Apify)    (SSRF & Anti-Noise)   (Procurement Heuristics) (29 Fields & Sizing)│
│                                                            │                           │
│     ┌──────────────────────────────────────────────────────┘                           │
│     ▼                                                                                  │
│  [ Policy Harness Triad ] ──▶ [ LangGraph 5-Node DAG ] ──▶ [ Hermes Episodic Memory ]  │
│  (ALLOW / REVIEW / DENY)       (Checkpoint Store)           (Sales Feedback Tuning)    │
│                                                            │                           │
│                                                            ▼                           │
│                                             [ HMAC-SHA256 CRM Webhooks ]               │
│                                             (HubSpot / Salesforce / n8n)               │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Enterprise Capabilities

### 1. Revenue Intelligence Engine (V9 Domain)
* **29-Field Commercial Dossier**: Extracts company profile, verified budget authority, project timeline, tech stack signals, pain points, and strategic outreach angles.
* **Lead Tier Classification**:
  * **Tier A (Gold)**: Verified budget authority + immediate or 1–3 month timeline + intent score $\ge 80$.
  * **Tier B (Blue)**: Confirmed buying demand with influencer authority or medium timeframe.
  * **Tier C (Slate)**: Exploratory intent or unconfirmed commercial fit.
* **Algorithmic Deal Sizing**: Sized into `$150K–$250K+ Enterprise`, `$50K–$150K Strategic Retainer`, `$40K–$100K Mid-Market`, and `$15K–$40K Boutique Scope`.

### 2. Multi-Agent Mesh Collaboration (V5)
* **Coordinator-Worker Hierarchy**:
  1. `MiningCoordinator`: Supervised task partitioning, worker routing, and handoff tracking.
  2. `SignalScoutAgent`: Social discovery, web scraping, and deduplication.
  3. `ComplianceGateAgent`: Anti-recruitment filtering, noise rejection, and policy enforcement.
  4. `IntentScorerAgent`: Two-tier heuristic procurement classification with confidence calibration.
  5. `RevenueEnricherAgent`: 29-field commercial enrichment, authority extraction, and tier assignment.
* **Handoff Tracing**: Structured audit logs recording step, target agent, action, and JSON payload summary.

### 3. LangGraph Stateful Pipeline & Checkpoint Recovery (V4)
* **Stateful DAG**: 5 sequential processing nodes with deterministic transitions.
* **Durable Checkpoints**: State is automatically persisted to disk (`backend/runtime/checkpoints/`) after each node transition to guarantee crash resilience and workflow resumability.

### 4. Hermes Adaptive Memory & Reflection Engine (V6)
* **Episodic Learning**: Closes the feedback loop between closed deals and buying intent heuristics by capturing `CLOSED_WON` and `CLOSED_LOST` rep feedback.
* **Procedural Reflection**: Computes win rates per heuristic rule, flags underperforming signals, and dynamically tunes scoring weights.

### 5. Webhook Streaming & CRM Integration (V10)
* **HMAC-SHA256 Signing**: Every payload includes an `X-LeadVault-Signature` header for cryptographic payload authenticity.
* **SSRF Protection**: Strict URL gateway rejects loopback (`127.0.0.1`), RFC 1918 subnets, and cloud metadata endpoints (`169.254.169.254`).
* **Resilient Dispatch**: Exponential backoff retries with full delivery audit logging.

### 6. Next.js 16 UI Control Plane
* **4-Tab Enterprise Navigation**:
  * `Lead Mining & ICP Engine`: Client wizard, ICP upload, brain generation, Apify/live-web modes, dual CSV/XLSX exports, and approval queue.
  * `Multi-Agent Mesh & LangGraph`: Interactive signal tester, live handoff trace cards across all 5 agents, and LangGraph DAG execution monitor.
  * `Hermes Adaptive Memory`: Real-time conversion rate gauge, high-yield/underperforming rules list, and sales outcome recording form.
  * `Webhook & CRM Streaming`: CRM webhook endpoint management, SSRF security indicator, and test dispatch runner.
* **29-Field Inspection Drawer**: One-click modal to inspect every commercial attribute of accepted leads.

---

## Test Suite Verification

LeadVault enforces continuous test coverage across unit, integration, and adversarial suites:

```bash
# Backend Test Suite
py -3.14 -m pytest backend/tests -q
# Output: 147 passed in 6.77s (100% passing)

# Frontend TypeScript & Build Check
cd frontend
npm run typecheck  # 0 errors (tsc --noEmit)
npm run build      # Clean production build via Turbopack in 1.5s
```

### Test Coverage Highlights
* [`test_adversarial.py`](backend/tests/test_adversarial.py): Anti-hallucination tests and prompt injection defenses.
* [`test_revenue_intelligence.py`](backend/tests/test_revenue_intelligence.py): 29-field extraction, deal sizing, and tier assignment.
* [`test_hermes_memory.py`](backend/tests/test_hermes_memory.py): Episodic reflection cycles and dynamic weight tuning.
* [`test_multi_agent_mesh.py`](backend/tests/test_multi_agent_mesh.py): 5-agent handoff traces and coordinator supervision.
* [`test_langgraph_pipeline.py`](backend/tests/test_langgraph_pipeline.py): 5-node DAG execution and crash recovery checkpoints.
* [`test_webmcp_bridge.py`](backend/tests/test_webmcp_bridge.py): Token-bucket rate limiter and circuit breakers.
* [`test_webhook_dispatcher.py`](backend/tests/test_webhook_dispatcher.py): SSRF guards, HMAC-SHA256 signatures, and backoff retries.
* [`test_enterprise_routes.py`](backend/tests/test_enterprise_routes.py): REST API contract validation across all endpoints.

---

## REST API Reference

| Endpoint | Method | Description |
|:---|:---:|:---|
| `/api/leadvault/health` | `GET` | Health check endpoint |
| `/api/leadvault/generate-brain` | `POST` | Generate client-specific mining brain from ICP parameters |
| `/api/leadvault/generate-brain-llm` | `POST` | AI-refined mining brain generation |
| `/api/leadvault/upload-icp` | `POST` | Parse and ingest client ICP spreadsheet (.xlsx/.csv) |
| `/api/leadvault/mine` | `POST` | Execute buyer-intent mining run (requires `confirmed=true`) |
| `/api/leadvault/mine-upload` | `POST` | Ingest ICP file and trigger mining run in one step |
| `/api/leadvault/linkedin-capture` | `POST` | Analyze and classify pasted LinkedIn posts or query text |
| `/api/leadvault/intelligence/analyze` | `POST` | Compute 29-field revenue dossier, deal sizing, and LeadTier |
| `/api/leadvault/hermes/conversion` | `POST` | Record closed deal outcome into Hermes episodic memory |
| `/api/leadvault/hermes/reflection` | `GET` | Retrieve latest Hermes reflection report and suggested weights |
| `/api/leadvault/mesh/process` | `POST` | Execute signals across the 5-agent coordinator-worker mesh |
| `/api/leadvault/langgraph/execute` | `POST` | Run 5-node stateful DAG with checkpoint persistence |
| `/api/leadvault/webhooks/register` | `POST` | Register client CRM endpoint with HMAC-SHA256 secret |
| `/api/leadvault/webhooks/dispatch` | `POST` | Dispatch signed lead notification with SSRF validation |
| `/api/leadvault/webhooks` | `GET` | List active webhook subscriptions for tenant |
| `/api/leadvault/export/accepted` | `GET` | Download accepted leads as XLSX |
| `/api/leadvault/export/rejected` | `GET` | Download rejected audit rows as XLSX |

---

## Local Development Quickstart

### Prerequisites
* Python 3.11+ (Python 3.14 fully supported)
* Node.js 20+
* Docker & Docker Compose (optional for containerized deployment)

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env

# Run FastAPI Server
uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to view the LeadVault Control Plane.

### 3. Docker Deployment
```bash
docker-compose up --build -d
```
* Backend API: `http://localhost:8000`
* Frontend UI: `http://localhost:3000`

---

## Production Planning Workbooks

Complete engineering plans, risk registers, and maturity roadmaps are maintained in [`docs/planning/excel/`](docs/planning/excel/):

1. `LEADVAULT_MASTER_TASK_PLAN_V11.xlsx`: 110 domain tasks across V1–V11 maturity milestones.
2. `LEADVAULT_EXECUTION_TRACKER.xlsx`: Live operational execution tracker.
3. `LEADVAULT_MASTER_GANTT_V11_VERSION_MATRIX.xlsx`: Gantt release timeline.
4. `LEADVAULT_ENTERPRISE_AGENT_DOMAIN_MATRIX.xlsx`: 10 agent domains $\times$ 11 versions.
5. `LEADVAULT_DETAILED_ENGINEERING_TASKS.xlsx`: Implementation contracts and acceptance criteria.
6. `LEADVAULT_ENGINEERING_RESPONSIBILITY_MATRIX.xlsx`: Engineering RACI assignments.
7. `LEADVAULT_FEATURE_CATALOG.xlsx`: Specifications for FEAT-001 through FEAT-014.
8. `LEADVAULT_EVALUATION_TEST_MATRIX.xlsx`: Benchmark datasets and regression gates.
9. `LEADVAULT_OBSERVABILITY_OPERATIONS_MATRIX.xlsx`: OpenTelemetry spans, metrics, and audit retention.
10. `LEADVAULT_SECURITY_RISK_GOVERNANCE.xlsx`: Threat models, SSRF mitigations, tenant isolation.
11. `LEADVAULT_RELEASE_DEPENDENCY_TRACKER.xlsx`: Upstream/downstream release blockers.

---

## License

Proprietary and Confidential. All rights reserved by LeadVault AI & Gethired Global.
