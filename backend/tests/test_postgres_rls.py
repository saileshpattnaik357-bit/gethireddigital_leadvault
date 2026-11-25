import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from backend.services.postgres_engine import PostgresStorageEngine, _validate_tenant_id
from backend.services.storage_engine import StorageEngine, get_storage_engine
from scripts.migrate_sqlite_to_postgres import migrate_sqlite_to_postgres


def test_rls_migration_sql_enforces_fail_closed_policies():
    sql_path = Path("migrations/versions/002_tenant_rls_policies.sql")
    assert sql_path.exists()
    sql = sql_path.read_text(encoding="utf-8")

    for table in ["tenants", "leadvault_specs", "leads", "hermes_conversions", "audit_logs", "webhooks"]:
        assert f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;" in sql
        assert f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;" in sql

    assert "NULLIF(current_setting('app.current_tenant', true), '')" in sql


def test_validate_tenant_id_fails_closed():
    assert _validate_tenant_id("acme_corp") == "acme_corp"
    with pytest.raises(ValueError):
        _validate_tenant_id("")
    with pytest.raises(ValueError):
        _validate_tenant_id("   ")


def test_pluggable_database_url_routing():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "fallback.db"
        engine_default = get_storage_engine(db_url="", db_path=db_path)
        assert isinstance(engine_default, StorageEngine)
        assert engine_default.health_check()["backend"] == "sqlite"
        engine_default.close()

        engine_sqlite = get_storage_engine(db_url=f"sqlite:///{db_path}", db_path=db_path)
        assert isinstance(engine_sqlite, StorageEngine)
        engine_sqlite.close()

    with patch("backend.services.postgres_engine.PostgresStorageEngine._bootstrap_schema") as mock_boot:
        pg_engine = get_storage_engine(db_url="postgresql://user:pass@ep-cool.neon.tech/leadvault?sslmode=require")
        assert isinstance(pg_engine, PostgresStorageEngine)
        mock_boot.assert_called_once()


def test_postgres_engine_sets_rls_tenant_context_per_transaction():
    mock_cur = MagicMock()
    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    with patch("backend.services.postgres_engine.PostgresStorageEngine._bootstrap_schema"):
        pg = PostgresStorageEngine("postgresql://user:pass@localhost/leadvault")

    with patch.object(pg, "_connect", return_value=mock_conn):
        pg.insert_lead("tenant_alpha", "lead_001", {"Company Name": "Beta Inc", "lead_tier": "A"})

    executed_sql = [call.args[0] for call in mock_cur.execute.call_args_list]
    assert any("set_config('app.current_tenant'" in s for s in executed_sql)
    tenant_args = [call.args[1] for call in mock_cur.execute.call_args_list if "set_config" in call.args[0]]
    assert all(args == ("tenant_alpha",) for args in tenant_args)


def test_sqlite_to_postgres_migration_dry_run_checksum_parity():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "source.db"
        engine = StorageEngine(db_path=db_path)
        engine.save_spec("tenant_mig", {"company_name": "MigCorp", "website": "https://mig.io", "lead_objective": "rfp"})
        engine.insert_lead("tenant_mig", "lead_m1", {"Company Name": "TargetCo", "lead_tier": "A"})
        engine.log_audit("tenant_mig", "AGENT_001", "MIGRATION_TEST", "OK", {"step": 1})
        engine.close()

        report = migrate_sqlite_to_postgres(db_path, database_url="", dry_run=True)
        assert report["dry_run"] is True
        assert report["tables"]["tenants"]["source_count"] >= 1
        assert report["tables"]["leads"]["source_count"] >= 1
        assert report["tables"]["audit_logs"]["source_count"] >= 1
        assert all(t["parity_verified"] for t in report["tables"].values())
