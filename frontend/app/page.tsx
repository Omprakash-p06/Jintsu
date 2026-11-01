'use client'

import { useMemo, useState } from 'react'
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
  Filter,
  GitBranch,
  History,
  Info,
  Menu,
  Moon,
  MoreHorizontal,
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
import { Button } from '@/components/ui/button'

const sampleSources = [
  { stance: 'supporting', title: 'World Economic Outlook Database, April 2025', domain: 'imf.org', date: 'Apr 2025', excerpt: 'India is projected to remain among the fastest-growing major economies, with growth supported by resilient domestic demand and public investment.', note: 'Directly corroborates the comparative growth trend.' },
  { stance: 'supporting', title: 'India remains the world’s fastest-growing major economy', domain: 'reuters.com', date: 'Jan 17, 2025', excerpt: 'India’s economy is expected to expand 6.7% this fiscal year, outpacing China as domestic consumption remains strong.', note: 'Independent reporting aligns with the macroeconomic data.' },
  { stance: 'refuting', title: 'China’s 2024 GDP growth meets official target', domain: 'stats.gov.cn', date: 'Jan 17, 2025', excerpt: 'China’s gross domestic product grew 5.0% in 2024, reaching the annual target set by the government.', note: 'Official Chinese figures provide useful comparison context.' },
]

const historySeed = [
  { claim: 'India\'s GDP grew faster than China\'s in 2024.', verdict: 'supported', time: '2 min ago' },
  { claim: 'The James Webb telescope discovered water on an exoplanet.', verdict: 'mixed', time: 'Yesterday' },
  { claim: 'Global temperatures were lower in 2024 than in 2023.', verdict: 'contradicted', time: 'Oct 24' },
]

const verdictMeta = {
  supported: { label: 'Supported', icon: CheckCircle2, tone: 'success', summary: 'The available evidence supports this claim.' },
  contradicted: { label: 'Contradicted', icon: XCircle, tone: 'danger', summary: 'The available evidence challenges this claim.' },
  mixed: { label: 'Mixed', icon: AlertCircle, tone: 'warning', summary: 'The evidence is divided or contains meaningful qualifications.' },
  insufficient_evidence: { label: 'Insufficient evidence', icon: Info, tone: 'neutral', summary: 'There is not enough reliable evidence to reach a conclusion.' },
  not_verifiable: { label: 'Not verifiable', icon: Info, tone: 'indigo', summary: 'This claim cannot be empirically evaluated with available sources.' },
}

type Verdict = keyof typeof verdictMeta

function VerdictBadge({ verdict }: { verdict: Verdict }) {
  const meta = verdictMeta[verdict]
  const Icon = meta.icon
  return <span className={`verdict-badge ${meta.tone}`}><Icon size={14} /> {meta.label}</span>
}

function SourceCard({ source }: { source: typeof sampleSources[number] }) {
  const [expanded, setExpanded] = useState(false)
  return <article className={`source-card ${source.stance}`}>
    <div className="source-topline"><span className="stance-label">{source.stance === 'supporting' ? 'Supports claim' : 'Challenges claim'}</span><button className="icon-btn" aria-label="More source actions"><MoreHorizontal size={16} /></button></div>
    <button className="source-title" onClick={() => setExpanded(!expanded)} aria-expanded={expanded}>
      <span>{source.title}</span><ChevronDown size={16} className={expanded ? 'rotate' : ''} />
    </button>
    <div className="source-meta"><span>{source.domain}</span><span>{source.date}</span><span className="validated"><Check size={12} /> Validated source</span></div>
    <p className="excerpt">“{source.excerpt}”</p>
    {expanded && <div className="source-note"><Sparkles size={14} /> <span><strong>Jintru interpretation</strong> {source.note}</span></div>}
    <div className="source-actions"><button className="text-btn">View evidence <ArrowUpRight size={13} /></button><button className="text-btn" onClick={() => navigator.clipboard?.writeText(source.excerpt)}><Copy size={13} /> Copy quote</button></div>
  </article>
}

function RelationshipGraph() {
  return <section className="relationship panel-section">
    <div className="section-heading"><div><span className="eyebrow">Evidence map</span><h2>How the evidence connects</h2></div><GitBranch size={18} /></div>
    <div className="graph"><div className="graph-node claim-node"><span>CLAIM</span><strong>India’s GDP grew faster than China’s in 2024.</strong></div><div className="graph-line" /><div className="graph-branches"><div className="graph-branch support-branch"><span className="branch-label">SUPPORTS</span><div className="mini-source">IMF database <small>imf.org</small></div><div className="mini-source">Reuters <small>reuters.com</small></div></div><div className="graph-branch refute-branch"><span className="branch-label">CONTEXT</span><div className="mini-source">China NBS <small>stats.gov.cn</small></div></div></div><div className="graph-line short" /><div className="graph-node final-node"><CheckCircle2 size={16} /><span>FINAL VERDICT</span><strong>Supported</strong></div></div>
  </section>
}

export default function Page() {
  const [claim, setClaim] = useState('')
  const [activeClaim, setActiveClaim] = useState('India\'s GDP grew faster than China\'s in 2024.')
  const [verdict, setVerdict] = useState<Verdict>('supported')
  const [loading, setLoading] = useState(false)
  const [collapsed, setCollapsed] = useState(false)
  const [mobileNav, setMobileNav] = useState(false)
  const [dark, setDark] = useState(true)
  const [history, setHistory] = useState(historySeed)
  const [filter, setFilter] = useState('all')
  const [showSettings, setShowSettings] = useState(false)
  const [copied, setCopied] = useState(false)

  const meta = verdictMeta[verdict]
  const filteredHistory = useMemo(() => filter === 'all' ? history : history.filter(item => item.verdict === filter), [filter, history])

  function verify() {
    if (claim.trim().length < 5 || loading) return
    setLoading(true)
    setTimeout(() => { setActiveClaim(claim.trim()); setLoading(false); setVerdict('supported'); setHistory([{ claim: claim.trim(), verdict: 'supported', time: 'Just now' }, ...history]) }, 1100)
  }
  function clearClaim() { if (activeClaim && !window.confirm('Clear the current verification result?')) return; setClaim(''); setActiveClaim('') }
  function copyReport() { navigator.clipboard?.writeText(`# Verification report\n\nClaim: ${activeClaim}\nVerdict: ${meta.label}\n\n${meta.summary}`); setCopied(true); setTimeout(() => setCopied(false), 1600) }
  function exportJson() { const blob = new Blob([JSON.stringify({ claim: activeClaim, verdict, summary: meta.summary, sources: sampleSources }, null, 2)], { type: 'application/json' }); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = 'jintru-verification.json'; a.click(); URL.revokeObjectURL(url) }

  return <div className={dark ? 'app dark' : 'app'}>
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''} ${mobileNav ? 'mobile-open' : ''}`}>
      <div className="brand">{!collapsed && <span className="brand-name">jintru</span>}<button className="mobile-close icon-btn" onClick={() => setMobileNav(false)}><X size={18} /></button></div>
      {!collapsed && <><div className="workspace-label">WORKSPACE</div><button className="new-check" onClick={clearClaim}><Plus size={16} /> New check <span>⌘ N</span></button><nav><a className="active"><ShieldCheck size={16} /> Verify a claim</a><a href="#history"><History size={16} /> History <span className="nav-count">{history.length}</span></a></nav><div className="sidebar-spacer" /><div className="system-status"><span className="status-dot" /><div><strong>System operational</strong><small>All providers connected</small></div></div><button className="sidebar-settings" onClick={() => setShowSettings(true)}><Settings2 size={16} /> Settings</button></>}
      <button className="collapse-btn icon-btn" onClick={() => setCollapsed(!collapsed)} aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}>{collapsed ? <PanelLeftOpen size={17} /> : <PanelLeftClose size={17} />}</button>
    </aside>
    {mobileNav && <button className="scrim" onClick={() => setMobileNav(false)} aria-label="Close navigation" />}
    <main className="main">
      <header className="topbar"><button className="mobile-menu icon-btn" onClick={() => setMobileNav(true)}><Menu size={20} /></button><div className="breadcrumbs"><span>Workspace</span><ChevronRight size={14} /><strong>Verify a claim</strong></div><div className="top-actions"><button className="top-link">Documentation <ArrowUpRight size={14} /></button><button className="theme-toggle icon-btn" onClick={() => setDark(!dark)} aria-label="Toggle theme">{dark ? <Sun size={17} /> : <Moon size={17} />}</button><button className="icon-btn" onClick={() => setShowSettings(true)} aria-label="Open settings"><Settings2 size={17} /></button><div className="avatar">OM</div></div></header>
      <div className="content"><div className="page-intro"><div><span className="eyebrow">REALITY CHECK AI</span><h1>Verify a claim</h1><p>Evidence, not assumptions. Examine what supports a claim, what challenges it, and exactly what remains unknown.</p></div><div className="live-pill"><span className="status-dot" /> Live web evidence</div></div>
        <section className="claim-panel"><div className="claim-header"><div><label htmlFor="claim">Your claim</label><p>Enter one factual assertion for Jintru to investigate.</p></div><span className="input-hint">⌘ ↵ to verify</span></div><textarea id="claim" value={claim} onChange={e => setClaim(e.target.value.slice(0, 500))} placeholder="Example: India's GDP grew faster than China's in 2024." disabled={loading} /><div className="claim-footer"><span className={claim.length > 450 ? 'near-limit' : ''}>{claim.length} / 500</span><div className="claim-actions"><button className="clear-btn" onClick={clearClaim} disabled={loading}><X size={14} /> Clear</button>{loading ? <button className="verify-btn" disabled><RefreshCw size={15} className="spin" /> Verifying…</button> : <button className="verify-btn" onClick={verify} disabled={claim.trim().length < 5}><Search size={15} /> Verify claim</button>}</div></div></section>
        {loading && <section className="progress-card"><div className="progress-head"><div><span className="eyebrow">PROCESSING</span><h2>Verification in progress</h2></div><span className="elapsed"><Clock3 size={14} /> 00:01</span></div><div className="progress-steps">{['Classifying claim','Searching available evidence','Looking for counterevidence','Synthesizing evidence','Validating citations','Saving verification'].map((step, i) => <div className={`progress-step ${i === 1 ? 'current' : i < 1 ? 'done' : ''}`} key={step}><span>{i < 1 ? <Check size={13} /> : `0${i + 1}`}</span>{step}</div>)}</div></section>}
        {activeClaim && !loading && <><div className="result-header"><div><span className="eyebrow">VERIFICATION RESULT</span><h2>Evidence review</h2></div><div className="result-actions"><button className="outline-btn" onClick={() => navigator.clipboard?.writeText(activeClaim)}><Copy size={14} /> Copy claim</button><button className="outline-btn" onClick={copyReport}>{copied ? <Check size={14} /> : <Copy size={14} />} {copied ? 'Copied' : 'Copy report'}</button><button className="outline-btn" onClick={exportJson}><FileDown size={14} /> Export JSON</button></div></div><section className={`verdict-card ${meta.tone}`}><div className="verdict-main"><VerdictBadge verdict={verdict} /><h2>{meta.label}</h2><p>{meta.summary}</p></div><div className="verdict-detail"><span className="eyebrow">CLAIM EVALUATED</span><p>{activeClaim}</p><div className="verified-time"><CheckCircle2 size={14} /> Verified today at 14:32 <span>·</span> 3 source families</div></div></section><RelationshipGraph /><div className="evidence-section"><div className="section-heading"><div><span className="eyebrow">SOURCE REVIEW</span><h2>Evidence</h2></div><div className="filter-pills"><button className={filter === 'all' ? 'selected' : ''} onClick={() => setFilter('all')}>All <span>3</span></button><button className={filter === 'supporting' ? 'selected' : ''} onClick={() => setFilter('supporting')}>Supporting <span>2</span></button><button className={filter === 'refuting' ? 'selected' : ''} onClick={() => setFilter('refuting')}>Refuting <span>1</span></button></div></div><div className="evidence-grid">{sampleSources.filter(source => filter === 'all' || source.stance === filter).map(source => <SourceCard source={source} key={source.title} />)}</div></div><section className="unknown panel-section"><div className="section-heading"><div><span className="eyebrow">BOUNDARIES OF THIS REVIEW</span><h2>What remains unknown</h2></div><ChevronDown size={18} /></div><div className="unknown-body"><Info size={16} /><p>The comparison depends on official GDP estimates and reporting available at the time of review. Final revised figures may differ from initial releases.</p></div></section></>}
        {!activeClaim && !loading && <div className="empty-workspace"><div className="empty-icon"><ShieldCheck size={28} /></div><h2>Ready when you are</h2><p>Enter a claim above to begin an evidence review. Jintru does not generate confidence scores — it shows you the evidence behind the verdict.</p></div>}
      </div>
    </main>
    {showSettings && <div className="settings-overlay" onClick={() => setShowSettings(false)}><section className="settings-panel" onClick={e => e.stopPropagation()}><div className="settings-head"><div><span className="eyebrow">PREFERENCES</span><h2>Settings</h2></div><button className="icon-btn" onClick={() => setShowSettings(false)}><X size={18} /></button></div><div className="setting-row"><div><strong>Appearance</strong><p>Choose how Jintru looks for you.</p></div><button className="theme-choice" onClick={() => setDark(!dark)}>{dark ? <Moon size={15} /> : <Sun size={15} />} {dark ? 'Dark mode' : 'Light mode'}</button></div><div className="setting-row"><div><strong>Backend connection</strong><p>Connected to the Jintru verification API.</p></div><span className="connected"><span className="status-dot" /> Connected</span></div><div className="setting-row"><div><strong>Providers</strong><p>Search providers available to this workspace.</p></div><span className="provider-list">Brave · Meta</span></div><div className="settings-foot">jintru frontend · Milestone 1</div></section></div>}
  </div>
}
