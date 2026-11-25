-- LeadVault AI — Phase 12: Hosted PostgreSQL Schema & Multi-Tenant Row-Level Security (RLS)
-- Tasks: LV-P12-001, LV-P12-002, LV-SEC-001
-- Enforces fail-closed tenant isolation via session variable `app.current_tenant`.

CREATE TABLE IF NOT EXISTS tenants (
    tenant_id TEXT PRIMARY KEY,
    company_name TEXT,
    website TEXT,
    industry TEXT,
    created_at_utc TEXT,
    updated_at_utc TEXT
);

CREATE TABLE IF NOT EXISTS leadvault_specs (
    tenant_id TEXT PRIMARY KEY REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    company_name TEXT,
    website TEXT,
    lead_objective TEXT,
    spec_json TEXT,
    updated_at_utc TEXT
);

CREATE TABLE IF NOT EXISTS leads (
    lead_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    company_name TEXT,
    domain TEXT,
    contact_name TEXT,
    lead_tier TEXT,
    deal_size_usd DOUBLE PRECISION,
    intent_score INTEGER,
    budget_authority INTEGER,
    procurement_timeline TEXT,
    raw_signal TEXT,
    dossier_json TEXT,
    status TEXT,
    created_at_utc TEXT
);

CREATE INDEX IF NOT EXISTS idx_leads_tenant ON leads(tenant_id);
CREATE INDEX IF NOT EXISTS idx_leads_tier ON leads(lead_tier);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);

CREATE TABLE IF NOT EXISTS hermes_conversions (
    conversion_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    lead_id TEXT,
    company_name TEXT,
    outcome TEXT,
    deal_value_usd DOUBLE PRECISION,
    feedback TEXT,
    matched_rules TEXT,
    created_at_utc TEXT
);

CREATE INDEX IF NOT EXISTS idx_hermes_tenant ON hermes_conversions(tenant_id);

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp_utc TEXT,
    tenant_id TEXT NOT NULL,
    agent_id TEXT,
    action TEXT,
    status TEXT,
    details_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_tenant ON audit_logs(tenant_id);

CREATE TABLE IF NOT EXISTS webhooks (
    webhook_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    target_url TEXT,
    secret_key TEXT,
    trigger_events TEXT,
    enabled INTEGER DEFAULT 1,
    created_at_utc TEXT
);

CREATE INDEX IF NOT EXISTS idx_webhooks_tenant ON webhooks(tenant_id);

-- =====================================================================
-- Row-Level Security (RLS) Policies — Fail-Closed Tenant Isolation
-- =====================================================================

ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenants FORCE ROW LEVEL SECURITY;

ALTER TABLE leadvault_specs ENABLE ROW LEVEL SECURITY;
ALTER TABLE leadvault_specs FORCE ROW LEVEL SECURITY;

ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads FORCE ROW LEVEL SECURITY;

ALTER TABLE hermes_conversions ENABLE ROW LEVEL SECURITY;
ALTER TABLE hermes_conversions FORCE ROW LEVEL SECURITY;

ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs FORCE ROW LEVEL SECURITY;

ALTER TABLE webhooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhooks FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation_tenants ON tenants;
CREATE POLICY tenant_isolation_tenants ON tenants
    USING (tenant_id = NULLIF(current_setting('app.current_tenant', true), ''))
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant', true), ''));

DROP POLICY IF EXISTS tenant_isolation_specs ON leadvault_specs;
CREATE POLICY tenant_isolation_specs ON leadvault_specs
    USING (tenant_id = NULLIF(current_setting('app.current_tenant', true), ''))
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant', true), ''));

DROP POLICY IF EXISTS tenant_isolation_leads ON leads;
CREATE POLICY tenant_isolation_leads ON leads
    USING (tenant_id = NULLIF(current_setting('app.current_tenant', true), ''))
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant', true), ''));

DROP POLICY IF EXISTS tenant_isolation_conversions ON hermes_conversions;
CREATE POLICY tenant_isolation_conversions ON hermes_conversions
    USING (tenant_id = NULLIF(current_setting('app.current_tenant', true), ''))
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant', true), ''));

DROP POLICY IF EXISTS tenant_isolation_audit ON audit_logs;
CREATE POLICY tenant_isolation_audit ON audit_logs
    USING (tenant_id = NULLIF(current_setting('app.current_tenant', true), ''))
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant', true), ''));

DROP POLICY IF EXISTS tenant_isolation_webhooks ON webhooks;
CREATE POLICY tenant_isolation_webhooks ON webhooks
    USING (tenant_id = NULLIF(current_setting('app.current_tenant', true), ''))
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant', true), ''));
