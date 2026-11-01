# LeadVault AI: Comprehensive Recovery Inventory & Artifact Registry

**Document ID:** `LV-DOC-REC-002`  
**Date:** 2026-11-01  
**Auditor:** LeadVault Principal Recovery Engineer & Chief Architect  
**Scope:** Physical disks `D:\`, `E:\`, `C:\Users\sailesh\`, Git histories, and web endpoints.

---

## 1. Executive Summary of Recovery Operations

A rigorous multi-drive disaster recovery scan was conducted across the local development machine, inspecting Git reflogs, hidden directories, nested repositories, Claude memories, Antigravity session caches, and corporate shared assets. 

**Total Identified Artifacts:**
- **546+** matched LeadVault project files and directories across `D:\`, `E:\`, and `C:\`.
- **4** distinct Git remote repositories identified.
- **2** nested Git repositories located inside `D:\ANTIGRAVITY\LEADVAULT`.
- **1** active, fully green backend test suite (115/115 passing unit and adversarial tests).
- **11** Master Engineering workbooks identified in the cross-project reference base (`E:\Sailesh\Gethired Global\DIGIX\Tech\SEO_ROCKET`).
- **Complete public marketing and feature codebase** extracted and decoded from `leadvaultai.com`.

---

## 2. Exhaustive Inventory of Recovered Sources

### Source 1: Local Working Trunk — Root Project Directory
- **Path:** `D:\ANTIGRAVITY\LEADVAULT`
- **Source Type:** Active Primary Development Worktree (Git Repo)
- **Last Modified:** 2026-10-26 (Git HEAD: commit `ab4cd3a`)
- **Key Artifacts:**
  - `backend/` (FastAPI, 115 passing tests, Policy Harness, Audit Engine, Tool Gateway, Multi-provider LLM adapter).
  - `frontend/` (Next.js 14 App Router, complete interactive dashboard, 44KB `page.tsx`).
  - `backend/runtime/` (`leadvault_specs.json`, `accepted_exports.json`, `rejected_audits.json`, `audit.jsonl`).
  - Core Docs: `AGENTS.md`, `CLAUDE.md`, `HANDOVER_TO_CLAUDE.md`, `HANDOVER_TO_CLAUDE_PROJECT.md`.
- **Verification Status:** **100% Verified.** All 115 unit/adversarial tests pass with Python 3.14.
- **Relevance:** **Primary Canonical Source of Truth** for core engine, security harness, and UI.

---

### Source 2: Nested Legacy Working Snapshot
- **Path:** `D:\ANTIGRAVITY\LEADVAULT\leadvault`
- **Source Type:** Embedded Git Sub-repository
- **Last Modified:** 2026-07-04 (Git HEAD: commit `aac7f8b`)
- **Recovered Functionality:**
  - Early implementation of `buying_intent_agent.py` (6.4KB vs. root's 17.6KB).
  - Early `leadvault_mining_runner.py` (21KB vs. root's 34KB).
  - Legacy `frontend/app/page.tsx` (35KB vs. root's 44KB).
  - Historical server execution logs (`backend_server.log`, `frontend_server.log`).
- **Conflicts & Differences:** Lacks the Agentic Control Harness (`backend/harness/`), evaluation benchmark runner (`backend/evaluation/`), adversarial test suites, and confidence scoring.
- **Relevance:** **Historical Baseline.** Kept for historical reference; root-level code is the strictly superior superset.

---

### Source 3: Claude Codebase Working Copy
- **Path:** `E:\Claude\leadvault`
- **Source Type:** Worktree / Mirrored Development Directory
- **Last Modified:** 2026-09-18
- **Recovered Functionality:** Identical file structure to `D:\ANTIGRAVITY\LEADVAULT` at commit `ebe59a2`. Contains the original evaluation reports (`eval_20260918T185652Z.json`, `silver_mistral.json`).
- **Relevance:** Secondary verified mirror confirming reproducibility across disk volumes.

---

### Source 4: Production Test Mirror Repository
- **Path:** `E:\Claude\leadvault-repo`
- **Source Type:** Git Clone / Standalone Working Copy
- **Unique Implementation:** Contains SQLite persistence databases:
  - `backend/runtime/leadvault_agent.db`
  - `backend/runtime/leadvault_agent.db-wal`
  - `backend/runtime/leadvault_agent.db-shm`
- **Relevance:** High. Provides evidence of early SQLite runtime persistence and schema structure.

---

### Source 5: Claude Project Memory & Context
- **Path:** `E:\Claude\PROJECT_CONTEXT\LEADVAULT.md` & `E:\Claude\.claude\projects\E--Claude\memory\leadvault_project_summary.md`
- **Source Type:** Structured Architectural System Memory
- **Last Modified:** 2026-09-10
- **Recovered Knowledge:**
  - 14 integrated enterprise skills (Harness Engineering, Database Sharding, Query Rewriting, RAG, Semantic Search, Reranking, Checkpointing, Distributed Tracing, Caching, Event-Driven Architecture, Kafka Queues, Load Balancing, Model Routing).
  - Detailed Agent definitions: `AGENT_009` (Enrichment), `AGENT_010` (Scoring), `AGENT_011` (Research).
  - Throughput targets: 1,000+ leads/day, P95 <100ms latency, 1M+ database scalability.
- **Relevance:** **Critical Architectural Standard.** Forms the foundation for the Enterprise V1–V11 Roadmap.

---

### Source 6: Public Production Website & JavaScript Bundle
- **Endpoint:** `https://leadvaultai.com/` (bundle: `/assets/index-COuZb-yP.js`)
- **Source Type:** Deployed Production Single-Page Application (Cloudflare / Vite)
- **Recovered Assets:**
  - 155+ extracted buyer-intent marketing propositions, FAQ copy, guarantee policies, pricing tiers.
  - Three commercial tiers: Pay Per Run, Pipeline Pro, Vault Elite.
  - Exact lead field schema: 15 Contact Fields, 24 Sales Fields, 29 Revenue Intelligence Fields.
  - Replacement warranty criteria: Free replacement on email bounce, inactive profile, or out-of-ICP lead.
- **Relevance:** Defines user-facing customer expectations and commercial packaging.

---

### Source 7: Corporate Commercial & GTM Asset Library
- **Path:** `E:\Sailesh\Gethired Global\Leadvault` & `E:\Sailesh\Gethired Global\DIGIX\Marketing\GTM\MISC\`
- **Source Type:** Executive Strategy, GTM, Pricing, and Brand Files
- **Recovered Assets:**
  - `LeadVaultAI_ICP_Form.csv` (Original ICP intake template).
  - `LeadVault_Apify_Budget_Model.xlsx` (Token economics and compute cost models).
  - `LeadVault_GTM_Master_Plan.xlsx` & `GHD_LeadVault_Commission_Structure.xlsx`.
  - Comprehensive sales scripts: `LEADVAULT_SQL_UPDATED_SALES_PLAYBOOK.docx`, `LeadVault_SDR_Playbook_Advanced.docx`.
  - High-resolution SVG and PNG master brand assets (`enhanced_leadvaultai_logo.png`, `leadvaultai_app_icon.png`).
- **Relevance:** High. Provides realistic operational numbers, token budgets, and ICP templates.

---

### Source 8: Visual Architecture & Case Study Blueprints
- **Path:** `E:\Claude\sailesh-site\src\assets\case-studies\leadvault`
- **Source Type:** Production WebP System Architecture Diagrams & Video Assets
- **Recovered Visual Schematics:**
  - `LEADVAULT_004_SYSTEM_ARCHITECTURE.webp`
  - `LEADVAULT_005_AGENT_SERVICE_ARCHITECTURE.webp`
  - `LEADVAULT_006_WORKFLOW.webp`
  - `LEADVAULT_007_KNOWLEDGE_GROUNDING.webp`
  - `LEADVAULT_008_EVALUATION_FRAMEWORK.webp`
  - `LEADVAULT_009_GOVERNANCE.webp`
  - `LEADVAULT_010_EVIDENCE_AVAILABILITY.webp`
  - `LEADVAULT_019_DECISION_INSPECTOR.webp`
- **Relevance:** Provides authoritative diagrams of the originally intended enterprise system.

---

### Source 9: Master Enterprise Agentic AI Reference
- **Path:** `E:\Sailesh\Gethired Global\DIGIX\Tech\SEO_ROCKET`
- **Source Type:** Production V1–V11 Enterprise Agentic AI Control Framework
- **Recovered Methodologies:**
  - Master Gantt and 25-domain evolution matrix (`SEOROCKET_MASTER_GANTT_V12_VERSION_MATRIX.xlsx`).
  - Master Task Plan (`SEOROCKET_ARYA_MASTER_TASK_PLAN_V11.xlsx`).
  - Engineering Control System (`SEOROCKET_ENGINEERING_CONTROL_SYSTEM.xlsx`).
  - Architectural blueprints: Orchestrators, Control Plane, Shared Intelligence Layer, Governance, Monitoring.
- **Relevance:** **The Gold Standard Methodology** to be applied directly to LeadVault AI's 11 Planning Workbooks.
