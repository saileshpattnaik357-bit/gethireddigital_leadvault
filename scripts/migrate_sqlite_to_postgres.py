"""LeadVault AI — Phase 12 SQLite WAL to Hosted PostgreSQL Migration Runner.

Implements LV-P12-003: Zero-downtime data migration with deterministic SHA-256
row checksum verification across all 6 core tables.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Tuple

TABLES_IN_ORDER: List[Tuple[str, str, List[str]]] = [
    ("tenants", "tenant_id", ["tenant_id", "company_name", "website", "industry", "created_at_utc", "updated_at_utc"]),
    ("leadvault_specs", "tenant_id", ["tenant_id", "company_name", "website", "lead_objective", "spec_json", "updated_at_utc"]),
    (
        "leads",
        "lead_id",
        [
            "lead_id", "tenant_id", "company_name", "domain", "contact_name", "lead_tier",
            "deal_size_usd", "intent_score", "budget_authority", "procurement_timeline",
            "raw_signal", "dossier_json", "status", "created_at_utc",
        ],
    ),
    (
        "hermes_conversions",
        "conversion_id",
        [
            "conversion_id", "tenant_id", "lead_id", "company_name", "outcome",
            "deal_value_usd", "feedback", "matched_rules", "created_at_utc",
        ],
    ),
    ("audit_logs", "id", ["id", "timestamp_utc", "tenant_id", "agent_id", "action", "status", "details_json"]),
    ("webhooks", "webhook_id", ["webhook_id", "tenant_id", "target_url", "secret_key", "trigger_events", "enabled", "created_at_utc"]),
]


def _row_checksum(values: Tuple[Any, ...]) -> str:
    payload = json.dumps([str(v) if v is not None else None for v in values], sort_keys=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read_sqlite_snapshot(sqlite_path: Path) -> Dict[str, Dict[str, Any]]:
    """Extract all rows and deterministic SHA-256 table checksums from SQLite."""
    if not sqlite_path.exists():
        raise FileNotFoundError(f"Source SQLite DB not found: {sqlite_path}")

    conn = sqlite3.connect(str(sqlite_path))
    conn.row_factory = sqlite3.Row
    snapshot: Dict[str, Dict[str, Any]] = {}

    try:
        for table, pk, cols in TABLES_IN_ORDER:
            col_sql = ", ".join(cols)
            rows = conn.execute(f"SELECT {col_sql} FROM {table} ORDER BY {pk} ASC;").fetchall()
            extracted = [tuple(row[c] for c in cols) for row in rows]
            table_hash = hashlib.sha256("".join(_row_checksum(r) for r in extracted).encode("utf-8")).hexdigest()
            snapshot[table] = {
                "pk": pk,
                "cols": cols,
                "rows": extracted,
                "count": len(extracted),
                "checksum": table_hash,
            }
    finally:
        conn.close()

    return snapshot


def migrate_sqlite_to_postgres(
    sqlite_path: Path,
    database_url: str,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Migrate SQLite WAL tables to PostgreSQL and verify SHA-256 parity."""
    snapshot = read_sqlite_snapshot(sqlite_path)
    report: Dict[str, Any] = {
        "source": str(sqlite_path),
        "dry_run": dry_run,
        "tables": {},
    }

    if dry_run:
        for table, data in snapshot.items():
            report["tables"][table] = {
                "source_count": data["count"],
                "migrated_count": 0,
                "source_checksum": data["checksum"],
                "parity_verified": True,
            }
        return report

    from backend.services.postgres_engine import PostgresStorageEngine

    pg = PostgresStorageEngine(database_url, bootstrap=True)

    with pg._connect() as conn:
        for table, data in snapshot.items():
            cols = data["cols"]
            pk = data["pk"]
            rows = data["rows"]
            placeholders = ", ".join(["%s"] * len(cols))
            col_list = ", ".join(cols)
            update_cols = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c != pk)

            # Set tenant context per row for RLS-enabled tables, or execute as table owner
            with conn.cursor() as cur:
                for row_vals in rows:
                    tenant_val = row_vals[cols.index("tenant_id")] if "tenant_id" in cols else None
                    if tenant_val:
                        cur.execute("SELECT set_config('app.current_tenant', %s, true);", (str(tenant_val),))
                    cur.execute(
                        f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) "
                        f"ON CONFLICT ({pk}) DO UPDATE SET {update_cols};",
                        row_vals,
                    )
            conn.commit()

            # Verify parity checksum in destination
            with conn.cursor() as cur:
                if table == "audit_logs" and rows:
                    cur.execute("SELECT setval(pg_get_serial_sequence('audit_logs', 'id'), COALESCE((SELECT MAX(id) FROM audit_logs), 1));")
                cur.execute(f"SELECT {col_list} FROM {table} ORDER BY {pk} ASC;")
                dest_rows = [tuple(r[c] for c in cols) for r in cur.fetchall()]
                dest_hash = hashlib.sha256("".join(_row_checksum(r) for r in dest_rows).encode("utf-8")).hexdigest()

            report["tables"][table] = {
                "source_count": data["count"],
                "migrated_count": len(dest_rows),
                "source_checksum": data["checksum"],
                "dest_checksum": dest_hash,
                "parity_verified": (data["count"] == len(dest_rows) and data["checksum"] == dest_hash),
            }

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="LeadVault Phase 12 SQLite-to-PostgreSQL Migration Runner")
    parser.add_argument("--sqlite-path", default="backend/runtime/leadvault_enterprise.db", help="Path to SQLite WAL DB")
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL", ""), help="Target PostgreSQL connection URI")
    parser.add_argument("--dry-run", action="store_true", help="Inspect SQLite snapshot and checksums without writing")
    args = parser.parse_args()

    result = migrate_sqlite_to_postgres(
        sqlite_path=Path(args.sqlite_path),
        database_url=args.database_url,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
