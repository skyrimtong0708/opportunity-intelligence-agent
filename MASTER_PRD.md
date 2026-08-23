# Opportunity Intelligence Agent — MASTER PRD

Status: MVP v0.1  
Reference niche: Seller Packing OS  
Initial universe: Seller Packing OS, Robot Vacuum Care, 3D Filament Dry Lab, Collector/Camera Preservation, Tropical Bonsai Lab

## 1. Product mission

Turn lawful, traceable observations into testable business opportunities. The system optimizes for recurring problems—not trending products—and preserves the evidence trail behind every conclusion.

The core loop is:

`collect → extract pains → cluster → propose opportunity → deterministic score → challenge → design experiment`

One shared engine processes all niches. A new niche is introduced through a configuration file and evidence adapter, without copying pipeline logic.

## 2. MVP users and decisions

Primary user: an operator/researcher choosing which micro-business opportunity to validate next.

The MVP supports three decisions:

1. Which problem cluster has the strongest current evidence?
2. Why did it receive its score, and what evidence supports it?
3. What is the cheapest falsifiable experiment to run next?

The MVP does not autonomously purchase, publish, contact people, scrape restricted sites, or claim product-market fit.

### Sourcing extension

The post-MVP sourcing track keeps product supply and media discovery separate from
validated problem evidence. It ranks product candidates on pain fit, demand signal,
repeatability, margin potential, supplier reliability, differentiation and ease of
test. It also ranks video metadata for human review. Neither score changes an
opportunity score until a reviewer promotes a record into the Evidence contract.

Supported source boundaries:

- YouTube Data API v3 for keyword search and public video statistics;
- TikTok Display API for videos explicitly authorized by their creator;
- Shopee Open Platform for the catalog of an authorized seller shop;
- licensed/manual exports for broader supplier or marketplace discovery.

Public-page scraping, unofficial mobile endpoints and TikTok Research API use for
commercial opportunity discovery remain out of scope.

## 3. Functional scope

### Six agent roles

| Role | Input | Output | MVP implementation |
|---|---|---|---|
| Scout | Niche config + adapters | Deduplicated evidence | Local samples; RSS/public API stubs |
| Extractor | Evidence | Structured pain points | Deterministic keyword heuristics |
| Clustering | Pain points | Problem clusters | Config-driven taxonomy |
| Opportunity | Clusters + pains | Offers + score dimensions | Templates and deterministic aggregation |
| Skeptic | Opportunities | Risks and disconfirming checks | Rule-based QA gates |
| Experiment | Challenged opportunity | 7-day validation plan | Reusable interview/smoke-test protocol |

These are roles, not six continuously running services. Each has a stable interface so a future LLM or specialized model can replace its deterministic MVP implementation independently.

### Niche configuration

Each `configs/niches/*.yaml` file is JSON-compatible YAML and contains:

- identity, actors and seed queries;
- pain vocabulary and cluster taxonomy;
- offer templates;
- approved source types/status;
- optional scoring weight overrides.

### Evidence and provenance

Every observation requires `source_type`, `source_name`, `source_url`, observation time and raw content. Synthetic fixtures are explicitly labeled. Opportunity records retain evidence IDs for auditability.

### Deterministic scoring v1

All dimensions use a 0–10 scale:

| Dimension | Weight |
|---|---:|
| Frequency | 18% |
| Severity | 18% |
| Willingness to pay | 16% |
| Evidence strength | 14% |
| Market reach | 10% |
| Repeatability | 10% |
| Data moat | 8% |
| Ease of test | 6% |

`total = Σ(dimension × weight)`

The function rejects missing/out-of-range dimensions and weights that do not sum to 1. Scores are reproducible but are prioritization signals, not market-size estimates. Evidence strength remains low for the supplied synthetic sample by design.

## 4. Non-functional requirements

- Deterministic: identical config and evidence produce identical IDs, ordering and scores.
- Auditable: each opportunity links to evidence and exposes dimension values.
- Config-driven: no niche branches in the pipeline engine.
- Local-first: no credentials or network required for the demo.
- PostgreSQL/pgvector-ready: production DDL contains JSONB, vectors, constraints and HNSW indexes.
- Safe acquisition: only first-party consented data, official/public APIs, licensed/open datasets and allowed RSS feeds.
- Replaceable intelligence: role interfaces remain stable when heuristics are upgraded to LLM/model calls.

## 5. Data flow and contracts

```text
Niche YAML ─┐
            ├─ Scout ─ Evidence ─ Extractor ─ PainPoint ─ Clustering ─ Cluster
Adapters ───┘                                                        │
                                                                     v
Snapshot/DB ← Experiment ← Skeptic ← Score ← Opportunity proposal ───┘
```

Canonical JSON contracts live in `contracts/`. Python dataclasses are runtime contracts. SQLite is the zero-dependency local store; `db/postgres_schema.sql` is the production-ready relational/vector target.

## 6. Source policy

Allowed by default:

- consented interviews, surveys and support tickets owned by the operator;
- official APIs under their documented terms;
- public feeds whose publisher permits automated consumption;
- open/licensed datasets with attribution and retention compliance;
- public manuals/research used within copyright and attribution rules.

Not allowed:

- bypassing authentication, CAPTCHAs, rate limits or robots controls;
- scraping marketplaces/social platforms against their terms;
- collecting private or sensitive personal data without a valid basis;
- republishing copyrighted content beyond permitted use.

An adapter must document authorization, rate limits, retention and deletion before activation. Network adapters are intentionally inert in the MVP.

## 7. MVP acceptance criteria

- One command runs all five niches without network access.
- Seller Packing OS completes every role and yields ranked opportunities.
- The same engine handles all five configs without niche-specific conditionals.
- Scores are stable and have a visible dimension breakdown.
- SQLite and JSON snapshots are produced.
- Dashboard filters by niche and shows score, risk, experiment and evidence trail.
- PostgreSQL schema enables pgvector and preserves source provenance.
- Product and media sourcing outputs exist for all five niche configurations.
- Automated tests cover config loading, score validation, deterministic pipeline and persistence.

## 8. Explicit limitations and next gates

This MVP proves system shape, not market truth. Sample evidence is synthetic, extraction is lexical, clustering uses a configured taxonomy, embeddings are not generated, and market reach is a proxy. No opportunity should receive spend before human review and first-party validation.

Recommended next gates:

1. Conduct 10 consented Seller Packing OS interviews and import their de-identified notes.
2. Calibrate extraction and scoring against two human reviewers.
3. Implement one approved source adapter with rate limiting and provenance tests.
4. Add evidence independence/source-diversity metrics.
5. Only then add embeddings/semantic retrieval and optional LLM extraction behind versioned prompts.
