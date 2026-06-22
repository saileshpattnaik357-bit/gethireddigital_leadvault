# Architecture

LeadVaultAI is split into a FastAPI backend and a Next.js frontend.

## Backend Structure

- `backend/main.py` creates the FastAPI app, configures CORS, and mounts the LeadVault router.
- `backend/api/routes/leadvault.py` exposes the public API.
- `backend/services/leadvault_agent.py` builds the mining brain from client ICP data.
- `backend/services/leadvault_mining_runner.py` runs mining and classification.
- `backend/services/buying_intent_agent.py` classifies procurement intent.
- `backend/services/final_verifier.py` performs final signal validation.
- `backend/services/accepted_export_store.py` persists accepted exports.
- `backend/services/rejected_audit_store.py` persists rejected rows and audit data.
- `backend/services/leadvault_spec_store.py` stores generated specs.

## Data Flow

1. User enters client details or uploads an ICP file.
2. Backend aggregates the ICP into a profile.
3. LeadVault generates buyer clusters, search phrases, negative filters, and a Python-ready query bank.
4. User confirms the generated brain.
5. Mining runs through live web, Apify, or paste/import workflows.
6. Buying-intent and final-verifier logic decide whether a row is accepted or rejected.
7. Accepted and rejected rows are stored and shown in the UI.

## Frontend Structure

- `frontend/app/page.tsx` contains the full operator workflow.
- `frontend/app/styles.css` defines the dashboard UI.
- `frontend/app/layout.tsx` provides the shell layout.

## Current Limitation

LinkedIn is supported through query generation and paste/import capture. Full browser-login scraping is not treated as complete in the current state.

