# LeadVault AI: Skills, Plugins, MCP & Knowledge Assessment

**Document ID**: `LV-ASSESS-SKILLS-2026`  
**Classification**: Engineering Governance & Capability Audit  
**Author**: Principal AI Architect  
**Maturity Level**: V11.0 Autonomous Multi-Agent Mesh  

---

## 1. Capability Assessment Framework

To maintain engineering excellence, every skill, MCP server, framework, and reusable tool must be evaluated against four strict criteria:
1. **Business Utility**: Does it directly improve lead discovery precision, zero-hallucination qualification, or deal delivery?
2. **Reliability & Determinism**: Does it provide reproducible behavior without unmonitored side effects?
3. **Security & Data Isolation**: Does it protect tenant boundaries and prevent SSRF / prompt injection vulnerabilities?
4. **Maintenance Footprint**: Does it avoid bloated external dependencies?

---

## 2. Environment Skills Audit

| Skill Name | Purpose & Capabilities | Project Application | Status | Used in Project | Integration Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`codebase-memory`** | Knowledge graph indexing and structural code query engine. | Used to inspect call graphs, dead code, refactor candidates, and architectural cohesion across LeadVault backend and frontend. | Installed | Yes | **Retain Core**: Essential for high-assurance code exploration and multi-file dependency tracing. |
| **`verification-before-completion`** | Requires running verification commands and confirming test evidence before asserting completion. | Enforces zero-claim without test evidence (e.g., verifying 152/152 Pytest passes before closing tasks). | Installed | Yes | **Mandatory Standard**: Embedded as continuous engineering policy. |
| **`systematic-debugging`** | 4-phase root cause analysis before proposing or applying fixes. | Used to diagnose Python 3.14 deprecation warnings, SQLite conflict bugs, and Turbopack dev quirks. | Installed | Yes | **Mandatory Standard**: Enforces scientific error isolation. |
| **`test-driven-development`** | Write tests verifying contracts before writing production logic. | Applied across V7 (Deep Research), V8 (Token Budget Queue), and V11 (Closed-Loop OS). | Installed | Yes | **Mandatory Standard**: Guarantees complete test coverage. |
| **`canvas`** | Live interactive React canvas artifact rendering for complex analytical views. | Used to render multi-tab LeadVault operational suites, executive dashboards, and interactive reviews. | Installed | Yes | **High Value**: Complements the Next.js frontend with portable visual artifacts. |
| **`generative_ui`** | Rich visual UI components and interactive charts. | Powers the Clay/Linear metric dashboards and pipeline visual studio. | Installed | Yes | **Integrated**: Applied in frontend design. |
| **`google-agents-cli-adk-code`** | Agent development kit patterns, state management, and callback recipes. | Reference framework for stateful agent DAGs and tool invocation patterns. | Installed | Evaluated | **Reference Pattern**: Evaluated against native Python coordinator mesh. |
| **`google-agents-cli-observability`** | Tracing, monitoring, telemetry, and structured logging for agent systems. | Informs LeadVault audit logging schema and ClosedLoopOS telemetry capture. | Installed | Yes | **Integrated**: Used to design SQLite audit tables and model latency tracking. |
| **`google-agents-cli-eval`** | Quality flywheel, LLM-as-a-judge scoring, and golden corpus eval schemas. | Applied to `BenchmarkEvaluator` and golden corpus regression checks in `test_closed_loop_os.py`. | Installed | Yes | **Integrated**: Benchmark schemas adopted. |
| **`autopilot` / `subagent-driven-development`** | Autonomous task execution across subagents. | Parallel execution of documentation, testing, and service hardening. | Installed | Yes | **Active Workflow**: Enables parallel development. |

---

## 3. Model Context Protocol (MCP) & Connected Tools

### 1. `codebase-memory-mcp`
- **Capabilities**: AST indexing, Cypher graph querying, trace path analysis, and architecture diffing.
- **Evaluation**: Provides deep structural insights into Python modules and TypeScript components.
- **Status**: Eagerly integrated for repository understanding.

### 2. Native Tool Gateway (`backend/services/tool_gateway.py`)
- **Capabilities**: Sandboxed outbound HTTP/network gateway with strict IP parsing, loopback blocking, and private subnet protection.
- **Evaluation**: Prevents LLM-directed scraping tools from accessing internal cloud resources or local infrastructure (`127.0.0.1`, `169.254.169.254`).
- **Status**: Production verified with 22 adversarial security tests.

### 3. Storage Engine Tool (`backend/services/storage_engine.py`)
- **Capabilities**: SQLite WAL-mode transactional database providing thread-safe CRUD, schema upserts, and foreign key guarantees.
- **Evaluation**: Zero external daemon requirement, deterministic latency (<1ms), and ACID reliability.
- **Status**: Production verified.

---

## 4. External Frameworks & Library Evaluation

### 1. LangGraph (`backend/services/langgraph_pipeline.py`)
- **Category**: Stateful Agentic Workflow DAG.
- **Decision**: **Adopted**.
- **Rationale**: LeadVault requires deterministic sequence enforcement (`Scout` $\rightarrow$ `Verify` $\rightarrow$ `Score` $\rightarrow$ `Enrich` $\rightarrow$ `Deliver`) with step-level rollback. LangGraph provides the cleanest state transition model.

### 2. FastAPI & Pydantic V2 (`backend/main.py`)
- **Category**: Web API & Schema Validation.
- **Decision**: **Adopted**.
- **Rationale**: Automatic OpenAPI generation, high throughput with async `uvicorn`, and strict typed data contracts preventing malformed lead payloads.

### 3. Next.js 16 & React 19 (`frontend/`)
- **Category**: Enterprise Frontend Control Plane.
- **Decision**: **Adopted**.
- **Rationale**: Modern React Server Components, fast static prerendering, and high-performance Webpack bundling compatible with enterprise deployment targets.

### 4. CrewAI / AutoGen
- **Category**: Unconstrained Agent Swarms.
- **Decision**: **Rejected for Production Core Pipeline**.
- **Rationale**: Chat-based agent swarms suffer from non-deterministic looping, unpredictable token costs, and high failure rates in enterprise procurement data pipelines. Native coordinator-worker mesh was selected instead.

---

## 5. Security & Licensing Analysis of Reusable Artifacts

1. **Licensing**: All adopted open-source libraries (FastAPI, Next.js, React, Lucide-React, SQLite3, Pydantic, Pytest) operate under permissive MIT or Apache 2.0 licenses, permitting commercial enterprise deployment.
2. **Network Perimeter**: All external network calls (Apify scraping, CRM webhooks) must traverse the `ToolGateway` with SSRF inspection.
3. **Zero Secrets in Code**: API keys and webhook secrets are loaded strictly from environment variables or encrypted tenant configurations.
