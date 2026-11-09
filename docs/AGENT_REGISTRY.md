# LeadVault AI: Comprehensive Agent Registry

**Document ID**: `LV-REG-AGENTS-2026`  
**Classification**: Enterprise Operational Standard  
**Maturity Level**: V11.0 Autonomous Multi-Agent Mesh  
**Source Master**: [`docs/planning/excel/LEADVAULT_ENTERPRISE_AGENT_DOMAIN_MATRIX.xlsx`](file:///D:/ANTIGRAVITY/LEADVAULT/docs/planning/excel/LEADVAULT_ENTERPRISE_AGENT_DOMAIN_MATRIX.xlsx)  
**Status**: 20/20 Agents Fully Specified and Verified  

---

## 1. Domain Architecture Agent Registry (10 Agents)

The 10 Domain Architecture Agents define the functional capabilities across the LeadVault revenue lifecycle.

---

### `AGENT_001` — MiningBrainSynthesizer
- **Codename**: `MiningBrainSynthesizer`
- **Domain**: ICP & Query Synthesis
- **Autonomy Level**: Bounded (Level 2)
- **Purpose**: Transform high-level client ICP profiles into optimized Boolean, LinkedIn, Google RFP, and Reddit search operators.
- **Responsibilities**: Deconstruct ICP criteria; generate negative exclusion keywords; construct multi-source query strings.
- **Inputs**: Client ICP JSON/CSV (industry, target roles, tech stack, geography).
- **Outputs**: `DiscoveryPlan` object containing structured search syntax.
- **Tools / APIs**: Query Synthesizer Engine, Regex Formatter.
- **Data Permissions**: Read-only access to client tenant ICP specs.
- **Memory Requirements**: Semantic memory of high-performing query templates.
- **Knowledge Sources**: B2B search operator taxonomies.
- **Parent Agent**: `MiningCoordinator`.
- **Delegation Rules**: Delegates generated queries to `AGENT_002` (PublicSignalCrawler).
- **Execution Workflow**: ICP Parse $\rightarrow$ Term Expansion $\rightarrow$ Negative Syntax Injection $\rightarrow$ Query Validation.
- **Error Handling**: Falls back to baseline keyword queries on expansion failure.
- **Evaluation Criteria**: Query syntax validity >98%, search precision score >85%.
- **Implementation Status**: **VERIFIED** ([`backend/services/discovery_plan.py`](file:///D:/ANTIGRAVITY/LEADVAULT/backend/services/discovery_plan.py)).

---

### `AGENT_002` — PublicSignalCrawler
- **Codename**: `PublicSignalCrawler`
- **Domain**: Signal Sourcing & Web Crawling
- **Autonomy Level**: Monitored (Level 3)
- **Purpose**: Ingest public posts, RFPs, and social discussions across LinkedIn, Reddit, and Google search indices.
- **Responsibilities**: Execute network queries; handle pagination; respect crawl delays; rotate proxies.
- **Inputs**: Search queries, target URLs, rate limit policies.
- **Outputs**: Unstructured post snippets, timestamps, author names, post URLs.
- **Tools / APIs**: Apify Scraper Client, SSRF-Guarded Tool Gateway.
- **Data Permissions**: Public Internet HTTP/HTTPS scraping only.
- **Memory Requirements**: Working memory of deduplication hashes (SHA-256).
- **Knowledge Sources**: Web scrapers, search indices.
- **Parent Agent**: `MiningCoordinator`.
- **Delegation Rules**: Feeds raw candidate snippets to `AGENT_004` (FinalVerifier).
- **Execution Workflow**: Query Dispatch $\rightarrow$ HTTP Scrape $\rightarrow$ HTML Cleaning $\rightarrow$ Deduplication $\rightarrow$ Candidate Stream.
- **Error Handling**: Automatic proxy rotation on 429/403; backoff on network timeout.
- **Evaluation Criteria**: Zero network loops, 100% adherence to SSRF guardrails.
- **Implementation Status**: **VERIFIED** ([`backend/services/scraper.py`](file:///D:/ANTIGRAVITY/LEADVAULT/backend/services/scraper.py)).

---

### `AGENT_003` — BuyingIntentClassifier
- **Codename**: `BuyingIntentClassifier`
- **Domain**: Intent Classification
- **Autonomy Level**: Autonomous (Level 1)
- **Purpose**: Classify candidate posts into discrete buyer-intent categories and compute procurement urgency scores.
- **Responsibilities**: Evaluate pain point urgency, budget authority markers, and purchase timelines.
- **Inputs**: Verified candidate post snippets, company context.
- **Outputs**: `IntentScore` (0–100), intent classification label, confidence score.
- **Tools / APIs**: Intent Classification Heuristics, Multi-Model LLM Classifier.
- **Data Permissions**: Read access to candidate snippets; no external API permissions.
- **Memory Requirements**: Procedural weights tuned by Hermes learning engine.
- **Knowledge Sources**: B2B procurement signal taxonomy (RFP, migration, vendor dissatisfaction).
- **Parent Agent**: `MiningCoordinator`.
- **Delegation Rules**: Hands scored signals to `AGENT_005` (DossierEnricher) if score $\ge 60$.
- **Execution Workflow**: Lexical Match $\rightarrow$ Multi-Head Intent Scoring $\rightarrow$ Urgency Weighting $\rightarrow$ Normalization.
- **Error Handling**: Graceful fallback to regex heuristics if LLM classification times out.
- **Evaluation Criteria**: Classification F1-score >0.85 against golden corpus.
- **Implementation Status**: **VERIFIED** ([`backend/services/intent_scorer.py`](file:///D:/ANTIGRAVITY/LEADVAULT/backend/services/intent_scorer.py)).

---

### `AGENT_004` — FinalVerifier
- **Codename**: `FinalVerifier`
- **Domain**: Verification & Anti-Hallucination
- **Autonomy Level**: Autonomous (Level 1)
- **Purpose**: Enforce dual-proof evidence and filter out recruitment noise, vendor promotions, and agency pitches.
- **Responsibilities**: Match signals against recruitment blacklists; verify contact identity against company domain.
- **Inputs**: Raw candidate signals, company domain records.
- **Outputs**: Verification decision (`APPROVED_BUYER` vs `REJECTED_RECRUITMENT_NOISE`).
- **Tools / APIs**: Anti-Hallucination Verification Engine, Domain Matcher.
- **Data Permissions**: Internal signal inspection.
- **Memory Requirements**: Working memory of recent candidate signatures.
- **Knowledge Sources**: Hiring keyword dictionaries, vendor pitch patterns.
- **Parent Agent**: `MiningCoordinator`.
- **Delegation Rules**: Immediately drops signals matching recruitment criteria; passes clean signals to `AGENT_003`.
- **Execution Workflow**: Pattern Match $\rightarrow$ Noise Filter $\rightarrow$ Evidence Corroboration $\rightarrow$ Verification Seal.
- **Error Handling**: Rejects signal on ambiguous evidence (fail-safe posture).
- **Evaluation Criteria**: False positive recruitment leak rate <2.0%.
- **Implementation Status**: **VERIFIED** ([`backend/services/anti_hallucination.py`](file:///D:/ANTIGRAVITY/LEADVAULT/backend/services/anti_hallucination.py)).

---

### `AGENT_005` — DossierEnricher
- **Codename**: `DossierEnricher`
- **Domain**: Revenue Intelligence & Enrichment
- **Autonomy Level**: Bounded (Level 2)
- **Purpose**: Synthesize verified buyer signals into standardized 29-field commercial revenue dossiers with deal valuations.
- **Responsibilities**: Compute algorithmic deal sizes ($15K–$250K); assign Lead Tiers (`Tier A`, `Tier B`, `Tier C`).
- **Inputs**: Verified company profile, intent score, pain points, budget indicators.
- **Outputs**: 29-Field Revenue Dossier JSON structure.
- **Tools / APIs**: Revenue Intelligence Engine, Deal Sizing Algorithm.
- **Data Permissions**: Read company records; write to lead storage.
- **Memory Requirements**: Semantic memory of industry deal benchmarks.
- **Knowledge Sources**: B2B contract value models, technology stack pricing tiers.
- **Parent Agent**: `MiningCoordinator`.
- **Delegation Rules**: Submits compiled dossier to `AGENT_006` (ControlPlaneHarness).
- **Execution Workflow**: Attribute Extraction $\rightarrow$ Tech Profiling $\rightarrow$ Valuation Modeling $\rightarrow$ Dossier Compilation.
- **Error Handling**: Sets deal size to conservative minimum ($15,000) if valuation data is incomplete.
- **Evaluation Criteria**: 100% schema compliance across all 29 fields.
- **Implementation Status**: **VERIFIED** ([`backend/services/revenue_intelligence.py`](file:///D:/ANTIGRAVITY/LEADVAULT/backend/services/revenue_intelligence.py)).

---

### `AGENT_006` — ControlPlaneHarness
- **Codename**: `ControlPlaneHarness`
- **Domain**: Governance & Policy
- **Autonomy Level**: Supervisor (Level 0)
- **Purpose**: Enforce out-of-band Policy Triad governance (`ALLOW`, `REQUIRE_APPROVAL`, `DENY`) across all actions.
- **Responsibilities**: Intercept privileged actions; enforce Policy `P-ACCEPT-02`; write tamper-evident audit logs.
- **Inputs**: Agent action requests, proposed payload, tenant security context.
- **Outputs**: Governance decision (`ALLOW`, `REQUIRE_APPROVAL`, `DENY`).
- **Tools / APIs**: Policy Triad Engine, SQLite Audit Logger.
- **Data Permissions**: Full administrative read/write over security policies and audit tables.
- **Memory Requirements**: Immutable audit log stream.
- **Knowledge Sources**: Corporate governance rules, data compliance standards (GDPR/CCPA).
- **Parent Agent**: Chief System Orchestrator.
- **Delegation Rules**: Routes `REQUIRE_APPROVAL` decisions to `AGENT_007` (ApprovalQueueManager).
- **Execution Workflow**: Action Intercept $\rightarrow$ Policy Evaluation $\rightarrow$ Triad Decision $\rightarrow$ Audit Logging.
- **Error Handling**: Hard `DENY` on rule ambiguity or internal policy exception.
- **Evaluation Criteria**: Zero policy bypasses; 100% audit log capture rate.
- **Implementation Status**: **VERIFIED** ([`backend/services/control_plane.py`](file:///D:/ANTIGRAVITY/LEADVAULT/backend/services/control_plane.py)).

---

### `AGENT_007` — ApprovalQueueManager
- **Codename**: `ApprovalQueueManager`
- **Domain**: Human-in-the-Loop Operations
- **Autonomy Level**: Supervised (Level 2)
- **Purpose**: Manage the operator review queue for borderline intent signals and high-value Tier-A opportunities.
- **Responsibilities**: Present lead dossiers to human reviewers; capture approve/reject decisions; record review rationale.
- **Inputs**: Leads flagged for review by `ControlPlaneHarness`.
- **Outputs**: Operator resolution (`APPROVED_BY_OPERATOR` / `REJECTED_BY_OPERATOR`).
- **Tools / APIs**: Review Queue Manager, Next.js UI WebSocket/REST notification.
- **Data Permissions**: Read/write lead review states.
- **Memory Requirements**: State of pending operator reviews.
- **Knowledge Sources**: Human reviewer feedback history.
- **Parent Agent**: `ControlPlaneHarness`.
- **Delegation Rules**: Releases approved leads to `AGENT_010` (DeliveryStreamGateway).
- **Execution Workflow**: Enqueue Lead $\rightarrow$ Alert Operator $\rightarrow$ Capture Sign-off $\rightarrow$ Dispatch Event.
- **Error Handling**: Automatically archives unreviewed leads after 14-day TTL.
- **Evaluation Criteria**: Mean time to operator resolution tracked; zero unapproved exports.
- **Implementation Status**: **VERIFIED** ([`backend/services/control_plane.py`](file:///D:/ANTIGRAVITY/LEADVAULT/backend/services/control_plane.py)).

---

### `AGENT_008` — TenantIsolationGuard
- **Codename**: `TenantIsolationGuard`
- **Domain**: Multi-Tenancy & Data Security
- **Autonomy Level**: Supervisor (Level 0)
- **Purpose**: Enforce tenant cryptographic boundaries and guarantee zero cross-tenant data contamination.
- **Responsibilities**: Validate `tenant_id` on all database transactions; enforce query scoping; manage per-tenant token budgets.
- **Inputs**: Storage transaction requests, tenant context tokens.
- **Outputs**: Scoped execution context or access denial exception.
- **Tools / APIs**: SQL Row-Level Filter, Token Budget Governor.
- **Data Permissions**: Multi-tenant authorization engine.
- **Memory Requirements**: Tenant active session mappings.
- **Knowledge Sources**: Multi-tenant isolation specifications.
- **Parent Agent**: Chief System Orchestrator.
- **Delegation Rules**: Halts operations exceeding tenant limits; blocks cross-tenant queries.
- **Execution Workflow**: Request Inspection $\rightarrow$ Tenant Context Validation $\rightarrow$ Query Scoping $\rightarrow$ Execution.
- **Error Handling**: Throws `TenantSecurityViolation` and logs security alert on unauthorized access.
- **Evaluation Criteria**: Zero cross-tenant data leaks across all adversarial tests.
- **Implementation Status**: **VERIFIED** ([`backend/services/storage_engine.py`](file:///D:/ANTIGRAVITY/LEADVAULT/backend/services/storage_engine.py)).

---

### `AGENT_009` — BenchmarkEvaluator
- **Codename**: `BenchmarkEvaluator`
- **Domain**: Evaluation & MLOps
- **Autonomy Level**: Autonomous (Level 1)
- **Purpose**: Execute continuous regression benchmarks against golden corpora to prevent intent scoring drift.
- **Responsibilities**: Run automated evaluation passes; compute precision, recall, and F1-score; alert on performance degradation.
- **Inputs**: Golden corpus benchmark dataset, current scoring pipeline.
- **Outputs**: Benchmark report (precision, recall, F1, accuracy).
- **Tools / APIs**: Pytest Evaluation Suite, Quality Flywheel Analyzer.
- **Data Permissions**: Read-only access to golden benchmark records.
- **Memory Requirements**: Historical benchmark regression logs.
- **Knowledge Sources**: Verified buyer-intent ground truth datasets.
- **Parent Agent**: Engineering Oversight.
- **Delegation Rules**: Triggers alert if F1 drops below 0.82 threshold.
- **Execution Workflow**: Load Dataset $\rightarrow$ Run Pipeline $\rightarrow$ Compute Metrics $\rightarrow$ Compare Drift $\rightarrow$ Publish Report.
- **Error Handling**: Fails CI build on regression detection.
- **Evaluation Criteria**: Accuracy >85% on standard test suites.
- **Implementation Status**: **VERIFIED** ([`backend/tests/test_closed_loop_os.py`](file:///D:/ANTIGRAVITY/LEADVAULT/backend/tests/test_closed_loop_os.py)).

---

### `AGENT_010` — DeliveryStreamGateway
- **Codename**: `DeliveryStreamGateway`
- **Domain**: Delivery & CRM Hub
- **Autonomy Level**: Bounded (Level 2)
- **Purpose**: Format, cryptographically sign, and stream verified lead dossiers to customer CRMs and export files.
- **Responsibilities**: Calculate HMAC-SHA256 signatures; enforce SSRF URL validation; generate CSV and Excel exports.
- **Inputs**: Approved 29-field lead dossiers, webhook configuration.
- **Outputs**: Signed HTTP webhook dispatches, CSV/XLSX download streams.
- **Tools / APIs**: Webhook Dispatcher, CSV/XLSX Export Engine, HMAC Crypto Module.
- **Data Permissions**: Read approved lead dossiers; make outbound HTTP requests to validated webhooks.
- **Memory Requirements**: Delivery status log and retry queues.
- **Knowledge Sources**: CRM webhook schemas (HubSpot, Salesforce, Webhook JSON).
- **Parent Agent**: `MiningCoordinator`.
- **Delegation Rules**: Emits successful delivery events to audit log.
- **Execution Workflow**: Dossier Formatting $\rightarrow$ URL SSRF Check $\rightarrow$ HMAC Signing $\rightarrow$ HTTP POST $\rightarrow$ Result Logging.
- **Error Handling**: Retries with exponential backoff on 5xx; records delivery failure in SQLite.
- **Evaluation Criteria**: 100% cryptographic signature verification, zero SSRF violations.
- **Implementation Status**: **VERIFIED** ([`backend/services/webhook_dispatcher.py`](file:///D:/ANTIGRAVITY/LEADVAULT/backend/services/webhook_dispatcher.py)).

---

## 2. Active Runtime Mesh Directory (10 Agents)

The 10 Runtime Mesh Agents execute in live production across asynchronous workers, event streams, and background queues.

| Mesh ID | Runtime Class | Architecture Role | Source Code Implementation | Input Payload | Output Artifact | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`MESH_001`** | `MiningCoordinator` | Supervisory Dispatcher & State Machine | [`backend/services/multi_agent_mesh.py`](file:///D:/ANTIGRAVITY/LEADVAULT/backend/services/multi_agent_mesh.py) | Raw procurement signal + tenant context | Fully coordinated multi-agent result | **VERIFIED** |
| **`MESH_002`** | `SignalScoutAgent` | Social & Web Scraping Worker | [`backend/services/multi_agent_mesh.py`](file:///D:/ANTIGRAVITY/LEADVAULT/backend/services/multi_agent_mesh.py) | Search query parameters | Extracted candidate signals | **VERIFIED** |
| **`MESH_003`** | `ComplianceGateAgent` | Anti-Recruitment Noise Guard | [`backend/services/multi_agent_mesh.py`](file:///D:/ANTIGRAVITY/LEADVAULT/backend/services/multi_agent_mesh.py) | Candidate post snippets | Verified candidate or rejection notice | **VERIFIED** |
| **`MESH_004`** | `IntentScorerAgent` | Multi-Head Attention Classifier | [`backend/services/multi_agent_mesh.py`](file:///D:/ANTIGRAVITY/LEADVAULT/backend/services/multi_agent_mesh.py) | Verified candidate text | Intent score (0–100) & confidence | **VERIFIED** |
| **`MESH_005`** | `RevenueEnricherAgent` | 29-Field Commercial Enricher | [`backend/services/multi_agent_mesh.py`](file:///D:/ANTIGRAVITY/LEADVAULT/backend/services/multi_agent_mesh.py) | Scored buyer intent lead | 29-Field Commercial Dossier | **VERIFIED** |
| **`MESH_006`** | `HermesMemoryAgent` | Episodic Deal Store & Procedural Tuner | [`backend/services/hermes_memory.py`](file:///D:/ANTIGRAVITY/LEADVAULT/backend/services/hermes_memory.py) | Closed-won/lost sales outcomes | Calibrated heuristic scoring weights | **VERIFIED** |
| **`MESH_007`** | `DeepResearchAgent` | Expansion Signal & Leadership Tracker | [`backend/services/deep_research.py`](file:///D:/ANTIGRAVITY/LEADVAULT/backend/services/deep_research.py) | Multi-source documents & company URLs | Executive hires (<90d) & funding rounds | **VERIFIED** |
| **`MESH_008`** | `TokenBudgetAgent` | Distributed Queue & Token Governor | [`backend/services/token_budget_queue.py`](file:///D:/ANTIGRAVITY/LEADVAULT/backend/services/token_budget_queue.py) | Batch lead intake tasks | Enqueued execution & token cost audit | **VERIFIED** |
| **`MESH_009`** | `ClosedLoopOSAgent` | Automated Failover & Self-Healing | [`backend/services/closed_loop_os.py`](file:///D:/ANTIGRAVITY/LEADVAULT/backend/services/closed_loop_os.py) | Model telemetry & proxy errors | Automated failover & proxy rotation | **VERIFIED** |
| **`MESH_010`** | `WebhookDispatcherAgent` | Cryptographic CRM Streamer | [`backend/services/webhook_dispatcher.py`](file:///D:/ANTIGRAVITY/LEADVAULT/backend/services/webhook_dispatcher.py) | Approved 29-field lead dossier | HMAC-signed outbound HTTP payload | **VERIFIED** |
