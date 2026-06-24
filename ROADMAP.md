# Roadmap

## Completed

- Standalone FastAPI backend created.
- Standalone Next.js frontend created.
- Client details form added.
- ICP CSV/XLSX upload path added.
- Mining brain generation added.
- Buyer-intent clusters, LinkedIn queries, Google/RFP queries, buyer phrases, and negative filters added.
- Confirm-before-mining gate added.
- LinkedIn paste-capture classification added.
- Accepted/rejected persistence added.
- Accepted/rejected CSV export added.
- Accepted/rejected XLSX export added.
- Tenant-aware saved run and rejected-audit history added.
- Tenant discovery endpoint and dashboard workspace switcher added.
- Downloadable ICP CSV template added.
- Expandable run details and live operation status added.
- API health checks and local runtime support added.
- LinkedIn search recency updated to past-week.
- **2026-06-24**: Fixed buyer-intent classifier to recognize "recommend" and "searching for" as procurement triggers.
- **2026-06-24**: Added 17-test regression suite covering classifier, scoring, export schema, and tenant isolation.
- **2026-06-24**: All regression tests passing. Backend compiles. Frontend typechecks.

## Outstanding

- Complete manual end-to-end browser UI walkthrough (computer-use access timed out).
- Harden Apify/public-web mining behavior and error reporting.
- Improve rejected-row explanations and classification confidence display.
- Add durable background jobs and resumable progress for long mining runs.
- Improve query deduplication and relevance ranking.

## Future Priorities

- Multi-tenant SaaS support.
- Supabase/PostgreSQL persistence.
- Redis/Celery background jobs.
- WebSocket job progress.
- Vector memory and semantic retrieval.
- Multi-agent orchestration.
- CRM sync and outreach automation.
