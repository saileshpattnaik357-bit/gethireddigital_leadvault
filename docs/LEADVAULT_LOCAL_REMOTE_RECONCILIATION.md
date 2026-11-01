# LeadVault AI: Local vs. Remote Reconciliation & Git Topology Analysis

**Document ID:** `LV-DOC-GIT-003`  
**Date:** 2026-11-01  
**Project:** LeadVault AI  
**Author:** LeadVault Principal Recovery Engineer & Release Manager  

---

## 1. Remote Repository Network Topology

Git remote inspection of `D:\ANTIGRAVITY\LEADVAULT` identified four configured upstream remotes, plus the target repository designated in the mission brief:

| Remote Alias | Configured URL | Protocol | Accessibility Status | Commit Alignment |
|---|---|---|---|---|
| `target` | `https://github.com/LeadVaultAI/LEADVAULTAI_TEST_PROJECT.git` | HTTPS | ✅ **Verified Active** | Exact match with local `main` (`ab4cd3a`) and `codex/leadvault-launch` (`a6d4fef`). |
| `origin` | `https://github.com/rxgptgethiredglobal/leadvault.git` | HTTPS | ❌ **Repository Not Found (404)** | Deprecated or deleted organization remote. |
| `gethired` | `https://github.com/saileshpattnaik357-bit/gethireddigital_leadvault.git` | HTTPS | ⚠️ Private / Auth Gated | Linked to user account `saileshpattnaik357-bit`. |
| `launchpad`| `https://github.com/saileshpattnaik357/Leadvault_Gethired_Digital.git` | HTTPS | ⚠️ Private / Auth Gated | Linked to user account `saileshpattnaik357`. |
| *Requested Target* | `https://github.com/saileshpattnaik357/LEADVAULT_AGENT_TEST_REPO` | HTTPS | ⚠️ **Access Blocker Identified** | GitHub CLI returned GraphQL error: "Could not resolve to a Repository with the name 'saileshpattnaik357/LEADVAULT_AGENT_TEST_REPO'". |

---

## 2. GitHub Access Blocker Root Cause Analysis

A diagnostic check with GitHub CLI (`gh auth status`) revealed the following authentication state on the host system:
1. Active logged-in account: `RxGPThealth2025` (Organization token with scopes `gist, read:org, repo, workflow`).
2. Stored but inactive credentials:
   - `rxgptgethiredglobal`
   - `saileshpatnaik491-pattnaik`
   - `saileshpattnaik357-bit`
3. **Blocker Explanation:**
   - The requested repository `saileshpattnaik357/LEADVAULT_AGENT_TEST_REPO` either:
     a) Has not yet been initialized on GitHub under `saileshpattnaik357`, OR
     b) Exists as a private repository under `saileshpattnaik357` to which the active `RxGPThealth2025` token lacks read/write permissions.
4. **Resolution Path:**
   - Development continues locally against the verified canonical source of truth.
   - When delivering to GitHub, git remote `repo_delivery` can be bound to `https://github.com/saileshpattnaik357/LEADVAULT_AGENT_TEST_REPO.git`, or the user can switch gh accounts via `gh auth switch --user saileshpattnaik357-bit` or create the repo via `gh repo create saileshpattnaik357/LEADVAULT_AGENT_TEST_REPO --private`.

---

## 3. Local Working Tree State & Staged Status

Inspecting `git --git-dir="D:\ANTIGRAVITY\LEADVAULT\.git" --work-tree="D:\ANTIGRAVITY\LEADVAULT" status`:

```text
On branch main
Your branch is up to date with 'target/main'.

Changes not staged for commit:
	modified:   frontend/next-env.d.ts
	modified:   leadvault (untracked content)

Untracked files:
	backend/runtime/
```

### Analysis of Changes:
1. `frontend/next-env.d.ts`: Trivial type declaration touch by Next.js compiler. Retained.
2. `leadvault (untracked content)`: The nested legacy git subfolder has minor local log files (`backend_server.log`, `frontend_server.log`). It must remain untouched to avoid disrupting historical logs.
3. `backend/runtime/`: Contains the live local operational stores:
   - `leadvault_specs.json` (200KB of saved client mining brains)
   - `accepted_exports.json` (14.5KB of verified leads)
   - `rejected_audits.json` (20.5KB of verified rejected noise)
   - `audit.jsonl` (34.8KB append-only immutable audit trail)
   *Decision:* These are production runtime stores and must remain intact, preserved as evidence.

---

## 4. Local vs. Nested Subdirectory Reconciliation

| File / Component | Root Location (`D:\ANTIGRAVITY\LEADVAULT\`) | Nested Location (`...\leadvault\`) | Winner / Canonical Standard | Rationale |
|---|---|---|---|---|
| `backend/harness/` | 9 files (Control Plane, Policy, Tools, Audit, Workflow, Approvals) | **Missing** | **Root** | Root contains the enterprise control harness. |
| `backend/evaluation/` | 10 files (Gold Corpus, Harness runner, 9 eval reports) | **Missing** | **Root** | Root contains the golden evaluation dataset and benchmark reports. |
| `backend/services/buying_intent_agent.py` | 17,647 bytes | 6,491 bytes | **Root** | Root includes confidence scoring, token budgeting, and multi-pattern heuristics. |
| `backend/services/leadvault_mining_runner.py` | 34,102 bytes | 21,015 bytes | **Root** | Root includes Apify actor bridging, error recovery, and policy checks. |
| `frontend/app/page.tsx` | 44,259 bytes | 35,849 bytes | **Root** | Root UI has harness control panel, run approval queue, and spec inspector. |
| `backend/tests/` | 3 test suites, 115 tests passing | 1 test suite, 22 tests | **Root** | Root provides complete adversarial, harness, and regression coverage. |

**Verdict:** The root project directory `D:\ANTIGRAVITY\LEADVAULT` is the complete, advanced canonical superset. The nested `leadvault` directory is an obsolete V1 development snapshot that has been safely isolated.
