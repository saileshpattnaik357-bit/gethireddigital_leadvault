# LeadVaultAI Handover to Claude

## Handover Snapshot

- Date: 2026-06-24
- Local project: `C:\Users\SOUMYA\leadvault`
- Primary GitHub repository: `https://github.com/saileshpattnaik357-bit/gethireddigital_leadvault`
- GitHub default branch: `main`
- Verified handover commit before this document: `ccbb526`
- Local development branch: `codex/leadvault-launch`
- Backup remote: `https://github.com/rxgptgethiredglobal/leadvault`

Read these files before editing:

1. `CLAUDE.md`
2. `HANDOVER_TO_CLAUDE.md`
3. `ARCHITECTURE.md`
4. `ROADMAP.md`
5. `DECISIONS.md`
6. `README.md`

## Executive Summary

LeadVaultAI is a standalone, local-first procurement-intelligence and lead-mining application. It accepts a client profile or ICP spreadsheet, generates client-specific procurement searches, mines or imports candidate signals, rejects recruitment/seller/educational noise, and exports accepted leads in a fixed legacy schema.

The working product is a FastAPI backend plus a Next.js frontend. It includes a Buying Intent Agent and deterministic final verifier, but it is not yet the full LangGraph/RAG/MCP operating system described in the long-term vision.

The current priority is reliability and lead precision, not architectural expansion.

## Business Objective

Find companies and decision-makers who are actively seeking an external:

- agency
- consultant
- vendor
- implementation partner
- outsourced team
- managed service provider

A valid lead requires both:

1. A business pain, initiative, or active project.
2. Evidence that the buyer seeks external help.

The engine must reject:

- employee recruitment and job posts
- service-provider self-promotion
- generic discussions
- educational content
- thought leadership
- news without procurement intent

## Completed Product Flow

The operator can:

1. Select or create a tenant/client workspace.
2. Enter client company details, services, ICP, geography, and positioning.
3. Download an ICP CSV template.
4. Upload a CSV/XLSX ICP file.
5. Generate a deterministic mining brain.
6. Optionally request LLM refinement when configured.
7. Review generated LinkedIn and Google/RFP queries.
8. Confirm the mining brain before API expenditure.
9. Run client-detail mining or upload-and-mine.
10. Paste LinkedIn content for buyer-intent classification.
11. Review accepted and rejected rows.
12. Inspect tenant-aware run history.
13. Export accepted or rejected data as CSV/XLSX.

## Implemented Backend

Main files:

- `backend/main.py`
- `backend/config.py`
- `backend/api/routes/leadvault.py`
- `backend/services/leadvault_agent.py`
- `backend/services/leadvault_mining_runner.py`
- `backend/services/buying_intent_agent.py`
- `backend/services/final_verifier.py`
- `backend/services/accepted_export_store.py`
- `backend/services/rejected_audit_store.py`
- `backend/services/leadvault_spec_store.py`

Available endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/leadvault/health` | Health check |
| POST | `/api/leadvault/plan` | Generate a mining brain |
| POST | `/api/leadvault/upload` | Parse an ICP file and generate a brain |
| GET | `/api/leadvault/specs` | Read saved mining specifications |
| GET | `/api/leadvault/runs` | Read tenant-aware accepted/rejected history |
| GET | `/api/leadvault/tenants` | Discover saved tenant workspaces |
| GET | `/api/leadvault/export/{kind}` | Download accepted/rejected XLSX |
| POST | `/api/leadvault/mine` | Mine from client details |
| POST | `/api/leadvault/mine-upload` | Upload ICP and mine |
| POST | `/api/leadvault/linkedin-capture` | Classify pasted candidate rows |
| POST | `/api/leadvault/linkedin-capture-upload` | Classify uploaded candidate rows |

Mining routes require `confirmed=true`.

## Implemented Frontend

Main files:

- `frontend/app/page.tsx`
- `frontend/app/styles.css`
- `frontend/app/layout.tsx`

Implemented UI:

- API health indicator
- tenant switcher
- new-client workspace flow
- client details form
- ICP CSV/XLSX upload
- ICP template download
- mining-brain metrics and query review
- confirmation gate
- mining controls and budget limits
- operation status display
- LinkedIn paste capture
- accepted/rejected tables
- expandable run-history details
- CSV and XLSX export center

## Exact Export Contract

Do not rename, remove, or reorder accepted-lead fields without explicit approval:

```text
Date Added
Estimated Deal Value
Client Name
Client LinkedIn Profile URL
Title
Company Name
Company Website
Industry
Region
Client Email
Client Phone
Number of Employees
Lead Source
Client Intent Signal
Client Exact Query
Client Query Post URL
Priority
Service Category
Outreach Status
Ajroni Offer
Notes
```

## Persistence

Current persistence is local JSON:

- `backend/runtime/leadvault_specs.json`
- `backend/runtime/accepted_exports.json`
- `backend/runtime/rejected_audits.json`

These files are intentionally ignored by Git because they can contain client and lead data.

The repository does not yet use SQLite, PostgreSQL, Supabase, Redis, or Celery.

## Configuration and Secrets

Use `backend/.env.example` as the template.

Supported configuration:

```env
FRONTEND_URL=http://localhost:3000
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
APIFY_API_TOKENS=
APIFY_LINKEDIN_ACTORS=supreme_coder/linkedin-post,harvestapi/linkedin-post-search,get-leads/linkedin-scraper
```

Real secrets belong only in `backend/.env`, which is ignored by Git.

Never commit:

- `.env`
- API keys
- Apify tokens
- runtime lead data
- accepted/rejected audit files

## Local Startup

Backend:

```powershell
cd C:\Users\SOUMYA\leadvault\backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd C:\Users\SOUMYA\leadvault\frontend
npm install
npm run dev -- -H 127.0.0.1 -p 3000
```

Open:

```text
http://127.0.0.1:3000
```

API:

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
```

## Verification Completed

The following passed before handover:

- Python module compilation.
- Frontend TypeScript checking.
- Next.js production build.
- FastAPI health, tenants, runs, plan, capture, and export route tests.
- Buyer example accepted.
- Recruitment example rejected.
- Accepted and rejected XLSX files opened as valid ZIP/XLSX payloads.
- Frontend and backend returned HTTP `200`.
- Rendered HTML contained the new workspace, template, export, and history controls.

Post-handover Claude verification (2026-06-24):

- ✅ Backend compiles without errors (Python 3.14).
- ✅ Frontend typechecks without errors (Next.js/TypeScript).
- ✅ All 17 regression tests passing:
  - 8 final verifier tests (buyer intent recognition, recruitment/seller/educational rejection).
  - 5 buying intent scoring tests.
  - 3 export schema validation tests.
  - 1 tenant isolation test.
- ✅ Defect fixed: Added "recommend" and "searching for" to procurement trigger words.
- ✅ Verified fix works: "Can anyone recommend a good SEO agency?" now correctly accepted.

Known verification limitation:

- Computer-use browser automation request timed out (request_access on Google Chrome).
- Full manual browser UI walkthrough via computer-use not completed.
- API and programmatic testing confirmed; visual walkthrough recommended for future session.

## Truth Boundary

Implemented:

- deterministic ICP analysis and query generation
- optional LLM refinement hooks
- procurement/buying-intent classification
- final validation
- Apify/public-web mining hooks
- local tenant-aware persistence
- exports and audit history

Not yet complete:

- reliable authenticated LinkedIn browser scraping
- production-grade Apify actor reliability
- Google/RFP provider integration with guaranteed coverage
- background job queue
- resumable mining
- WebSocket progress
- enrichment APIs
- CRM sync
- automated outreach
- LangGraph agent orchestration
- MCP tool discovery
- vector database/RAG memory
- local embedding pipeline
- multi-LLM cost router
- authentication/RBAC
- Supabase/PostgreSQL deployment

Do not describe these pending capabilities as implemented.

## Known Risks

1. Live mining quality depends on source/provider availability and credentials.
2. JSON stores are adequate for local use but not concurrent multi-user use.
3. Classification needs a regression corpus drawn from real accepted and rejected posts.
4. Query generation can produce repetitive phrases and needs relevance/deduplication tuning.
5. Long synchronous mining calls can block requests.
6. Rejected XLSX values may contain JSON-serialized nested classifier data by design.
7. LinkedIn automation must be implemented with legal, platform, and account-safety constraints.

## Recommended Next Work

Work in this order:

1. Run the complete local UI manually with a real sample ICP.
2. Build a permanent regression fixture of buyer, recruitment, seller, and educational posts.
3. Add backend tests for the classifier, exact export schema, tenant isolation, and nested XLSX values.
4. Improve Apify/public-web error reporting, retries, deduplication, and source attribution.
5. Add durable background jobs and progress polling.
6. Replace JSON stores with SQLite first, then PostgreSQL/Supabase when SaaS deployment is approved.
7. Add enrichment and CRM integrations only after mining precision is measured.
8. Add LangGraph/MCP/vector memory only where they solve measured workflow limitations.

## Claude Working Rules

- Inspect source before changing architecture.
- Preserve the accepted export schema exactly.
- Preserve the `confirmed=true` cost gate.
- Prefer precision over lead volume.
- Keep rejected rows explainable.
- Do not commit secrets or runtime data.
- Do not rewrite working modules merely to introduce an agent framework.
- Run backend compile, frontend typecheck, production build, and focused API tests after changes.
- Keep `CLAUDE.md`, `ROADMAP.md`, and this handover updated when project state changes.

## Git Workflow

Primary target repository:

```text
https://github.com/saileshpattnaik357-bit/gethireddigital_leadvault
```

Current remote names:

```text
gethired -> primary handover repository
origin   -> backup repository owned by rxgptgethiredglobal
```

Before pushing:

```powershell
git status -sb
git diff --check
git remote -v
```

Do not force-push or overwrite unrelated history.

