# LeadVault AI: Agentic AI Architecture Specification

**Document ID**: `LV-ARCH-AGENTIC-2026`  
**Classification**: Enterprise Technical Architecture  
**Author**: Principal AI Architect & CTO  
**Maturity Level**: V11.0 Autonomous Closed-Loop Operating System  
**Test Baseline**: 152/152 Pytest Automated Tests Passing  

---

## 1. Architectural Philosophy & Core Tenets

LeadVault AI is engineered on the principle that **deterministic business logic should remain deterministic, while agentic LLM reasoning must be applied where cognitive ambiguity, semantic interpretation, and complex synthesis create high business value**.

Blindly wrapping every single data transform in an LLM prompt leads to unpredictable latencies, high token costs, and catastrophic hallucinations. Conversely, rigid regex-only systems fail on nuanced B2B buyer intent expressions. LeadVault AI solves this through a **hybrid multi-agent architecture** combining:
1. **Deterministic Guards**: Fast regex heuristics, SSRF validation, schema validation, and SQL storage.
2. **Cognitive Agents**: LLM-driven query synthesis, multi-head intent classification, dual-proof verification, and deep research extraction.
3. **Supervisory State Machines**: Coordinator-worker mesh and LangGraph stateful DAG with persistent checkpointing.
4. **Out-of-Band Governance**: Policy Triad (`ALLOW`, `REQUIRE_APPROVAL`, `DENY`) running independently of LLM outputs.

---

## 2. 5-Level Agent Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                LEVEL 1: CENTRAL ORCHESTRATION                          │
│                                                                                         │
│   [ MiningCoordinator ] ─── Coordinates Mesh Dispatch, Task Routing & State Machine     │
│   [ LangGraphPipeline ] ─── 5-Node Acyclic Workflow DAG + Persistent CheckpointStore    │
└────────────────────────────────────────┬────────────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────▼────────────────────────────────────────────────┐
│                                LEVEL 2: DOMAIN ORCHESTRATION                            │
│                                                                                         │
│   [ Signal Sourcing Supervisor ]   [ Classification Supervisor ]   [ Delivery Gateway ] │
└────────────────────────────────────────┬────────────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────▼────────────────────────────────────────────────┐
│                                LEVEL 3: SPECIALIST AGENTS                               │
│                                                                                         │
│   ├─ [ SignalScoutAgent ] ──────── Scrapes LinkedIn, Google RFP, Reddit via Apify       │
│   ├─ [ ComplianceGateAgent ] ───── Enforces Dual-Proof & Filters Recruitment Noise      │
│   ├─ [ IntentScorerAgent ] ─────── Multi-Head Intent Classification & Confidence Scoring│
│   ├─ [ RevenueEnricherAgent ] ──── Generates 29-Field Commercial Dossier & Deal Sizing  │
│   ├─ [ DeepResearchAgent ] ─────── Extracts Executive Hires (<90d) & Series Funding     │
│   ├─ [ TokenBudgetAgent ] ──────── Enforces Tenant Token Quotas ($USD) & Batch Queues   │
│   └─ [ ClosedLoopOSAgent ] ─────── Manages 3-Tier Model Failover & Self-Healing Proxies │
└────────────────────────────────────────┬────────────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────▼────────────────────────────────────────────────┐
│                                LEVEL 4: SHARED INTELLIGENCE                             │
│                                                                                         │
│   [ HermesMemoryEngine ] ───────── Episodic Deal Store & Procedural Weight Self-Tuner   │
│   [ StorageEngine (SQLite WAL) ] ── ACID Relational Database & Foreign Key Consistency  │
│   [ Hybrid Retrieval / RAG ] ───── Local Vector & Heuristic Search Indices             │
└────────────────────────────────────────┬────────────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────▼────────────────────────────────────────────────┐
│                                LEVEL 5: GOVERNANCE & POLICY                             │
│                                                                                         │
│   [ ControlPlaneHarness ] ──────── Policy Triad (ALLOW / REQUIRE_APPROVAL / DENY)       │
│   [ ToolGateway / SSRF Guard ] ─── Enforces RFC 1918 & Cloud Metadata Interception      │
│   [ WebhookDispatcher ] ────────── HMAC-SHA256 Cryptographic Payload Signing            │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Major Architectural Decisions & Rationales

### Decision 1: LangGraph Stateful DAG vs. Autonomeous Swarm (CrewAI / AutoGen)
- **Why it is needed**: B2B lead qualification requires strict sequence invariance: a signal *must* be cleared for recruitment noise before being scored for intent, and *must* pass policy checks before export.
- **Problem solved**: In unconstrained swarms (AutoGen / CrewAI chat loops), agents can loop endlessly, skip critical validation gates, or prematurely invoke delivery tools without operator sign-off.
- **Why appropriate**: LangGraph provides explicit state contracts (`LeadState`), conditional branching, and deterministic disk checkpointing (`CheckpointStore`).
- **Code integration**: Implemented in [`backend/services/langgraph_pipeline.py`](file:///D:/ANTIGRAVITY/LEADVAULT/backend/services/langgraph_pipeline.py).
- **Alternatives considered**: CrewAI (too opaque, hidden prompt injections), AutoGen (conversational overhead, high latency).
- **Trade-offs**: Requires explicit state graph definitions, but yields 100% deterministic reproducibility.

### Decision 2: 3-Tier Model Failover Cascade
- **Why it is needed**: Upstream model outages, rate limits, or latency spikes must never halt lead generation pipelines.
- **Problem solved**: Downtime on primary foundation model providers (e.g. Anthropic API 529 or OpenAI 429 errors).
- **Why appropriate**: The cascade uses `Claude 3.5 Sonnet` as primary (highest reasoning accuracy for intent), falling back to `GPT-4o` on failure/latency >4s, and finally to `Claude 3.5 Haiku` for basic heuristic extraction.
- **Code integration**: Implemented in [`backend/services/closed_loop_os.py`](file:///D:/ANTIGRAVITY/LEADVAULT/backend/services/closed_loop_os.py) with automated telemetry logging.
- **Alternatives considered**: Single-provider retry with exponential backoff (causes pipeline stalls of >60 seconds).
- **Trade-offs**: Slightly different prompt output formats managed by strict Pydantic parsing.

### Decision 3: Out-of-Band Policy Triad Governance (`ALLOW` / `REQUIRE_APPROVAL` / `DENY`)
- **Why it is needed**: Prevents the LLM from executing privileged actions without security authorization.
- **Problem solved**: LLM jailbreaks or prompt injections embedded in scraped public posts attempting to trigger automated emails or data exfiltration.
- **Why appropriate**: The Policy Harness evaluates actions *outside* the agent's LLM context. Even if an LLM decides to export a Tier-A lead, Policy `P-ACCEPT-02` intercepts the call and forces a `REQUIRE_APPROVAL` state.
- **Code integration**: Implemented in [`backend/services/control_plane.py`](file:///D:/ANTIGRAVITY/LEADVAULT/backend/services/control_plane.py).
- **Alternatives considered**: System prompt instructions (e.g., "Do not export without permission") — fundamentally insecure.
- **Trade-offs**: Introduces human-in-the-loop latency for Tier-A leads, which aligns exactly with enterprise sales requirements.

### Decision 4: Hermes Episodic Memory & Procedural Weight Self-Tuning
- **Why it is needed**: Fixed heuristic scoring weights decay over time as market dynamics and buyer terminology change.
- **Problem solved**: Disconnect between what an AI marks as "high intent" and what sales reps actually close.
- **Why appropriate**: The Hermes engine captures conversion outcomes (`WON`, `LOST`, `DISQUALIFIED`) with deal values and sales feedback, dynamically tuning procedural weights (`budget_authority_weight`, `timeline_weight`, `pain_point_weight`).
- **Code integration**: Implemented in [`backend/services/hermes_memory.py`](file:///D:/ANTIGRAVITY/LEADVAULT/backend/services/hermes_memory.py).
- **Alternatives considered**: Static quarterly prompt reviews (slow, manual, unscientific).
- **Trade-offs**: Requires downstream CRM win/loss feedback ingestion.

### Decision 5: SQLite WAL Mode Relational Storage vs. Pure NoSQL
- **Why it is needed**: Strict transactional consistency, foreign key integrity, and zero-configuration local deployment.
- **Problem solved**: Broken references between tenants, lead records, audit logs, and conversion events.
- **Why appropriate**: SQLite in Write-Ahead Logging (`WAL`) mode supports concurrent readers without blocking writes, provides atomic transactions, and requires no external daemon.
- **Code integration**: Implemented in [`backend/services/storage_engine.py`](file:///D:/ANTIGRAVITY/LEADVAULT/backend/services/storage_engine.py).
- **Alternatives considered**: MongoDB (schema drift, higher infrastructure footprint), PostgreSQL (requires local service management).
- **Trade-offs**: SQLite WAL handles tens of thousands of leads easily on a single node; can be pointed to PostgreSQL in distributed enterprise deployments.

---

## 4. Context Engineering & Memory Architecture

| Memory Tier | Storage Backend | Purpose | Persistence | Scope |
| :--- | :--- | :--- | :--- | :--- |
| **Working Memory** | Memory Dict / LangGraph State | Current lead candidate evaluation & state propagation | Transient (Job duration) | Request |
| **Episodic Memory** | SQLite `hermes_conversions` | Historical deal outcomes, sales feedback, conversion logs | Permanent (ACID) | Tenant-Scoped |
| **Semantic Memory** | Vector Embeddings / FAISS | ICP specifications, market segments, company profile matching | Permanent (Disk) | Tenant-Scoped |
| **Procedural Memory** | JSON / Config / DB | Scoring engine weights, routing rules, failover thresholds | Versioned (Auto-tuning) | Global & Tenant |

---

## 5. Multi-Agent Communication Protocol

Agents communicate via structured typed messages:
- **Payload Validation**: Every message is validated against Pydantic schemas before ingestion.
- **Correlation Tracking**: Every message carries a `task_id`, `tenant_id`, and `trace_id` for end-to-end distributed tracing.
- **Failure Containment**: Agent crashes do not crash the orchestrator; dead-letter queues capture failed payloads for offline inspection.
