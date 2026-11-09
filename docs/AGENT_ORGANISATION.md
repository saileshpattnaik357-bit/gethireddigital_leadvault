# LeadVault AI: Enterprise Agent Organisation

**Document ID**: `LV-ORG-AGENTS-2026`  
**Classification**: Organizational & Operational Standard  
**Standard**: SEORocket Enterprise Engineering Control Standard  
**Maturity Level**: V11.0 Autonomous Multi-Agent Mesh  

---

## 1. Business Purpose & Operating Model

LeadVault AI organizes its artificial intelligence capabilities around the B2B revenue mining lifecycle:
1. **Targeting & Signal Acquisition**: Discover where buyers are voicing pain, budget availability, or vendor dissatisfaction.
2. **Signal Verification & Anti-Noise**: Filter out recruitment pitches, sales spam, and false positives.
3. **Intent Scoring & Deep Research**: Classify buying signals by urgency, extract executive movement (<90d), and identify tech stack migrations.
4. **Commercial Enrichment**: Synthesize 29-field commercial revenue dossiers with algorithmic deal valuations ($15K–$250K) and Lead Tiers (`Tier A`, `Tier B`, `Tier C`).
5. **Governance & Delivery**: Enforce policy controls (Policy Triad), sign outbound webhook payloads with HMAC-SHA256, and close the loop with CRM conversion learning.

To maximize reliability and cost efficiency, **no LLM is permitted to operate unmonitored without deterministic guardrails, typed message interfaces, and policy enforcement**.

---

## 2. Structural Hierarchy & Division of Labor

```
                                  ┌─────────────────────────────┐
                                  │     CHIEF ORCHESTRATOR      │
                                  │      MiningCoordinator      │
                                  └──────────────┬──────────────┘
                                                 │
                   ┌─────────────────────────────┼─────────────────────────────┐
                   │                             │                             │
                   ▼                             ▼                             ▼
    ┌─────────────────────────────┐┌───────────────────────────┐┌─────────────────────────────┐
    │  SIGNAL SOURCING SUPERVISOR ││ CLASSIFICATION SUPERVISOR ││   DELIVERY & CRM GATEWAY    │
    └──────────────┬──────────────┘└─────────────┬─────────────┘└──────────────┬──────────────┘
                   │                             │                             │
       ┌───────────┴───────────┐     ┌───────────┴───────────┐                 │
       ▼                       ▼     ▼                       ▼                 ▼
┌──────────────┐ ┌──────────────┐┌──────────────┐ ┌──────────────┐      ┌──────────────┐
│ SignalScout  │ │ DeepResearch ││ComplianceGate│ │ IntentScorer │      │WebhookStream │
│    Agent     │ │    Agent     ││    Agent     │ │    Agent     │      │  Dispatcher  │
└──────────────┘ └──────────────┘└──────────────┘ └──────────────┘      └──────────────┘
                                                 │
                                                 ▼
                                        ┌───────────────────┐
                                        │  RevenueEnricher  │
                                        │       Agent       │
                                        └─────────┬─────────┘
                                                  │
                                                  ▼
                                 ┌───────────────────────────────────┐
                                 │   SHARED INTELLIGENCE & POLICY    │
                                 │  - Hermes Episodic Memory Engine  │
                                 │  - Control Plane Policy Harness   │
                                 │  - Token Budget & Queue Manager   │
                                 │  - Closed-Loop OS Self-Healing    │
                                 └───────────────────────────────────┘
```

---

## 3. Organizational Roles & Responsibilities

### Level 1: Central Orchestration
- **`MiningCoordinator`** (`backend/services/multi_agent_mesh.py`):
  - Primary dispatching supervisor.
  - Controls lifecycle transitions: `INIT` $\rightarrow$ `SCOUT` $\rightarrow$ `VERIFY` $\rightarrow$ `SCORE` $\rightarrow$ `ENRICH` $\rightarrow$ `GOVERN` $\rightarrow$ `DELIVER`.
  - Maintains state consistency and emits audit metrics to SQLite.
- **`LangGraphPipeline`** (`backend/services/langgraph_pipeline.py`):
  - Provides stateful acyclic DAG execution for high-assurance batch processing.
  - Manages durable step checkpointing and state rollback via `CheckpointStore`.

### Level 2: Domain Supervisors
- **Signal Sourcing Supervisor**: Decomposes client ICP into Boolean search strategies and coordinates crawling tasks across LinkedIn, Google RFP, and Reddit.
- **Classification Supervisor**: Oversees noise rejection, anti-hallucination dual-proof checks, and multi-head intent scoring.
- **Delivery Gateway Supervisor**: Verifies policy compliance before formatting dossiers into CSV, XLSX, or signed JSON webhooks.

### Level 3: Specialist Execution Agents
1. **`SignalScoutAgent`**:
   - Queries public social graphs and RFP feeds.
   - Normalizes raw posts into structured candidate signal objects.
2. **`ComplianceGateAgent`**:
   - Applies dual-proof verification: rejects recruitment listings, vendor marketing, and self-promotional spam.
   - Verifies contact authority markers (e.g. VP, Director, Head of Engineering).
3. **`IntentScorerAgent`**:
   - Evaluates procurement urgency (Immediate RFP vs. Long-term discovery).
   - Computes weighted intent score based on pain points, timeline, and budget indicators.
4. **`DeepResearchAgent`**:
   - Ingests company filings, tech blogs, and news.
   - Detects executive hires within the past 90 days and recent funding rounds (Series A–E).
5. **`RevenueEnricherAgent`**:
   - Generates the standard 29-field commercial dossier.
   - Computes algorithmic deal value ranges ($15K–$250K) and assigns Lead Tiers.
6. **`TokenBudgetAgent`**:
   - Monitors per-tenant token usage and USD costs.
   - Triggers soft warnings at 80% quota and halts execution at 100% quota.
7. **`ClosedLoopOSAgent`**:
   - Monitors model health and API response latencies.
   - Manages automatic fallback cascade (`Claude 3.5 Sonnet` $\rightarrow$ `GPT-4o` $\rightarrow$ `Haiku`) and proxy rotation.
8. **`WebhookDispatcherAgent`**:
   - Computes HMAC-SHA256 signatures for payload integrity.
   - Verifies target URLs against SSRF rules before transmitting to CRMs.

### Level 4: Shared Intelligence Layer
- **`HermesMemoryEngine`** (`backend/services/hermes_memory.py`):
  - Captures closed sales outcomes (`WON`, `LOST`, `DISQUALIFIED`).
  - Auto-tunes scoring weights dynamically using procedural memory feedback loops.
- **`StorageEngine`** (`backend/services/storage_engine.py`):
  - SQLite WAL mode ACID relational engine enforcing tenant isolation and referential integrity.

### Level 5: Governance & Compliance Layer
- **`ControlPlaneHarness`** (`backend/services/control_plane.py`):
  - Enforces Policy Triad decisions: `ALLOW`, `REQUIRE_APPROVAL`, `DENY`.
  - Strictly enforces Policy `P-ACCEPT-02` (requiring human operator sign-off for Tier-A leads).
- **`ToolGateway`** (`backend/services/tool_gateway.py`):
  - Inspects all outbound URLs to block loopback (127.0.0.1), private RFC 1918 subnets, and cloud metadata services (169.254.169.254).

---

## 4. Delegation Rules & Escalation Policies

| Trigger Condition | Responsible Agent | Escalation Target | Action Taken |
| :--- | :--- | :--- | :--- |
| Candidate signal contains recruitment keywords | `ComplianceGateAgent` | `MiningCoordinator` | Dropped immediately; marked `REJECTED_RECRUITMENT_NOISE`. |
| Primary LLM API returns 5xx error or latency >4.0s | `ClosedLoopOSAgent` | Model Failover Cascade | Automatically rerouted to `GPT-4o` or `Haiku`. |
| Lead evaluated as `Tier A` ($50K+ deal value) | `RevenueEnricherAgent` | `ControlPlaneHarness` | Policy `P-ACCEPT-02` intercepts; queued for operator approval. |
| Tenant token consumption reaches 80% quota | `TokenBudgetAgent` | Billing Service / Admin | Emits soft quota warning log; processing continues. |
| Tenant token consumption reaches 100% quota | `TokenBudgetAgent` | `MiningCoordinator` | Immediate execution halt; returns HTTP 429 Quota Exceeded. |
| Outbound webhook target resolves to private IP | `ToolGateway` | Security Audit Log | Blocked with `SSRF_VIOLATION_BLOCKED`; alert logged to SQLite. |
| Sales conversion recorded in CRM (Won/Lost) | CRM Webhook Ingestion | `HermesMemoryEngine` | Recalibrates heuristic scoring weights in procedural memory. |

---

## 5. Human-in-the-Loop (HITL) Execution Model

LeadVault AI implements a **Supervised Autonomy** paradigm:
- Low-risk and high-confidence tasks (scraping, noise rejection, heuristic parsing) execute with full autonomy (Level 1 Autonomy).
- High-consequence commercial decisions (exporting Tier-A high-value deals to CRM, firing external outreach campaigns) mandate human operator sign-off (Level 2 Bounded Autonomy).
- The operator reviews leads directly inside the 8-tab Next.js control plane before releasing them to the outbound pipeline.
