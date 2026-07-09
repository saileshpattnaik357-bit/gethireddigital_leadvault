from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


DB_FILE = Path(__file__).resolve().parent.parent / "runtime" / "leadvault_agent.db"
DB_FILE.parent.mkdir(parents=True, exist_ok=True)
LOCK = threading.Lock()


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=NORMAL")
    return connection


def init_db() -> None:
    with LOCK, _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_records (
                record_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                created_at_utc TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_agent_records_tenant_kind ON agent_records (tenant_id, kind, created_at_utc DESC)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_agent_records_kind_created ON agent_records (kind, created_at_utc DESC)")
        connection.commit()


def save_record(kind: str, tenant_id: str, payload: dict[str, Any], record_id: str | None = None) -> dict[str, Any]:
    init_db()
    created_at = datetime.now(timezone.utc).isoformat()
    storage_id = record_id or f"{kind}_{uuid4().hex[:12]}"
    with LOCK, _connect() as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO agent_records (record_id, tenant_id, kind, created_at_utc, payload_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                storage_id,
                tenant_id or "default",
                kind,
                created_at,
                json.dumps(payload, ensure_ascii=False, default=str),
            ),
        )
        connection.commit()
    return {
        "record_id": storage_id,
        "tenant_id": tenant_id or "default",
        "kind": kind,
        "created_at_utc": created_at,
    }


def list_records(kind: str | None = None, tenant_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    init_db()
    clauses: list[str] = []
    params: list[Any] = []
    if kind:
        clauses.append("kind = ?")
        params.append(kind)
    if tenant_id:
        clauses.append("tenant_id = ?")
        params.append(tenant_id)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    params.append(max(1, min(limit, 500)))
    with LOCK, _connect() as connection:
        rows = connection.execute(
            f"SELECT record_id, tenant_id, kind, created_at_utc, payload_json FROM agent_records{where} ORDER BY created_at_utc DESC LIMIT ?",
            params,
        ).fetchall()
    records: list[dict[str, Any]] = []
    for row in rows:
        payload = json.loads(row["payload_json"])
        records.append({
            "record_id": row["record_id"],
            "tenant_id": row["tenant_id"],
            "kind": row["kind"],
            "created_at_utc": row["created_at_utc"],
            "payload": payload,
        })
    return records


def storage_stats(tenant_id: str | None = None) -> dict[str, Any]:
    init_db()
    params: list[Any] = []
    where = ""
    if tenant_id:
        where = " WHERE tenant_id = ?"
        params.append(tenant_id)
    with LOCK, _connect() as connection:
        rows = connection.execute(
            f"SELECT kind, COUNT(*) AS total FROM agent_records{where} GROUP BY kind ORDER BY kind",
            params,
        ).fetchall()
    return {
        "db_file": str(DB_FILE),
        "tenant_id": tenant_id,
        "counts": {row["kind"]: row["total"] for row in rows},
    }
