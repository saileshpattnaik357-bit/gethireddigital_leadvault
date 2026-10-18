# LeadVault AI: Claude Handover & System Architecture Guide

**Project:** LeadVault AI - Agentic Lead Mining & Qualification Engine  
**Repository:** [LeadVaultAI/LEADVAULTAI_TEST_PROJECT](https://github.com/LeadVaultAI/LEADVAULTAI_TEST_PROJECT)  
**Main Branch:** `main` (also available: `codex/leadvault-launch`)  
**Status:** Production-Ready Core Engine + Harness Control Plane | 115/115 Unit & Adversarial Tests Passing  
**Local Codebase Location:** `E:\Claude\leadvault`  
**Workspace Root:** `D:\ANTIGRAVITY\LEADVAULT`

---

## 1. Executive Summary

LeadVault is an agentic AI-driven lead-mining and qualification platform. It ingests an Ideal Customer Profile (ICP), service portfolio, value positioning, target audience, and website URLs, then synthesizes a multi-dimensional client-specific **Mining Brain**:

- **Buying Intent Clusters:** Synthesizes procurement signals, explicit need statements, replacement signals, and budget triggers.
- **Search Query Matrix:** Generates targeted LinkedIn search parameters and Google/Serp Boolean query strings.
- **Two-Tier Intent Classifier:** Combines fast deterministic heuristic pattern matching with an optional LLM second-opinion arbitration layer for borderline signals.
- **Lead Qualification & Anti-Hallucination Pipeline:** Enforces multi-step verification (FinalVerifier) to eliminate spam, student/job seekers, service providers, and irrelevant noise before generating verified leads.
- **Agentic Control Harness:** An out-of-band policy engine, audit log system, and human-in-the-loop review mechanism ensuring AI actions (API calls, data mutations, export actions) comply with safety invariants.

---

## 2. Repository & Branch Details

- **GitHub Remote:** `https://github.com/LeadVaultAI/LEADVAULTAI_TEST_PROJECT.git`
- **Branches Pushed:**
  - `main`: Clean production trunk with updated `.gitignore`, test suites, harness control plane, and docs.
  - `codex/leadvault-launch`: Feature development branch with full commit history.

---

## 3. Architecture & Codebase Layout

```text
E:\Claude\leadvault/
├── backend/
│   ├── api/
│   │   └── routes/
│   │       ├── leadvault.py           # Core mining and spec generation routes
│   │       └── harness.py             # Control plane, policy, audit, workflow routes
│   ├── harness/                       # Agentic Control Plane & Governance
│   │   ├── policy.py                  # ALLOW / REQUIRE_APPROVAL / DENY enforcement
│   │   ├── audit.py                   # Append-only structured audit logger
│   │   ├── tools.py                   # Whitelisted tool registry & network gateway
│   │   ├── registry.py                # Component manifests & declared autonomy levels
│   │   ├── workflow.py                # Mining execution state machine
│   │   ├── approvals.py               # Human-in-the-loop queue for high-impact rows
│   │   ├── context.py                 # Untrusted external content isolation
│   │   ├── llm.py                    # Multi-provider LLM adapter (Ollama/Anthropic/OpenAI)
│   │   └── metrics.py                 # Per-run latency, tool calls, and cost tracking
│   ├── services/
│   │   ├── leadvault_agent.py         # Spec generator from ICP
│   │   ├── leadvault_mining_runner.py # Multi-actor mining execution orchestrator
│   │   ├── buying_intent_agent.py     # Signal detection & confidence scoring
│   │   ├── final_verifier.py          # Anti-hallucination verification pipeline
│   │   ├── ai_service.py              # LLM integration bridge
│   │   ├── rejected_audit_store.py    # Discarded lead audit repository
│   │   └── apify_service.py           # External LinkedIn/web scraping integration
│   ├── evaluation/
│   │   ├── gold_corpus.jsonl          # Benchmark test dataset for intent accuracy
│   │   ├── harness.py                 # Evaluation benchmark runner
│   │   └── reports/                   # Performance and precision reports
│   ├── tests/
│   │   ├── test_buying_intent_classifier.py  # Intent matching & scoring tests
│   │   ├── test_harness.py                   # Policy, tool-gateway & workflow tests
│   │   ├── test_adversarial.py               # SSRF, prompt injection, and bypass tests
│   │   └── conftest.py                       # Test fixtures and shared mocks
│   ├── config.py                      # Pydantic v2 application settings
│   ├── main.py                        # FastAPI application entrypoint
│   └── requirements.txt               # Backend dependencies
├── frontend/                          # Next.js 14 App Router UI
│   ├── app/
│   │   ├── page.tsx                   # Main interactive dashboard
│   │   ├── layout.tsx                 # Root layout
│   │   └── styles.css                 # Custom styling
│   └── package.json                   # Frontend dependencies
├── .claude/
│   └── launch.json                    # Claude Code runner configurations
├── AGENTS.md                          # Multi-agent specifications & boundaries
├── ARCHITECTURE.md                    # Detailed structural blueprints
├── BUSINESS_CONTEXT.md                # Product positioning and market context
├── CLAUDE.md                          # Claude development guidelines
└── HANDOVER_TO_CLAUDE.md              # Historical context and transition log
```

---

## 4. Test Suite & Validation Status

The full backend test suite passes completely with zero failures:

```bash
cd E:\Claude\leadvault
python -m pytest backend/tests -v
# 115 passed in 6.11s
```

### Test Coverage Highlights:
1. **Adversarial & Security (`test_adversarial.py`):**
   - Private IP and SSRF blocking (`127.0.0.1`, `10.0.0.0/8`, `192.168.0.0/16`, AWS/GCP cloud metadata `169.254.169.254`).
   - Non-HTTP scheme rejection (`file://`, `ftp://`).
   - Prompt injection resistance in untrusted post content.
2. **Buying Intent Classification (`test_buying_intent_classifier.py`):**
   - Procurement vs. recruitment vs. educational vs. vendor-promotion signal segregation.
   - Confidence scoring thresholds and bounded scores `[0.0, 1.0]`.
   - Strict export schema contract (no missing, extra, or renamed keys).
3. **Agentic Harness (`test_harness.py`):**
   - Enforces human confirmation before live mining starts (`confirmed=true`).
   - Enforces approval gates for Tier 1 high-impact exports.
   - Denial of outbound actions (unsolicited email, bulk outreach, CRM mutation).
   - Strict tenant data isolation.

---

## 5. How to Run Locally

### Backend (FastAPI on Port 8000)
```powershell
cd E:\Claude\leadvault\backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
# Copy environment configuration
copy .env.example .env
# Start development server
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend (Next.js on Port 3000)
```powershell
cd E:\Claude\leadvault\frontend
npm install
npm run dev -- -H 127.0.0.1 -p 3000
```

### Evaluation Benchmark
```powershell
cd E:\Claude\leadvault
python -m backend.evaluation.harness
```

---

## 6. Key Configuration Parameters

Managed via `backend/config.py` and `.env`:
- `APIFY_API_TOKENS`: Comma-delimited list of Apify API keys for LinkedIn scraping actors.
- `LEADVAULT_LLM_VALIDATION`: Toggle (`0` or `1`) for second-opinion LLM arbitration.
- `LEADVAULT_LLM_PROVIDER`: `ollama` (default local, cost-free) | `anthropic` | `openai`.
- `LEADVAULT_LLM_MODEL`: e.g. `mistral` (Ollama), `claude-3-5-sonnet-20241022` (Anthropic), or `gpt-4o-mini` (OpenAI).

---

## 7. Immediate Priorities for Claude Code

1. **Live Mining Smoke Test:** Run an end-to-end test with a sample client ICP using mock or live Apify actors.
2. **DIGIX Integration Contract:** LeadVault exposes clean HTTP endpoints (`/api/leadvault/plan`, `/api/leadvault/mine`, `/api/leadvault/specs`) so DIGIX can trigger mining sessions as an external microservice.
3. **Approval Queue UI:** Connect the frontend approvals dashboard to `/api/leadvault/harness/approvals` for interactive one-click human review.
