'use client';

import { useEffect, useMemo, useState } from 'react';
import snapshot from './snapshot.json';

type Evidence = {
  id: string; niche_id: string; source_type: string; source_name: string; source_url: string;
  title: string; content: string; observed_at: string; engagement: number; metadata: { synthetic?: boolean };
};
type PainPoint = {
  id: string; niche_id: string; evidence_id: string; statement: string; actor: string;
  workaround: string; purchase_trigger: string; frequency: number; severity: number;
  willingness_to_pay: number; confidence: number; tags: string[];
};
type Cluster = {
  id: string; niche_id: string; label: string; description: string; pain_point_ids: string[];
  evidence_count: number; keywords: string[];
};
type Opportunity = {
  id: string; niche_id: string; cluster_id: string; title: string; problem: string;
  target_customer: string; proposed_offer: string; business_model: string; score: number;
  evidence_ids: string[]; dimensions: Record<string, number>; risks: string[];
  experiment: { hypothesis: string; method: string; sample_size: number; duration_days: number;
    success_metrics: Record<string, string | number>; stop_rule: string };
};
type ProductCandidate = {
  id: string; niche_id: string; source_type: string; source_name: string; source_url: string; title: string;
  supplier_name: string; marketplace: string; price: number; currency: string; min_order_quantity: number;
  shipping_origin: string; rating: number | null; review_count: number; sold_count: number; problem_tags: string[];
  dimensions: Record<string, number>; sourcing_score: number; risks: string[]; metadata: { synthetic?: boolean };
};
type MediaSignal = {
  id: string; niche_id: string; platform: string; source_type: string; source_url: string; title: string;
  description: string; creator: string; published_at: string; query: string; view_count: number; like_count: number;
  comment_count: number; relevance_score: number; problem_tags: string[]; metadata: { synthetic?: boolean };
};
type NicheData = { evidence: Evidence[]; pain_points: PainPoint[]; clusters: Cluster[]; opportunities: Opportunity[]; product_candidates: ProductCandidate[]; media_signals: MediaSignal[] };
type View = 'overview' | 'signals' | 'sourcing' | 'evidence' | 'experiments';
type Sort = 'score' | 'evidence' | 'risk';

const data = snapshot as Record<string, NicheData>;
const nicheMeta: Record<string, { name: string; short: string; tone: string }> = {
  seller_packing_os: { name: 'Seller Packing OS', short: 'SP', tone: '#c7f464' },
  robot_vacuum_care: { name: 'Robot Vacuum Care', short: 'RV', tone: '#72d6ff' },
  filament_dry_lab: { name: '3D Filament Dry Lab', short: '3D', tone: '#ffb36b' },
  collector_camera_preservation: { name: 'Collector Preservation', short: 'CP', tone: '#c6adff' },
  tropical_bonsai_lab: { name: 'Tropical Bonsai Lab', short: 'TB', tone: '#72e0aa' },
};
const allOpportunities = Object.values(data).flatMap((niche) => niche.opportunities);
const allEvidence = Object.values(data).flatMap((niche) => niche.evidence);
const allPains = Object.values(data).flatMap((niche) => niche.pain_points);
const allClusters = Object.values(data).flatMap((niche) => niche.clusters);
const allProducts = Object.values(data).flatMap((niche) => niche.product_candidates);
const allMedia = Object.values(data).flatMap((niche) => niche.media_signals);
const dimensionLabels: Record<string, string> = {
  frequency: 'Frequency', severity: 'Severity', willingness_to_pay: 'Willingness to pay',
  evidence_strength: 'Evidence strength', market_reach: 'Market reach', repeatability: 'Repeatability',
  data_moat: 'Data moat', ease_of_test: 'Ease of test',
};

function titleOf(opportunity: Opportunity) { return opportunity.title.split(': ')[1] ?? opportunity.title; }
function maturity(opportunity: Opportunity) {
  if (opportunity.score >= 5.8) return { label: 'Emerging', className: 'emerging' };
  if (opportunity.evidence_ids.length >= 2) return { label: 'Validate', className: 'validate' };
  return { label: 'Watch', className: 'watch' };
}

export default function Home() {
  const [view, setView] = useState<View>('overview');
  const [activeNiche, setActiveNiche] = useState('all');
  const [search, setSearch] = useState('');
  const [scoreFloor, setScoreFloor] = useState(0);
  const [sortBy, setSortBy] = useState<Sort>('score');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [drawerTab, setDrawerTab] = useState<'brief' | 'evidence' | 'experiment'>('brief');
  const [shortlist, setShortlist] = useState<string[]>([]);
  const [showCompare, setShowCompare] = useState(false);
  const [runState, setRunState] = useState<'idle' | 'running' | 'done'>('idle');
  const [lastRun, setLastRun] = useState('24 Aug · 01:18');

  const nicheOpportunities = activeNiche === 'all' ? allOpportunities : data[activeNiche].opportunities;
  const opportunities = useMemo(() => {
    const query = search.trim().toLowerCase();
    return nicheOpportunities
      .filter((item) => item.score >= scoreFloor)
      .filter((item) => !query || `${item.title} ${item.problem} ${item.proposed_offer} ${item.target_customer}`.toLowerCase().includes(query))
      .sort((a, b) => sortBy === 'score' ? b.score - a.score : sortBy === 'evidence' ? b.evidence_ids.length - a.evidence_ids.length : a.risks.length - b.risks.length);
  }, [nicheOpportunities, scoreFloor, search, sortBy]);

  const evidence = (activeNiche === 'all' ? allEvidence : data[activeNiche].evidence)
    .filter((item) => !search.trim() || `${item.title} ${item.content} ${item.source_name}`.toLowerCase().includes(search.toLowerCase()));
  const pains = activeNiche === 'all' ? allPains : data[activeNiche].pain_points;
  const clusters = activeNiche === 'all' ? allClusters : data[activeNiche].clusters;
  const products = (activeNiche === 'all' ? allProducts : data[activeNiche].product_candidates)
    .filter((item) => !search.trim() || `${item.title} ${item.supplier_name} ${item.problem_tags.join(' ')}`.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => b.sourcing_score - a.sourcing_score);
  const mediaSignals = (activeNiche === 'all' ? allMedia : data[activeNiche].media_signals)
    .filter((item) => !search.trim() || `${item.title} ${item.description} ${item.query}`.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => b.relevance_score - a.relevance_score);
  const topOpportunity = opportunities[0] ?? nicheOpportunities.sort((a, b) => b.score - a.score)[0];
  const selected = allOpportunities.find((item) => item.id === selectedId) ?? null;
  const compared = shortlist.map((id) => allOpportunities.find((item) => item.id === id)).filter(Boolean) as Opportunity[];

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') { setSelectedId(null); setShowCompare(false); }
      if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault(); document.querySelector<HTMLInputElement>('#global-search')?.focus();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  function openOpportunity(id: string, tab: 'brief' | 'evidence' | 'experiment' = 'brief') {
    setSelectedId(id); setDrawerTab(tab);
  }
  function toggleShortlist(id: string) {
    setShortlist((current) => current.includes(id) ? current.filter((item) => item !== id) : current.length < 3 ? [...current, id] : current);
  }
  function refreshSnapshot() {
    if (runState === 'running') return;
    setRunState('running');
    window.setTimeout(() => { setRunState('done'); setLastRun('just now'); window.setTimeout(() => setRunState('idle'), 1600); }, 900);
  }

  const evidenceCount = activeNiche === 'all' ? allEvidence.length : data[activeNiche].evidence.length;
  const painCount = activeNiche === 'all' ? allPains.length : data[activeNiche].pain_points.length;

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand-mark">OI</div>
        <nav aria-label="Điều hướng chính">
          {([
            ['overview', '⌂', 'Overview'], ['signals', '◇', 'Signals'], ['sourcing', '⌁', 'Sourcing'], ['evidence', '◎', 'Evidence'], ['experiments', '↗', 'Tests'],
          ] as [View, string, string][]).map(([id, icon, label]) => (
            <button key={id} className={`nav-item ${view === id ? 'active' : ''}`} onClick={() => setView(id)} aria-label={label} aria-current={view === id ? 'page' : undefined}>
              <span>{icon}</span><em>{label}</em>
            </button>
          ))}
        </nav>
        <div className="sidebar-foot"><span className="pulse" />Snapshot live</div>
      </aside>

      <section className="workspace">
        <header className="utility-bar">
          <div className="breadcrumbs"><span>Opportunity Intelligence</span><b>/</b><strong>{view}</strong></div>
          <label className="search-box" htmlFor="global-search"><span>⌕</span><input id="global-search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search problems, offers, evidence…" /><kbd>⌘ K</kbd></label>
          <button className={`run-button ${runState}`} onClick={refreshSnapshot} aria-live="polite"><i />{runState === 'running' ? 'Refreshing…' : runState === 'done' ? 'Snapshot ready' : 'Refresh snapshot'}</button>
        </header>

        <div className="niche-tabs" role="tablist" aria-label="Lọc theo niche">
          <button className={activeNiche === 'all' ? 'selected' : ''} onClick={() => setActiveNiche('all')}>All niches <b>5</b></button>
          {Object.entries(nicheMeta).map(([id, meta]) => (
            <button key={id} className={activeNiche === id ? 'selected' : ''} onClick={() => setActiveNiche(id)}>
              <i style={{ background: meta.tone }} />{meta.name}
            </button>
          ))}
        </div>

        {view === 'overview' && <>
          <header className="hero-heading">
            <div><p className="eyebrow">DECISION DESK / AUGUST 2026</p><h1>Good decisions start<br />with <span>real evidence.</span></h1></div>
            <div className="last-updated"><span>Last snapshot</span><strong>{lastRun}</strong><small>deterministic scoring v1</small></div>
          </header>

          <section className="metric-grid" aria-label="Pipeline summary">
            <article className="metric primary"><p>Evidence captured</p><strong>{evidenceCount}</strong><span>traceable observations</span></article>
            <article className="metric"><p>Pain signals</p><strong>{painCount}</strong><span>structured problems</span></article>
            <article className="metric"><p>Opportunity clusters</p><strong>{clusters.length}</strong><span>ranked hypotheses</span></article>
            <article className="metric score"><p>Leading score</p><strong>{topOpportunity?.score.toFixed(2)}</strong><span>out of 10 · synthetic data</span></article>
          </section>

          <section className="content-grid">
            <div className="ranking-panel">
              <div className="section-heading"><div><p className="eyebrow">LIVE PRIORITY QUEUE</p><h2>Where to investigate next</h2></div><button onClick={() => setView('signals')}>View all <span>→</span></button></div>
              <OpportunityList items={opportunities.slice(0, 5)} shortlist={shortlist} onOpen={openOpportunity} onToggle={toggleShortlist} />
            </div>
            {topOpportunity && <FocusCard opportunity={topOpportunity} onOpen={openOpportunity} />}
          </section>

          <section className="lower-grid">
            <article className="pipeline-card">
              <div className="section-heading"><div><p className="eyebrow">SYSTEM HEALTH</p><h2>Six-role pipeline</h2></div><span className="healthy"><i />All checks passed</span></div>
              <div className="pipeline-flow">
                {[['01','Scout','21'],['02','Extract','21'],['03','Cluster','15'],['04','Opportunity','15'],['05','Skeptic','15'],['06','Experiment','15']].map(([index,label,count]) => (
                  <div key={label}><small>{index}</small><b>{label}</b><span>{count} items</span></div>
                ))}
              </div>
            </article>
            <article className="next-card">
              <p className="eyebrow">NEXT HUMAN ACTION</p><h2>Validate before building.</h2>
              <p>Current evidence is synthetic. Start with ten consented Seller Packing OS interviews before allocating capital.</p>
              <button onClick={() => { setActiveNiche('seller_packing_os'); setView('experiments'); }}>Open experiment queue <span>↗</span></button>
            </article>
          </section>
        </>}

        {view === 'signals' && <section className="page-view">
          <PageHeader kicker="OPPORTUNITY BOARD" title="Ranked signals" description="Compare business hypotheses without losing their evidence trail." count={opportunities.length} />
          <div className="control-row">
            <label>Score floor <strong>{scoreFloor.toFixed(1)}</strong><input type="range" min="0" max="7" step="0.1" value={scoreFloor} onChange={(e) => setScoreFloor(Number(e.target.value))} /></label>
            <div className="segmented" aria-label="Sắp xếp">
              {([['score','Score'],['evidence','Evidence'],['risk','Low risk']] as [Sort,string][]).map(([id,label]) => <button key={id} className={sortBy === id ? 'selected' : ''} onClick={() => setSortBy(id)}>{label}</button>)}
            </div>
            <span className="result-count">{opportunities.length} results</span>
          </div>
          <div className="signal-grid">
            {opportunities.map((opportunity, index) => <SignalCard key={opportunity.id} opportunity={opportunity} rank={index + 1} selected={shortlist.includes(opportunity.id)} onOpen={openOpportunity} onToggle={toggleShortlist} />)}
          </div>
          {!opportunities.length && <EmptyState message="No signals match this filter. Lower the score threshold or clear search." />}
        </section>}

        {view === 'sourcing' && <section className="page-view">
          <PageHeader kicker="SUPPLY & CONTENT RADAR" title="Sourcing desk" description="Match problem-led opportunities with testable products and review-worthy content." count={products.length + mediaSignals.length} />
          <div className="source-readiness">
            <article><span className="source-logo youtube">YT</span><div><strong>YouTube Data API</strong><small>Keyword discovery + public statistics</small></div><b>API key</b></article>
            <article><span className="source-logo tiktok">TT</span><div><strong>TikTok Display API</strong><small>Creator-authorized videos only</small></div><b>OAuth</b></article>
            <article><span className="source-logo shopee">S</span><div><strong>Shopee Open Platform</strong><small>Seller-authorized catalog, no scraping</small></div><b>Partner auth</b></article>
          </div>
          <div className="sourcing-heading"><div><p className="eyebrow">PRODUCT SHORTLIST</p><h2>Products worth validating</h2></div><div><strong>{products.length}</strong><span>candidates</span></div></div>
          <div className="product-grid">
            {products.map((product, index) => <article className="product-card" key={product.id}>
              <div className="product-top"><span className="product-rank">#{String(index + 1).padStart(2,'0')}</span><span className="marketplace">{product.marketplace}</span><span className="fixture">{product.metadata.synthetic ? 'fixture' : 'live'}</span></div>
              <p><i style={{ background: nicheMeta[product.niche_id].tone }} />{nicheMeta[product.niche_id].name}</p>
              <h3>{product.title}</h3><span className="supplier">{product.supplier_name} · {product.shipping_origin}</span>
              <div className="product-price"><strong>{new Intl.NumberFormat('vi-VN').format(product.price)} {product.currency}</strong><small>MOQ {product.min_order_quantity}</small></div>
              <div className="product-stats"><span>Score<strong>{product.sourcing_score.toFixed(1)}</strong></span><span>Rating<strong>{product.rating?.toFixed(1) ?? '—'}</strong></span><span>Sold<strong>{product.sold_count || '—'}</strong></span></div>
              <div className="product-tags">{product.problem_tags.slice(0,3).map((tag) => <span key={tag}>{tag}</span>)}</div>
              <div className="product-fit"><span>Pain fit</span><i><b style={{ width: `${product.dimensions.pain_fit * 10}%` }} /></i><strong>{product.dimensions.pain_fit.toFixed(1)}</strong></div>
              <button disabled={product.source_url.startsWith('sample://')} onClick={() => !product.source_url.startsWith('sample://') && window.open(product.source_url, '_blank', 'noopener,noreferrer')}>{product.source_url.startsWith('sample://') ? 'Synthetic — verify at source' : 'Open authorized source'} <span>↗</span></button>
            </article>)}
          </div>
          <div className="sourcing-heading media-heading"><div><p className="eyebrow">CONTENT SIGNALS</p><h2>Videos for human review</h2></div><div><strong>{mediaSignals.length}</strong><span>signals</span></div></div>
          <div className="media-list">
            {mediaSignals.map((item) => <article key={item.id}>
              <span className={`source-logo ${item.platform.toLowerCase()}`}>{item.platform === 'YouTube' ? 'YT' : 'TT'}</span>
              <div><p>{nicheMeta[item.niche_id].name} · query: {item.query}</p><h3>{item.title}</h3><small>{item.description}</small></div>
              <div className="media-metrics"><span>Views<strong>{new Intl.NumberFormat('en', { notation: 'compact' }).format(item.view_count)}</strong></span><span>Comments<strong>{new Intl.NumberFormat('en', { notation: 'compact' }).format(item.comment_count)}</strong></span><span>Review score<strong>{item.relevance_score.toFixed(1)}</strong></span></div>
              <div className="media-tags">{item.problem_tags.slice(0,2).map((tag) => <span key={tag}>{tag}</span>)}</div>
              <button disabled={item.source_url.startsWith('sample://')} onClick={() => !item.source_url.startsWith('sample://') && window.open(item.source_url, '_blank', 'noopener,noreferrer')}>↗</button>
            </article>)}
          </div>
          {!products.length && !mediaSignals.length && <EmptyState message="No sourcing records match your search." />}
          <div className="compliance-banner"><span>!</span><p><strong>Promotion gate</strong><small>Views, ratings and sold counts are directional signals only. Verify authorization, landed cost and source truth before promoting any record into opportunity evidence.</small></p></div>
        </section>}

        {view === 'evidence' && <section className="page-view">
          <PageHeader kicker="SOURCE EXPLORER" title="Evidence ledger" description="Every signal remains traceable to an observation, source and timestamp." count={evidence.length} />
          <div className="evidence-summary">
            <div><strong>{evidence.length}</strong><span>observations</span></div><div><strong>{new Set(evidence.map((item) => item.source_name)).size}</strong><span>source groups</span></div><div><strong>{Math.round(evidence.reduce((sum,item) => sum + item.engagement, 0) / Math.max(evidence.length, 1))}</strong><span>avg. engagement</span></div><div className="warning"><strong>100%</strong><span>synthetic fixtures</span></div>
          </div>
          <div className="evidence-table" role="table">
            <div className="evidence-head" role="row"><span>Observation</span><span>Source</span><span>Observed</span><span>Signals</span><span /></div>
            {evidence.map((item) => {
              const related = allPains.filter((pain) => pain.evidence_id === item.id);
              const relatedOpportunity = allOpportunities.find((opportunity) => opportunity.evidence_ids.includes(item.id));
              return <article className="evidence-row" key={item.id} role="row">
                <div><span className="niche-dot" style={{ background: nicheMeta[item.niche_id].tone }} /><p>{nicheMeta[item.niche_id].name}</p><h3>{item.title}</h3><small>{item.content}</small></div>
                <div><b>{item.source_name}</b><span>{item.source_type.replaceAll('_',' ')}</span></div>
                <time>{new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(item.observed_at))}</time>
                <div className="tag-stack">{related.flatMap((pain) => pain.tags).slice(0, 3).map((tag) => <span key={tag}>{tag}</span>)}</div>
                <button disabled={!relatedOpportunity} onClick={() => relatedOpportunity && openOpportunity(relatedOpportunity.id, 'evidence')}>↗</button>
              </article>;
            })}
          </div>
          {!evidence.length && <EmptyState message="No evidence matches your search." />}
        </section>}

        {view === 'experiments' && <section className="page-view">
          <PageHeader kicker="VALIDATION LAB" title="Experiment queue" description="Turn promising signals into small, falsifiable commitments." count={opportunities.length} />
          <div className="experiment-grid">
            {opportunities.map((opportunity, index) => {
              const status = maturity(opportunity);
              return <article className="experiment-card" key={opportunity.id}>
                <div className="experiment-meta"><span className={`status ${status.className}`}>{status.label}</span><small>TEST {String(index + 1).padStart(2,'0')}</small></div>
                <p>{nicheMeta[opportunity.niche_id].name}</p><h2>{titleOf(opportunity)}</h2>
                <blockquote>{opportunity.experiment.hypothesis}</blockquote>
                <div className="experiment-facts"><div><span>Duration</span><strong>{opportunity.experiment.duration_days} days</strong></div><div><span>Sample</span><strong>{opportunity.experiment.sample_size} people</strong></div><div><span>Score</span><strong>{opportunity.score.toFixed(1)}</strong></div></div>
                <div className="success-line"><span>Primary success gate</span><strong>{Object.values(opportunity.experiment.success_metrics)[0]}</strong></div>
                <button onClick={() => openOpportunity(opportunity.id, 'experiment')}>Review protocol <span>↗</span></button>
              </article>;
            })}
          </div>
        </section>}
      </section>

      {shortlist.length > 0 && <div className="compare-tray"><div><span>{shortlist.length}</span><p><strong>Comparison shortlist</strong><small>{shortlist.length < 2 ? 'Select one more signal' : 'Ready to compare'}</small></p></div><div className="compare-dots">{shortlist.map((id) => { const item = allOpportunities.find((opportunity) => opportunity.id === id)!; return <i key={id} title={titleOf(item)} style={{ background: nicheMeta[item.niche_id].tone }} />; })}</div><button disabled={shortlist.length < 2} onClick={() => setShowCompare(true)}>Compare {shortlist.length} <span>↗</span></button><button className="clear" onClick={() => setShortlist([])}>×</button></div>}
      {selected && <OpportunityDrawer opportunity={selected} tab={drawerTab} setTab={setDrawerTab} onClose={() => setSelectedId(null)} />}
      {showCompare && <CompareModal opportunities={compared} onClose={() => setShowCompare(false)} />}
    </main>
  );
}

function PageHeader({ kicker, title, description, count }: { kicker: string; title: string; description: string; count: number }) {
  return <header className="page-heading"><div><p className="eyebrow">{kicker}</p><h1>{title}<sup>{count}</sup></h1><span>{description}</span></div><div className="quality-stamp"><i>✓</i><p><strong>Auditable snapshot</strong><small>IDs and scores are deterministic</small></p></div></header>;
}

function OpportunityList({ items, shortlist, onOpen, onToggle }: { items: Opportunity[]; shortlist: string[]; onOpen: (id:string, tab?: 'brief'|'evidence'|'experiment') => void; onToggle: (id:string) => void }) {
  return <div className="opportunity-list">{items.map((opportunity, index) => { const meta = nicheMeta[opportunity.niche_id]; return <article className="opportunity-row" key={opportunity.id}>
    <span className="rank">{String(index + 1).padStart(2,'0')}</span><button className={`shortlist-toggle ${shortlist.includes(opportunity.id) ? 'on' : ''}`} onClick={() => onToggle(opportunity.id)} aria-label="Thêm vào so sánh">{shortlist.includes(opportunity.id) ? '✓' : '+'}</button>
    <span className="niche-badge" style={{ '--tone': meta.tone } as React.CSSProperties}>{meta.short}</span><button className="opportunity-copy" onClick={() => onOpen(opportunity.id)}><p>{meta.name}</p><h3>{titleOf(opportunity)}</h3><span>{opportunity.evidence_ids.length} evidence · {opportunity.risks.length} open risks</span></button>
    <ScoreRing score={opportunity.score} /><button className="row-action" onClick={() => onOpen(opportunity.id)} aria-label={`Mở ${opportunity.title}`}>↗</button>
  </article>; })}</div>;
}

function ScoreRing({ score }: { score: number }) {
  return <div className="score-ring" style={{ '--score': score * 10 } as React.CSSProperties}><strong>{score.toFixed(1)}</strong><small>/10</small></div>;
}

function FocusCard({ opportunity, onOpen }: { opportunity: Opportunity; onOpen: (id:string) => void }) {
  return <aside className="focus-card"><div className="focus-top"><span>TOP SIGNAL</span><b>01</b></div><p className="focus-niche">{nicheMeta[opportunity.niche_id].name}</p><h2>{titleOf(opportunity)}</h2><p className="focus-problem">{opportunity.problem}</p><div className="dimension-list">{Object.entries(opportunity.dimensions).slice(0, 4).map(([label, value]) => <div key={label}><span>{dimensionLabels[label]}</span><i><b style={{ width: `${value * 10}%` }} /></i><strong>{value.toFixed(1)}</strong></div>)}</div><button className="focus-action" onClick={() => onOpen(opportunity.id)}>Open decision brief <span>↗</span></button></aside>;
}

function SignalCard({ opportunity, rank, selected, onOpen, onToggle }: { opportunity: Opportunity; rank: number; selected: boolean; onOpen: (id:string) => void; onToggle: (id:string) => void }) {
  const meta = nicheMeta[opportunity.niche_id]; const status = maturity(opportunity);
  return <article className="signal-card"><div className="signal-card-top"><span className="signal-rank">#{String(rank).padStart(2,'0')}</span><span className={`status ${status.className}`}>{status.label}</span><button className={`shortlist-button ${selected ? 'on' : ''}`} onClick={() => onToggle(opportunity.id)}>{selected ? '✓ Shortlisted' : '+ Compare'}</button></div><div className="signal-identity"><span className="niche-badge" style={{ '--tone': meta.tone } as React.CSSProperties}>{meta.short}</span><p>{meta.name}</p></div><h2>{titleOf(opportunity)}</h2><p className="signal-problem">{opportunity.problem}</p><div className="signal-score"><ScoreRing score={opportunity.score} /><div><span>Evidence</span><strong>{opportunity.evidence_ids.length} observations</strong></div><div><span>Open risks</span><strong>{opportunity.risks.length} checks</strong></div></div><div className="signal-bars">{Object.entries(opportunity.dimensions).slice(0,3).map(([label,value]) => <div key={label}><span>{dimensionLabels[label]}</span><i><b style={{ width: `${value*10}%` }} /></i><strong>{value.toFixed(1)}</strong></div>)}</div><button className="card-action" onClick={() => onOpen(opportunity.id)}>Open decision brief <span>↗</span></button></article>;
}

function OpportunityDrawer({ opportunity, tab, setTab, onClose }: { opportunity: Opportunity; tab: 'brief'|'evidence'|'experiment'; setTab: (tab:'brief'|'evidence'|'experiment') => void; onClose: () => void }) {
  const meta = nicheMeta[opportunity.niche_id]; const relatedEvidence = allEvidence.filter((item) => opportunity.evidence_ids.includes(item.id)); const status = maturity(opportunity);
  return <div className="drawer-layer" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}><aside className="drawer" role="dialog" aria-modal="true" aria-label={opportunity.title}>
    <header className="drawer-header"><div><span className="niche-badge" style={{ '--tone': meta.tone } as React.CSSProperties}>{meta.short}</span><p>{meta.name}</p></div><button onClick={onClose} aria-label="Đóng">×</button></header>
    <div className="drawer-title"><div><span className={`status ${status.className}`}>{status.label}</span><small>{opportunity.id}</small></div><h1>{titleOf(opportunity)}</h1><p>{opportunity.target_customer}</p></div>
    <div className="drawer-tabs">{(['brief','evidence','experiment'] as const).map((id) => <button key={id} className={tab === id ? 'selected' : ''} onClick={() => setTab(id)}>{id}<b>{id === 'evidence' ? relatedEvidence.length : ''}</b></button>)}</div>
    <div className="drawer-body">
      {tab === 'brief' && <><section className="score-hero"><ScoreRing score={opportunity.score} /><div><span>Deterministic score v1</span><strong>{opportunity.score.toFixed(2)} / 10</strong><small>Prioritization signal, not market size</small></div></section><section className="brief-block"><p className="eyebrow">PROBLEM</p><h3>{opportunity.problem}</h3></section><section className="offer-block"><p className="eyebrow">PROPOSED OFFER</p><h3>{opportunity.proposed_offer}</h3><span>{opportunity.business_model}</span></section><section><p className="eyebrow">SCORE PROFILE</p><div className="full-dimensions">{Object.entries(opportunity.dimensions).map(([label,value]) => <div key={label}><span>{dimensionLabels[label]}</span><i><b style={{ width: `${value*10}%` }} /></i><strong>{value.toFixed(1)}</strong></div>)}</div></section><section><p className="eyebrow">SKEPTIC CHECK</p><ul className="risk-list">{opportunity.risks.map((risk) => <li key={risk}><span>!</span>{risk}</li>)}</ul></section></>}
      {tab === 'evidence' && <><div className="provenance-note"><span>◎</span><p><strong>Complete provenance trail</strong><small>{relatedEvidence.length} observations currently support this hypothesis.</small></p></div>{relatedEvidence.map((item) => <article className="drawer-evidence" key={item.id}><div><span>{item.source_type.replaceAll('_',' ')}</span><time>{new Date(item.observed_at).toLocaleDateString('en-GB')}</time></div><h3>{item.title}</h3><p>{item.content}</p><small>{item.source_name} · engagement {item.engagement}</small></article>)}</>}
      {tab === 'experiment' && <><section className="hypothesis"><p className="eyebrow">HYPOTHESIS</p><blockquote>{opportunity.experiment.hypothesis}</blockquote></section><div className="experiment-facts drawer-facts"><div><span>Duration</span><strong>{opportunity.experiment.duration_days} days</strong></div><div><span>Sample</span><strong>{opportunity.experiment.sample_size} people</strong></div></div><section className="protocol"><p className="eyebrow">METHOD</p><p>{opportunity.experiment.method}</p></section><section><p className="eyebrow">SUCCESS GATES</p><div className="gates">{Object.entries(opportunity.experiment.success_metrics).map(([label,value]) => <div key={label}><span>✓</span><p>{label.replaceAll('_',' ')}</p><strong>{value}</strong></div>)}</div></section><section className="stop-rule"><p className="eyebrow">STOP RULE</p><p>{opportunity.experiment.stop_rule}</p></section></>}
    </div>
  </aside></div>;
}

function CompareModal({ opportunities, onClose }: { opportunities: Opportunity[]; onClose: () => void }) {
  return <div className="modal-layer" onMouseDown={(event) => event.target === event.currentTarget && onClose()}><section className="compare-modal" role="dialog" aria-modal="true" aria-label="Compare opportunities"><header><div><p className="eyebrow">DECISION COMPARISON</p><h1>Signal side-by-side</h1></div><button onClick={onClose}>×</button></header><div className="compare-grid">{opportunities.map((opportunity) => <article key={opportunity.id}><span className="niche-badge" style={{ '--tone': nicheMeta[opportunity.niche_id].tone } as React.CSSProperties}>{nicheMeta[opportunity.niche_id].short}</span><p>{nicheMeta[opportunity.niche_id].name}</p><h2>{titleOf(opportunity)}</h2><ScoreRing score={opportunity.score} /><div className="compare-facts"><span>Evidence<strong>{opportunity.evidence_ids.length}</strong></span><span>Risks<strong>{opportunity.risks.length}</strong></span><span>Test days<strong>{opportunity.experiment.duration_days}</strong></span></div><div className="full-dimensions">{Object.entries(opportunity.dimensions).map(([label,value]) => <div key={label}><span>{dimensionLabels[label]}</span><i><b style={{ width: `${value*10}%` }} /></i><strong>{value.toFixed(1)}</strong></div>)}</div></article>)}</div></section></div>;
}

function EmptyState({ message }: { message: string }) { return <div className="empty-state"><span>⌕</span><h2>Nothing here yet</h2><p>{message}</p></div>; }
