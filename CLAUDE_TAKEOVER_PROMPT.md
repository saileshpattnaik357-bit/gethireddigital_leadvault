# Claude Takeover Prompt

Use this prompt in a new Claude Code session opened at `C:\Users\SOUMYA\leadvault`.

```text
You are taking over development of LeadVaultAI.

Repository:
https://github.com/saileshpattnaik357-bit/gethireddigital_leadvault

Local folder:
C:\Users\SOUMYA\leadvault

Before making any changes, read these files completely:
1. CLAUDE.md
2. HANDOVER_TO_CLAUDE.md
3. ARCHITECTURE.md
4. ROADMAP.md
5. DECISIONS.md
6. README.md

Then inspect the actual backend and frontend source. Treat the source code as authoritative if documentation differs.

Product objective:
LeadVaultAI must find high-intent procurement leads for any uploaded client ICP. A lead is valid only when it contains both a business pain/initiative and evidence that the buyer seeks external help from an agency, consultant, vendor, implementation partner, outsourced team, or managed service provider.

Critical rules:
- Preserve the exact accepted-lead export schema documented in HANDOVER_TO_CLAUDE.md.
- Preserve the confirmed=true gate before mining/API spend.
- Prioritize precision over volume.
- Reject recruitment, seller promotion, education, thought leadership, and generic discussions.
- Never commit backend/.env, API credentials, Apify tokens, or backend/runtime client data.
- Do not claim LangGraph, MCP, RAG, authenticated LinkedIn scraping, CRM sync, or enrichment are complete; they are roadmap items.
- Do not perform a broad rewrite before validating the current working flow.

Current implementation:
- FastAPI backend.
- Next.js/React frontend.
- CSV/XLSX ICP upload.
- Client-specific mining-brain generation.
- Buying Intent Agent and final verifier.
- Public-web/Apify mining hooks.
- LinkedIn paste/import classification.
- Tenant switcher and local tenant-aware JSON persistence.
- Accepted/rejected CSV and XLSX exports.
- Run history and audit details.

First assignment:
1. Run git status and inspect current remotes/branch.
2. Run Python compile checks.
3. Run frontend TypeScript check and production build.
4. Start backend on 127.0.0.1:8000 and frontend on 127.0.0.1:3000.
5. Perform a manual browser walkthrough:
   - create/select a workspace
   - download the ICP template
   - upload a sample ICP
   - generate the mining brain
   - confirm it
   - classify one real buyer example and one recruitment example
   - inspect accepted/rejected history
   - download accepted and rejected XLSX
6. Record any defects with file and line references.
7. Fix verified defects with focused changes.
8. Add regression tests for buyer-vs-job classification, tenant isolation, exact export fields, and nested rejected XLSX values.
9. Update CLAUDE.md, HANDOVER_TO_CLAUDE.md, and ROADMAP.md with the verified state.

Do not stop after writing a plan. Continue through implementation and verification unless genuinely blocked by missing credentials or permissions. Clearly separate verified working behavior from provider-dependent behavior.
```

