'use client'

import { useEffect, useMemo, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Brain,
  Check,
  CheckCircle2,
  Copy,
  Database,
  DollarSign,
  Download,
  Eye,
  FileSpreadsheet,
  Layers,
  Network,
  Play,
  Plus,
  Radar,
  RefreshCw,
  Send,
  ShieldCheck,
  Sparkles,
  Upload,
  XCircle,
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
type OperationState = 'idle' | 'uploading' | 'generating' | 'mining' | 'analyzing' | 'success' | 'error'
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
  const [historyLoading, setHistoryLoading] = useState(false)
  const [tenants, setTenants] = useState<TenantSummary[]>([])
  const [operation, setOperation] = useState<OperationState>('idle')
  const [approvals, setApprovals] = useState<ApprovalItem[]>([])
  const [workflows, setWorkflows] = useState<WorkflowItem[]>([])
  const [reviewer, setReviewer] = useState('operator')
  const [deciding, setDeciding] = useState<string | null>(null)

  // Drawer modal state for viewing full 29 revenue fields
  const [inspectLead, setInspectLead] = useState<Record<string, unknown> | null>(null)

  // Hermes Learning state
  const [hermesReport, setHermesReport] = useState<HermesReflectionReport | null>(null)
  const [hermesForm, setHermesForm] = useState({
    lead_id: 'lead-001',
    company_name: '',
    outcome: 'CLOSED_WON',
    deal_value: '50000',
    feedback: 'Procurement decision-maker closed within 2 weeks.',
    matched_rules: 'RULE_AGENCY_PROCUREMENT,RULE_BUDGET_CONFIRMED',
  })
  const [hermesRecording, setHermesRecording] = useState(false)

  // Mesh & LangGraph state
  const [meshSignalText, setMeshSignalText] = useState(
    'Looking for an agency partner to rebuild our Shopify Plus store ASAP. Approved budget ready.'
  )
  const [meshRunning, setMeshRunning] = useState(false)
  const [meshSummary, setMeshSummary] = useState<MultiAgentRunSummary | null>(null)
  const [langGraphState, setLangGraphState] = useState<Record<string, unknown> | null>(null)

  // Webhooks state
  const [webhooks, setWebhooks] = useState<WebhookConfigItem[]>([])
  const [webhookUrl, setWebhookUrl] = useState('https://api.hubspot.com/v3/events')
  const [webhookSecret, setWebhookSecret] = useState('whsec_leadvault_live_2026')
  const [webhookDispatching, setWebhookDispatching] = useState(false)
  const [webhookLogs, setWebhookLogs] = useState<string[]>([])

  const readyToGenerate = Boolean(form.company_name.trim() || form.website.trim() || form.icp.trim() || icpFile)
  const acceptedRows = result?.accepted ?? []
  const rejectedRows = result?.rejected ?? []

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
    setMessage(`Workspace switched to ${tenantId}.`)
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
    setMessage('New client workspace ready. Rename it before generating the brain.')
  }

  async function loadHistory() {
    setHistoryLoading(true)
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
    } finally {
      setHistoryLoading(false)
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
      if (res.ok) {
        setHermesReport(await res.json())
      }
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
          candidates: [
            {
              text: meshSignalText,
              title: 'Decision Maker',
              source: 'LinkedIn Live Stream',
            },
          ],
        }),
      })
      if (res.ok) {
        const data = await res.json()
        setMeshSummary(data)
        setMessage(`Mesh execution complete: ${data.total_candidates_processed} processed, ${data.qualified_leads.length} qualified in ${Math.round(data.execution_time_ms)}ms`)
      } else {
        throw new Error('Mesh execution failed')
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
          candidates: [
            {
              text: meshSignalText,
              title: 'VP of Technology',
              source: 'LangGraph Input Stream',
            },
          ],
        }),
      })
      if (res.ok) {
        const data = await res.json()
        setLangGraphState(data)
        setMessage(`LangGraph DAG completed at checkpoint step ${data.checkpoint_step}!`)
      } else {
        throw new Error('LangGraph execution failed')
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
      if (res.ok) {
        const data = await res.json()
        setWebhooks(data.items ?? [])
      }
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
        setMessage('Webhook registered successfully with HMAC-SHA256 signing!')
        await loadWebhooks()
      } else {
        const err = await res.json()
        setMessage(err.detail ?? 'Registration failed')
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
          `[${new Date().toLocaleTimeString()}] Dispatched to ${data.dispatched_count} endpoint(s). Status: ${JSON.stringify(data.results[0] ?? {})}`,
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

  async function uploadIcp(file: File | null, autoMine = false) {
    if (!file) return
    setLoading(true)
    setOperation('uploading')
    setMessage('')
    try {
      const payload = new FormData()
      payload.append('file', file)
      payload.append('tenant_id', form.tenant_id)
      payload.append('lead_objective', form.lead_objective)
      payload.append('auto_mine', String(autoMine))
      const res = await fetch(`${API}/api/leadvault/upload-icp`, { method: 'POST', body: payload })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? 'Upload failed')
      hydrateFormFromProfile(data.profile ?? {})
      if (data.spec) {
        setSpec(data.spec)
        setConfirmed(false)
      }
      setMessage(`ICP imported: ${data.row_count} rows processed from ${data.filename}. Review the form and generate the brain.`)
      setOperation('idle')
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Upload failed')
      setOperation('error')
    } finally {
      setLoading(false)
    }
  }

  async function generate(useLlm = false) {
    setLoading(true)
    setOperation('generating')
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
      setMessage('Mining brain generated. Review the queries and clusters below, then check the confirmation box.')
      setOperation('idle')
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Brain generation failed')
      setOperation('error')
    } finally {
      setLoading(false)
    }
  }

  async function mine() {
    if (!confirmed) {
      setMessage('Please review and confirm the generated mining brain before mining.')
      return
    }
    setMining(true)
    setOperation('mining')
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
      setMessage(`Mining complete: ${data.summary.accepted} accepted, ${data.summary.pending_approval ?? 0} awaiting approval, ${data.summary.rejected} rejected, ${data.summary.candidates_reviewed} reviewed.`)
      setOperation('success')
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Mining failed')
      setOperation('error')
    } finally {
      setMining(false)
    }
  }

  async function uploadAndMine() {
    if (!icpFile) {
      setMessage('Choose a CSV or Excel ICP file first.')
      return
    }
    if (!confirmed) {
      setMessage('Confirm the mining brain before Upload + Mine.')
      return
    }
    setMining(true)
    setOperation('mining')
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
      setMessage(`Upload mining complete: ${data.summary.accepted} accepted, ${data.summary.rejected} rejected from ${data.summary.source_filename}.`)
      setOperation('success')
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Upload mining failed')
      setOperation('error')
    } finally {
      setMining(false)
    }
  }

  async function analyzeCapture() {
    if (!captureText.trim()) {
      setMessage('Paste LinkedIn posts or search results into the capture box first.')
      return
    }
    setMining(true)
    setOperation('analyzing')
    setMessage('')
    try {
      const res = await fetch(`${API}/api/leadvault/linkedin-capture`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tenant_id: form.tenant_id,
          lead_objective: form.lead_objective,
          posts_text: captureText,
          query: 'linkedin_paste_capture',
          max_results: boundedNumber(maxResults, 1, 100, 25),
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? 'Capture analysis failed')
      setResult(data)
      await loadHistory()
      await loadTenants()
      setMessage(`Capture analyzed: ${data.summary.accepted} accepted, ${data.summary.rejected} rejected, ${data.summary.candidates_reviewed} reviewed.`)
      setOperation('success')
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Capture analysis failed')
      setOperation('error')
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
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail ?? 'Decision rejected by backend')
      }
      await loadHarness()
      await loadHistory()
      setMessage(`Approval ${approvalId} marked ${decision} by ${reviewer}.`)
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Decision failed')
    } finally {
      setDeciding(null)
    }
  }

  function copySnippet() {
    if (!spec?.python_snippet) return
    navigator.clipboard.writeText(spec.python_snippet)
    setMessage('Python query bank snippet copied.')
  }

  const apiBadge = useMemo(() => {
    if (apiState === 'online') return { text: 'Backend Live (FastAPI)', tone: 'good' }
    if (apiState === 'checking') return { text: 'Checking...', tone: 'neutral' }
    return { text: 'Backend Offline', tone: 'bad' }
  }, [apiState])

  return (
    <main className="shell">
      <section className="hero">
        <div>
          <p className="eyebrow">LeadVault Enterprise Agentic AI</p>
          <h1>Autonomous Lead Mining, ICP Intelligence & Revenue Orchestration.</h1>
          <p className="hero-copy">
            Enterprise procurement intelligence engine: ICP matching, 29-field deal valuation ($15K–$250K), 5-agent mesh collaboration, Hermes adaptive memory, and HMAC-signed CRM webhooks.
          </p>
        </div>
        <div className={`status ${apiBadge.tone}`}>
          {apiState === 'online' ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
          <span>{apiBadge.text}</span>
          <button className="ghost" onClick={checkApi}>Recheck</button>
        </div>
      </section>

      {/* Enterprise Tab Navigation */}
      <nav className="tab-nav">
        <button
          className={`tab-btn ${activeTab === 'mining' ? 'active' : ''}`}
          onClick={() => setActiveTab('mining')}
        >
          <Radar size={16} /> Lead Mining & ICP Engine
        </button>
        <button
          className={`tab-btn ${activeTab === 'mesh' ? 'active' : ''}`}
          onClick={() => setActiveTab('mesh')}
        >
          <Network size={16} /> Multi-Agent Mesh & LangGraph
        </button>
        <button
          className={`tab-btn ${activeTab === 'hermes' ? 'active' : ''}`}
          onClick={() => setActiveTab('hermes')}
        >
          <Brain size={16} /> Hermes Adaptive Memory
        </button>
        <button
          className={`tab-btn ${activeTab === 'webhooks' ? 'active' : ''}`}
          onClick={() => setActiveTab('webhooks')}
        >
          <Send size={16} /> Webhook & CRM Streaming
        </button>
      </nav>

      {/* Global Workspace Bar */}
      <section className="workspace-bar">
        <div>
          <span className="workspace-label">Active Workspace</span>
          <select value={form.tenant_id} onChange={(event) => switchTenant(event.target.value)}>
            {!tenants.some((item) => item.tenant_id === form.tenant_id) ? <option value={form.tenant_id}>{form.tenant_id}</option> : null}
            {tenants.map((tenant) => <option key={tenant.tenant_id} value={tenant.tenant_id}>{tenant.company_name} ({tenant.tenant_id})</option>)}
          </select>
        </div>
        <div className="workspace-actions">
          <span>{tenants.length} saved workspace{tenants.length === 1 ? '' : 's'}</span>
          <button onClick={() => void loadTenants()}><RefreshCw size={14} /> Refresh</button>
          <button onClick={newTenant}><Plus size={14} /> New Client</button>
        </div>
      </section>

      {/* TAB 1: LEAD MINING & ICP ENGINE */}
      {activeTab === 'mining' ? (
        <>
          <section className="steps">
            <Step number="1" title="Client Details" active />
            <Step number="2" title="ICP Upload" active={Boolean(icpFile)} />
            <Step number="3" title="Mining Brain" active={Boolean(spec)} />
            <Step number="4" title="Accepted Leads" active={Boolean(result)} />
          </section>

          <section className="grid two">
            <div className="panel raised">
              <div className="panel-title"><Brain size={17} /> Client Details</div>
              <Input label="Tenant / Client Workspace" placeholder="acme-ai-agency" value={form.tenant_id} onChange={(v) => setForm({ ...form, tenant_id: v })} />
              <label>
                <span>Lead Mining Objective</span>
                <select value={form.lead_objective} onChange={(event) => setForm({ ...form, lead_objective: event.target.value })}>
                  {leadObjectiveOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                </select>
              </label>
              <p className="muted objective-hint">{leadObjectiveOptions.find((option) => option.value === form.lead_objective)?.hint}</p>
              <div className="grid two no-margin">
                <Input label="Client Company" placeholder="Client name" value={form.company_name} onChange={(v) => setForm({ ...form, company_name: v })} />
                <Input label="Website" placeholder="https://client.com" value={form.website} onChange={(v) => setForm({ ...form, website: v })} />
              </div>
              <Input label="Target Geography" placeholder="US, UK, India, Global..." value={form.geography} onChange={(v) => setForm({ ...form, geography: v })} />
              <Textarea label="Services / Offers" placeholder="AI implementation&#10;RevOps consulting&#10;SEO agency services" value={form.services} onChange={(v) => setForm({ ...form, services: v })} rows={4} />
              <Textarea label="ICP / Buyer Profile" placeholder="Founders, CMOs, RevOps leaders at B2B SaaS companies..." value={form.icp} onChange={(v) => setForm({ ...form, icp: v })} rows={4} />
              <Textarea label="Positioning / Value Proposition" placeholder="What the client sells, why buyers choose them, proof points..." value={form.positioning} onChange={(v) => setForm({ ...form, positioning: v })} rows={4} />
              <Textarea label="Sample Clients / Industries / Examples" placeholder="Healthcare SaaS&#10;B2B agencies&#10;Series A startups" value={form.customer_examples} onChange={(v) => setForm({ ...form, customer_examples: v })} rows={3} />
              <Input label="Founder / LinkedIn Notes" placeholder="Founder profile or LinkedIn URL" value={form.founder_profile} onChange={(v) => setForm({ ...form, founder_profile: v })} />
            </div>

            <div className="panel raised">
              <div className="panel-title"><FileSpreadsheet size={17} /> ICP Upload + Brain Controls</div>
              <label className="dropzone">
                <Upload size={22} />
                <strong>{icpFile ? icpFile.name : 'Upload client ICP Excel or CSV'}</strong>
                <span>Accepted: .xlsx, .xlsm, .xls, .csv. Columns can include company, website, services, ICP, geography, positioning, industries, notes.</span>
                <input type="file" accept=".csv,.xlsx,.xlsm,.xls" onChange={(e) => setIcpFile(e.target.files?.[0] ?? null)} />
              </label>
              <div className="actions">
                <button onClick={downloadIcpTemplate}><Download size={14} /> ICP Template</button>
                <button onClick={() => uploadIcp(icpFile, false)} disabled={!icpFile || loading}><Upload size={14} /> Upload ICP</button>
                <button onClick={() => generate(false)} disabled={!readyToGenerate || loading}>{loading ? 'Generating...' : 'Generate Brain'}</button>
                <button onClick={() => generate(true)} disabled={!readyToGenerate || loading}>AI Refine</button>
              </div>

              <div className="divider" />

              <div className="metrics">
                <Metric label="Clusters" value={spec?.buyer_clusters.length ?? 0} />
                <Metric label="LinkedIn" value={spec?.linkedin_queries.length ?? 0} />
                <Metric label="Google/RFP" value={spec?.google_queries.length ?? 0} />
                <Metric label="Buyer Phrases" value={spec?.buyer_phrases.length ?? 0} />
              </div>
              {spec?.objective_label ? <p className="muted">Active objective: {spec.objective_label}</p> : null}

              <label className="confirm">
                <input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} />
                <span>I reviewed the generated mining brain and approve mining/API usage.</span>
              </label>

              <div className="grid three no-margin">
                <label>
                  <span>Mode</span>
                  <select value={mode} onChange={(e) => setMode(e.target.value)}>
                    <option value="hybrid">Hybrid</option>
                    <option value="apify">Apify only</option>
                    <option value="public_web">Public web only</option>
                  </select>
                </label>
                <Input label="Max Results" value={maxResults} onChange={setMaxResults} />
                <Input label="Apify Queries" value={maxApifyQueries} onChange={setMaxApifyQueries} />
              </div>
              <div className="grid two no-margin">
                <Input label="Posts Per Query" value={maxPostsPerQuery} onChange={setMaxPostsPerQuery} />
                <label className="toggle">
                  <input type="checkbox" checked={liveWeb} onChange={(e) => setLiveWeb(e.target.checked)} />
                  <span>Live web / Apify enabled</span>
                </label>
              </div>

              <div className="actions">
                <button className="primary" onClick={mine} disabled={!confirmed || mining}><Play size={14} /> {mining ? 'Mining...' : 'Mine Client Details'}</button>
                <button onClick={uploadAndMine} disabled={!icpFile || !confirmed || mining}><Radar size={14} /> Upload + Mine</button>
                <button onClick={copySnippet} disabled={!spec?.python_snippet}><Copy size={14} /> Copy Python</button>
              </div>

              {operation !== 'idle' ? (
                <div className={`operation ${operation}`} aria-live="polite">
                  <div className="operation-row"><strong>{operationLabel(operation)}</strong><span>{operation === 'success' || operation === 'error' ? 'Finished' : 'Please keep this page open'}</span></div>
                  {operation !== 'success' && operation !== 'error' ? <div className="progress"><span /></div> : null}
                </div>
              ) : null}
              {message ? <div className={`message ${operation === 'error' ? 'error' : ''}`}>{message}</div> : null}
            </div>
          </section>

          <section className="grid three">
            <List title="LinkedIn Search URLs / Queries" items={spec?.linkedin_queries ?? []} />
            <List title="Google + Procurement Queries" items={spec?.google_queries ?? []} />
            <List title="Buyer Intent Phrases" items={spec?.buyer_phrases ?? []} />
          </section>

          <section className="grid two">
            <div className="panel">
              <div className="panel-title"><Radar size={17} /> LinkedIn Paste Capture</div>
              <p className="muted">For LinkedIn, paste copied posts/search-result text here. LeadVault classifies rows according to the selected objective, then exports only valid matches.</p>
              <Textarea label="LinkedIn posts or rows" value={captureText} onChange={setCaptureText} rows={8} placeholder="Paste LinkedIn post text here..." />
              <div className="actions">
                <button onClick={analyzeCapture} disabled={mining || !captureText.trim()}><Radar size={14} /> Analyze Capture</button>
              </div>
            </div>

            <div className="panel">
              <div className="panel-title"><Download size={17} /> Export Center</div>
              <div className="metrics two-metrics">
                <Metric label="Accepted" value={acceptedRows.length} />
                <Metric label="Rejected" value={rejectedRows.length} />
              </div>
              <div className="actions">
                <button onClick={() => downloadCsv('leadvault_accepted.csv', acceptedRows, leadColumns)} disabled={!acceptedRows.length}><Download size={14} /> Accepted CSV</button>
                <button onClick={() => downloadCsv('leadvault_rejected.csv', rejectedRows)} disabled={!rejectedRows.length}><Download size={14} /> Rejected CSV</button>
                <button onClick={() => void downloadBackendXlsx('accepted', form.tenant_id).catch((error) => setMessage(error instanceof Error ? error.message : 'Failed to download accepted XLSX'))}><Download size={14} /> Accepted XLSX</button>
                <button onClick={() => void downloadBackendXlsx('rejected', form.tenant_id).catch((error) => setMessage(error instanceof Error ? error.message : 'Failed to download rejected XLSX'))}><Download size={14} /> Rejected XLSX</button>
              </div>
              <p className="muted">Accepted rows are also persisted by the backend audit/export stores when mining runs.</p>
            </div>
          </section>

          {/* Approvals Queue & Workflow Activity */}
          <section className="grid two">
            <div className="panel raised">
              <div className="panel-title"><ShieldCheck size={17} /> Approvals Queue ({approvals.length})</div>
              <p className="muted">Tier-1 (hot) leads are parked here by policy P-ACCEPT-02. Nothing reaches the accepted export until a named reviewer decides.</p>
              <Input label="Reviewer (recorded on every decision)" value={reviewer} onChange={setReviewer} placeholder="your name" />
              {approvals.length ? (
                <div className="approval-list">
                  {approvals.slice(0, 8).map((item) => (
                    <div key={item.approval_id} className="approval-item">
                      <div className="approval-head">
                        <strong>{String(item.lead['Client Name'] ?? 'Unknown')}</strong>
                        <span className="pill">score {String(item.lead.intent_score ?? '?')}</span>
                        <span className="pill">{String(item.lead.category ?? '')}</span>
                        {item.evidence?.llm?.verdict ? <span className="pill">llm: {item.evidence.llm.verdict}</span> : null}
                      </div>
                      <p className="approval-text">{String(item.lead['Client Intent Signal'] ?? '').slice(0, 260)}</p>
                      <p className="muted small">
                        Why: {(item.evidence?.evidence ?? []).slice(0, 4).join(', ') || 'no rule evidence'}
                        {item.evidence?.negative_signals?.length ? ` · against: ${item.evidence.negative_signals.slice(0, 3).join(', ')}` : ''}
                        {typeof item.evidence?.confidence === 'number' ? ` · confidence ${Math.round(item.evidence.confidence * 100)}%` : ''}
                      </p>
                      <div className="actions">
                        <button className="primary" disabled={deciding === item.approval_id} onClick={() => void decideApproval(item.approval_id, 'approved')}><CheckCircle2 size={14} /> Approve</button>
                        <button disabled={deciding === item.approval_id} onClick={() => void decideApproval(item.approval_id, 'rejected')}><XCircle size={14} /> Reject</button>
                        <span className="muted small">{item.recommended_action}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="muted">No leads awaiting review for this workspace.</p>
              )}
            </div>

            <div className="panel">
              <div className="panel-title"><Activity size={17} /> Agent Activity ({workflows.length})</div>
              <p className="muted">Each mining run is an explicit workflow. Every state change and tool call is audited.</p>
              {workflows.length ? (
                <div className="history-list">
                  {workflows.slice(0, 6).map((wf) => (
                    <details key={wf.workflow_id} className="history-item">
                      <summary>
                        <span className={`state state-${wf.state.toLowerCase()}`}>{wf.state}</span> {wf.workflow_id} · {wf.objective}
                        {typeof wf.metrics?.latency_seconds === 'number' ? ` · ${wf.metrics.latency_seconds}s` : ''}
                        {typeof wf.metrics?.estimated_cost_usd === 'number' ? ` · ~$${wf.metrics.estimated_cost_usd.toFixed(3)}` : ''}
                      </summary>
                      <div className="history-detail">
                        <ol className="timeline">
                          {wf.history.map((h, i) => (
                            <li key={i}><code>{h.to}</code> <span className="muted small">by {h.actor}{h.note ? ` — ${h.note}` : ''}</span></li>
                          ))}
                        </ol>
                        {wf.metrics?.tool_calls && Object.keys(wf.metrics.tool_calls).length ? (
                          <p className="muted small">Tools: {Object.entries(wf.metrics.tool_calls).map(([k, v]) => `${k}×${v}`).join(', ')}
                            {wf.metrics.tool_errors && Object.keys(wf.metrics.tool_errors).length ? ` · errors: ${Object.entries(wf.metrics.tool_errors).map(([k, v]) => `${k}×${v}`).join(', ')}` : ''}
                          </p>
                        ) : <p className="muted small">No external tools called.</p>}
                        {wf.error ? <p className="error small">Error: {wf.error}</p> : null}
                      </div>
                    </details>
                  ))}
                </div>
              ) : (
                <p className="muted">No workflows yet for this workspace.</p>
              )}
            </div>
          </section>

          {/* Leads Table with Enhanced Tiers & Deal Value Gauges */}
          {result ? (
            <section className="grid two">
              <EnhancedLeadsTable
                title={`Accepted Leads (${result.summary.accepted})`}
                rows={acceptedRows}
                onInspect={(lead) => setInspectLead(lead)}
              />
              <Table
                title={`Rejected Audit (${result.summary.rejected})`}
                rows={rejectedRows}
                columns={['rejection_reason', 'category', 'query', 'source', 'text']}
              />
            </section>
          ) : null}

          <section className="grid two">
            <HistoryPanel
              title={`Accepted Run History (${history.accepted_exports.length})`}
              items={history.accepted_exports}
              subtitle={historyLoading ? 'Refreshing...' : 'Recent accepted export runs for this tenant'}
              emptyText="No accepted export history yet."
            />
            <HistoryPanel
              title={`Rejected Audit History (${history.rejected_audits.length})`}
              items={history.rejected_audits}
              subtitle={historyLoading ? 'Refreshing...' : 'Recent rejected audit rows for this tenant'}
              emptyText="No rejected audit history yet."
            />
          </section>
        </>
      ) : null}

      {/* TAB 2: MULTI-AGENT MESH & LANGGRAPH */}
      {activeTab === 'mesh' ? (
        <section className="panel raised">
          <div className="panel-title"><Network size={18} /> Multi-Agent Mesh Architecture & Stateful DAG Execution</div>
          <p className="muted">
            LeadVault deploys a coordinator-worker mesh of 5 specialized autonomous agents communicating through structured handoffs, alongside a 5-node LangGraph stateful pipeline with checkpoint recovery.
          </p>

          <div className="mesh-nodes-grid">
            <div className="mesh-node-card">
              <strong>1. MiningCoordinator</strong>
              <span>Mesh orchestration, candidate assignment, handoff logging & pipeline supervision.</span>
            </div>
            <div className="mesh-node-card">
              <strong>2. SignalScoutAgent</strong>
              <span>Web crawling, social discovery, WebMCP scraping & candidate deduplication.</span>
            </div>
            <div className="mesh-node-card">
              <strong>3. ComplianceGateAgent</strong>
              <span>SSRF protection, anti-recruitment filtering, spam rejection & security policies.</span>
            </div>
            <div className="mesh-node-card">
              <strong>4. IntentScorerAgent</strong>
              <span>Two-tier heuristic buying intent scoring, RFP detection & confidence calibration.</span>
            </div>
            <div className="mesh-node-card">
              <strong>5. RevenueEnricherAgent</strong>
              <span>29-field commercial extraction, deal sizing ($15K–$250K), authority & tier assignment.</span>
            </div>
          </div>

          <div className="grid two">
            <div className="panel">
              <div className="panel-title"><Sparkles size={16} /> Interactive Agent Pipeline Runner</div>
              <p className="muted">Test signals directly across the 5 agents or execute the LangGraph DAG with checkpointing.</p>
              <Textarea
                label="Raw Candidate / Post Text"
                value={meshSignalText}
                onChange={setMeshSignalText}
                rows={5}
                placeholder="Enter post text..."
              />
              <div className="actions">
                <button
                  className="primary"
                  onClick={runMeshSignals}
                  disabled={meshRunning || !meshSignalText.trim()}
                >
                  <Network size={14} /> {meshRunning ? 'Executing...' : 'Run Multi-Agent Mesh'}
                </button>
                <button
                  onClick={runLangGraphDAG}
                  disabled={meshRunning || !meshSignalText.trim()}
                >
                  <Layers size={14} /> {meshRunning ? 'Executing...' : 'Run LangGraph DAG'}
                </button>
              </div>
            </div>

            <div className="panel">
              <div className="panel-title"><Activity size={16} /> Live Handoff Trace & Results</div>
              {meshSummary ? (
                <div className="handoff-box">
                  <div className="metrics two-metrics">
                    <Metric label="Processed" value={meshSummary.total_candidates_processed} />
                    <Metric label="Qualified" value={meshSummary.qualified_leads.length} />
                  </div>
                  <p className="muted small">Execution time: {Math.round(meshSummary.execution_time_ms)}ms · Completed: {meshSummary.completed_at}</p>
                  {meshSummary.handoff_trace.map((h, i) => (
                    <div key={i} className="handoff-card">
                      <div className="handoff-head">
                        <span className="handoff-agents">{h.from_agent} <ArrowRight size={12} /> {h.to_agent}</span>
                        <span className="pill">{h.status}</span>
                      </div>
                      <span className="handoff-action">{h.action}</span>
                      <pre style={{ maxHeight: '100px', fontSize: '11px' }}>{JSON.stringify(h.payload_summary, null, 2)}</pre>
                    </div>
                  ))}
                  {meshSummary.qualified_leads.length ? (
                    <div style={{ marginTop: '10px' }}>
                      <strong>Qualified Lead Output:</strong>
                      <div className="approval-item" style={{ marginTop: '6px' }}>
                        <div className="approval-head">
                          <span className={`tier-badge tier-${String(meshSummary.qualified_leads[0]?.lead_tier ?? 'b').toLowerCase()}`}>
                            Tier {String(meshSummary.qualified_leads[0]?.lead_tier ?? 'B')}
                          </span>
                          <span className="deal-gauge">{String(meshSummary.qualified_leads[0]?.estimated_deal_value ?? '$50K–$150K Strategic')}</span>
                          <span className="authority-pill">{meshSummary.qualified_leads[0]?.budget_authority ? 'Budget Confirmed' : 'Influencer'}</span>
                        </div>
                        <p className="approval-text">{String(meshSummary.qualified_leads[0]?.text ?? '')}</p>
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : langGraphState ? (
                <div className="handoff-box">
                  <div className="status good" style={{ marginBottom: '10px' }}>
                    <CheckCircle2 size={16} />
                    <span>LangGraph Pipeline Status: {String(langGraphState.status)} (Step {String(langGraphState.checkpoint_step)}/5)</span>
                  </div>
                  <p className="muted small">Workflow ID: {String(langGraphState.workflow_id)}</p>
                  <pre>{JSON.stringify({
                    current_node: langGraphState.current_node,
                    compliance_passed: Array.isArray(langGraphState.compliance_passed) ? langGraphState.compliance_passed.length : 0,
                    enriched_leads: Array.isArray(langGraphState.enriched_leads) ? langGraphState.enriched_leads.length : 0,
                    final_accepted: Array.isArray(langGraphState.final_accepted) ? langGraphState.final_accepted.length : 0,
                    final_pending: Array.isArray(langGraphState.final_pending) ? langGraphState.final_pending.length : 0,
                  }, null, 2)}</pre>
                </div>
              ) : (
                <p className="muted">Run the interactive pipeline runner to visualize live multi-agent handoffs.</p>
              )}
            </div>
          </div>
        </section>
      ) : null}

      {/* TAB 3: HERMES ADAPTIVE MEMORY */}
      {activeTab === 'hermes' ? (
        <section className="panel raised">
          <div className="panel-title"><Brain size={18} /> Hermes Episodic Memory & Reflection Engine</div>
          <p className="muted">
            Hermes closes the feedback loop between closed deals and buying intent heuristics, continuously adjusting scoring weights based on verified sales outcomes.
          </p>

          <div className="hermes-grid" style={{ marginBottom: '20px' }}>
            <div className="hermes-stat-card">
              <span className="workspace-label">Conversion Rate</span>
              <div className="hermes-metric-big">
                {hermesReport ? `${Math.round(hermesReport.conversion_rate * 100)}%` : '0%'}
              </div>
              <span className="muted small">Based on {hermesReport?.total_outcomes_evaluated ?? 0} closed sales outcomes</span>
            </div>

            <div className="hermes-stat-card">
              <span className="workspace-label">High-Yield Heuristic Rules</span>
              <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {(hermesReport?.high_yield_rules?.length ? hermesReport.high_yield_rules : ['None recorded yet']).map((r, i) => (
                  <span key={i} className="pill" style={{ color: '#4ade80', background: 'rgba(74, 222, 128, 0.1)' }}>
                    <Check size={12} /> {r}
                  </span>
                ))}
              </div>
            </div>

            <div className="hermes-stat-card">
              <span className="workspace-label">Underperforming Rules</span>
              <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {(hermesReport?.underperforming_rules?.length ? hermesReport.underperforming_rules : ['None flagged']).map((r, i) => (
                  <span key={i} className="pill" style={{ color: '#fb7185', background: 'rgba(251, 113, 133, 0.1)' }}>
                    <AlertTriangle size={12} /> {r}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="grid two">
            <div className="panel">
              <div className="panel-title"><DollarSign size={16} /> Record Sales Conversion Outcome</div>
              <p className="muted">Submit real-world rep feedback to update episodic memory and dynamically retune scoring weights.</p>
              <div className="grid two no-margin">
                <Input
                  label="Lead ID"
                  value={hermesForm.lead_id}
                  onChange={(v) => setHermesForm({ ...hermesForm, lead_id: v })}
                />
                <Input
                  label="Company Name"
                  placeholder="Apex SaaS"
                  value={hermesForm.company_name}
                  onChange={(v) => setHermesForm({ ...hermesForm, company_name: v })}
                />
              </div>
              <div className="grid two no-margin">
                <label>
                  <span>Outcome</span>
                  <select
                    value={hermesForm.outcome}
                    onChange={(e) => setHermesForm({ ...hermesForm, outcome: e.target.value })}
                  >
                    <option value="CLOSED_WON">CLOSED_WON ($ Verified)</option>
                    <option value="CLOSED_LOST">CLOSED_LOST (No Budget)</option>
                    <option value="MEETING_BOOKED">MEETING_BOOKED</option>
                    <option value="DISQUALIFIED">DISQUALIFIED (Bad Fit)</option>
                  </select>
                </label>
                <Input
                  label="Contract Deal Value ($)"
                  value={hermesForm.deal_value}
                  onChange={(v) => setHermesForm({ ...hermesForm, deal_value: v })}
                />
              </div>
              <Input
                label="Matched Rules (comma-separated)"
                value={hermesForm.matched_rules}
                onChange={(v) => setHermesForm({ ...hermesForm, matched_rules: v })}
              />
              <Textarea
                label="Rep Feedback / Closing Notes"
                value={hermesForm.feedback}
                onChange={(v) => setHermesForm({ ...hermesForm, feedback: v })}
                rows={3}
              />
              <div className="actions">
                <button
                  className="primary"
                  onClick={submitHermesConversion}
                  disabled={hermesRecording}
                >
                  <Send size={14} /> {hermesRecording ? 'Saving...' : 'Record to Hermes Memory'}
                </button>
                <button onClick={loadHermesReflection}>
                  <RefreshCw size={14} /> Run Reflection Cycle
                </button>
              </div>
            </div>

            <div className="panel">
              <div className="panel-title"><Database size={16} /> Dynamic Weight Tuning</div>
              <p className="muted">Suggested weights computed during the last Hermes autonomous reflection cycle:</p>
              {hermesReport?.suggested_weight_adjustments ? (
                <div style={{ marginTop: '12px' }}>
                  <pre>{JSON.stringify(hermesReport.suggested_weight_adjustments, null, 2)}</pre>
                  <p className="muted small" style={{ marginTop: '8px' }}>
                    Reflection generated at: {hermesReport.generated_at}
                  </p>
                </div>
              ) : (
                <p className="muted">No reflection report generated yet for this workspace.</p>
              )}
            </div>
          </div>
        </section>
      ) : null}

      {/* TAB 4: WEBHOOK & CRM STREAMING */}
      {activeTab === 'webhooks' ? (
        <section className="panel raised">
          <div className="panel-title"><Send size={18} /> Enterprise Webhook & CRM Streaming</div>
          <p className="muted">
            Deliver verified SQL/MQL leads in real-time to external CRMs (HubSpot, Salesforce, Make, n8n) with HMAC-SHA256 signature verification and strict SSRF protection.
          </p>

          <div className="grid two">
            <div className="panel">
              <div className="panel-title"><ShieldCheck size={16} /> Register Webhook Target</div>
              <p className="muted">Target URLs are evaluated against loopback, private subnets, and cloud metadata by ToolGateway.</p>
              <Input
                label="Target CRM Webhook URL"
                placeholder="https://api.hubspot.com/v3/events"
                value={webhookUrl}
                onChange={setWebhookUrl}
              />
              <Input
                label="Secret Key (for HMAC-SHA256 Signing)"
                value={webhookSecret}
                onChange={setWebhookSecret}
              />
              <div className="actions">
                <button className="primary" onClick={registerWebhook}>
                  <Plus size={14} /> Register Webhook
                </button>
                <button
                  onClick={dispatchTestWebhook}
                  disabled={webhookDispatching || !webhooks.length}
                >
                  <Send size={14} /> {webhookDispatching ? 'Dispatching...' : 'Dispatch Test Payload'}
                </button>
              </div>
            </div>

            <div className="panel">
              <div className="panel-title"><Activity size={16} /> Active Endpoints & Dispatch Logs</div>
              <p className="muted">Registered endpoints for workspace <strong>{form.tenant_id}</strong>:</p>
              {webhooks.length ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '14px' }}>
                  {webhooks.map((wh, idx) => (
                    <div key={idx} className="approval-item">
                      <div className="approval-head">
                        <strong>{wh.target_url}</strong>
                        <span className="pill" style={{ color: '#4ade80' }}>Active</span>
                      </div>
                      <p className="muted small">Events: {wh.trigger_events.join(', ')}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="muted" style={{ marginBottom: '14px' }}>No webhooks registered for this workspace yet.</p>
              )}

              <strong>Dispatch Execution Log:</strong>
              <div style={{ marginTop: '8px', maxHeight: '180px', overflowY: 'auto' }}>
                {webhookLogs.length ? (
                  webhookLogs.map((log, i) => (
                    <p key={i} className="small muted" style={{ fontFamily: 'monospace', margin: '4px 0' }}>
                      {log}
                    </p>
                  ))
                ) : (
                  <p className="muted small">Click "Dispatch Test Payload" to test end-to-end delivery.</p>
                )}
              </div>
            </div>
          </div>
        </section>
      ) : null}

      {/* 29-Field Revenue Profile Drawer Modal */}
      {inspectLead ? (
        <div className="drawer-backdrop" onClick={() => setInspectLead(null)}>
          <div className="drawer-content" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-header">
              <div>
                <h2>{String(inspectLead['Client Name'] || inspectLead['Company Name'] || 'Lead Profile')}</h2>
                <span className="muted">{String(inspectLead['Company Website'] || inspectLead['Title'] || '')}</span>
              </div>
              <button className="ghost" onClick={() => setInspectLead(null)}>✕ Close</button>
            </div>

            <div className="approval-head">
              <span className={`tier-badge tier-${String(inspectLead.lead_tier || inspectLead.Priority || 'b').toLowerCase()}`}>
                Tier {String(inspectLead.lead_tier || inspectLead.Priority || 'B')}
              </span>
              <span className="deal-gauge">{String(inspectLead['Revenue Deal Value'] || inspectLead['Estimated Deal Value'] || '$50K–$150K Strategic')}</span>
              <span className="authority-pill">{inspectLead.budget_authority ? 'Budget Confirmed' : 'Influencer'}</span>
              <span className="timeline-pill">{String(inspectLead.timeline || 'Immediate')}</span>
            </div>

            <h3>29 Revenue Intelligence Fields</h3>
            <div className="field-grid">
              {Object.entries(inspectLead).map(([key, val]) => (
                <div key={key} className="field-item">
                  <label>{key}</label>
                  <span>{val == null ? 'N/A' : typeof val === 'object' ? JSON.stringify(val) : String(val)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </main>
  )
}

/* --- Helpers & Subcomponents --- */

function lines(value: string) {
  return value.split('\n').map((item) => item.trim()).filter(Boolean)
}

function objectiveInstruction(objective: string) {
  const instructions: Record<string, string> = {
    agency_procurement: 'Only accept external agency, consultant, vendor, RFP, implementation partner, outsourcing, or managed service procurement intent. Reject hiring, seller promotion, jobs, and educational content.',
    recruitment_clients: 'Accept companies showing active hiring demand or asking for recruitment, staffing, RPO, or talent acquisition support. Reject staffing agency self-promotion, candidate self-promotion, education, and generic news.',
    candidate_job_search: 'Accept real job openings, open roles, hiring manager posts, and apply-now career opportunities that match the candidate ICP. Reject agency pitches, career advice, courses, and candidate self-promotion.',
    fractional_executive: 'Accept companies seeking fractional executives, interim leaders, GTM advisors, RevOps consultants, growth consultants, or executive advisory support. Reject full-time job posts, consultant self-promotion, education, and thought leadership.',
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
  const keys = preferredColumns?.length
    ? preferredColumns
    : Array.from(new Set(rows.flatMap((row) => Object.keys(row))))
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
  const example = ['Example Client', 'https://example.com', 'agency_procurement', 'AI implementation; RevOps consulting', 'CMOs and RevOps leaders at B2B SaaS companies', 'US; UK', 'External implementation partner for growth teams', 'Series A SaaS; Healthcare technology', 'https://linkedin.com/in/founder', 'Use agency_procurement, recruitment_clients, candidate_job_search, or fractional_executive']
  const csv = [columns, example].map((row) => row.map(csvValue).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'leadvault_icp_template.csv'
  link.click()
  URL.revokeObjectURL(url)
}

function operationLabel(operation: OperationState) {
  const labels: Record<OperationState, string> = {
    idle: 'Ready', uploading: 'Reading ICP file', generating: 'Generating mining brain',
    mining: 'Mining and validating buyer intent', analyzing: 'Classifying pasted posts',
    success: 'Run completed', error: 'Run needs attention',
  }
  return labels[operation]
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

function Input({ label, value, placeholder, onChange }: { label: string; value: string; placeholder?: string; onChange: (value: string) => void }) {
  return (
    <label>
      <span>{label}</span>
      <input value={value} placeholder={placeholder} onChange={(e) => onChange(e.target.value)} />
    </label>
  )
}

function Textarea({ label, value, placeholder, rows = 4, onChange }: { label: string; value: string; placeholder?: string; rows?: number; onChange: (value: string) => void }) {
  return (
    <label>
      <span>{label}</span>
      <textarea value={value} placeholder={placeholder} onChange={(e) => onChange(e.target.value)} rows={rows} />
    </label>
  )
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function Step({ number, title, active }: { number: string; title: string; active: boolean }) {
  return (
    <div className={`step ${active ? 'active' : ''}`}>
      <strong>{number}</strong>
      <span>{title}</span>
    </div>
  )
}

function List({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="panel">
      <div className="panel-title">{title}</div>
      <div className="chips">
        {(items.length ? items : ['No data yet']).slice(0, 18).map((item, index) => <span key={`${item}-${index}`}>{item}</span>)}
      </div>
    </div>
  )
}

function EnhancedLeadsTable({
  title,
  rows,
  onInspect,
}: {
  title: string
  rows: Array<Record<string, unknown>>
  onInspect: (lead: Record<string, unknown>) => void
}) {
  return (
    <div className="panel table-panel">
      <div className="panel-title">{title}</div>
      {rows.length ? (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Tier</th>
                <th>Deal Value</th>
                <th>Client Name</th>
                <th>Company</th>
                <th>Title</th>
                <th>Authority</th>
                <th>Intent Signal</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {rows.slice(0, 15).map((row, rowIndex) => {
                const tier = String(row.lead_tier || row.Priority || 'B').toUpperCase()
                const tierClass = tier === 'A' ? 'tier-a' : tier === 'C' ? 'tier-c' : 'tier-b'
                const dealVal = String(row['Revenue Deal Value'] || row['Estimated Deal Value'] || '$50K–$150K')
                const authority = Boolean(row.budget_authority || row.Title?.toString().match(/vp|director|head|founder|cmo/i))

                return (
                  <tr key={rowIndex}>
                    <td>
                      <span className={`tier-badge ${tierClass}`}>Tier {tier}</span>
                    </td>
                    <td>
                      <span className="deal-gauge">{dealVal}</span>
                    </td>
                    <td><strong>{String(row['Client Name'] || 'Unknown')}</strong></td>
                    <td>{String(row['Company Name'] || '')}</td>
                    <td>{String(row['Title'] || '')}</td>
                    <td>
                      <span className="authority-pill">
                        {authority ? 'Confirmed' : 'Influencer'}
                      </span>
                    </td>
                    <td>{String(row['Client Intent Signal'] || '').slice(0, 100)}...</td>
                    <td>
                      <button className="ghost small" onClick={() => onInspect(row)}>
                        <Eye size={12} /> Inspect
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="muted">No leads yet.</p>
      )}
    </div>
  )
}

function Table({ title, rows, columns }: { title: string; rows: Array<Record<string, unknown>>; columns: string[] }) {
  return (
    <div className="panel table-panel">
      <div className="panel-title">{title}</div>
      {rows.length ? (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr>
            </thead>
            <tbody>
              {rows.slice(0, 12).map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {columns.map((column) => <td key={column}>{String(row[column] ?? '').slice(0, 180)}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="muted">No rows yet.</p>
      )}
    </div>
  )
}

function HistoryPanel({
  title,
  subtitle,
  items,
  emptyText,
}: {
  title: string
  subtitle: string
  items: Array<Record<string, unknown>>
  emptyText: string
}) {
  return (
    <div className="panel">
      <div className="panel-title">{title}</div>
      <p className="muted">{subtitle}</p>
      {items.length ? (
        <div className="history-list">
          {items.slice(0, 10).map((item, index) => (
            <details key={index} className="history-item">
              <summary>{describeHistoryItem(item, index)}</summary>
              <HistoryDetail item={item} />
            </details>
          ))}
        </div>
      ) : (
        <p className="muted">{emptyText}</p>
      )}
    </div>
  )
}

function HistoryDetail({ item }: { item: Record<string, unknown> }) {
  const payload = item.payload && typeof item.payload === 'object' ? item.payload as Record<string, unknown> : {}
  const rows = Array.isArray(item.rows) ? item.rows : []
  const detail = rows.length ? rows.slice(0, 5) : [payload]
  return (
    <div className="history-detail">
      <span>Saved: {String(item.saved_at_utc ?? 'unknown')}</span>
      <span>Tenant: {String(item.tenant_id ?? 'default')}</span>
      <pre>{JSON.stringify(detail, null, 2)}</pre>
    </div>
  )
}

function describeHistoryItem(item: Record<string, unknown>, index: number) {
  const payload = item.payload && typeof item.payload === 'object' ? (item.payload as Record<string, unknown>) : {}
  const id = String(item.export_id ?? item.audit_id ?? item.saved_at_utc ?? item.created_at ?? `item_${index}`)
  const detail = String(item.row_count ?? payload.row_count ?? item.query ?? payload.query ?? 'record')
  return `${id} | ${detail}`
}
