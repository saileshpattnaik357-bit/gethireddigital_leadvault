# Claude Handover Prompt for LeadVaultAI

Copy this entire prompt into Claude / Claude Code and ask it to continue from the local project folder.

```markdown
You are taking over the LeadVaultAI project from the local folder:

C:\Users\SOUMYA\leadvault

Do not start from scratch. Inspect the current project first, then continue development from the existing implementation.

## First Step

Before changing code, read these files completely in this order:

1. CLAUDE.md
2. HANDOVER_TO_CLAUDE.md
3. CLAUDE_TAKEOVER_PROMPT.md
4. README.md
5. ARCHITECTURE.md
6. ROADMAP.md
7. DECISIONS.md
8. BUSINESS_CONTEXT.md
9. TECH_STACK.md

After reading the docs, inspect the backend and frontend source code directly. Treat the actual source code as authoritative if documentation is outdated.

## Project Summary

LeadVaultAI is an autonomous ICP-driven procurement intelligence and lead-mining platform for GetHired Digital / Ajroni-style clients.

It is not intended to be a simple scraper or static workflow tool.

The product goal is to:

- accept client details and ICP files
- understand the client's services, ICP, buyer personas, pain points, and procurement language
- generate ICP-specific buying-intent logic
- generate search/query logic for procurement opportunities
- mine or import candidate buyer signals
- reject hiring posts, seller posts, thought leadership, education, news, and generic content
- validate buyer intent using the Buying Intent Agent and final verifier
- store accepted and rejected audit rows
- export accepted leads in the existing required schema
- support tenant-aware client workspaces
- eventually support live LinkedIn, Google, RFP, and procurement-source mining

## Current Implementation

The app currently exists as a local standalone project:

Local folder:

```text
C:\Users\SOUMYA\leadvault
```

Primary GitHub repository:

```text
https://github.com/saileshpattnaik357-bit/gethireddigital_leadvault
```

Current branch/workflow:

- local branch: codex/leadvault-launch
- pushed to GitHub main
- last known handover commit: 5a73d00 Add Claude project handover

## Backend

The backend is a FastAPI app with local-first JSON persistence.

Important backend files:

- backend/main.py
- backend/config.py
- backend/api/routes/leadvault.py
- backend/services/leadvault_agent.py
- backend/services/leadvault_mining_runner.py
- backend/services/buying_intent_agent.py
- backend/services/final_verifier.py
- backend/services/accepted_export_store.py
- backend/services/rejected_audit_store.py
- backend/services/leadvault_spec_store.py
- backend/services/universal_engine.py

Current backend capabilities include:

- health endpoint
- client plan generation
- ICP CSV/XLSX upload
- tenant-aware plan/run storage
- Buying Intent Agent
- final lead verifier
- accepted lead persistence
- rejected audit persistence
- accepted/rejected CSV export
- accepted/rejected XLSX export
- LinkedIn paste/import classification flow
- confirm-before-mining API spend gate

## Frontend

The frontend is a Next.js / React UI.

Important frontend files:

- frontend/app/page.tsx
- frontend/app/styles.css
- frontend/app/layout.tsx

Current frontend capabilities include:

- client details form
- ICP upload area
- tenant switcher
- new client workspace flow
- mining confirmation flow
- operation status
- accepted/rejected export center
- history/audit panels
- expandable run details
- ICP CSV template download

## Current API Routes

Expected LeadVault routes include:

- GET /api/leadvault/health
- POST /api/leadvault/plan
- POST /api/leadvault/upload
- GET /api/leadvault/specs
- GET /api/leadvault/runs
- GET /api/leadvault/tenants
- GET /api/leadvault/export/{kind}
- POST /api/leadvault/mine
- POST /api/leadvault/mine-upload
- POST /api/leadvault/linkedin-capture
- POST /api/leadvault/linkedin-capture-upload

## Required Export Schema

Do not change this schema. Accepted leads must remain compatible with the existing Python/Excel/CSV workflow.

Accepted export fields:

- Date Added
- Estimated Deal Value
- Client Name
- Client LinkedIn Profile URL
- Title
- Company Name
- Company Website
- Industry
- Region
- Client Email
- Client Phone
- Number of Employees
- Lead Source
- Client Intent Signal
- Client Exact Query
- Client Query Post URL
- Priority
- Service Category
- Outreach Status
- Ajroni Offer
- Notes

## Core Qualification Rule

A valid lead must contain both:

1. business pain or initiative
2. external help-seeking / procurement intent

Accept examples:

- looking for agency
- looking for consultant
- looking for vendor
- need implementation partner
- need external support
- outsourcing request
- RFP/RFQ
- vendor recommendation request
- agency recommendation request

Reject examples:

- job posts
- hiring posts
- employee recruitment
- seller promotions
- agencies pitching services
- educational posts
- thought leadership
- news
- generic discussions
- people offering services

Precision matters more than volume.

## Known Completed Work

Already implemented:

- standalone LeadVault app
- FastAPI backend
- Next.js frontend
- local env separation
- local git repo
- tenant-aware saved plans and audit records
- tenant switcher
- new client workspace flow
- Buying Intent Agent
- final verifier
- accepted vs rejected audit trails
- accepted/rejected CSV export
- accepted/rejected XLSX export
- real XLSX file download
- ICP upload parsing
- ICP template download
- mining confirmation flow
- LinkedIn paste/import classification
- basic Apify/public-web hooks
- debug and audit storage
- project memory docs
- GitHub push to primary repo

Previously verified:

- backend compile passed
- API routes loaded
- frontend typecheck passed
- Next production build passed
- plan generation worked
- capture/import flow worked
- accepted/rejected classification worked on sample data
- XLSX exports produced valid Excel files

## Known Limitations / Not Fully Done

Do not claim these are complete unless you implement and verify them:

- reliable authenticated LinkedIn scraping
- production-grade Google scraping
- production-grade RFP/procurement portal scraping
- enrichment pipeline using Apollo/Clay/Clearbit/Hunter/etc.
- CRM sync
- automated outreach execution
- Redis/Celery background jobs
- WebSocket progress updates
- Supabase/PostgreSQL persistence
- LangGraph orchestration
- MCP tool routing
- RAG/vector memory
- Qdrant/Chroma/Weaviate integration
- OpenRouter multi-LLM routing
- Ollama/local LLM routing
- auth/login/RBAC
- production deployment hardening

## Development Rules

- Preserve the exact accepted lead export schema.
- Do not commit secrets.
- Do not commit backend/.env.
- Do not commit Apify tokens or API credentials.
- Do not commit backend/runtime client data.
- Keep runtime data ignored.
- Keep the confirm-before-mining flow before any paid/API scraping.
- Prefer deterministic filters and local logic before LLM calls.
- Prioritize precision over lead volume.
- Update documentation when changing architecture or behavior.
- Commit meaningful, scoped changes.
- Push completed work to GitHub.

## Suggested Local Verification

Backend compile:

```powershell
cd C:\Users\SOUMYA\leadvault
python -m py_compile backend\main.py backend\api\routes\leadvault.py backend\services\accepted_export_store.py backend\services\rejected_audit_store.py
```

Run backend:

```powershell
cd C:\Users\SOUMYA\leadvault\backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Run frontend:

```powershell
cd C:\Users\SOUMYA\leadvault\frontend
npm run dev -- -H 127.0.0.1 -p 3000
```

Frontend typecheck:

```powershell
cd C:\Users\SOUMYA\leadvault\frontend
$env:NODE_OPTIONS='--max-old-space-size=4096'
.\node_modules\.bin\tsc.cmd --noEmit --pretty false
```

Frontend build:

```powershell
cd C:\Users\SOUMYA\leadvault\frontend
$env:NODE_OPTIONS='--max-old-space-size=4096'
npm run build
```

Health check:

```powershell
curl.exe http://127.0.0.1:8000/api/leadvault/health
```

## Recommended Next Work

Focus next on making the product actually usable for a client lead-mining session tonight:

1. Verify local backend and frontend startup.
2. Test client details + ICP upload from the UI.
3. Test generated mining plan.
4. Test pasted LinkedIn/sample post capture.
5. Confirm accepted/rejected rows persist.
6. Confirm CSV/XLSX downloads work.
7. Improve the live mining path only after the local upload/import flow is stable.
8. Add safer scraping adapters behind the confirm-before-mining gate.
9. Move persistence from local JSON to SQLite or PostgreSQL/Supabase when stable.
10. Continue toward LangGraph/MCP/RAG only after the core workflow is reliable.

## Immediate Mission

Continue from the current implementation and make LeadVaultAI usable end-to-end:

- upload client ICP/details
- generate procurement intelligence
- mine/import candidate signals
- classify buying intent
- reject noise
- save accepted/rejected audits
- export accepted leads
- keep the UI clear enough for the user to test tonight

Do not rebuild the whole system. Stabilize and extend what already exists.
```

