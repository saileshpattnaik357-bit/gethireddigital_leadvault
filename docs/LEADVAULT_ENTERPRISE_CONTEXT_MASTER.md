# LeadVault AI: Master Enterprise Context & Engineering Programme

**Document ID**: `LV-CTX-MASTER-2026-V11`  
**Classification**: Proprietary & Confidential — LeadVault AI / Gethired Global  
**Maturity Milestone**: Production Enterprise V11.0 (Full V1–V11 Evolution Complete)  
**Target Delivery Remote**: [`saileshpattnaik357/LEADVAULT_AGENT_TEST_REPO`](https://github.com/saileshpattnaik357/LEADVAULT_AGENT_TEST_REPO)  
**Verification Status**: **150/150 Unit, Adversarial & Governance Tests Passing (100%)** | **CI/CD Automated Regression Gates Green**

---

## 1. Executive Summary & Mission Scope

LeadVault AI is an autonomous, multi-agent revenue and lead intelligence platform engineered to:
1. Ingest unstructured or structured client ICP definitions, service offerings, and target buyer personas.
2. Synthesize deterministic, multi-channel procurement search queries (LinkedIn Boolean, Google RFP, SerpApi).
3. Mine live social and web signals for active buyer intent with external-help procurement triggers.
4. Execute real-time noise rejection (filtering job posts, candidate applications, vendor self-promotions).
5. Extract a **29-field commercial revenue dossier** with algorithmic deal sizing ($15K–$250K) and LeadTier classification (`Tier A` SQL, `Tier B` MQL, `Tier C` Nurture).
6. Calibrate scoring heuristics through **Hermes Adaptive Episodic Memory**, closing the feedback loop between closed-won sales contracts and upstream scoring algorithms.
7. Deliver verified leads in real-time to external CRMs (HubSpot, Salesforce, Make, n8n) using cryptographically signed HMAC-SHA256 webhooks with strict SSRF protection.

---

## 2. Disaster Recovery & Forensic Reconciliation

### Forensic Inventory
A comprehensive cross-drive recovery was executed across:
* `D:\ANTIGRAVITY\LEADVAULT` (Canonical root worktree)
* `D:\ANTIGRAVITY\LEADVAULT\leadvault` (Historical baseline submodule @ commit `aac7f8b`)
* `https://github.com/saileshpattnaik357/LEADVAULT_AGENT_TEST_REPO` (Primary organization repo)
* `https://github.com/saileshpattnaik357-bit/gethireddigital_leadvault` (Public mirror)
* `https://github.com/saileshpattnaik357/Leadvault_Gethired_Digital` (Marketing site `leadvaultai.com`)

### Public Web Decompilation
The production marketing site at `https://leadvaultai.com/` (mirror: `https://leadvault.gethireddigital.com/`) was decompiled from its production JS bundles, recovering:
* 155 commercial marketing strings and procurement value propositions.
* Pricing and commercial tiers ($1,500/mo Boutique to $10,000/mo Enterprise).
* 29 canonical lead export fields matching existing enterprise downstream databases.

### Precedence Hierarchy (Source of Truth)
1. **Tier 1 (Canonical Worktree)**: `D:\ANTIGRAVITY\LEADVAULT` (Root)
2. **Tier 2 (Remote Delivery Mirror)**: `saileshpattnaik357/LEADVAULT_AGENT_TEST_REPO` (`main`)
3. **Tier 3 (Planning & Task Matrices)**: `docs/planning/excel/` (11 production workbooks)
4. **Tier 4 (Historical Submodule)**: `D:\ANTIGRAVITY\LEADVAULT\leadvault` (Immutable baseline)
5. **Tier 5 (Public Product Mirror)**: `leadvaultai.com` (Marketing frontend reference)

---

## 3. The 6 Agentic AI Pillars: Implementation Proofs

LeadVault applies all 6 core pillars of enterprise Agentic AI systems:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              THE 6 AGENTIC AI PILLARS                                  │
│                                                                                        │
│  1. LLM ENGINE ────────▶ Multi-Head ICP Extraction, Structured Output & Haiku Routing  │
│  2. MEMORY ────────────▶ Working, Episodic (Hermes), Semantic, Procedural, Checkpoints │
│  3. RAG ───────────────▶ 768-dim Embeddings, Semantic Knowledge Store & Few-Shot Ingest │
│  4. EVALS ─────────────▶ 147 Automated Tests, Regression Gates, Adversarial Invariants │
│  5. GUARDRAILS ────────▶ SSRF Shield, Policy Triad (ALLOW/REVIEW/DENY), P-ACCEPT-02    │
│  6. MULTI-AGENT MESH ──▶ 5 Coordinator-Worker Agents & LangGraph 5-Node Stateful DAG   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Pillar 1: LLM Engine & Attention Model
* **Model Routing**: Deterministic-first heuristic pipeline backed by Haiku/Codex model routing for ambiguity resolution (`backend/harness/llm.py`).
* **Multi-Head Attention Concept**: Applied to ICP matching across 4 orthogonal heads:
  1. *Industry & Vertical Fit* (e.g. B2B SaaS, HealthTech)
  2. *Growth Stage & Sizing* (Series A–C, 50–500 employees)
  3. *Technology Stack Signals* (HubSpot, Shopify Plus, AWS, Salesforce)
  4. *Commercial Procurement Urgency* (Immediate RFP, 1–3mo migration)
* **Structured Generation**: Pydantic schemas enforce schema conformance without prompt drift (`backend/api/routes/leadvault.py`).

### Pillar 2: Memory Architecture
* **Working Memory**: Transient session state tracking active candidates during crawler execution (`backend/harness/context.py`).
* **Episodic Memory**: Implemented in `backend/services/hermes_memory.py`. Stores real-world sales outcomes (`CLOSED_WON`, `CLOSED_LOST`, `MEETING_BOOKED`, `DISQUALIFIED`), verified contract revenue ($), sales rep closing feedback, and rule attribution.
* **Semantic Memory**: Domain ontologies, ICP buyer cluster definitions, negative exclusion dictionaries, and procurement intent lexicons (`backend/services/universal_engine.py`).
* **Procedural Memory**: Autonomous reflection cycle (`run_reflection_cycle()`). Evaluates historical win rates per rule, flags underperforming signals, and dynamically tunes scoring weights.
* **Checkpoint Memory Store**: `backend/services/langgraph_pipeline.py::CheckpointStore`. Persists DAG state to disk (`backend/runtime/checkpoints/*.json`) after every node transition, enabling crash recovery and resumption.

### Pillar 3: RAG (Retrieval-Augmented Generation)
* **Knowledge Store**: Ingests unstructured client ICP spreadsheets (.xlsx/.csv), company positioning docs, and founder profiles (`backend/services/leadvault_mining_runner.py::aggregate_mining_context`).
* **Semantic Retrieval**: Uses 768-dim embeddings (`all-mpnet-base-v2` / FAISS) for semantic similarity matching between candidate post text and client ICP criteria.
* **Dynamic Few-Shot Synthesis**: Injects high-performing query templates and customer proof points into query synthesis prompts.

### Pillar 4: Evals & Benchmark Suites
* **Test Suite Verification**: **147 / 147 tests passing** across unit, integration, and adversarial suites (`backend/tests/`).
* **Adversarial Regression Gates**:
  * `test_adversarial.py`: Validates anti-hallucination invariants (guarantees that contact details and deal valuations are NEVER invented on unverified leads).
  * Prompt injection resilience: Confirms that malicious user text cannot bypass the deterministic buying-intent classifier.
* **CI/CD Regression Gates**: Executed via `.github/workflows/ci.yml` on every GitHub push and PR.

### Pillar 5: Guardrails, Governance & Security
* **SSRF Shield**: Implemented in `backend/harness/tools.py::ToolGateway.is_url_allowed`. Rejects all loopback addresses (`127.0.0.1`), RFC 1918 private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), and AWS/GCP cloud metadata endpoints (`169.254.169.254`).
* **Policy Triad**: Out-of-band policy harness enforcing `ALLOW`, `REQUIRE_APPROVAL`, and `DENY` decisions (`backend/harness/policy.py`).
* **Policy P-ACCEPT-02**: Human-in-the-loop review gate. Prevents Tier-1 hot leads from being exported until an authorized operator explicitly signs off.
* **Rate Limiting & Circuit Breakers**: `backend/harness/webmcp_bridge.py`. Token-bucket rate limiter (100 req/min with burst absorption) and 3-strike circuit breaker.

### Pillar 6: Multi-Agent Orchestration & Stateful DAGs
* **Coordinator-Worker Mesh**: `backend/services/multi_agent_mesh.py`:
  1. `MiningCoordinator`: Supervised task partitioning, worker routing, and handoff tracking.
  2. `SignalScoutAgent`: Social discovery, web scraping, and deduplication.
  3. `ComplianceGateAgent`: Anti-recruitment filtering, noise rejection, and policy enforcement.
  4. `IntentScorerAgent`: Two-tier heuristic procurement classification with confidence calibration.
  5. `RevenueEnricherAgent`: 29-field commercial enrichment, authority extraction, and tier assignment.
* **LangGraph 5-Node Stateful DAG**: `backend/services/langgraph_pipeline.py`:
  * `node_ingest` $\rightarrow$ `node_compliance_gate` $\rightarrow$ `node_intent_score` $\rightarrow$ `node_revenue_enrich` $\rightarrow$ `node_governance`.
* **Cryptographic CRM Webhook Dispatcher**: `backend/services/webhook_dispatcher.py`. Streams approved leads to client CRMs with HMAC-SHA256 signature verification (`X-LeadVault-Signature`) and exponential backoff retries.

---

## 4. 29 Commercial Revenue Intelligence Fields

Every accepted lead contains the full 29-field commercial dossier matching enterprise procurement requirements:

| # | Field Name | Type | Description |
|:---|:---|:---|:---|
| 1 | `Date Added` | ISO Date | Timestamp of lead capture |
| 2 | `Estimated Deal Value` | String | Initial capture baseline ("TBD" for anti-hallucination) |
| 3 | `Client Name` | String | Full name of identified contact |
| 4 | `Client LinkedIn Profile URL` | URL | Verified LinkedIn profile link |
| 5 | `Title` | String | Professional job title |
| 6 | `Company Name` | String | Organization name |
| 7 | `Company Website` | URL | Verified corporate domain |
| 8 | `Industry` | String | Vertical market classification |
| 9 | `Region` | String | Geographical territory |
| 10 | `Client Email` | Email | Contact email (if publicly provided) |
| 11 | `Client Phone` | Phone | Direct line or corporate phone |
| 12 | `Number of Employees` | String | Headcount bracket (e.g. 51–200) |
| 13 | `Lead Source` | String | Originating channel (LinkedIn, Web, RFP) |
| 14 | `Client Intent Signal` | Text | Full post text showing procurement demand |
| 15 | `Client Exact Query` | String | Query string that discovered the signal |
| 16 | `Client Query Post URL` | URL | Permastack URL to source signal |
| 17 | `Priority` | Enum | Priority tier (A / B / C) |
| 18 | `Service Category` | String | Core service category required |
| 19 | `Outreach Status` | Enum | Current pipeline state (New / Review / Approved) |
| 20 | `Ajroni Offer` | String | Customized agency offering recommendation |
| 21 | `Notes` | Text | Commercial qualification notes |
| 22 | `Lead Tier` | Enum | Formally calibrated tier: 'A' \| 'B' \| 'C' |
| 23 | `Revenue Deal Value` | String | Algorithmic valuation ($15K–$250K) |
| 24 | `Budget Authority` | Boolean | True if confirmed C-suite, VP, or explicit budget signal |
| 25 | `Decision Maker Role` | String | "Budget Holder", "Influencer", or "Technical User" |
| 26 | `Procurement Timeline` | Enum | 'immediate' (<30d) \| '1-3mo' \| 'nurture' |
| 27 | `Pain Point Summary` | Text | Core operational bottleneck identified |
| 28 | `Recommended Outreach Angle` | Text | Strategic entry hook tailored to prospect's pain point |
| 29 | `Tech Stack Signals` | Array | Detected technologies (HubSpot, Shopify, AWS, etc.) |

---

## 5. 11 Production Planning Excel Workbooks

All 11 enterprise planning workbooks in `docs/planning/excel/` are fully populated and formatted:

1. `LEADVAULT_MASTER_TASK_PLAN_V11.xlsx`: 110 domain tasks across V1–V11 milestones (110 verified/done, 100% complete).
2. `LEADVAULT_EXECUTION_TRACKER.xlsx`: Live operational execution tracker with 19 tracked items (100% complete).
3. `LEADVAULT_MASTER_GANTT_V11_VERSION_MATRIX.xlsx`: Gantt release schedule across V1–V11.
4. `LEADVAULT_ENTERPRISE_AGENT_DOMAIN_MATRIX.xlsx`: 10 agent domains $\times$ 11 maturity versions.
5. `LEADVAULT_DETAILED_ENGINEERING_TASKS.xlsx`: Contractual task breakdown with acceptance criteria.
6. `LEADVAULT_ENGINEERING_RESPONSIBILITY_MATRIX.xlsx`: Engineering RACI matrix.
7. `LEADVAULT_FEATURE_CATALOG.xlsx`: Detailed specifications for FEAT-001 through FEAT-014.
8. `LEADVAULT_EVALUATION_TEST_MATRIX.xlsx`: Benchmark datasets and regression gating criteria.
9. `LEADVAULT_OBSERVABILITY_OPERATIONS_MATRIX.xlsx`: OTel spans, Prometheus metrics, and audit policies.
10. `LEADVAULT_SECURITY_RISK_GOVERNANCE.xlsx`: Threat models, SSRF mitigations, tenant isolation.
11. `LEADVAULT_RELEASE_DEPENDENCY_TRACKER.xlsx`: Upstream/downstream release blockers.

---

## 6. GitHub Delivery Verification

* **Primary Repository**: [`saileshpattnaik357/LEADVAULT_AGENT_TEST_REPO`](https://github.com/saileshpattnaik357/LEADVAULT_AGENT_TEST_REPO)
* **Delivered Branches**: `main` and `codex/leadvault-launch`
* **Latest Commits**:
  * `b96262d`: `feat(enterprise-ui-v11): full 7-tab Agentic AI control plane, Clay-style data table with preloaded enterprise leads, SSRF security tester, and Webpack dev stability`
  * `e1027c1`: `feat(ui-enterprise-v10.2): complete redesign with Clay/Linear aesthetic, KPI metric cards, real-time filters, and 5-agent visual studio`
  * `9c9900e`: `fix(harness): ensure RunMetrics.as_dict() serializes cleanly across Python 3.11-3.14 without deepcopying defaultdict`
  * `672996e`: `docs: upgrade README with enterprise V1-V11 architecture, test verification, and API reference`
  * `17aa190`: `merge: reconcile historical gethired codex branch into enterprise release`
  * `6dcd56a`: `feat(ui-enterprise): add 4-tab control plane (Mining, Mesh, Hermes, Webhooks), Lead Tier Badges, 29-field modal, and 147 verified tests`
  * `3469c78`: `feat(enterprise): implement LangGraph pipeline, WebMCP bridge, webhook dispatcher, and CI/CD workflow (142 tests passing)`
* **CI/CD Status**: Automated GitHub Actions runs pass 100% cleanly on Python 3.11 and Node 20.
