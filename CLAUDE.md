# LeadVaultAI Project Memory

Last updated: 2026-06-24

For the current takeover state, also read `HANDOVER_TO_CLAUDE.md`. It supersedes stale status or roadmap statements in older sections of this file.

This file is the permanent project memory for future Claude/Codex sessions. Read it before making changes. It explains what LeadVaultAI is, what has already been built, what must not be broken, and what should happen next.

## 1. Business Overview

LeadVaultAI is a standalone local application for ICP-aware procurement lead mining.

The product helps service businesses find companies and decision-makers who are actively seeking external help, such as agencies, consultants, vendors, implementation partners, outsourcing teams, or managed service providers.

LeadVaultAI is currently built for local use by the owner/user, with the long-term direction of becoming a multi-tenant SaaS module and an autonomous procurement intelligence operating system.

Primary business use cases:

- A digital marketing agency wants high-intent leads looking for marketing, SEO, paid media, content, automation, or GTM support.
- An AI automation agency wants leads seeking AI implementation partners, workflow automation support, AI SDR systems, or AI transformation help.
- A recruitment or staffing firm wants companies seeking external hiring, staffing, manpower, or recruitment vendor support.
- A fractional CMO, RevOps, or GTM consultant wants posts/signals from founders and executives seeking external consulting help.
- A consulting business wants procurement signals from public web, RFP pages, LinkedIn posts, community discussions, and vendor-request pages.

The system must not behave like a generic scraper. It should behave like a procurement intelligence layer that understands a client business, dynamically generates search logic, classifies buyer intent, rejects noise, and exports production-ready leads.

## 2. Product Vision

LeadVaultAI should become an autonomous ICP-driven procurement intelligence platform.

The long-term vision is an AI-native operating system that can:

- Understand any client business.
- Understand the client ICP, buyer psychology, services, positioning, and target markets.
- Dynamically generate buyer-intent clusters and procurement search logic.
- Discover where buyers for that ICP are active.
- Mine high-intent procurement signals from LinkedIn, public web, RFP portals, vendor request pages, and communities.
- Reject hiring, seller promotion, educational, and thought-leadership noise.
- Enrich and score accepted opportunities.
- Preserve the legacy lead export schema.
- Learn from accepted/rejected outcomes.
- Eventually support multi-agent orchestration, memory, semantic retrieval, multi-model routing, cost optimization, CRM sync, outreach automation, and tenant-level intelligence.

Immediate product objective:

Make the local LeadVaultAI app reliable enough for real client lead-mining runs: upload ICP, generate mining brain, confirm mining, classify pasted/imported/live candidates, export accepted/rejected rows.

## 3. Customer Problem

The user's existing lead-mining process had a quality failure:

- Hundreds of posts were evaluated.
- Only a few passed.
- Most accepted rows were not real buyer leads.
- False positives included job posts, vendor pitches, educational posts, and generic thought leadership.

Root causes:

- Search queries were too broad, such as "need help" or "need demand gen."
- Keyword filters treated "looking for developer" similarly to "looking for agency."
- Hiring detection was too narrow.
- There was no strong procurement-intent classifier.
- Rejected-post audit visibility was limited.

Core customer pain:

The customer does not need more scraped rows. They need fewer, higher-quality leads that represent actual external purchasing intent.

The product must answer:

"Who is actively looking to buy the services my client sells?"

Not:

"Who posted content mentioning those services?"

## 4. ICP

Primary ICP for LeadVaultAI itself:

- Agencies and consultants who sell services to businesses.
- Founders/operators running lead-generation, GTM, digital marketing, AI automation, RevOps, recruitment, staffing, and consulting businesses.
- Teams that need high-intent outbound lead lists without manually reading hundreds of posts.
- Users who are comfortable with local tools and want practical output tonight, not abstract architecture only.

Best-fit customer segments:

- AI automation agencies.
- Digital marketing agencies.
- SEO/content/performance marketing agencies.
- Recruitment/staffing firms.
- Fractional CMOs and GTM consultants.
- RevOps and HubSpot/Salesforce consultants.
- Web/app/software development agencies.
- B2B SaaS service providers.
- Consulting firms that sell implementation/transformation services.

Target buyer for accepted leads:

- Founder.
- CEO.
- CMO.
- VP Marketing.
- VP Sales.
- Head of Growth.
- Head of RevOps.
- Operations leader.
- Procurement leader.
- Transformation leader.
- Department owner seeking an external partner.

Valid buyer signals must include both:

1. Business pain / initiative / project demand.
2. External help seeking / procurement intent / vendor search.

## 5. User Personas

### Operator / Owner

The main local user. Wants to run LeadVaultAI for real client lead-mining jobs.

Needs:

- Simple local run commands.
- Upload ICP Excel/CSV.
- Enter client details.
- Generate queries and buyer intent logic.
- Confirm before spending API/Apify budget.
- Export accepted leads.
- See why rows were rejected.

### Agency Founder

Wants buyer leads for their agency.

Needs:

- Leads actively seeking services.
- Clear procurement signal.
- No job posts or vendor-promotion noise.
- Export rows compatible with existing outreach workflow.

### GTM / Sales Researcher

Uses the output for prospecting and outreach.

Needs:

- Accurate buyer signal.
- Company/contact fields.
- Source URL and exact query.
- Prioritization and notes.
- Exportable CSV/XLSX.

### Future Admin / SaaS User

Will manage multiple client workspaces.

Needs:

- Tenant switcher.
- Saved client profiles.
- Saved runs.
- Audit history.
- CRM sync.
- Role-based access.

## 6. Core Features

### Currently Implemented

- Local standalone FastAPI backend.
- Local standalone Next.js frontend.
- Client details form.
- ICP CSV/XLSX upload endpoint.
- ICP profile aggregation.
- Mining brain generation.
- Buyer-intent clusters.
- LinkedIn search queries.
- Google/RFP procurement queries.
- Buyer phrases.
- Negative filters.
- Python query bank.
- Confirmation gate before mining.
- Mining endpoint.
- Upload + Mine endpoint.
- LinkedIn paste-capture classification endpoint.
- Accepted lead rows.
- Rejected audit rows.
- Accepted/rejected CSV export in UI.
- Accepted/rejected XLSX export.
- Buying Intent Agent.
- Final verifier.
- Accepted export persistence.
- Rejected audit persistence.
- Spec persistence.
- Tenant discovery and workspace switcher.
- Tenant-aware accepted/rejected run history.
- Downloadable ICP CSV template.
- Expandable history details.
- Live operation status and error display.
- API health check.
- Frontend API status display.
- Past-week LinkedIn search URL freshness.

### Critical Procurement Logic

A valid lead requires both:

- Service/business pain, initiative, or project demand.
- External help seeking, vendor search, agency search, consultant search, outsourcing, implementation partner search, RFP/RFQ, or recommendation request.

Accept examples:

- "Looking for an AI implementation partner."
- "Need external RevOps consultant."
- "Seeking outbound automation agency."
- "Need SEO agency recommendation."
- "Looking for HubSpot implementation partner."
- "Can anyone recommend a content marketing agency?"

Reject examples:

- "We are hiring a software engineer."
- "Looking for a developer with 5+ years experience."
- "We help companies scale with AI."
- "DM me for SEO."
- "5 AI trends for 2026."
- "How to build GTM workflows."
- "Open for projects."
- "Job opening: marketing manager."

## 7. Technical Architecture

Project root:

```text
C:\Users\SOUMYA\leadvault
```

Backend:

```text
C:\Users\SOUMYA\leadvault\backend
```

Frontend:

```text
C:\Users\SOUMYA\leadvault\frontend
```

### Backend Stack

- Python.
- FastAPI.
- Pydantic settings.
- OpenPyXL for Excel parsing.
- Local filesystem persistence.
- Apify configuration hooks.
- Standard-library URL fetching for public web paths.

Important backend files:

```text
backend\main.py
backend\config.py
backend\api\routes\leadvault.py
backend\services\leadvault_agent.py
backend\services\leadvault_mining_runner.py
backend\services\buying_intent_agent.py
backend\services\final_verifier.py
backend\services\accepted_export_store.py
backend\services\rejected_audit_store.py
backend\services\leadvault_spec_store.py
```

Important backend routes:

```text
GET  /api/leadvault/health
POST /api/leadvault/plan
POST /api/leadvault/upload
GET  /api/leadvault/specs
POST /api/leadvault/mine
POST /api/leadvault/mine-upload
POST /api/leadvault/linkedin-capture
POST /api/leadvault/linkedin-capture-upload
```

Mining requires:

```json
{
  "confirmed": true
}
```

This confirmation gate exists to prevent accidental API/Apify spend.

### Frontend Stack

- Next.js.
- React.
- TypeScript.
- Local CSS.
- Lucide icons.

Important frontend files:

```text
frontend\app\page.tsx
frontend\app\styles.css
frontend\app\layout.tsx
frontend\package.json
```

The current UI workflow:

```text
Client Details -> ICP Upload -> Generate Brain -> Confirm -> Mine -> Review/Export
```

### Runtime URLs

Backend:

```text
http://127.0.0.1:8000
```

Backend health:

```text
http://127.0.0.1:8000/api/leadvault/health
```

Frontend:

```text
http://127.0.0.1:3000
```

### Local Run Commands

Run backend:

```powershell
cd C:\Users\SOUMYA\leadvault\backend
C:\Users\SOUMYA\AppData\Local\Python\pythoncore-3.14-64\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Run frontend:

```powershell
cd C:\Users\SOUMYA\leadvault\frontend
npm run dev
```

Backend compile:

```powershell
cd C:\Users\SOUMYA\leadvault\backend
C:\Users\SOUMYA\AppData\Local\Python\pythoncore-3.14-64\python.exe -m py_compile main.py api\routes\leadvault.py services\leadvault_mining_runner.py
```

Frontend typecheck:

```powershell
cd C:\Users\SOUMYA\leadvault\frontend
node_modules\.bin\tsc.cmd --noEmit
```

## 8. Current Status

LeadVaultAI is functional as a local prototype/application with verified regression tests.

Working:

- Backend imports and compiles (Python 3.14).
- All API routes respond (health, plan, upload, mine, linkedin-capture, tenants, runs, export).
- Frontend renders and typechecks without errors (Next.js).
- Client details form and ICP upload functional.
- Mining brain generation working.
- LinkedIn paste capture classification working with 17 automated regression tests.
- Accepted/rejected CSV/XLSX export functional with exact schema preservation.
- Backend persistence stores functional for specs, accepted exports, rejected audits.
- Tenant-aware workspace switcher working.

Verified behavior (via regression tests):

- ✓ Procurement intent recognized:
  - "Looking for an AI implementation partner"
  - "Can anyone recommend a good SEO agency?" (fixed in commit 7dc1a86)
  - "Seeking an implementation partner"
  
- ✓ Noise correctly rejected:
  - Recruitment: "We are hiring a Python developer, 5+ years experience"
  - Seller promo: "We help brands with AI. DM me for services"
  - Thought leadership: "5 AI trends for 2026"

Recent fixes:

- **2026-06-24**: Fixed buyer-intent classifier to recognize "recommend" and "searching for" as procurement triggers (commit 7dc1a86).
- **2026-06-24**: Added comprehensive regression test suite with 17 test cases covering classifier, scoring, and export schema.

Important limitation:

Full browser-login LinkedIn scraping is not complete. The safe current LinkedIn workflow is:

1. Generate LinkedIn queries.
2. Search LinkedIn manually or through approved tools.
3. Paste/import post text into LinkedIn Capture.
4. Classify accepted/rejected rows.
5. Export accepted leads.

Apify/public-web hooks exist, but live scraping reliability needs more hardening.

## 9. Project Goals

Immediate goals:

- Perform a fresh manual browser walkthrough with a real client ICP.
- Build classifier and export regression tests.
- Harden provider-dependent live mining and its error reporting.
- Improve query quality, deduplication, and rejected-row explanations.
- Add durable background execution for long mining runs.

Near-term goals:

- Improve Apify/public-web mining reliability.
- Improve rejected audit explainability.
- Make LinkedIn paste/import workflow smoother.
- Harden the Buying Intent Agent with a real regression corpus.
- Move local persistence to SQLite before multi-user deployment.

Long-term goals:

- Multi-tenant SaaS.
- Supabase/PostgreSQL persistence.
- Redis/Celery background jobs.
- WebSocket job progress.
- Semantic/vector memory.
- LangGraph multi-agent orchestration.
- MCP tool-routing layer.
- Multi-LLM routing through OpenRouter or similar.
- Local embeddings and low-cost model support.
- CRM sync.
- Outreach generation.
- Learning loop from accepted/rejected outcomes.

## 10. Constraints

### Export Schema Constraint

Accepted leads must preserve this exact schema:

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

Do not rename fields.
Do not remove fields.
Do not redesign the export schema without explicit user approval.

### Quality Constraint

Precision matters more than volume.

The product should export fewer leads if necessary, but they must be real procurement/buyer-intent leads.

### Cost Constraint

Prefer low-cost operation:

- Deterministic logic before LLMs.
- Local parsing/classification where possible.
- Confirmation before API/Apify spend.
- Cache/reuse generated brain and queries.
- Limit live queries by budget controls.

### Compliance Constraint

Be careful with LinkedIn automation. Do not claim full LinkedIn browser-login scraping is done unless it is actually implemented and approved. Current safe workflow is query generation plus paste/import classification and Apify/public-web hooks.

### Scope Constraint

Do not rewrite the entire application unless explicitly asked.

Preserve working local functionality first.

## 11. Success Metrics

Lead quality metrics:

- Accepted lead precision: target 80-95%+ real buyer/procurement intent.
- False positive rate: keep low for hiring, seller promotion, and educational content.
- Rejected audit usefulness: each rejected row should have a clear reason.
- Procurement confidence: accepted rows should include explainable buyer signals.

Workflow metrics:

- Time from ICP upload to generated brain: under 1 minute for normal files.
- Time from candidate import/paste to accepted/rejected review: under 1 minute for small batches.
- User can export accepted leads without editing code.
- User can run the app locally with documented commands.

Business metrics:

- Leads are usable for outreach.
- Export remains compatible with existing Python/CSV/Excel workflow.
- Client-specific queries feel relevant to the uploaded ICP and services.
- Manual review burden decreases significantly.

## 12. Coding Standards

### Python

- Keep service files modular.
- Keep route handlers thin where possible.
- Use clear function names.
- Avoid hidden global state unless it is config/cache.
- Validate user inputs.
- Preserve current API contracts.
- Use deterministic logic where it improves cost and reliability.
- Keep candidate classification explainable.
- Avoid broad exception swallowing unless the error is recorded in audit/status.

### TypeScript / React

- Keep UI state clear and explicit.
- Avoid over-abstracting components while the product is evolving.
- Type important API responses.
- Show useful user-facing errors.
- Disable buttons during loading/mining.
- Preserve confirmation gate before mining.
- Do not introduce unnecessary heavy dependencies.

### File Editing

- Prefer targeted changes.
- Do not break working endpoints.
- Do not rename core files casually.
- Run compile/typecheck after meaningful backend/frontend changes.

## 13. Design Standards

LeadVaultAI should feel like an enterprise-grade AI operations dashboard, not a generic form app.

Current design direction:

- Dark command-center UI.
- Clear staged workflow.
- Strong visual distinction between client input, mining brain, controls, and export center.
- Obvious API status.
- Obvious confirmation before mining.
- Accepted/rejected review panels.

UX principles:

- The user should always know what step they are on.
- The user should see why mining is blocked.
- The user should not need to touch code for normal use.
- Export controls should be visible after results.
- Errors should explain how to fix the issue.

Design must support:

- Client details entry.
- File upload.
- Review generated queries/phrases.
- Confirm before spend.
- Mining progress/status.
- Accepted/rejected review.
- Export.

## 14. Deployment Standards

Current deployment is local-first.

Local standards:

- Backend on port 8000.
- Frontend on port 3000.
- Secrets only in `backend\.env`.
- Do not commit real API keys.

Future deployment direction:

- Docker Compose.
- Backend service.
- Frontend service.
- Optional Redis/Celery.
- Optional PostgreSQL/Supabase.
- Optional Qdrant/Chroma.
- VPS/Render/Railway deployment.

Before production deployment:

- Add environment variable documentation.
- Add proper `.env.example`.
- Add secret handling.
- Add CORS configuration by environment.
- Add auth.
- Add rate limiting.
- Add job queue for long mining runs.
- Add persistent database instead of local files only.

## 15. Documentation Standards

Documentation should be practical and operator-focused.

Always document:

- What the feature does.
- How to run it locally.
- What inputs it expects.
- What outputs it produces.
- Any cost/API implications.
- Any known limitations.

Important docs:

- `README.md`: lightweight project intro and run instructions.
- `CLAUDE.md`: permanent detailed project memory.
- Future docs should include:
  - ICP upload template.
  - API reference.
  - Export schema reference.
  - Troubleshooting guide.
  - Filter/classifier tuning guide.
  - Deployment guide.

## 16. Decision Log

### 2026-06-08 to 2026-06-10: Standalone Split

Decision:

LeadVaultAI should exist as a standalone local app in `C:\Users\SOUMYA\leadvault`, separate from the broader DIGIX ecosystem.

Reason:

The user needs a focused tool that can be tested and developed independently.

### 2026-06-08 to 2026-06-10: Preserve Legacy Export Schema

Decision:

Accepted rows must preserve the existing lead export schema.

Reason:

The user already has existing Python, CSV, Excel, and workflow expectations around those fields.

### 2026-06-08 to 2026-06-10: Confirm Before Mining

Decision:

Mining endpoints require `confirmed=true`.

Reason:

Live mining can spend Apify/API resources. The user must review the generated mining brain before execution.

### 2026-06-08 to 2026-06-10: Precision Over Volume

Decision:

The classifier should aggressively reject hiring, seller promotion, and educational content.

Reason:

The previous failure mode was too many false positives, especially job posts and vendor pitches.

### 2026-06-08 to 2026-06-10: Past-Week LinkedIn Freshness

Decision:

Generated LinkedIn search URLs use `past-week` instead of `past-month`.

Reason:

Procurement opportunities move quickly. Fresher signals are more actionable.

### 2026-06-08 to 2026-06-10: Safe LinkedIn Workflow

Decision:

Use generated LinkedIn search queries and paste/import capture rather than claiming full LinkedIn login scraping.

Reason:

This is safer, more transparent, and already functional for local testing.

### 2026-06-10: UI Rebuild

Decision:

The frontend was rebuilt into a proper workflow:

```text
Client Details -> ICP Upload -> Generate Brain -> Confirm -> Mine -> Review/Export
```

Reason:

The earlier UI did not clearly allow client ICP upload and mining flow for a real user.

## 17. Future Roadmap

### Phase 1: Local Usability Hardening

- Saved run history UI completed.
- Saved accepted/rejected audit viewer completed.
- Sample ICP template download completed.
- API status and operation error display completed.
- Tenant switcher completed.
- Add copy/open buttons for generated LinkedIn queries.
- Add import CSV of LinkedIn posts.
- Improve manual LinkedIn capture review.

### Phase 2: Classification Quality

- Expand procurement phrase library.
- Strengthen job-post detection.
- Strengthen seller-promotion detection.
- Add confidence explanations.
- Add category labels:
  - PROCUREMENT_BUYER
  - RECRUITMENT
  - SELLER_PROMOTION
  - EDUCATIONAL
  - THOUGHT_LEADERSHIP
  - NEWS
  - UNKNOWN
- Add optional LLM validation layer for borderline cases.
- Add rejected-post audit tuning UI.

### Phase 3: Live Mining Reliability

- Harden Apify actor integrations.
- Add actor fallback.
- Add budget controls and status reporting.
- Add public web search/RFP discovery improvements.
- Add dedupe by URL/text/company.
- Add retry/backoff.
- Add live progress updates.

### Phase 4: Persistence and Multi-Tenant SaaS

- Add SQLite or PostgreSQL/Supabase persistence.
- Add tenant profiles.
- Add saved plans.
- Add saved runs.
- Add saved exports.
- Add CRM sync record persistence.
- Add auth.
- Add RBAC.

### Phase 5: Agentic AI Architecture

- Add LangGraph orchestration.
- Add agent roles:
  - ICP Analyzer Agent.
  - Procurement Signal Agent.
  - Query Generator Agent.
  - Search Platform Discovery Agent.
  - Scraping Orchestrator Agent.
  - Procurement Classifier Agent.
  - Decision Maker Agent.
  - Semantic Matching Agent.
  - Lead Scoring Agent.
  - Enrichment Agent.
  - Outreach Agent.
  - Memory Agent.
  - Reflection Agent.
  - Cost Governor Agent.
  - Tool Router Agent.
- Add MCP tool-router layer.
- Add reasoning traces and workflow checkpoints.

### Phase 6: Semantic Memory and RAG

- Add local embeddings.
- Add Qdrant/Chroma.
- Store:
  - successful queries.
  - accepted leads.
  - rejected examples.
  - procurement phrases.
  - service mappings.
  - industry-specific signals.
- Add semantic query explorer.
- Add vector memory explorer.
- Add self-improving retrieval from accepted/rejected outcomes.

### Phase 7: Enrichment and Outreach

- Add enrichment APIs:
  - Apollo.
  - Clay.
  - Hunter.
  - Clearbit.
  - BuiltWith.
- Add email and LinkedIn outreach copy.
- Add outreach status tracking.
- Add CRM sync.
- Add follow-up sequence generation.

## Immediate Next-Step Recommendation

If taking over this project, do not start with a full architecture rewrite.

Start with:

1. Run backend compile.
2. Run frontend typecheck.
3. Start backend and frontend.
4. Test client details -> generate brain.
5. Test ICP upload -> generate brain.
6. Test LinkedIn paste capture.
7. Add automated regression tests for classification, tenant isolation, and exports.
8. Harden live mining reliability, retries, dedupe, and source-level errors.

The user wants a usable lead-mining tool first. Big agent architecture comes after the local workflow is reliable.
