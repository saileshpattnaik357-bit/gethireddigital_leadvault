"""Shared fixtures: redirect every harness/store file to a temp dir so tests never touch runtime/."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


@pytest.fixture(autouse=True)
def isolated_stores(tmp_path, monkeypatch):
    from harness import approvals, audit, workflow
    from services import accepted_export_store, leadvault_spec_store, rejected_audit_store

    monkeypatch.setattr(audit, "AUDIT_FILE", tmp_path / "audit.jsonl")
    monkeypatch.setattr(workflow, "STORE_FILE", tmp_path / "workflows.json")
    monkeypatch.setattr(approvals, "STORE_FILE", tmp_path / "approvals.json")
    monkeypatch.setattr(accepted_export_store, "STORE_FILE", tmp_path / "accepted.json")
    monkeypatch.setattr(rejected_audit_store, "STORE_FILE", tmp_path / "rejected.json")
    monkeypatch.setattr(leadvault_spec_store, "STORE_FILE", tmp_path / "specs.json")
    yield tmp_path
