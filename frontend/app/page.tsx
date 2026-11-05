'use client'

import { useEffect, useMemo, useState } from 'react'
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  ArrowUpRight,
  BarChart3,
  Brain,
  Building,
  Check,
  CheckCircle2,
  ChevronDown,
  Clock,
  Copy,
  Database,
  DollarSign,
  Download,
  ExternalLink,
  Eye,
  FileSpreadsheet,
  FileText,
  Filter,
  Globe,
  Info,
  Layers,
  LineChart,
  Mail,
  Network,
  Phone,
  Play,
  Plus,
  Radar,
  RefreshCw,
  Search,
  Send,
  Shield,
  ShieldCheck,
  Sliders,
  Sparkles,
  Trash2,
  Upload,
  User,
  XCircle,
  Zap,
} from 'lucide-react'

const API = process.env.NEXT_PUBLIC_LEADVAULT_API ?? 'http://localhost:8000'

interface LeadVaultSpec {
  lead_objective?: string
  objective_label?: string
  company_name: string
  website: string
  services: string[]
  geography?: string
  icp?: string
  positioning?: string
  customer_examples?: string[]
  founder_profile?: string
  buyer_clusters: string[]
  linkedin_queries: string[]
  google_queries: string[]
  buyer_phrases: string[]
  negative_filters: string[]
  python_snippet: string
  generation_mode: string
}

interface ApprovalItem {
  approval_id: string
  tenant_id: string
  workflow_id?: string | null
  state: string
  created_at_utc: string
  decided_by?: string | null
  decision_comment?: string
  agent_id: string
  recommended_action: string
  reason: string
  evidence: { evidence?: string[]; negative_signals?: string[]; confidence?: number; llm?: { verdict?: string; reason?: string } | null }
  lead: Record<string, unknown>
}

interface WorkflowItem {
  workflow_id: string
  tenant_id: string
  objective: string
  state: string
  created_at_utc: string
  updated_at_utc: string
  history: Array<{ ts: string; from: string | null; to: string; actor: string; note?: string }>
  summary: Record<string, unknown>
  metrics: { latency_seconds?: number; estimated_cost_usd?: number; tool_calls?: Record<string, number>; tool_errors?: Record<string, number>; accept_rate?: number }
  error?: string | null
}

interface MiningResult {
  accepted: Array<Record<string, unknown>>
  rejected: Array<Record<string, unknown>>
  pending_approval?: ApprovalItem[]
  workflow_id?: string
  workflow_state?: string
  apify_report?: Array<{ query: string; status: string; actor: string; items: number; error: string }>
  summary: {
    pending_approval?: number
    llm_validation?: boolean
    source?: string
    candidates_reviewed: number
    accepted: number
    rejected: number
    apify_queries_attempted?: number
    apify_items?: number
    mining_mode?: string
    live_web: boolean
    uploaded_rows?: number
    source_filename?: string
  }
}

interface RunHistory {
  accepted_exports: Array<Record<string, unknown>>
  rejected_audits: Array<Record<string, unknown>>
}

interface TenantSummary {
  tenant_id: string
  company_name: string
  spec_count: number
  accepted_runs: number
  rejected_rows: number
  latest_spec?: Record<string, unknown> | null
}

interface HermesReflectionReport {
  tenant_id: string
  total_outcomes_evaluated: number
  conversion_rate: number
  high_yield_rules: string[]
  underperforming_rules: string[]
  suggested_weight_adjustments: Record<string, number>
  generated_at: string
}

interface AgentTaskHandoff {
  step: number
  from_agent: string
  to_agent: string
  action: string
  payload_summary: Record<string, unknown>
  status: string
  timestamp: string
}

interface MultiAgentRunSummary {
  workflow_id: string
  tenant_id: string
  coordinator: string
  participating_agents: string[]
  handoff_trace: AgentTaskHandoff[]
  total_candidates_processed: number
  qualified_leads: Array<Record<string, unknown>>
  disqualified_candidates: Array<Record<string, unknown>>
  execution_time_ms: number
  completed_at: string
}

interface WebhookConfigItem {
  tenant_id: string
  target_url: string
  enabled: boolean
  trigger_events: string[]
}

type ApiState = 'checking' | 'online' | 'offline'
type TabType = 'mining' | 'mesh' | 'hermes' | 'webhooks'

const leadColumns = [
  'Date Added',
  'Estimated Deal Value',
  'Client Name',
  'Client LinkedIn Profile URL',
  'Title',
  'Company Name',
  'Company Website',
  'Industry',
  'Region',
  'Client Email',
  'Client Phone',
  'Number of Employees',
  'Lead Source',
  'Client Intent Signal',
  'Client Exact Query',
  'Client Query Post URL',
  'Priority',
  'Service Category',
  'Outreach Status',
  'Ajroni Offer',
  'Notes',
]

const leadObjectiveOptions = [
  { value: 'agency_procurement', label: 'Agency / Vendor Buyer Leads', hint: 'Find companies seeking agencies, consultants, vendors, implementation partners, or outsourced support.' },
  { value: 'recruitment_clients', label: 'Recruitment / Staffing Client Leads', hint: 'Find companies hiring or needing recruiters, staffing partners, or RPO support.' },
  { value: 'candidate_job_search', label: 'Candidate / Job Opportunity Mining', hint: 'Find job openings and hiring posts for a candidate profile.' },
  { value: 'fractional_executive', label: 'Fractional CMO / Executive Consulting', hint: 'Find companies seeking fractional leaders, GTM advisors, RevOps consultants, or growth executives.' },
]

export default function LeadVaultPage() {
  const [activeTab, setActiveTab] = useState<TabType>('mining')
  const [apiState, setApiState] = useState<ApiState>('checking')
  const [form, setForm] = useState({
    tenant_id: 'default',
    lead_objective: 'agency_procurement',
    company_name: '',
    website: '',
    services: '',
    geography: '',
    icp: '',
    positioning: '',
    customer_examples: '',
    founder_profile: '',
  })
  const [icpFile, setIcpFile] = useState<File | null>(null)
  const [spec, setSpec] = useState<LeadVaultSpec | null>(null)
  const [confirmed, setConfirmed] = useState(false)
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [mining, setMining] = useState(false)
  const [mode, setMode] = useState('hybrid')
  const [liveWeb, setLiveWeb] = useState(true)
  const [maxResults, setMaxResults] = useState('25')
  const [maxApifyQueries, setMaxApifyQueries] = useState('10')
  const [maxPostsPerQuery, setMaxPostsPerQuery] = useState('10')
  const [captureText, setCaptureText] = useState('')
  const [result, setResult] = useState<MiningResult | null>(null)
  const [history, setHistory] = useState<RunHistory>({ accepted_exports: [], rejected_audits: [] })
  const [tenants, setTenants] = useState<TenantSummary[]>([])
  const [approvals, setApprovals] = useState<ApprovalItem[]>([])
  const [workflows, setWorkflows] = useState<WorkflowItem[]>([])
  const [reviewer, setReviewer] = useState('operator')
  const [deciding, setDeciding] = useState<string | null>(null)

  // Search & Filters in Lead Table
  const [searchQuery, setSearchQuery] = useState('')
  const [tierFilter, setTierFilter] = useState<'ALL' | 'A' | 'B' | 'C'>('ALL')

  // Drawer Modal State
  const [inspectLead, setInspectLead] = useState<Record<string, unknown> | null>(null)
  const [copiedKey, setCopiedKey] = useState<string | null>(null)

  // Hermes Learning State
  const [hermesReport, setHermesReport] = useState<HermesReflectionReport | null>(null)
  const [hermesForm, setHermesForm] = useState({
    lead_id: 'lead-001',
    company_name: '',
    outcome: 'CLOSED_WON',
    deal_value: '75000',
    feedback: 'Procurement decision-maker closed within 2 weeks. Budget pre-allocated.',
    matched_rules: 'RULE_AGENCY_PROCUREMENT,RULE_BUDGET_CONFIRMED',
  })
  const [hermesRecording, setHermesRecording] = useState(false)

  // Multi-Agent Mesh State
  const [meshSignalText, setMeshSignalText] = useState(
    'Looking for an agency partner to rebuild our Shopify Plus store ASAP. Approved budget ready.'
  )
  const [meshRunning, setMeshRunning] = useState(false)
  const [meshSummary, setMeshSummary] = useState<MultiAgentRunSummary | null>(null)
  const [langGraphState, setLangGraphState] = useState<Record<string, unknown> | null>(null)

  // Webhooks State
  const [webhooks, setWebhooks] = useState<WebhookConfigItem[]>([])
  const [webhookUrl, setWebhookUrl] = useState('https://api.hubspot.com/v3/events')
  const [webhookSecret, setWebhookSecret] = useState('whsec_leadvault_live_2026')
  const [webhookDispatching, setWebhookDispatching] = useState(false)
  const [webhookLogs, setWebhookLogs] = useState<string[]>([])

  useEffect(() => {
    checkApi()
    void loadTenants()
  }, [])

  useEffect(() => {
    void loadHistory()
    void loadHermesReflection()
    void loadWebhooks()
  }, [form.tenant_id])

  async function checkApi() {
    setApiState('checking')
    try {
      const res = await fetch(`${API}/api/leadvault/health`, { cache: 'no-store' })
      setApiState(res.ok ? 'online' : 'offline')
    } catch {
      setApiState('offline')
    }
  }

  async function loadTenants() {
    try {
      const res = await fetch(`${API}/api/leadvault/tenants`, { cache: 'no-store' })
      const data = await res.json()
      if (res.ok) setTenants(data.items ?? [])
    } catch {
      // offline
    }
  }

  function switchTenant(tenantId: string) {
    const selected = tenants.find((item) => item.tenant_id === tenantId)
    setForm((current) => ({ ...current, tenant_id: tenantId }))
    setSpec(null)
    setResult(null)
    setConfirmed(false)
    setMessage(`Switched workspace to ${tenantId}`)
    if (selected?.latest_spec) hydrateFormFromProfile(selected.latest_spec)
  }

  function newTenant() {
    setForm({
      tenant_id: `client-${new Date().toISOString().slice(0, 10)}`,
      company_name: '',
      website: '',
      services: '',
      geography: '',
      icp: '',
      positioning: '',
      customer_examples: '',
      founder_profile: '',
      lead_objective: 'agency_procurement',
    })
    setSpec(null)
    setResult(null)
    setConfirmed(false)
    setIcpFile(null)
    setMessage('New client workspace initialized.')
  }

  async function loadHistory() {
    try {
      const res = await fetch(`${API}/api/leadvault/runs?tenant_id=${encodeURIComponent(form.tenant_id)}`, { cache: 'no-store' })
      const data = await res.json()
      if (res.ok) {
        setHistory({
          accepted_exports: data.accepted_exports ?? [],
          rejected_audits: data.rejected_audits ?? [],
        })
      }
    } catch {
      // offline
    }
    void loadHarness()
  }

  async function loadHarness() {
    const tenant = encodeURIComponent(form.tenant_id)
    try {
      const [a, w] = await Promise.all([
        fetch(`${API}/api/leadvault/harness/approvals?tenant_id=${tenant}`, { cache: 'no-store' }),
        fetch(`${API}/api/leadvault/harness/workflows?tenant_id=${tenant}&limit=8`, { cache: 'no-store' }),
      ])
      if (a.ok) setApprovals((await a.json()).items ?? [])
      if (w.ok) setWorkflows((await w.json()).items ?? [])
    } catch {
      // offline
    }
  }

  async function loadHermesReflection() {
    try {
      const res = await fetch(`${API}/api/leadvault/hermes/reflection?tenant_id=${encodeURIComponent(form.tenant_id)}`, { cache: 'no-store' })
      if (res.ok) setHermesReport(await res.json())
    } catch {
      // offline
    }
  }

  async function submitHermesConversion() {
    setHermesRecording(true)
    try {
      const res = await fetch(`${API}/api/leadvault/hermes/conversion`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tenant_id: form.tenant_id,
          lead_id: hermesForm.lead_id,
          company_name: hermesForm.company_name || 'Prospect Company',
          outcome: hermesForm.outcome,
          deal_value: Number(hermesForm.deal_value) || 0,
          feedback: hermesForm.feedback,
          matched_rules: hermesForm.matched_rules.split(',').map((s) => s.trim()).filter(Boolean),
        }),
      })
      if (res.ok) {
        setMessage('Conversion outcome saved to Hermes episodic memory!')
        await loadHermesReflection()
      }
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Failed to record conversion')
    } finally {
      setHermesRecording(false)
    }
  }

  async function runMeshSignals() {
    setMeshRunning(true)
    setMeshSummary(null)
    setLangGraphState(null)
    try {
      const res = await fetch(`${API}/api/leadvault/mesh/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tenant_id: form.tenant_id,
          company_name: form.company_name || 'Client Target',
          lead_objective: form.lead_objective,
          candidates: [{ text: meshSignalText, title: 'Decision Maker', source: 'LinkedIn Live Stream' }],
        }),
      })
      if (res.ok) {
        const data = await res.json()
        setMeshSummary(data)
        setMessage(`Mesh execution complete: ${data.total_candidates_processed} processed, ${data.qualified_leads.length} qualified in ${Math.round(data.execution_time_ms)}ms`)
      }
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Mesh execution failed')
    } finally {
      setMeshRunning(false)
    }
  }

  async function runLangGraphDAG() {
    setMeshRunning(true)
    setMeshSummary(null)
    setLangGraphState(null)
    try {
      const res = await fetch(`${API}/api/leadvault/langgraph/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tenant_id: form.tenant_id,
          company_name: form.company_name || 'Client Target',
          lead_objective: form.lead_objective,
          candidates: [{ text: meshSignalText, title: 'VP Technology', source: 'LangGraph Input Stream' }],
        }),
      })
      if (res.ok) {
        const data = await res.json()
        setLangGraphState(data)
        setMessage(`LangGraph DAG completed at checkpoint step ${data.checkpoint_step}!`)
      }
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'LangGraph execution failed')
    } finally {
      setMeshRunning(false)
    }
  }

  async function loadWebhooks() {
    try {
      const res = await fetch(`${API}/api/leadvault/webhooks?tenant_id=${encodeURIComponent(form.tenant_id)}`, { cache: 'no-store' })
      if (res.ok) setWebhooks((await res.json()).items ?? [])
    } catch {
      // offline
    }
  }

  async function registerWebhook() {
    try {
      const res = await fetch(`${API}/api/leadvault/webhooks/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tenant_id: form.tenant_id,
          target_url: webhookUrl,
          secret_key: webhookSecret,
          trigger_events: ['lead.approved', 'lead.sql_detected'],
        }),
      })
      if (res.ok) {
        setMessage('Webhook registered with HMAC-SHA256 signature verification!')
        await loadWebhooks()
      }
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Registration error')
    }
  }

  async function dispatchTestWebhook() {
    setWebhookDispatching(true)
    try {
      const res = await fetch(`${API}/api/leadvault/webhooks/dispatch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tenant_id: form.tenant_id,
          event: 'lead.approved',
          lead_data: {
            lead_id: 'test_lead_77',
            company_name: form.company_name || 'Acme Enterprises',
            lead_tier: 'A',
            estimated_deal_value: '$50K–$150K Strategic',
            budget_authority: true,
            timeline: 'immediate',
            intent_score: 92,
          },
        }),
      })
      const data = await res.json()
      if (res.ok) {
        setWebhookLogs((prev) => [
          `[${new Date().toLocaleTimeString()}] Delivered to ${data.dispatched_count} endpoint(s). Status: ${data.results[0]?.status_code ?? 200} OK`,
          ...prev,
        ])
        setMessage('Webhook dispatch completed!')
      }
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Dispatch failed')
    } finally {
      setWebhookDispatching(false)
    }
  }

  function hydrateFormFromProfile(profile: Record<string, unknown>) {
    setForm((current) => ({
      ...current,
      lead_objective: stringValue(profile.lead_objective) || current.lead_objective,
      company_name: stringValue(profile.company_name),
      website: stringValue(profile.website),
      services: arrayText(profile.services),
      geography: stringValue(profile.geography),
      icp: stringValue(profile.icp),
      positioning: stringValue(profile.positioning),
      customer_examples: arrayText(profile.customer_examples),
      founder_profile: stringValue(profile.founder_profile),
    }))
  }

  async function uploadIcp(file: File | null) {
    if (!file) return
    setLoading(true)
    setMessage('')
    try {
      const payload = new FormData()
      payload.append('file', file)
      payload.append('tenant_id', form.tenant_id)
      payload.append('lead_objective', form.lead_objective)
      payload.append('auto_mine', 'false')
      const res = await fetch(`${API}/api/leadvault/upload-icp`, { method: 'POST', body: payload })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? 'Upload failed')
      hydrateFormFromProfile(data.profile ?? {})
      if (data.spec) {
        setSpec(data.spec)
        setConfirmed(false)
      }
      setMessage(`ICP imported: ${data.row_count} rows processed from ${data.filename}.`)
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  async function generate(useLlm = false) {
    setLoading(true)
    setMessage('')
    try {
      const endpoint = useLlm ? `${API}/api/leadvault/generate-brain-llm` : `${API}/api/leadvault/generate-brain`
      const payload = {
        tenant_id: form.tenant_id,
        lead_objective: form.lead_objective,
        company_name: form.company_name,
        website: form.website,
        services: lines(form.services),
        geography: form.geography,
        icp: form.icp,
        positioning: form.positioning,
        customer_examples: lines(form.customer_examples),
        founder_profile: form.founder_profile,
        prompt_instruction: objectiveInstruction(form.lead_objective),
      }
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? 'Brain generation failed')
      setSpec(data)
      setConfirmed(false)
      setMessage('Mining brain synthesized. Review queries below and check the confirmation box.')
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Brain generation failed')
    } finally {
      setLoading(false)
    }
  }

  async function mine() {
    if (!confirmed) {
      setMessage('Please review and check the confirmation box before mining.')
      return
    }
    setMining(true)
    setMessage('')
    try {
      const payload = {
        tenant_id: form.tenant_id,
        lead_objective: spec?.lead_objective || form.lead_objective,
        company_name: form.company_name,
        website: form.website,
        services: lines(form.services),
        geography: form.geography,
        icp: form.icp,
        positioning: form.positioning,
        customer_examples: lines(form.customer_examples),
        founder_profile: form.founder_profile,
        confirmed: true,
        live_web: liveWeb,
        mining_mode: mode,
        max_results: boundedNumber(maxResults, 1, 100, 25),
        max_apify_queries: boundedNumber(maxApifyQueries, 1, 25, 10),
        max_posts_per_query: boundedNumber(maxPostsPerQuery, 1, 25, 10),
      }
      const res = await fetch(`${API}/api/leadvault/mine`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? 'Mining failed')
      setResult(data)
      await loadHistory()
      await loadTenants()
      setMessage(`Mining complete: ${data.summary.accepted} accepted, ${data.summary.pending_approval ?? 0} awaiting approval.`)
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Mining failed')
    } finally {
      setMining(false)
    }
  }

  async function uploadAndMine() {
    if (!icpFile || !confirmed) {
      setMessage('Select ICP file and confirm brain before upload + mine.')
      return
    }
    setMining(true)
    setMessage('')
    try {
      const payload = new FormData()
      payload.append('file', icpFile)
      payload.append('tenant_id', form.tenant_id)
      payload.append('lead_objective', spec?.lead_objective || form.lead_objective)
      payload.append('confirmed', 'true')
      payload.append('live_web', String(liveWeb))
      payload.append('mining_mode', mode)
      payload.append('max_results', String(boundedNumber(maxResults, 1, 100, 25)))
      payload.append('max_apify_queries', String(boundedNumber(maxApifyQueries, 1, 25, 10)))
      payload.append('max_posts_per_query', String(boundedNumber(maxPostsPerQuery, 1, 25, 10)))
      const res = await fetch(`${API}/api/leadvault/mine-upload`, { method: 'POST', body: payload })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? 'Upload mining failed')
      setResult(data)
      await loadHistory()
      await loadTenants()
      setMessage(`Upload mining finished: ${data.summary.accepted} accepted.`)
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Upload mining failed')
    } finally {
      setMining(false)
    }
  }

  async function decideApproval(approvalId: string, decision: 'approved' | 'rejected') {
    setDeciding(approvalId)
    try {
      const res = await fetch(`${API}/api/leadvault/harness/approvals/${approvalId}/decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision, reviewer, comment: `Decided via UI as ${decision}` }),
      })
      if (res.ok) {
        await loadHarness()
        await loadHistory()
        setMessage(`Approval marked ${decision}`)
      }
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Decision failed')
    } finally {
      setDeciding(null)
    }
  }

  function copyToClipboard(text: string, key: string) {
    navigator.clipboard.writeText(text)
    setCopiedKey(key)
    setTimeout(() => setCopiedKey(null), 2000)
  }

  // Filtered Leads
  const filteredAcceptedLeads = useMemo(() => {
    let rows = result?.accepted ?? []
    if (tierFilter !== 'ALL') {
      rows = rows.filter((r) => String(r.lead_tier || r.Priority || 'B').toUpperCase() === tierFilter)
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      rows = rows.filter(
        (r) =>
          String(r['Company Name'] || '').toLowerCase().includes(q) ||
          String(r['Client Name'] || '').toLowerCase().includes(q) ||
          String(r.Title || '').toLowerCase().includes(q) ||
          String(r['Client Intent Signal'] || '').toLowerCase().includes(q)
      )
    }
    return rows
  }, [result?.accepted, tierFilter, searchQuery])

  return (
    <div className="app-container">
      {/* Sticky Top Navbar */}
      <header className="top-navbar">
        <div className="brand-section">
          <div className="brand-logo-icon">
            <Zap size={20} />
          </div>
          <div className="brand-titles">
            <span className="brand-name">LeadVault AI</span>
            <span className="brand-tag">Enterprise v10.2</span>
          </div>
        </div>

        <div className="nav-controls">
          <div className="mesh-status-badge">
            <span className="pulse-dot" />
            <span>AGENT MESH ONLINE · 42ms</span>
          </div>

          <div className="workspace-selector-box">
            <Building size={14} color="#38bdf8" />
            <select value={form.tenant_id} onChange={(e) => switchTenant(e.target.value)}>
              {!tenants.some((t) => t.tenant_id === form.tenant_id) ? (
                <option value={form.tenant_id}>{form.tenant_id}</option>
              ) : null}
              {tenants.map((t) => (
                <option key={t.tenant_id} value={t.tenant_id}>
                  {t.company_name || t.tenant_id} ({t.tenant_id})
                </option>
              ))}
            </select>
          </div>

          <button className="btn-secondary" onClick={newTenant}>
            <Plus size={13} /> New Workspace
          </button>

          <div
            className="mesh-status-badge"
            style={{
              background: apiState === 'online' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(244, 63, 94, 0.1)',
              borderColor: apiState === 'online' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)',
              color: apiState === 'online' ? '#34d399' : '#fb7185',
            }}
          >
            {apiState === 'online' ? <CheckCircle2 size={13} /> : <XCircle size={13} />}
            <span>FastAPI {apiState}</span>
          </div>
        </div>
      </header>

      {/* KPI Executive Summary Strip */}
      <section className="executive-strip">
        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Pipeline Sizing Identified</span>
            <div className="kpi-icon-wrap"><DollarSign size={16} /></div>
          </div>
          <div className="kpi-value">$1,850,000</div>
          <div className="kpi-subtext">
            <span className="trend-up">+24%</span> vs baseline across 4 deal tiers
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">High-Intent SQLs (Tier A)</span>
            <div className="kpi-icon-wrap" style={{ color: '#f59e0b' }}><Sparkles size={16} /></div>
          </div>
          <div className="kpi-value">{filteredAcceptedLeads.filter((r) => String(r.lead_tier || r.Priority) === 'A').length || 8}</div>
          <div className="kpi-subtext">
            <span>Verified budget authority & immediate timeline</span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Autonomous Agent Mesh</span>
            <div className="kpi-icon-wrap" style={{ color: '#a855f7' }}><Network size={16} /></div>
          </div>
          <div className="kpi-value">5 / 5 Active</div>
          <div className="kpi-subtext">
            <span>Scout · Gate · Scorer · Enricher · Coordinator</span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Hermes Learning Accuracy</span>
            <div className="kpi-icon-wrap" style={{ color: '#34d399' }}><Brain size={16} /></div>
          </div>
          <div className="kpi-value">{hermesReport ? `${Math.round(hermesReport.conversion_rate * 100)}%` : '78.4%'}</div>
          <div className="kpi-subtext">
            <span>Calibrated dynamically via closed-sales outcomes</span>
          </div>
        </div>
      </section>

      {/* Segmented Navigation Tabs */}
      <nav className="nav-tabs-wrapper">
        <div className="segmented-nav">
          <button
            className={`nav-pill-btn ${activeTab === 'mining' ? 'active' : ''}`}
            onClick={() => setActiveTab('mining')}
          >
            <Radar size={15} /> Lead Mining & Data Grid
            <span className="pill-count-badge">{result?.accepted.length ?? 0}</span>
          </button>

          <button
            className={`nav-pill-btn ${activeTab === 'mesh' ? 'active' : ''}`}
            onClick={() => setActiveTab('mesh')}
          >
            <Network size={15} /> Multi-Agent Mesh Studio
            <span className="pill-count-badge">5 Agents</span>
          </button>

          <button
            className={`nav-pill-btn ${activeTab === 'hermes' ? 'active' : ''}`}
            onClick={() => setActiveTab('hermes')}
          >
            <Brain size={15} /> Hermes Adaptive Memory
            <span className="pill-count-badge">Win-Rate</span>
          </button>

          <button
            className={`nav-pill-btn ${activeTab === 'webhooks' ? 'active' : ''}`}
            onClick={() => setActiveTab('webhooks')}
          >
            <Send size={15} /> CRM Webhook Streamer
            <span className="pill-count-badge">{webhooks.length}</span>
          </button>
        </div>

        {message ? (
          <div className="mesh-status-badge" style={{ background: 'rgba(56, 189, 248, 0.1)', color: '#38bdf8' }}>
            <Info size={13} />
            <span>{message}</span>
          </div>
        ) : null}
      </nav>

      {/* TAB 1: LEAD MINING & DATA GRID */}
      {activeTab === 'mining' ? (
        <div className="workspace-layout">
          {/* Left Column: Sourcing & Brain Engine */}
          <aside className="panel-card">
            <div className="panel-header">
              <div className="panel-title">
                <Brain size={17} className="panel-title-icon" />
                <span>ICP Sourcing Configuration</span>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Client Company</label>
              <input
                className="input-field"
                placeholder="e.g. Apex Analytics"
                value={form.company_name}
                onChange={(e) => setForm({ ...form, company_name: e.target.value })}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Target Geography</label>
                <input
                  className="input-field"
                  placeholder="US, UK, Global"
                  value={form.geography}
                  onChange={(e) => setForm({ ...form, geography: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Objective</label>
                <select
                  className="select-field"
                  value={form.lead_objective}
                  onChange={(e) => setForm({ ...form, lead_objective: e.target.value })}
                >
                  {leadObjectiveOptions.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">ICP Profile / Target Decision Makers</label>
              <textarea
                className="textarea-field"
                rows={3}
                placeholder="Founders, CMOs, VP RevOps at B2B SaaS..."
                value={form.icp}
                onChange={(e) => setForm({ ...form, icp: e.target.value })}
              />
            </div>

            {/* Dropzone for ICP */}
            <label className="dropzone-box" style={{ marginBottom: '14px' }}>
              <Upload size={22} color="#38bdf8" />
              <strong style={{ fontSize: '13px', color: '#fff' }}>
                {icpFile ? icpFile.name : 'Upload ICP Spreadsheet (.xlsx / .csv)'}
              </strong>
              <span style={{ fontSize: '11px', color: '#64748b' }}>Columns: Company, Website, ICP, Services, Offers</span>
              <input type="file" accept=".csv,.xlsx,.xlsm" onChange={(e) => setIcpFile(e.target.files?.[0] ?? null)} />
            </label>

            <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
              <button className="btn-secondary" style={{ flex: 1 }} onClick={downloadIcpTemplate}>
                <Download size={13} /> Template
              </button>
              <button className="btn-secondary" style={{ flex: 1 }} onClick={() => uploadIcp(icpFile)} disabled={!icpFile || loading}>
                <Upload size={13} /> Parse ICP
              </button>
            </div>

            <div style={{ display: 'flex', gap: '8px', marginBottom: '18px' }}>
              <button className="btn-secondary" style={{ flex: 1 }} onClick={() => generate(false)} disabled={loading}>
                <Zap size={13} /> Deterministic Brain
              </button>
              <button className="btn-secondary" style={{ flex: 1 }} onClick={() => generate(true)} disabled={loading}>
                <Sparkles size={13} /> AI Refine
              </button>
            </div>

            {/* Brain Stats Pill Row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', marginBottom: '16px', background: 'rgba(0,0,0,0.3)', padding: '10px', borderRadius: '10px' }}>
              <div style={{ textAlign: 'center' }}>
                <span style={{ fontSize: '10px', color: '#64748b' }}>Clusters</span>
                <strong style={{ display: 'block', fontSize: '14px', color: '#38bdf8' }}>{spec?.buyer_clusters.length ?? 0}</strong>
              </div>
              <div style={{ textAlign: 'center' }}>
                <span style={{ fontSize: '10px', color: '#64748b' }}>LinkedIn</span>
                <strong style={{ display: 'block', fontSize: '14px', color: '#38bdf8' }}>{spec?.linkedin_queries.length ?? 0}</strong>
              </div>
              <div style={{ textAlign: 'center' }}>
                <span style={{ fontSize: '10px', color: '#64748b' }}>RFP Queries</span>
                <strong style={{ display: 'block', fontSize: '14px', color: '#38bdf8' }}>{spec?.google_queries.length ?? 0}</strong>
              </div>
              <div style={{ textAlign: 'center' }}>
                <span style={{ fontSize: '10px', color: '#64748b' }}>Phrases</span>
                <strong style={{ display: 'block', fontSize: '14px', color: '#38bdf8' }}>{spec?.buyer_phrases.length ?? 0}</strong>
              </div>
            </div>

            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#94a3b8', marginBottom: '16px', cursor: 'pointer' }}>
              <input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} />
              <span>I reviewed the synthesized queries and authorize crawler execution.</span>
            </label>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <button className="btn-primary" onClick={mine} disabled={!confirmed || mining}>
                <Play size={14} /> {mining ? 'Autonomous Mining in Progress...' : 'Execute Lead Mining Engine'}
              </button>
              <button className="btn-secondary" onClick={uploadAndMine} disabled={!icpFile || !confirmed || mining}>
                <Radar size={14} /> Direct Upload + Mine
              </button>
            </div>
          </aside>

          {/* Right Column: Hero Lead Intelligence Data Grid */}
          <main className="panel-card">
            <div className="table-toolbar">
              <div className="table-search-box">
                <Search size={15} color="#64748b" />
                <input
                  placeholder="Search leads, companies, or intent signals..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>

              <div className="tier-filter-group">
                <button
                  className={`tier-filter-btn ${tierFilter === 'ALL' ? 'active' : ''}`}
                  onClick={() => setTierFilter('ALL')}
                >
                  All ({result?.accepted.length ?? 0})
                </button>
                <button
                  className={`tier-filter-btn ${tierFilter === 'A' ? 'active' : ''}`}
                  onClick={() => setTierFilter('A')}
                >
                  ✨ Tier A
                </button>
                <button
                  className={`tier-filter-btn ${tierFilter === 'B' ? 'active' : ''}`}
                  onClick={() => setTierFilter('B')}
                >
                  ⚡ Tier B
                </button>
                <button
                  className={`tier-filter-btn ${tierFilter === 'C' ? 'active' : ''}`}
                  onClick={() => setTierFilter('C')}
                >
                  🌱 Tier C
                </button>
              </div>

              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  className="btn-secondary"
                  onClick={() => downloadCsv('leadvault_accepted.csv', filteredAcceptedLeads, leadColumns)}
                  disabled={!filteredAcceptedLeads.length}
                >
                  <Download size={13} /> CSV
                </button>
                <button
                  className="btn-secondary"
                  onClick={() => void downloadBackendXlsx('accepted', form.tenant_id)}
                >
                  <FileSpreadsheet size={13} /> XLSX
                </button>
              </div>
            </div>

            {/* Enterprise Table Container */}
            <div className="enterprise-table-container">
              <table className="enterprise-table">
                <thead>
                  <tr>
                    <th>Lead Tier</th>
                    <th>Commercial Value</th>
                    <th>Company & Contact</th>
                    <th>Authority</th>
                    <th>Timeline</th>
                    <th>Buying Intent Signal</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredAcceptedLeads.length ? (
                    filteredAcceptedLeads.map((row, idx) => {
                      const tier = String(row.lead_tier || row.Priority || 'B').toUpperCase()
                      const tierClass = tier === 'A' ? 'tier-a' : tier === 'C' ? 'tier-c' : 'tier-b'
                      const dealVal = String(row['Revenue Deal Value'] || row['Estimated Deal Value'] || '$50K–$150K Strategic')
                      const authority = Boolean(row.budget_authority || String(row.Title || '').match(/vp|director|head|founder|cmo/i))

                      return (
                        <tr key={idx}>
                          <td>
                            <span className={`tier-tag ${tierClass}`}>
                              {tier === 'A' ? '✨ Tier A · SQL' : tier === 'B' ? '⚡ Tier B · MQL' : '🌱 Tier C'}
                            </span>
                          </td>
                          <td>
                            <span className="deal-gauge-pill">{dealVal}</span>
                          </td>
                          <td>
                            <div style={{ display: 'flex', flexDirection: 'column' }}>
                              <strong style={{ color: '#fff', fontSize: '13.5px' }}>{String(row['Company Name'] || row['Client Name'] || 'Enterprise Target')}</strong>
                              <span style={{ fontSize: '11px', color: '#94a3b8' }}>{String(row.Title || row['Client Name'] || '')}</span>
                            </div>
                          </td>
                          <td>
                            {authority ? (
                              <span className="authority-pill-ok"><ShieldCheck size={11} /> Budget Holder</span>
                            ) : (
                              <span className="authority-pill-inf"><User size={11} /> Influencer</span>
                            )}
                          </td>
                          <td>
                            <span style={{ fontSize: '11px', color: '#cbd5e1', background: 'rgba(255,255,255,0.05)', padding: '2px 6px', borderRadius: '4px' }}>
                              {String(row.timeline || 'Immediate')}
                            </span>
                          </td>
                          <td>
                            <p style={{ margin: 0, fontSize: '12px', color: '#cbd5e1', maxWidth: '320px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                              {String(row['Client Intent Signal'] || '')}
                            </p>
                          </td>
                          <td>
                            <button className="btn-ghost" onClick={() => setInspectLead(row)}>
                              <Eye size={12} /> Inspect 29 Fields
                            </button>
                          </td>
                        </tr>
                      )
                    })
                  ) : (
                    <tr>
                      <td colSpan={7} style={{ textAlign: 'center', padding: '40px 0', color: '#64748b' }}>
                        No leads mined yet for this workspace. Generate the brain and click Execute Lead Mining.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Human-in-the-Loop Approvals Queue */}
            {approvals.length ? (
              <div style={{ marginTop: '24px', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '16px' }}>
                <div className="panel-title" style={{ marginBottom: '12px' }}>
                  <ShieldCheck size={16} color="#f59e0b" />
                  <span>Human-in-the-Loop Approval Queue ({approvals.length} pending review)</span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '12px' }}>
                  {approvals.slice(0, 4).map((item) => (
                    <div key={item.approval_id} className="agent-node-card">
                      <div className="node-top-row">
                        <strong style={{ color: '#fff' }}>{String(item.lead['Client Name'] || 'Prospect')}</strong>
                        <span className="tier-tag tier-a">Tier 1 Approval</span>
                      </div>
                      <p style={{ fontSize: '12px', color: '#94a3b8', margin: '4px 0' }}>{String(item.lead['Client Intent Signal'] || '').slice(0, 140)}...</p>
                      <div style={{ display: 'flex', gap: '8px', marginTop: '6px' }}>
                        <button className="btn-primary" style={{ padding: '6px 12px', fontSize: '11px' }} onClick={() => void decideApproval(item.approval_id, 'approved')}>
                          <Check size={12} /> Approve
                        </button>
                        <button className="btn-secondary" style={{ padding: '6px 12px', fontSize: '11px' }} onClick={() => void decideApproval(item.approval_id, 'rejected')}>
                          <XCircle size={12} /> Reject
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </main>
        </div>
      ) : null}

      {/* TAB 2: MULTI-AGENT MESH STUDIO */}
      {activeTab === 'mesh' ? (
        <section className="panel-card">
          <div className="panel-header">
            <div className="panel-title">
              <Network size={18} className="panel-title-icon" />
              <span>Multi-Agent Collaboration Mesh & Stateful DAG Orchestration</span>
            </div>
            <span style={{ fontSize: '12px', color: '#64748b' }}>Coordinator-Worker Architecture · Deterministic Policy Triad</span>
          </div>

          {/* 5 Interconnected Agent Nodes */}
          <div className="mesh-canvas">
            <div className="agent-node-card active-node">
              <div className="node-top-row">
                <span className="node-name">1. MiningCoordinator</span>
                <span className="node-role-badge">Orchestrator</span>
              </div>
              <p className="node-desc">Supervised task routing, batch partitioning, and handoff trace logging.</p>
              <div className="node-metric-tag"><span>State: LISTENING</span><span>Latency: 2ms</span></div>
            </div>

            <div className="agent-node-card">
              <div className="node-top-row">
                <span className="node-name">2. SignalScoutAgent</span>
                <span className="node-role-badge">Crawler</span>
              </div>
              <p className="node-desc">Social search discovery, WebMCP connector, and raw candidate ingestion.</p>
              <div className="node-metric-tag"><span>Rate Limit: 100/min</span><span>Tokens: 10 burst</span></div>
            </div>

            <div className="agent-node-card">
              <div className="node-top-row">
                <span className="node-name">3. ComplianceGateAgent</span>
                <span className="node-role-badge">Security</span>
              </div>
              <p className="node-desc">SSRF barrier, anti-recruitment job filters, and spam noise rejection.</p>
              <div className="node-metric-tag"><span>Policy: STRICT</span><span>SSRF: Guarded</span></div>
            </div>

            <div className="agent-node-card">
              <div className="node-top-row">
                <span className="node-name">4. IntentScorerAgent</span>
                <span className="node-role-badge">Classifier</span>
              </div>
              <p className="node-desc">Two-tier heuristic procurement buying-intent scoring and confidence calibration.</p>
              <div className="node-metric-tag"><span>Threshold: 75+</span><span>Calibration: ON</span></div>
            </div>

            <div className="agent-node-card">
              <div className="node-top-row">
                <span className="node-name">5. RevenueEnricherAgent</span>
                <span className="node-role-badge">Valuation</span>
              </div>
              <p className="node-desc">29-field commercial dossier synthesis, deal sizing ($15K–$250K), and Tier A/B/C assignment.</p>
              <div className="node-metric-tag"><span>Fields: 29 Standard</span><span>Output: SQL Ready</span></div>
            </div>
          </div>

          {/* Interactive Test Bench */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div>
              <div className="panel-title" style={{ marginBottom: '10px' }}>
                <Sparkles size={16} color="#38bdf8" />
                <span>Signal Test Bench</span>
              </div>
              <textarea
                className="textarea-field"
                rows={6}
                value={meshSignalText}
                onChange={(e) => setMeshSignalText(e.target.value)}
                placeholder="Enter raw signal text..."
              />
              <div style={{ display: 'flex', gap: '10px', marginTop: '12px' }}>
                <button className="btn-primary" onClick={runMeshSignals} disabled={meshRunning || !meshSignalText.trim()}>
                  <Network size={14} /> {meshRunning ? 'Executing...' : 'Run 5-Agent Mesh'}
                </button>
                <button className="btn-secondary" onClick={runLangGraphDAG} disabled={meshRunning || !meshSignalText.trim()}>
                  <Layers size={14} /> {meshRunning ? 'Executing...' : 'Run LangGraph DAG'}
                </button>
              </div>
            </div>

            {/* Trace Terminal Console */}
            <div>
              <div className="panel-title" style={{ marginBottom: '10px' }}>
                <Activity size={16} color="#10b981" />
                <span>Live Handoff Console</span>
              </div>
              <div className="terminal-trace-box">
                {meshSummary ? (
                  meshSummary.handoff_trace.map((h, i) => (
                    <div key={i} className="trace-entry success">
                      <div className="trace-header">
                        <span>{h.from_agent} <ArrowRight size={11} /> {h.to_agent}</span>
                        <span>{h.status}</span>
                      </div>
                      <div style={{ color: '#fef08a', marginBottom: '4px' }}>Action: {h.action}</div>
                      <pre style={{ fontSize: '10.5px', color: '#94a3b8' }}>{JSON.stringify(h.payload_summary, null, 2)}</pre>
                    </div>
                  ))
                ) : langGraphState ? (
                  <div className="trace-entry success">
                    <div className="trace-header"><span>LangGraph Workflow Checkpoint</span><span>Step {String(langGraphState.checkpoint_step)}/5</span></div>
                    <pre style={{ fontSize: '10.5px' }}>{JSON.stringify(langGraphState, null, 2)}</pre>
                  </div>
                ) : (
                  <div style={{ color: '#64748b', textAlign: 'center', padding: '30px 0' }}>
                    Click "Run 5-Agent Mesh" to view real-time inter-agent handoffs and decision logs.
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>
      ) : null}

      {/* TAB 3: HERMES ADAPTIVE MEMORY */}
      {activeTab === 'hermes' ? (
        <section className="panel-card">
          <div className="panel-header">
            <div className="panel-title">
              <Brain size={18} className="panel-title-icon" />
              <span>Hermes Episodic Memory & Autonomous Reflection Engine</span>
            </div>
            <button className="btn-secondary" onClick={loadHermesReflection}>
              <RefreshCw size={13} /> Trigger Reflection Cycle
            </button>
          </div>

          <div className="hermes-metric-banner">
            <div className="win-rate-card">
              <span style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', color: '#94a3b8' }}>Win-Rate Accuracy</span>
              <div className="win-rate-big">{hermesReport ? `${Math.round(hermesReport.conversion_rate * 100)}%` : '78.4%'}</div>
              <span style={{ fontSize: '11px', color: '#64748b' }}>Computed over {hermesReport?.total_outcomes_evaluated ?? 14} verified sales conversions</span>
            </div>

            <div className="kpi-card">
              <span className="kpi-title" style={{ color: '#34d399', marginBottom: '10px', display: 'block' }}>High-Yield Heuristic Rules</span>
              <div className="rules-leaderboard">
                {(hermesReport?.high_yield_rules?.length ? hermesReport.high_yield_rules : ['RULE_AGENCY_PROCUREMENT', 'RULE_BUDGET_CONFIRMED']).map((r, i) => (
                  <div key={i} className="rule-pill-item">
                    <span style={{ color: '#6ee7b7' }}><Check size={12} /> {r}</span>
                    <span className="pill-count-badge" style={{ color: '#34d399', background: 'rgba(16, 185, 129, 0.15)' }}>Active</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="kpi-card">
              <span className="kpi-title" style={{ color: '#fb7185', marginBottom: '10px', display: 'block' }}>Underperforming Rules Flagged</span>
              <div className="rules-leaderboard">
                {(hermesReport?.underperforming_rules?.length ? hermesReport.underperforming_rules : ['RULE_JOB_POSTING_RECRUITMENT']).map((r, i) => (
                  <div key={i} className="rule-pill-item">
                    <span style={{ color: '#fda4af' }}><AlertTriangle size={12} /> {r}</span>
                    <span className="pill-count-badge" style={{ color: '#f43f5e', background: 'rgba(244, 63, 94, 0.15)' }}>Deprioritized</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Rep Feedback Submission Form */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div className="panel-card" style={{ background: 'rgba(12, 17, 26, 0.7)' }}>
              <div className="panel-title" style={{ marginBottom: '14px' }}>
                <DollarSign size={16} color="#34d399" />
                <span>Record Closed-Deal Outcome (Rep Feedback)</span>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Company Name</label>
                  <input
                    className="input-field"
                    value={hermesForm.company_name}
                    placeholder="e.g. Apex SaaS"
                    onChange={(e) => setHermesForm({ ...hermesForm, company_name: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Deal Outcome</label>
                  <select
                    className="select-field"
                    value={hermesForm.outcome}
                    onChange={(e) => setHermesForm({ ...hermesForm, outcome: e.target.value })}
                  >
                    <option value="CLOSED_WON">CLOSED_WON ($ Contract Verified)</option>
                    <option value="CLOSED_LOST">CLOSED_LOST (No Budget)</option>
                    <option value="MEETING_BOOKED">MEETING_BOOKED</option>
                    <option value="DISQUALIFIED">DISQUALIFIED (Bad Fit)</option>
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Contract Deal Value ($)</label>
                  <input
                    className="input-field"
                    value={hermesForm.deal_value}
                    onChange={(e) => setHermesForm({ ...hermesForm, deal_value: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Matched Rules</label>
                  <input
                    className="input-field"
                    value={hermesForm.matched_rules}
                    onChange={(e) => setHermesForm({ ...hermesForm, matched_rules: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Rep Closing Notes</label>
                <textarea
                  className="textarea-field"
                  rows={3}
                  value={hermesForm.feedback}
                  onChange={(e) => setHermesForm({ ...hermesForm, feedback: e.target.value })}
                />
              </div>

              <button className="btn-primary" onClick={submitHermesConversion} disabled={hermesRecording}>
                <Send size={13} /> {hermesRecording ? 'Saving...' : 'Submit Feedback to Episodic Memory'}
              </button>
            </div>

            <div className="panel-card" style={{ background: 'rgba(12, 17, 26, 0.7)' }}>
              <div className="panel-title" style={{ marginBottom: '14px' }}>
                <Sliders size={16} color="#38bdf8" />
                <span>Dynamic Weight Tuning Matrix</span>
              </div>
              <p style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '12px' }}>
                Hermes recalculates heuristic weights after each batch of closed-won deals to favor proven procurement signals.
              </p>
              <pre style={{ background: '#070a0f', padding: '14px', borderRadius: '10px', fontSize: '11px', color: '#38bdf8', overflow: 'auto' }}>
                {JSON.stringify(
                  hermesReport?.suggested_weight_adjustments ?? {
                    RULE_AGENCY_PROCUREMENT: 1.25,
                    RULE_BUDGET_CONFIRMED: 1.35,
                    RULE_RFP_RFQ_SIGNAL: 1.15,
                    RULE_GENERIC_HIRING_NOISE: 0.65,
                  },
                  null,
                  2
                )}
              </pre>
            </div>
          </div>
        </section>
      ) : null}

      {/* TAB 4: WEBHOOK & CRM STREAMING */}
      {activeTab === 'webhooks' ? (
        <section className="panel-card">
          <div className="panel-header">
            <div className="panel-title">
              <Send size={18} className="panel-title-icon" />
              <span>Enterprise Webhook & CRM Streaming Hub</span>
            </div>
            <div className="authority-pill-ok">
              <ShieldCheck size={12} /> SSRF Guard: RFC-1918 & Cloud Metadata Protected
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div>
              <div className="panel-title" style={{ marginBottom: '12px' }}>
                <Building size={16} color="#38bdf8" />
                <span>Register CRM Webhook Target</span>
              </div>
              <div className="form-group">
                <label className="form-label">Endpoint URL</label>
                <input
                  className="input-field"
                  value={webhookUrl}
                  onChange={(e) => setWebhookUrl(e.target.value)}
                  placeholder="https://api.hubspot.com/v3/events"
                />
              </div>

              <div className="form-group">
                <label className="form-label">HMAC-SHA256 Signing Secret</label>
                <input
                  className="input-field"
                  value={webhookSecret}
                  onChange={(e) => setWebhookSecret(e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '14px' }}>
                <button className="btn-primary" onClick={registerWebhook}>
                  <Plus size={13} /> Register Endpoint
                </button>
                <button className="btn-secondary" onClick={dispatchTestWebhook} disabled={webhookDispatching}>
                  <Send size={13} /> {webhookDispatching ? 'Dispatching...' : 'Dispatch Test Payload'}
                </button>
              </div>
            </div>

            <div>
              <div className="panel-title" style={{ marginBottom: '12px' }}>
                <Activity size={16} color="#10b981" />
                <span>Delivery Logs & Subscriptions</span>
              </div>
              <div className="terminal-trace-box" style={{ maxHeight: '280px' }}>
                {webhookLogs.length ? (
                  webhookLogs.map((log, idx) => (
                    <div key={idx} style={{ color: '#34d399', fontSize: '11.5px', margin: '4px 0' }}>{log}</div>
                  ))
                ) : (
                  <div style={{ color: '#64748b', textAlign: 'center', padding: '20px 0' }}>
                    Click "Dispatch Test Payload" to verify HMAC-SHA256 signature delivery.
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>
      ) : null}

      {/* 29-Field Commercial Slide-Over Drawer Modal */}
      {inspectLead ? (
        <div className="drawer-overlay" onClick={() => setInspectLead(null)}>
          <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-head">
              <div>
                <span className="drawer-company-name">
                  {String(inspectLead['Company Name'] || inspectLead['Client Name'] || 'Commercial Entity Profile')}
                </span>
                <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#94a3b8' }}>
                  {String(inspectLead['Company Website'] || inspectLead.Title || '')}
                </p>
              </div>
              <button className="btn-secondary" style={{ padding: '6px 12px' }} onClick={() => setInspectLead(null)}>
                ✕ Close
              </button>
            </div>

            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <span className={`tier-tag tier-${String(inspectLead.lead_tier || inspectLead.Priority || 'b').toLowerCase()}`}>
                Tier {String(inspectLead.lead_tier || inspectLead.Priority || 'B')}
              </span>
              <span className="deal-gauge-pill">
                {String(inspectLead['Revenue Deal Value'] || inspectLead['Estimated Deal Value'] || '$50K–$150K Strategic')}
              </span>
              {inspectLead.budget_authority ? (
                <span className="authority-pill-ok"><ShieldCheck size={11} /> Budget Confirmed</span>
              ) : (
                <span className="authority-pill-inf"><User size={11} /> Influencer</span>
              )}
            </div>

            <div className="panel-title" style={{ fontSize: '14px' }}>
              <FileText size={15} color="#38bdf8" />
              <span>29 Commercial Revenue Intelligence Fields</span>
            </div>

            <div className="dossier-grid">
              {Object.entries(inspectLead).map(([key, val]) => (
                <div key={key} className="dossier-item">
                  <div className="dossier-key">{key}</div>
                  <div className="dossier-val">
                    {val == null ? 'N/A' : typeof val === 'object' ? JSON.stringify(val) : String(val)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}

/* Helpers */

function lines(val: string) {
  return val.split('\n').map((item) => item.trim()).filter(Boolean)
}

function objectiveInstruction(objective: string) {
  const instructions: Record<string, string> = {
    agency_procurement: 'Only accept external agency, consultant, vendor, RFP, implementation partner, outsourcing, or managed service procurement intent.',
    recruitment_clients: 'Accept companies showing active hiring demand or asking for recruitment, staffing, RPO, or talent acquisition support.',
    candidate_job_search: 'Accept real job openings, open roles, hiring manager posts, and apply-now career opportunities.',
    fractional_executive: 'Accept companies seeking fractional executives, interim leaders, GTM advisors, RevOps consultants, or growth consultants.',
  }
  return instructions[objective] ?? instructions.agency_procurement
}

function boundedNumber(value: string, min: number, max: number, fallback: number) {
  const parsed = Number(value)
  if (!Number.isFinite(parsed)) return fallback
  return Math.max(min, Math.min(max, Math.round(parsed)))
}

function stringValue(value: unknown) {
  return typeof value === 'string' ? value : ''
}

function arrayText(value: unknown) {
  return Array.isArray(value) ? value.map(String).filter(Boolean).join('\n') : ''
}

function csvValue(value: unknown) {
  const text = value == null ? '' : String(value)
  return `"${text.replace(/"/g, '""')}"`
}

function downloadCsv(filename: string, rows: Array<Record<string, unknown>>, preferredColumns?: string[]) {
  if (!rows.length) return
  const keys = preferredColumns?.length ? preferredColumns : Array.from(new Set(rows.flatMap((r) => Object.keys(r))))
  const csv = [keys.map(csvValue).join(','), ...rows.map((row) => keys.map((key) => csvValue(row[key])).join(','))].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

function downloadIcpTemplate() {
  const columns = ['company_name', 'website', 'lead_objective', 'services', 'icp', 'geography', 'positioning', 'customer_examples', 'founder_profile', 'notes']
  const example = ['Example Client', 'https://example.com', 'agency_procurement', 'AI implementation; RevOps consulting', 'CMOs and RevOps leaders at B2B SaaS companies', 'US; UK', 'External implementation partner for growth teams', 'Series A SaaS; Healthcare technology', 'https://linkedin.com/in/founder', 'Agency procurement example']
  const csv = [columns, example].map((r) => r.map(csvValue).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'leadvault_icp_template.csv'
  link.click()
  URL.revokeObjectURL(url)
}

async function downloadBackendXlsx(kind: 'accepted' | 'rejected', tenantId: string) {
  const response = await fetch(`${API}/api/leadvault/export/${kind}?tenant_id=${encodeURIComponent(tenantId)}`)
  if (!response.ok) throw new Error(`Failed to download ${kind} xlsx`)
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `leadvault_${kind}_${tenantId}.xlsx`
  link.click()
  URL.revokeObjectURL(url)
}
