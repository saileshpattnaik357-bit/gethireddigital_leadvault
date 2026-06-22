# Decisions

## Standalone App

Decision:

- Keep LeadVaultAI as a standalone local project in `C:\Users\SOUMYA\leadvault`.

Reason:

- The user needs an independent tool that can be tested and evolved without depending on DIGIX internals.

## Preserve Export Schema

Decision:

- Preserve the legacy accepted-lead export schema exactly.

Reason:

- The existing Python export workflow, CSV output, and downstream usage already depend on those fields.

## Confirm Before Mining

Decision:

- Require `confirmed=true` before mining runs.

Reason:

- Mining may consume Apify/API budget and should only run after the user reviews the generated brain.

## Precision Over Volume

Decision:

- Reject hiring, seller promotion, educational, and generic posts aggressively.

Reason:

- The main problem being solved is false positives, not lead volume.

## Past-Week Search Freshness

Decision:

- Use `past-week` in LinkedIn search URLs.

Reason:

- Procurement intent is fresher and more actionable in a shorter time window.

