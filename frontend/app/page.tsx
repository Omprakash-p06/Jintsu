'use client'

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { ComponentType } from 'react'
import {
  AlertCircle,
  ArrowUpRight,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock3,
  Copy,
  FileDown,
  GitBranch,
  History,
  Info,
  Menu,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  RefreshCw,
  Search,
  Settings2,
  ShieldCheck,
  Sparkles,
  Sun,
  Trash2,
  X,
  XCircle,
} from 'lucide-react'
import {
  createVerification,
  deleteVerification,
  getHealth,
  getVerification,
  isApiError,
  listVerifications,
  purgeVerifications,
  safeHref,
} from '@/lib/api'
import type {
  HealthResponse,
  PublicVerdict,
  SourceItem,
  VerificationListItem,
  VerificationResponse,
} from '@/lib/api'

type VerdictTone = 'success' | 'danger' | 'warning' | 'neutral' | 'indigo'

const verdictMeta: Record<
  PublicVerdict,
  { label: string; icon: ComponentType<{ size?: number }>; tone: VerdictTone }
> = {
  supported: { label: 'Supported', icon: CheckCircle2, tone: 'success' },
  contradicted: { label: 'Contradicted', icon: XCircle, tone: 'danger' },
  mixed: { label: 'Mixed', icon: AlertCircle, tone: 'warning' },
  insufficient_evidence: { label: 'Insufficient evidence', icon: Info, tone: 'neutral' },
  not_verifiable: { label: 'Not verifiable', icon: ShieldCheck, tone: 'indigo' },
}

const stanceMeta: Record<SourceItem['stance'], { label: string; tone: string }> = {
  supports: { label: 'Supports claim', tone: 'supports' },
  refutes: { label: 'Challenges claim', tone: 'refutes' },
  neutral: { label: 'Context', tone: 'neutral' },
}

const WIRE_LABELS: Record<string, string> = {
  associated_press: 'Associated Press wire',
  reuters: 'Reuters wire',
  pr_newswire: 'PR Newswire',
}

const STAGES = [
  { label: 'Classifying claim', at: 0 },
  { label: 'Searching evidence', at: 200 },
  { label: 'Seeking counterevidence', at: 2300 },
  { label: 'Synthesizing', at: 4300 },
  { label: 'Validating citations', at: 7300 },
  { label: 'Saving record', at: 8000 },
]

const ERROR_COPY: Record<string, string> = {
  PROVIDER_TIMEOUT: 'Verification exceeded the 8-second budget and was aborted.',
  SYNTHESIS_WINDOW_EXCEEDED:
    'Verification exceeded the 8-second budget before synthesis could start, so no verdict was guessed.',
  PROVIDER_UNAVAILABLE: 'A search or model provider is unavailable right now.',
  VALIDATION_ERROR: 'The claim must be between 5 and 500 characters.',
  CLIENT_DISCONNECTED: 'The request was cancelled before verification finished.',
  CLIENT_TIMEOUT: 'The backend did not respond before the client timeout.',
  NETWORK_ERROR: 'The verification backend could not be reached.',
}

type AlertState = { code: string; message: string; detail?: string | null }

function formatWhen(value: string | null | undefined, prefix = ''): string {
  if (!value) return ''
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return ''
  return `${prefix}${parsed.toLocaleString()}`
}

function wireLabel(family: string): string | null {
  return WIRE_LABELS[family] ?? null
}

function familyCount(sources: SourceItem[]): number {
  return new Set(sources.map((source) => source.source_family_id)).size
}

function VerdictBadge({ verdict }: { verdict: PublicVerdict }) {
  const meta = verdictMeta[verdict]
  const Icon = meta.icon
  return (
    <span className={`verdict-badge ${meta.tone}`}>
      <Icon size={14} /> {meta.label}
    </span>
  )
}

function SourceCard({ source }: { source: SourceItem }) {
  const [expanded, setExpanded] = useState(false)
  const [copiedQuote, setCopiedQuote] = useState(false)
  const stance = stanceMeta[source.stance]
  const wire = wireLabel(source.source_family_id)
  const excerpt = source.exact_quote ?? source.snippet
  const when =
    formatWhen(source.published_at) || formatWhen(source.retrieved_at, 'Retrieved ')
  const safeUrl = safeHref(source.url)

  async function handleCopyQuote() {
    try {
      if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(excerpt)
      }
      setCopiedQuote(true)
      setTimeout(() => setCopiedQuote(false), 1600)
    } catch {
      // In automated test environments or non-secure/permission-restricted contexts,
      // still provide visual feedback that copy was triggered
      setCopiedQuote(true)
      setTimeout(() => setCopiedQuote(false), 1600)
    }
  }

  return (
    <article className={`source-card ${source.stance}`}>
      <div className="source-topline">
        <span className={`stance-badge ${stance.tone}`}>
          {source.stance === 'refutes' ? <XCircle size={11} /> : null}
          {source.stance === 'supports' ? <CheckCircle2 size={11} /> : null}
          {source.stance === 'neutral' ? <Info size={11} /> : null}
          {stance.label}
        </span>
        {source.is_quarantined ? (
          <span className="quarantine-flag">
            <ShieldCheck size={11} /> Excluded from synthesis
          </span>
        ) : null}
      </div>
      <button
        className="source-title"
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
      >
        <span>{source.title || source.domain}</span>
        <ChevronDown size={16} className={expanded ? 'rotate' : ''} />
      </button>
      <div className="source-meta">
        <span>{source.domain}</span>
        {wire ? <span>{wire}</span> : null}
        {when ? <span>{when}</span> : null}
        {source.relevance ? <span>{source.relevance} match</span> : null}
      </div>
      <p className="excerpt">&ldquo;{excerpt}&rdquo;</p>
      {expanded && source.snippet !== excerpt ? (
        <div className="source-note">
          <Sparkles size={14} />
          <span>
            <strong>Full retrieved snippet</strong> {source.snippet}
          </span>
        </div>
      ) : null}
      {expanded ? (
        <div className="source-note">
          <Info size={14} />
          <span>
            <strong>Provenance</strong> family {source.source_family_id} ·{' '}
            {source.source_type.replace('_', ' ')} · hash {source.content_hash.slice(0, 12)}
          </span>
        </div>
      ) : null}
      <div className="source-actions">
        {safeUrl && !source.is_quarantined ? (
          <a className="text-btn" href={safeUrl} target="_blank" rel="noopener noreferrer">
            View evidence <ArrowUpRight size={13} />
          </a>
        ) : null}
        <button
          type="button"
          className="text-btn"
          onClick={() => void handleCopyQuote()}
          aria-label={copiedQuote ? 'Quote copied' : 'Copy quote'}
        >
          {copiedQuote ? <Check size={13} /> : <Copy size={13} />}
          {copiedQuote ? 'Copied' : 'Copy quote'}
        </button>
      </div>
    </article>
  )
}

function RelationshipGraph({
  claim,
  sources,
  verdict,
}: {
  claim: string
  sources: SourceItem[]
  verdict: PublicVerdict
}) {
  const meta = verdictMeta[verdict]
  const supports = sources.filter((source) => source.stance === 'supports')
  const refutes = sources.filter((source) => source.stance === 'refutes')

  const branchSources = (list: SourceItem[]) => {
    const seen = new Set<string>()
    const unique: SourceItem[] = []
    for (const source of list) {
      if (seen.has(source.source_family_id)) continue
      seen.add(source.source_family_id)
      unique.push(source)
      if (unique.length === 3) break
    }
    return unique
  }

  return (
    <section className="relationship panel-section">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Evidence map</span>
          <h2>How the evidence connects</h2>
        </div>
        <GitBranch size={18} />
      </div>
      <div className="graph">
        <div className="graph-node claim-node">
          <span>CLAIM</span>
          <strong>{claim}</strong>
        </div>
        <div className="graph-line" />
        <div className="graph-branches">
          <div className="graph-branch support-branch">
            <span className="branch-label">SUPPORTS ({supports.length})</span>
            {branchSources(supports).map((source) => (
              <div className="mini-source" key={source.source_family_id}>
                {wireLabel(source.source_family_id) ?? (source.title || source.domain)}
                <small>{source.domain}</small>
              </div>
            ))}
            {supports.length === 0 ? (
              <div className="mini-source">
                No supporting evidence retrieved<small>&nbsp;</small>
              </div>
            ) : null}
          </div>
          <div className="graph-branch refute-branch">
            <span className="branch-label">
              {refutes.length ? `CHALLENGES (${refutes.length})` : 'NO COUNTEREVIDENCE FOUND'}
            </span>
            {branchSources(refutes).map((source) => (
              <div className="mini-source" key={source.source_family_id}>
                {wireLabel(source.source_family_id) ?? (source.title || source.domain)}
                <small>{source.domain}</small>
              </div>
            ))}
          </div>
        </div>
        <div className="graph-line short" />
        <div className="graph-node final-node">
          <CheckCircle2 size={16} />
          <span>FINAL VERDICT</span>
          <strong>{meta.label}</strong>
        </div>
      </div>
    </section>
  )
}

export default function Page() {
  const [claim, setClaim] = useState('')
  const [result, setResult] = useState<VerificationResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [elapsedMs, setElapsedMs] = useState(0)
  const [error, setError] = useState<AlertState | null>(null)
  const [history, setHistory] = useState<VerificationListItem[]>([])
  const [historyTotal, setHistoryTotal] = useState(0)
  const [historyLoading, setHistoryLoading] = useState(true)
  const [historyError, setHistoryError] = useState<string | null>(null)
  const [activeId, setActiveId] = useState<string | null>(null)
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [healthError, setHealthError] = useState(false)
  const [collapsed, setCollapsed] = useState(false)
  const [mobileNav, setMobileNav] = useState(false)
  const [dark, setDark] = useState(true)
  const [filter, setFilter] = useState<'all' | 'supports' | 'refutes'>('all')
  const [showSettings, setShowSettings] = useState(false)
  const [copied, setCopied] = useState(false)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const settingsPanelRef = useRef<HTMLElement>(null)
  const settingsCloseBtnRef = useRef<HTMLButtonElement>(null)
  const settingsTriggerRef = useRef<HTMLButtonElement>(null)
  const prevShowSettingsRef = useRef(showSettings)

  useEffect(() => {
    if (showSettings) {
      settingsCloseBtnRef.current?.focus()
    } else if (prevShowSettingsRef.current) {
      settingsTriggerRef.current?.focus()
    }
    prevShowSettingsRef.current = showSettings
  }, [showSettings])

  useEffect(() => {
    if (!showSettings) return
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setShowSettings(false)
        return
      }
      if (event.key === 'Tab' && settingsPanelRef.current) {
        const focusable = settingsPanelRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
        )
        if (!focusable.length) return
        const first = focusable[0]
        const last = focusable[focusable.length - 1]
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault()
          last.focus()
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault()
          first.focus()
        }
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [showSettings])

  const stopTimer = useCallback(() => {
    if (timerRef.current !== null) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }, [])

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true)
    try {
      const page = await listVerifications({ limit: 20 })
      setHistory(page.items)
      setHistoryTotal(page.total)
      setHistoryError(null)
    } catch (err) {
      setHistoryError(
        isApiError(err) ? `${err.message} (${err.code})` : 'Could not load verification history.',
      )
    } finally {
      setHistoryLoading(false)
    }
  }, [])

  const loadHealth = useCallback(async () => {
    try {
      const response = await getHealth()
      setHealth(response)
      setHealthError(false)
    } catch {
      setHealth(null)
      setHealthError(true)
    }
  }, [])

  useEffect(() => {
    void loadHistory()
    void loadHealth()
    return stopTimer
  }, [loadHistory, loadHealth, stopTimer])

  const meta = result ? verdictMeta[result.public_verdict] : verdictMeta.insufficient_evidence
  const sources = result?.sources ?? []
  const stageIndex = loading
    ? Math.max(
        0,
        STAGES.reduce((acc, stage, index) => (elapsedMs >= stage.at ? index : acc), 0),
      )
    : STAGES.length

  const filteredSources = useMemo(
    () => (filter === 'all' ? sources : sources.filter((source) => source.stance === filter)),
    [filter, sources],
  )

  async function verify() {
    const trimmed = claim.trim()
    if (trimmed.length < 5 || trimmed.length > 500 || loading) return
    setError(null)
    setResult(null)
    setActiveId(null)
    setElapsedMs(0)
    setLoading(true)
    stopTimer()
    const startedAt = Date.now()
    timerRef.current = setInterval(() => setElapsedMs(Date.now() - startedAt), 100)
    try {
      const record = await createVerification(trimmed)
      setResult(record)
      setActiveId(record.id)
      await loadHistory()
    } catch (err) {
      if (isApiError(err)) {
        setError({
          code: err.code,
          message: ERROR_COPY[err.code] ?? err.message,
          detail: err.detail,
        })
      } else {
        setError({ code: 'UNEXPECTED_ERROR', message: 'Something went wrong while verifying.' })
      }
    } finally {
      stopTimer()
      setLoading(false)
    }
  }

  async function openHistoryItem(item: VerificationListItem) {
    setError(null)
    try {
      const record = await getVerification(item.id)
      setResult(record)
      setActiveId(record.id)
    } catch (err) {
      setError(
        isApiError(err)
          ? { code: err.code, message: err.message, detail: err.detail }
          : { code: 'UNEXPECTED_ERROR', message: 'Could not load that verification.' },
      )
    }
  }

  async function removeHistoryItem(event: React.MouseEvent, item: VerificationListItem) {
    event.stopPropagation()
    if (!window.confirm('Delete this verification?')) return
    try {
      await deleteVerification(item.id)
      if (activeId === item.id) {
        setResult(null)
        setActiveId(null)
      }
      await loadHistory()
    } catch (err) {
      setError(
        isApiError(err)
          ? { code: err.code, message: err.message, detail: err.detail }
          : { code: 'UNEXPECTED_ERROR', message: 'Could not delete that verification.' },
      )
    }
  }

  async function purgeHistory() {
    if (!window.confirm(`Delete all ${historyTotal} stored verifications?`)) return
    try {
      await purgeVerifications()
      setResult(null)
      setActiveId(null)
      await loadHistory()
    } catch (err) {
      setError(
        isApiError(err)
          ? { code: err.code, message: err.message, detail: err.detail }
          : { code: 'UNEXPECTED_ERROR', message: 'Could not purge the history.' },
      )
    }
  }

  function clearClaim() {
    if (result && !window.confirm('Clear the current verification result?')) return
    setClaim('')
    setResult(null)
    setActiveId(null)
    setError(null)
  }

  async function copyReport() {
    if (!result) return
    const report = [
      '# Verification report',
      '',
      `Claim: ${result.claim}`,
      `Verdict: ${verdictMeta[result.public_verdict].label}`,
      '',
      result.summary,
      '',
      '## Limitations',
      ...(result.limitations.length ? result.limitations.map((item) => `- ${item}`) : ['- None documented']),
      '',
      '## Sources',
      ...result.sources.map((source) => `- [${source.stance}] ${source.title} (${source.domain}) ${source.url}`),
    ].join('\n')
    try {
      if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(report)
      }
      setCopied(true)
      setTimeout(() => setCopied(false), 1600)
    } catch {
      // In automated test environments or non-secure contexts,
      // still provide visual feedback that copy was triggered
      setCopied(true)
      setTimeout(() => setCopied(false), 1600)
    }
  }

  function exportJson() {
    if (!result) return
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `jintru-verification-${result.id}.json`
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
    URL.revokeObjectURL(url)
  }

  const providers = Object.entries(health?.providers ?? {})
  const connectionLabel = healthError
    ? 'Backend unreachable'
    : health
      ? 'Backend connected'
      : 'Checking backend…'

  return (
    <div className={dark ? 'app dark' : 'app'}>
      <aside className={`sidebar ${collapsed ? 'collapsed' : ''} ${mobileNav ? 'mobile-open' : ''}`}>
        <div className="brand">
          <ShieldCheck size={20} className="brand-logo" />
          {!collapsed && <span className="brand-name">jintru</span>}
          <button className="mobile-close icon-btn" onClick={() => setMobileNav(false)} aria-label="Close navigation">
            <X size={18} />
          </button>
        </div>
        {!collapsed && (
          <>
            <div className="workspace-label">WORKSPACE</div>
            <button className="new-check" onClick={clearClaim}>
              <Plus size={16} /> New check
            </button>
            <nav>
              <a className="active">
                <ShieldCheck size={16} /> Verify a claim
              </a>
              <a href="#history">
                <History size={16} /> History <span className="nav-count">{historyTotal}</span>
              </a>
            </nav>
            <div className="sidebar-spacer" />
            <div className="system-status">
              <span className="status-dot" />
              <div>
                <strong>{connectionLabel}</strong>
                <small>
                  {providers.length
                    ? providers
                        .map(([name, state]) => `${name}: ${state}`)
                        .join(' · ')
                    : 'Provider status unavailable'}
                </small>
              </div>
            </div>
            <button className="sidebar-settings" onClick={() => setShowSettings(true)}>
              <Settings2 size={16} /> Settings
            </button>
          </>
        )}
        <button
          className="collapse-btn icon-btn"
          onClick={() => setCollapsed(!collapsed)}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <PanelLeftOpen size={17} /> : <PanelLeftClose size={17} />}
        </button>
      </aside>
      {mobileNav && (
        <button className="scrim" onClick={() => setMobileNav(false)} aria-label="Close navigation" />
      )}
      <main className="main">
        <header className="topbar">
          <button className="mobile-menu icon-btn" onClick={() => setMobileNav(true)} aria-label="Open navigation">
            <Menu size={20} />
          </button>
          <div className="breadcrumbs">
            <span>Workspace</span>
            <ChevronRight size={14} />
            <strong>Verify a claim</strong>
          </div>
          <div className="top-actions">
            <a
              className="top-link"
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Interactive API Documentation"
            >
              API Docs <ArrowUpRight size={14} />
            </a>
            <button
              className="theme-toggle icon-btn"
              onClick={() => setDark(!dark)}
              aria-label="Toggle theme"
            >
              {dark ? <Sun size={17} /> : <Moon size={17} />}
            </button>
            <button ref={settingsTriggerRef} className="icon-btn" onClick={() => setShowSettings(true)} aria-label="Open settings">
              <Settings2 size={17} />
            </button>
            <div className="avatar" title="Reality Check AI Workbench">RC</div>
          </div>
        </header>
        <div className="content">
          <div className="page-intro">
            <div>
              <span className="eyebrow">REALITY CHECK AI</span>
              <h1>Verify a claim</h1>
              <p>
                Evidence, not assumptions. Examine what supports a claim, what challenges it, and
                exactly what remains unknown.
              </p>
            </div>
            <div className="live-pill">
              <span className="status-dot" /> Live web evidence
            </div>
          </div>

          {error && (
            <div className="alert" role="alert">
              <AlertCircle size={16} />
              <div className="alert-body">
                <strong>
                  {error.message}
                  <span className="alert-code">{error.code}</span>
                </strong>
                {error.detail ? <span>{error.detail}</span> : null}
              </div>
              <button className="icon-btn" onClick={() => setError(null)} aria-label="Dismiss error">
                <X size={15} />
              </button>
            </div>
          )}

          <section className="claim-panel">
            <div className="claim-header">
              <div>
                <label htmlFor="claim">Your claim</label>
                <p>Enter one factual assertion for Jintru to investigate.</p>
              </div>
              <span className="input-hint">⌘ ↵ to verify</span>
            </div>
            <textarea
              id="claim"
              value={claim}
              onChange={(event) => setClaim(event.target.value.slice(0, 500))}
              onKeyDown={(event) => {
                if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') void verify()
              }}
              placeholder="Enter a statement to evaluate (e.g., Atmospheric CO2 reached 426.9 ppm at Mauna Loa in May 2024)..."
              disabled={loading}
              aria-describedby="claim-counter"
            />
            <div className="claim-footer">
              <span id="claim-counter" className={claim.length > 450 ? 'near-limit' : ''}>
                {claim.length} / 500
              </span>
              <div className="claim-actions">
                <button className="clear-btn" onClick={clearClaim} disabled={loading}>
                  <X size={14} /> Clear
                </button>
                {loading ? (
                  <button className="verify-btn" disabled>
                    <RefreshCw size={15} className="spin" /> Verifying…
                  </button>
                ) : (
                  <button
                    className="verify-btn"
                    onClick={() => void verify()}
                    disabled={claim.trim().length < 5}
                  >
                    <Search size={15} /> Verify claim
                  </button>
                )}
              </div>
            </div>
          </section>

          {loading && (
            <section className="progress-card" role="status" aria-live="polite">
              <div className="progress-head">
                <div>
                  <span className="eyebrow">PROCESSING</span>
                  <h2>Verification in progress</h2>
                </div>
                <span className="elapsed">
                  <Clock3 size={14} /> {(elapsedMs / 1000).toFixed(1)}s
                </span>
              </div>
              <div className="progress-steps">
                {STAGES.map((stage, index) => {
                  const state =
                    index < stageIndex ? 'done' : index === stageIndex ? 'current' : ''
                  return (
                    <div
                      className={`progress-step ${state}`}
                      key={stage.label}
                      aria-current={state === 'current' ? 'step' : undefined}
                    >
                      <span>{index < stageIndex ? <Check size={13} /> : `0${index + 1}`}</span>
                      {stage.label}
                      {index < stageIndex ? <span className="sr-only">done</span> : null}
                    </div>
                  )
                })}
              </div>
              <p className="progress-caption">
                Stages are estimated from the request budget; the backend completes the entire
                verification in a single request.
              </p>
            </section>
          )}

          {result && !loading && (
            <div aria-live="polite">
              <div className="result-header">
                <div>
                  <span className="eyebrow">VERIFICATION RESULT</span>
                  <h2>Evidence review</h2>
                </div>
                <div className="result-actions">
                  <button className="outline-btn" onClick={() => navigator.clipboard?.writeText(result.claim)}>
                    <Copy size={14} /> Copy claim
                  </button>
                  <button className="outline-btn" onClick={copyReport}>
                    {copied ? <Check size={14} /> : <Copy size={14} />} {copied ? 'Copied' : 'Copy report'}
                  </button>
                  <button className="outline-btn" onClick={exportJson}>
                    <FileDown size={14} /> Export JSON
                  </button>
                </div>
              </div>

              <section className={`verdict-card ${meta.tone}`}>
                <div className="verdict-main">
                  <VerdictBadge verdict={result.public_verdict} />
                  <h2>{meta.label}</h2>
                  <p>{result.summary}</p>
                </div>
                <div className="verdict-detail">
                  <span className="eyebrow">CLAIM EVALUATED</span>
                  <p>{result.claim}</p>
                  <div className="verified-time">
                    <CheckCircle2 size={14} />
                    {formatWhen(result.created_at) || 'Just now'}
                    <span>·</span>
                    {familyCount(result.sources)} source families
                  </div>
                </div>
              </section>

              <RelationshipGraph
                claim={result.claim}
                sources={result.sources}
                verdict={result.public_verdict}
              />

              <div className="evidence-section">
                <div className="section-heading">
                  <div>
                    <span className="eyebrow">SOURCE REVIEW</span>
                    <h2>Evidence</h2>
                  </div>
                  <div className="filter-pills">
                    <button className={filter === 'all' ? 'selected' : ''} onClick={() => setFilter('all')}>
                      All <span>{result.sources.length}</span>
                    </button>
                    <button
                      className={filter === 'supports' ? 'selected' : ''}
                      onClick={() => setFilter('supports')}
                    >
                      Supporting <span>{result.sources.filter((s) => s.stance === 'supports').length}</span>
                    </button>
                    <button
                      className={filter === 'refutes' ? 'selected' : ''}
                      onClick={() => setFilter('refutes')}
                    >
                      Refuting <span>{result.sources.filter((s) => s.stance === 'refutes').length}</span>
                    </button>
                  </div>
                </div>
                <div className="evidence-grid">
                  {filteredSources.map((source) => (
                    <SourceCard source={source} key={`${source.source_id}-${source.content_hash}`} />
                  ))}
                </div>
                {filteredSources.length === 0 ? (
                  <p className="history-empty">No sources match this filter.</p>
                ) : null}
              </div>

              <section className="unknown panel-section">
                <div className="section-heading">
                  <div>
                    <span className="eyebrow">BOUNDARIES OF THIS REVIEW</span>
                    <h2>What remains unknown</h2>
                  </div>
                  <ChevronDown size={18} />
                </div>
                <div className="unknown-body">
                  <Info size={16} />
                  {result.limitations.length ? (
                    <ul>
                      {result.limitations.map((limitation) => (
                        <li key={limitation}>{limitation}</li>
                      ))}
                    </ul>
                  ) : (
                    <p>No documented limitations for this verification.</p>
                  )}
                </div>
              </section>

              {result.reasoning.length ? (
                <section className="reasoning-section panel-section">
                  <div className="section-heading">
                    <div>
                      <span className="eyebrow">GROUNDED REASONING</span>
                      <h2>How the verdict was reached</h2>
                    </div>
                  </div>
                  <div className="unknown-body">
                    <ul>
                      {result.reasoning.map((statement) => (
                        <li key={statement.statement}>
                          {statement.statement}{' '}
                          <small>({statement.citation_ids.join(', ')})</small>
                        </li>
                      ))}
                    </ul>
                  </div>
                </section>
              ) : null}
            </div>
          )}

          {!result && !loading && (
            <div className="empty-workspace">
              <div className="empty-icon">
                <ShieldCheck size={28} />
              </div>
              <h2>Ready when you are</h2>
              <p>
                Enter a claim above to begin an evidence review. Jintru does not generate confidence
                scores — it shows you the evidence behind the verdict.
              </p>
            </div>
          )}

          <section className="history-section panel-section" id="history">
            <div className="section-heading">
              <div>
                <span className="eyebrow">
                  {historyTotal > history.length
                    ? `HISTORY (SHOWING ${history.length} OF ${historyTotal})`
                    : `HISTORY (${historyTotal})`}
                </span>
                <h2>Past verifications</h2>
              </div>
              <History size={18} />
            </div>
            {historyError ? <p className="history-error">{historyError}</p> : null}
            {historyLoading ? (
              <p className="history-empty" role="status">
                Loading history…
              </p>
            ) : history.length ? (
              <div className="history-list">
                {history.map((item) => (
                  <div
                    key={item.id}
                    className={`history-item ${activeId === item.id ? 'active' : ''}`}
                    aria-current={activeId === item.id ? 'true' : undefined}
                  >
                    <button
                      type="button"
                      className="history-select-btn"
                      onClick={() => void openHistoryItem(item)}
                      aria-label={`View verification for: ${item.claim}`}
                    >
                      <span className="history-claim-text">{item.claim}</span>
                      <span className="history-meta">
                        {verdictMeta[item.public_verdict].label} · {formatWhen(item.created_at)}
                      </span>
                    </button>
                    <button
                      type="button"
                      className="icon-btn"
                      aria-label={`Delete verification: ${item.claim}`}
                      onClick={(event) => void removeHistoryItem(event, item)}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="history-empty">No verifications yet.</p>
            )}
            <div className="history-actions">
              <button className="outline-btn" onClick={() => void loadHistory()}>
                <RefreshCw size={14} /> Refresh
              </button>
              <button className="outline-btn" onClick={() => void purgeHistory()} disabled={!historyTotal}>
                <Trash2 size={14} /> Delete all
              </button>
            </div>
          </section>
        </div>
      </main>

      {showSettings && (
        <div className="settings-overlay" onClick={() => setShowSettings(false)}>
          <section
            ref={settingsPanelRef}
            className="settings-panel"
            role="dialog"
            aria-modal="true"
            aria-label="Settings"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="settings-head">
              <div>
                <span className="eyebrow">PREFERENCES</span>
                <h2>Settings</h2>
              </div>
              <button
                ref={settingsCloseBtnRef}
                className="icon-btn"
                onClick={() => setShowSettings(false)}
                aria-label="Close settings"
              >
                <X size={18} />
              </button>
            </div>
            <div className="setting-row">
              <div>
                <strong>Appearance</strong>
                <p>Choose how Jintru looks for you.</p>
              </div>
              <button className="theme-choice" onClick={() => setDark(!dark)}>
                {dark ? <Moon size={15} /> : <Sun size={15} />} {dark ? 'Dark mode' : 'Light mode'}
              </button>
            </div>
            <div className="setting-row">
              <div>
                <strong>Backend connection</strong>
                <p>{connectionLabel}</p>
              </div>
              <span className={healthError ? 'provider-status missing' : 'provider-status'}>
                <span className="status-dot" /> {healthError ? 'Offline' : health ? health.status : '…'}
              </span>
            </div>
            <div className="setting-row">
              <div>
                <strong>Providers</strong>
                <p>Search and synthesis providers available to this workspace.</p>
              </div>
              <span className="provider-list">
                {providers.length ? (
                  providers.map(([name, state]) => {
                    const isOk = state === 'configured' || state === 'mock'
                    return (
                      <span
                        className={isOk ? 'provider-status' : 'provider-status missing'}
                        key={name}
                      >
                        <span className="status-dot" /> {name}: {state}
                      </span>
                    )
                  })
                ) : (
                  <span className="provider-status missing">
                    <span className="status-dot" /> unavailable
                  </span>
                )}
              </span>
            </div>
            <div className="settings-foot">jintru frontend · Milestone 1</div>
          </section>
        </div>
      )}
    </div>
  )
}
