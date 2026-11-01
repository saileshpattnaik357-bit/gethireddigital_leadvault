# LeadVault AI: Comprehensive Feature Catalog & Technical Specifications

**Document ID:** `LV-DOC-FEAT-007`  
**Date:** 2026-11-01  
**Project:** LeadVault AI  
**Author:** LeadVault Principal Systems Architect & Engineering Lead  

---

## 1. Feature Catalog Overview

This catalog enumerates all foundational, operational, and roadmap capabilities of LeadVault AI. Every capability is tracked with unique identifiers, domain mappings, technical specifications, and verification criteria.

---

## 2. Core Feature Specifications

### `FEAT-001`: Client ICP Ingestion & Deterministic Mining Brain Synthesis
- **Feature ID:** `FEAT-001`
- **Product Domain:** ICP & Query Generation
- **User Problem:** Sales teams struggle to translate their Ideal Customer Profile into effective Boolean and parametric web queries without generating massive false-positive noise.
- **Business Outcome:** Reduces query setup time from 4 hours to under 30 seconds; eliminates irrelevant search results upfront.
- **Functionality:** Ingests client company details, value propositions, service categories, target verticals, geographies, and negative exclusions. Generates a structured Mining Brain containing targeted LinkedIn and Google Boolean strings.
- **Required Agents:** `AGENT_009` (Spec & Enrichment), `AGENT_010` (Scoring Engine)
- **APIs:** `POST /api/leadvault/plan`, `POST /api/leadvault/upload`
- **Tools:** `csv_parser`, `query_synthesizer`
- **Database:** Local Spec Store (`leadvault_specs.json`) / PostgreSQL `client_specs` table
- **Frontend:** Next.js ICP configuration modal, CSV upload dropzone, query matrix preview tab
- **Backend:** `backend/services/leadvault_agent.py`, `backend/services/leadvault_spec_store.py`
- **Security:** Input validation on uploaded file formats (.csv, .xlsx only); size cap of 5MB.
- **Dependencies:** None (deterministic base)
- **Acceptance Criteria:** Brain generated within 2 seconds; contains valid Boolean syntax without unclosed quotes or syntax errors.
- **Test Requirements:** Unit test on CSV parsing and spec persistence; verify roundtrip serialization.
- **Implementation Status:** **Implemented & Verified (Production Ready)**

---

### `FEAT-002`: Two-Tier Buying Intent Classification & Confidence Scoring
- **Feature ID:** `FEAT-002`
- **Product Domain:** Intent & Qualification
- **User Problem:** Simple keyword scrapers treat any mention of "agency" or "developer" as a lead, creating massive false alarms from recruitment posts and spam.
- **Business Outcome:** >94% intent precision; sales reps only spend time reaching out to active buyers.
- **Functionality:** 
  - Tier 1: Fast regex-based evaluation across 150+ procurement triggers; assigns confidence score (0.00 – 1.00).
  - Tier 2: Boundary signals (0.50 – 0.69) trigger optional LLM arbitration via isolated context packet.
- **Required Agents:** `AGENT_010` (Buying Intent Agent), `AGENT_011` (Research & Arbitration)
- **APIs:** Internal service call via `BuyingIntentAgent.classify(post_text)`
- **Tools:** Heuristic Regex Library, Multi-provider LLM bridge (`backend/harness/llm.py`)
- **Database:** `gold_corpus.jsonl` benchmark reference
- **Frontend:** Confidence score gauge (0–100%), intent trigger pill badge, trigger phrase highlight
- **Backend:** `backend/services/buying_intent_agent.py`
- **Security:** Untrusted external post content is sanitized and wrapped in protective isolation tags before any LLM ingestion.
- **Dependencies:** `FEAT-001`
- **Acceptance Criteria:** Classifies explicit procurement queries (e.g., "looking for an agency") as `buyer` with score ≥0.85; rejects recruitment posts (e.g., "we're hiring") as `noise` with score <0.50.
- **Test Requirements:** Full coverage in `test_buying_intent_classifier.py`; 100% pass on 40 benchmark samples.
- **Implementation Status:** **Implemented & Verified (Production Ready)**

---

### `FEAT-003`: FinalVerifier Anti-Hallucination & Noise Rejection Pipeline
- **Feature ID:** `FEAT-003`
- **Product Domain:** Verification & Data Quality
- **User Problem:** Generative AI models hallucinate contact information, misread seller pitches as buyer leads, and invent fake budget figures.
- **Business Outcome:** Zero hallucinated contact details delivered; 100% replacement warranty adherence.
- **Functionality:** Deterministic multi-stage filter enforcing the dual-condition requirement: (1) Active problem/need, and (2) Proof of seeking external partner. Filters seller self-promotions, student queries, and employee hiring. Never synthesizes emails or phones.
- **Required Agents:** `FinalVerifier` Service
- **APIs:** Internal verification method `FinalVerifier.verify(candidate_signal)`
- **Tools:** Rule-based keyword matching and phrase boundaries
- **Database:** Rejected Audit Store (`rejected_audits.json`)
- **Frontend:** Rejected Leads tab with filter reason breakdown (e.g., "Recruitment Noise", "Seller Promotion")
- **Backend:** `backend/services/final_verifier.py`, `backend/services/rejected_audit_store.py`
- **Security:** Immutable audit entry logged for every rejected row with raw excerpt.
- **Dependencies:** `FEAT-002`
- **Acceptance Criteria:** Rejects 100% of seller pitches and job hiring posts, regardless of adversarial prompt injection attempts.
- **Test Requirements:** Tested in `test_adversarial.py` under `TestHallucinatedData` and `TestFooledModelCannotAutoExport`.
- **Implementation Status:** **Implemented & Verified (Production Ready)**

---

### `FEAT-004`: Out-of-Band Control Plane Harness & Governance Policy
- **Feature ID:** `FEAT-004`
- **Product Domain:** Governance & Security
- **User Problem:** Autonomous agents running uncontrolled can execute unauthorized writes, leak data, or hit forbidden external endpoints.
- **Business Outcome:** SOC2/Enterprise compliance readiness; complete auditability for corporate security teams.
- **Functionality:** Enforces `ALLOW`, `REQUIRE_APPROVAL`, `DENY` policy matrix. Hard-denies unauthorized outbound outreach and CRM mutations. Logs every state change and tool invocation to append-only JSONL.
- **Required Agents:** Harness Control Plane (`policy.py`, `audit.py`, `approvals.py`)
- **APIs:** `GET /api/leadvault/harness/policy`, `GET /api/leadvault/harness/audit`, `POST /api/leadvault/harness/approvals/{id}`
- **Tools:** Immutable Append-Only Audit Logger
- **Database:** `audit.jsonl`
- **Frontend:** Policy inspection panel, live audit viewer, pending approvals badge counter
- **Backend:** `backend/harness/policy.py`, `backend/harness/audit.py`, `backend/harness/approvals.py`
- **Security:** Cross-tenant approvals rejected with HTTP 409; tamper-evident log sequencing.
- **Dependencies:** None
- **Acceptance Criteria:** Any attempt to perform `bulk_outreach` or `crm_write` without review raises `PolicyViolationError`.
- **Test Requirements:** Tested in `test_harness.py` under `TestPolicyEngine` and `TestApprovals`.
- **Implementation Status:** **Implemented & Verified (Production Ready)**

---

### `FEAT-005`: SSRF-Protected Tool Gateway & Network Sandbox
- **Feature ID:** `FEAT-005`
- **Product Domain:** Security & Network
- **User Problem:** Web scraping agents can be tricked via malicious URLs into crawling internal cloud metadata services (e.g., `169.254.169.254` or `localhost`).
- **Business Outcome:** Prevents infrastructure compromise and credential theft.
- **Functionality:** Validates all external HTTP/HTTPS fetch targets. Rejects private RFC 1918 subnets, loopbacks, local hostnames, and cloud metadata endpoints.
- **Required Agents:** `ToolGateway`
- **APIs:** Internal tool invocation gateway `tools.fetch(url)`
- **Tools:** `network_guard`, `dns_resolver`
- **Database:** Audit trail
- **Frontend:** None (transparent security layer)
- **Backend:** `backend/harness/tools.py`
- **Security:** Blocks schemes other than `http` and `https`; resolves DNS before connection to prevent rebinding attacks.
- **Dependencies:** `FEAT-004`
- **Acceptance Criteria:** Refuses `http://169.254.169.254/latest/meta-data/`, `http://localhost/admin`, and `file:///etc/passwd` with immediate security audit record.
- **Test Requirements:** Tested in `test_harness.py` under `TestToolGateway`.
- **Implementation Status:** **Implemented & Verified (Production Ready)**

---

### `FEAT-006`: Human-in-the-Loop Review & Approval Queue
- **Feature ID:** `FEAT-006`
- **Product Domain:** Operations & Quality Assurance
- **User Problem:** High-value or borderline leads require human sign-off before being exported or routed to CRM.
- **Business Outcome:** Eliminates customer-facing errors on high-stakes enterprise prospect accounts.
- **Functionality:** Holds candidate leads with confidence between 0.50 and 0.69 (or those flagged by policy) in a tenant-scoped pending approval queue. Operators can accept, reject, or reclassify with documented rationale.
- **Required Agents:** `ApprovalsQueue`
- **APIs:** `GET /api/leadvault/harness/approvals`, `POST /api/leadvault/harness/approvals/decide`
- **Tools:** Approval store
- **Database:** Local JSON / SQLite approvals queue
- **Frontend:** Dedicated "Pending Review" queue table with Accept/Reject action buttons and reason dropdown
- **Backend:** `backend/harness/approvals.py`
- **Security:** Decisions require authenticated actor identity; cross-tenant approvals strictly prohibited.
- **Dependencies:** `FEAT-004`
- **Acceptance Criteria:** A lead placed in review is never visible in `accepted_exports` until explicitly approved by an operator.
- **Test Requirements:** Tested in `test_adversarial.py` under `TestApprovalBypass`.
- **Implementation Status:** **Implemented & Verified (Production Ready)**

---

### `FEAT-007`: Multi-Dimensional Lead Enrichment Dossier (15/24/29 Fields)
- **Feature ID:** `FEAT-007`
- **Product Domain:** Data Enrichment & Intelligence
- **User Problem:** Sales reps receive raw email addresses without company context, requiring hours of manual LinkedIn research.
- **Business Outcome:** Sales reps can personalize outreach within 60 seconds; conversion rates jump 3x.
- **Functionality:** Enriches verified leads across three tiers of fields: 15 Contact Fields, 24 Sales Fields, and 29 Revenue Intelligence Fields (company ARR tier, tech stack, pain point hook, deal estimation).
- **Required Agents:** `AGENT_009` (Enrichment Agent)
- **APIs:** `GET /api/leadvault/runs`, `GET /api/leadvault/export/{kind}`
- **Tools:** `enrichment_pipeline`, `firmographic_lookup`
- **Database:** `accepted_exports.json`
- **Frontend:** Detailed Lead Card drawer, expandable table rows, column visibility toggles
- **Backend:** `backend/services/leadvault_mining_runner.py`, `backend/services/accepted_export_store.py`
- **Security:** Public signals only; compliance with GDPR Article 6(1)(f) legitimate interest.
- **Dependencies:** `FEAT-002`, `FEAT-003`
- **Acceptance Criteria:** Exported leads contain complete firmographic and signal dossiers in standardized column formats.
- **Test Requirements:** Verified in end-to-end capture and mining tests.
- **Implementation Status:** **Implemented & Verified (Production Ready)**

---

### `FEAT-008`: Golden Corpus Automated Evaluation Benchmark Runner
- **Feature ID:** `FEAT-008`
- **Product Domain:** MLOps & Quality Evaluation
- **User Problem:** Regex additions or prompt tweaks can cause silent accuracy regressions on previously working patterns.
- **Business Outcome:** Continuous quality assurance; ensures precision stays above the 94% threshold.
- **Functionality:** Executes automated benchmark evaluations against `gold_corpus.jsonl`. Computes precision, recall, F1, false positive rate, and latency. Generates versioned timestamped JSON reports in `backend/evaluation/reports/`.
- **Required Agents:** Evaluation Harness
- **APIs:** CLI command `python -m backend.evaluation.harness`
- **Tools:** Scikit-learn / custom confusion matrix calculators
- **Database:** `gold_corpus.jsonl`
- **Frontend:** Evaluation metrics display tab (Roadmap)
- **Backend:** `backend/evaluation/harness.py`
- **Security:** Read-only access to evaluation corpus; no mutation of production stores.
- **Dependencies:** `FEAT-002`
- **Acceptance Criteria:** Benchmark runner outputs precision, recall, and accuracy across buyer, seller, and recruitment classes.
- **Test Requirements:** Validated via automated test harness runs.
- **Implementation Status:** **Implemented & Verified (Production Ready)**

---

### `FEAT-009`: Multi-Tenant Workspace & Client Isolation
- **Feature ID:** `FEAT-009`
- **Product Domain:** Multi-Tenancy & Tenant Isolation
- **User Problem:** Agencies running lead generation for multiple competing clients risk cross-contaminating leads and proprietary ICP strategies.
- **Business Outcome:** Complete enterprise tenant safety; enables multi-client agency reselling.
- **Functionality:** Scopes all specs, runs, approval items, and exported files to specific `tenant_id` namespaces. Blocks any cross-tenant data retrieval or state mutation.
- **Required Agents:** Control Plane Harness
- **APIs:** `GET /api/leadvault/tenants`, tenant header `X-Tenant-ID` enforcement
- **Tools:** Tenant Scoper
- **Database:** Partitioned JSON stores / PostgreSQL row-level security
- **Frontend:** Workspace switcher dropdown in top navigation bar
- **Backend:** `backend/api/routes/leadvault.py`, `backend/api/routes/harness.py`
- **Security:** API returns HTTP 409 on attempted cross-tenant approvals; tenant isolation rigorously tested.
- **Dependencies:** `FEAT-004`
- **Acceptance Criteria:** Tenant A cannot see, approve, or export leads belonging to Tenant B.
- **Test Requirements:** Tested in `test_adversarial.py` under `TestTenantIsolation`.
- **Implementation Status:** **Implemented & Verified (Production Ready)**

---

### `FEAT-010`: Real-Time Webhook Streaming & Export Hub
- **Feature ID:** `FEAT-010`
- **Product Domain:** Delivery & CRM Integration
- **User Problem:** Delays in delivering buying signals reduce lead response rates; sales teams need instant alerts.
- **Business Outcome:** Instant notification (<60s) of high-intent SQL leads; first-mover sales advantage.
- **Functionality:** Generates formatted XLSX/CSV exports on demand; dispatches verified SQL leads via webhook payloads to configured CRM endpoints (HubSpot, Salesforce, Slack).
- **Required Agents:** `AGENT_010` (Delivery Engine)
- **APIs:** `GET /api/leadvault/export/accepted`, `GET /api/leadvault/export/rejected`, `POST /api/leadvault/webhook/test`
- **Tools:** OpenPyXL export writer, Webhook dispatcher
- **Database:** Accepted Export Store
- **Frontend:** "Export to CSV/XLSX" button, Webhook configuration drawer
- **Backend:** `backend/services/accepted_export_store.py`, `backend/api/routes/leadvault.py`
- **Security:** Outbound webhooks require explicit HMAC secret signing; target URLs validated by SSRF guard.
- **Dependencies:** `FEAT-004`, `FEAT-007`
- **Acceptance Criteria:** Exports generate valid .xlsx and .csv files matching legacy schemas without corrupting special characters or emojis.
- **Test Requirements:** Export route tests; file integrity validation.
- **Implementation Status:** **Implemented & Verified (Production Ready)**
