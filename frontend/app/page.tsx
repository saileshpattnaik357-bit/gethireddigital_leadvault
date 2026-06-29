'use client'

import { useEffect, useMemo, useState } from 'react'
import { Brain, CheckCircle2, Copy, Download, FileSpreadsheet, Play, Plus, Radar, RefreshCw, Upload, XCircle } from 'lucide-react'

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

interface MiningResult {
  accepted: Array<Record<string, unknown>>
  rejected: Array<Record<string, unknown>>
  apify_report?: Array<{ query: string; status: string; actor: string; items: number; error: string }>
  summary: {
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

type ApiState = 'checking' | 'online' | 'offline'
type OperationState = 'idle' | 'uploading' | 'generating' | 'mining' | 'analyzing' | 'success' | 'error'

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

  const readyToGenerate = Boolean(form.company_name.trim() || form.website.trim() || form.icp.trim() || icpFile)
  const acceptedRows = result?.accepted ?? []
  const rejectedRows = result?.rejected ?? []

  useEffect(() => {
    checkApi()
    void loadTenants()
  }, [])

  useEffect(() => {
    void loadHistory()
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
      // The API badge already communicates an offline backend.
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
      company_name: '', website: '', services: '', geography: '', icp: '',
      positioning: '', customer_examples: '', founder_profile: '', lead_objective: 'agency_procurement',
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
      // keep existing history if offline
    } finally {
      setHistoryLoading(false)
    }
  }

  async function generate(useLlm = false) {
    if (!readyToGenerate) {
      setMessage('Add client details or upload an ICP file first.')
      return
    }
    setLoading(true)
    setOperation('generating')
    setMessage('')
    setResult(null)
    try {
      if (icpFile && !form.company_name.trim() && !form.icp.trim()) {
        await uploadIcp(icpFile, useLlm)
        return
      }

      const res = await fetch(`${API}/api/leadvault/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...form,
          services: lines(form.services),
          customer_examples: lines(form.customer_examples),
          target_audience: form.icp,
          notes: objectiveInstruction(form.lead_objective),
          use_llm: useLlm,
          save: true,
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? 'Generation failed')
      setSpec(data.spec)
      setConfirmed(false)
      setMessage(`Brain ready: ${data.summary.linkedin_queries} LinkedIn queries, ${data.summary.google_queries} Google/RFP queries, ${data.summary.buyer_phrases} buyer phrases.`)
      setOperation('success')
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Generation failed')
      setOperation('error')
    } finally {
      setLoading(false)
    }
  }

  async function uploadIcp(file: File | null, useLlm = false) {
    if (!file) {
      setMessage('Choose a CSV or Excel ICP file first.')
      return
    }
    setLoading(true)
    setOperation('uploading')
    setMessage('')
    setResult(null)
    try {
      const payload = new FormData()
      payload.append('file', file)
      payload.append('tenant_id', form.tenant_id)
      payload.append('lead_objective', form.lead_objective)
      payload.append('save', 'true')
      payload.append('use_llm', String(useLlm))
      const res = await fetch(`${API}/api/leadvault/upload`, { method: 'POST', body: payload })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? 'Upload failed')
      setSpec(data.spec)
      hydrateFormFromProfile(data.source_profile ?? data.spec)
      setConfirmed(false)
      setMessage(`ICP uploaded: ${data.summary.uploaded_rows} rows. Generated ${data.summary.linkedin_queries} LinkedIn queries and ${data.summary.google_queries} Google/RFP queries.`)
      await loadTenants()
      setOperation('success')
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Upload failed')
      setOperation('error')
    } finally {
      setLoading(false)
    }
  }

  async function mine() {
    if (!confirmed) {
      setMessage('Confirm the mining brain before running. This prevents accidental API spend.')
      return
    }
    setMining(true)
    setOperation('mining')
    setMessage('')
    try {
      const payload = {
        tenant_id: form.tenant_id,
        company_name: spec?.company_name || form.company_name,
        website: spec?.website || form.website,
        services: spec?.services?.length ? spec.services : lines(form.services),
        geography: spec?.geography || form.geography,
        icp: spec?.icp || form.icp,
        positioning: spec?.positioning || form.positioning,
        customer_examples: spec?.customer_examples?.length ? spec.customer_examples : lines(form.customer_examples),
        founder_profile: spec?.founder_profile || form.founder_profile,
        lead_objective: spec?.lead_objective || form.lead_objective,
        confirmed: true,
        mining_mode: mode,
        max_apify_queries: boundedNumber(maxApifyQueries, 1, 25, 10),
        max_posts_per_query: boundedNumber(maxPostsPerQuery, 1, 25, 10),
        max_results: boundedNumber(maxResults, 1, 100, 25),
        live_web: liveWeb,
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
      setMessage(`Mining complete: ${data.summary.accepted} accepted, ${data.summary.rejected} rejected, ${data.summary.candidates_reviewed} reviewed.`)
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
          posts_text: captureText,
          query: 'manual_linkedin_capture',
          max_results: boundedNumber(maxResults, 1, 100, 25),
          lead_objective: spec?.lead_objective || form.lead_objective,
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? 'LinkedIn capture failed')
      setResult(data)
      await loadHistory()
      await loadTenants()
      setMessage(`LinkedIn capture analyzed: ${data.summary.accepted} accepted, ${data.summary.rejected} rejected.`)
      setOperation('success')
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'LinkedIn capture failed')
      setOperation('error')
    } finally {
      setMining(false)
    }
  }

  async function copySnippet() {
    if (!spec?.python_snippet) return
    await navigator.clipboard.writeText(spec.python_snippet)
    setMessage('Python query bank copied.')
  }

  function hydrateFormFromProfile(profile: Record<string, unknown>) {
    setForm((current) => ({
      ...current,
      company_name: stringValue(profile.company_name) || current.company_name,
      website: stringValue(profile.website) || current.website,
      services: arrayText(profile.services) || current.services,
      geography: stringValue(profile.geography) || current.geography,
      icp: stringValue(profile.icp) || current.icp,
      positioning: stringValue(profile.positioning) || current.positioning,
      customer_examples: arrayText(profile.customer_examples) || current.customer_examples,
      founder_profile: stringValue(profile.founder_profile) || current.founder_profile,
      lead_objective: stringValue(profile.lead_objective) || current.lead_objective,
    }))
  }

  const apiBadge = useMemo(() => {
    if (apiState === 'online') return { text: 'API online', tone: 'good' }
    if (apiState === 'offline') return { text: 'API offline - start backend on :8000', tone: 'bad' }
    return { text: 'Checking API...', tone: 'wait' }
  }, [apiState])

  return (
    <main className="shell">
      <section className="hero">
        <div>
          <p className="eyebrow">LeadVault Agentic AI Engine</p>
          <h1>Upload a client ICP, generate the mining brain, then mine buyer-intent leads.</h1>
          <p className="hero-copy">The engine requires procurement intent plus external-help intent, then exports accepted rows in the existing lead schema.</p>
        </div>
        <div className={`status ${apiBadge.tone}`}>
          {apiState === 'online' ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
          <span>{apiBadge.text}</span>
          <button className="ghost" onClick={checkApi}>Recheck</button>
        </div>
      </section>

      <section className="steps">
        <Step number="1" title="Client Details" active />
        <Step number="2" title="ICP Upload" active={Boolean(icpFile)} />
        <Step number="3" title="Mining Brain" active={Boolean(spec)} />
        <Step number="4" title="Accepted Leads" active={Boolean(result)} />
      </section>

      <section className="workspace-bar">
        <div>
          <span className="workspace-label">Active workspace</span>
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

      {result ? (
        <section className="grid two">
          <Table title={`Accepted Leads (${result.summary.accepted})`} rows={acceptedRows} columns={leadColumns.slice(0, 8).concat(['Client Intent Signal', 'Priority', 'Service Category'])} />
          <Table title={`Rejected Audit (${result.summary.rejected})`} rows={rejectedRows} columns={['rejection_reason', 'category', 'query', 'source', 'text']} />
        </section>
      ) : null}

      {result?.apify_report?.length ? (
        <section className="panel">
          <div className="panel-title">Apify / Mining Report</div>
          <div className="chips">
            {result.apify_report.slice(0, 24).map((row, index) => (
              <span key={`${row.query}-${index}`}>{row.status} | {row.items} items | {row.actor || 'actor'} | {row.query}</span>
            ))}
          </div>
        </section>
      ) : null}

      {spec?.python_snippet ? (
        <section className="panel">
          <div className="panel-title">Python Query Bank</div>
          <pre>{spec.python_snippet}</pre>
        </section>
      ) : null}
    </main>
  )
}

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
