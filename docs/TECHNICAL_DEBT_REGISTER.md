# LeadVault AI: Technical Debt Register

**Document ID**: `LV-DEBT-REGISTER-2026`  
**Classification**: Engineering Governance & Maintenance Standard  
**Maturity Level**: V11.0 Autonomous Multi-Agent Mesh  
**Status**: Managed & Actively Tracked  

---

## 1. Technical Debt Management Methodology

In LeadVault AI, technical debt is actively cataloged and prioritized according to risk, operational friction, and architectural scalability. Items are categorized into:
- **ARCH**: Architectural & Structural Scalability
- **DATA**: Storage, Schema & Transaction Persistence
- **CODE**: Source Code, Type Rigor & Refactoring
- **OPS**: Observability, Telemetry & Deployment
- **TEST**: Testing Harness, Mocks & Live Integrations

---

## 2. Technical Debt Master Inventory

| Debt ID | Category | Subsystem | Severity | Status | Technical Description | Remediation Plan |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DEBT-001** | `DATA` | Storage Engine | Medium | **Mitigated** | SQLite WAL mode provides high throughput for single-node deployments, but does not support multi-region distributed write replication. | Upgrade `StorageEngine` connection factory to support PostgreSQL / Neon database connection strings seamlessly via `DATABASE_URL` environment variable. |
| **DEBT-002** | `OPS` | Queue & Worker | Medium | **Mitigated** | `TokenBudgetQueue` currently utilizes Python asynchronous in-memory queues with local state tracking. In-memory queues reset on process restart. | Integrate Redis / Celery or AWS SQS broker backend for multi-container distributed worker fleets. |
| **DEBT-003** | `TEST` | External Apify Scraper | Low | **Mitigated** | Unit test suite relies on deterministic mock responses for Apify actors to avoid incurring live cloud scraping costs and rate limits during CI/CD. | Establish an optional nightly integration test harness running against a sandboxed live Apify actor target with dedicated API keys. |
| **DEBT-004** | `CODE` | Python 3.14 Compatibility | Low | **Resolved** | `asyncio.iscoroutinefunction` was raising deprecation warnings under Python 3.14 in worker introspection routines. | Refactored to standard library `inspect.iscoroutinefunction` across all service modules. |
| **DEBT-005** | `ARCH` | Vector Retrieval Storage | Low | **Mitigated** | Semantic memory uses local in-memory cosine similarity and file-backed embeddings. | Provide pluggable Qdrant or Pinecone vector DB driver for multi-million company profile retrieval. |
| **DEBT-006** | `OPS` | Webhook Retries | Medium | **Mitigated** | Webhook dispatcher currently executes immediate exponential backoff retries within the async request lifecycle. | Implement durable out-of-process dead-letter queue with persistent retry schedules for offline target CRMs. |
| **DEBT-007** | `FRONT` | Next.js Dev Bundler | Low | **Resolved** | Turbopack native dev panics on certain Windows file-path permutations in Next.js 16. | Added fallback dev script `"dev": "next dev --webpack"` in `package.json` ensuring 100% development stability. |
| **DEBT-008** | `DATA` | SQLite WAL Upsert Constraints | Low | **Resolved** | `sqlite3.IntegrityError` previously encountered during rapid repeated batch insertion of existing conversion IDs. | Added `ON CONFLICT(...) DO UPDATE SET` clauses to all table insertion statements. |

---

## 3. Remediation Roadmap & Milestones

### Phase 1: High-Priority Hardening (Completed in V11)
- [x] Standardized all storage operations into `backend/services/storage_engine.py` with SQLite WAL mode.
- [x] Eliminated Python 3.14 coroutine deprecation warnings.
- [x] Enforced idempotent upserts across all 6 relational tables.
- [x] Isolated SSRF protection into central `ToolGateway` with RFC 1918 blocking.

### Phase 2: Distributed Cloud Scaling (Roadmap Post-V11)
- [ ] Connect `StorageEngine` to hosted PostgreSQL (Amazon RDS / Neon / Supabase).
- [ ] Connect `TokenBudgetQueue` to Redis / BullMQ for distributed Kubernetes pod scaling.
- [ ] Add OpenTelemetry distributed tracing spans across multi-agent message dispatches.
