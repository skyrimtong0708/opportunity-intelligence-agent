# Opportunity Intelligence Agent MVP

A runnable, config-driven research pipeline for five opportunity niches. Seller Packing OS is the reference configuration; the engine itself contains no niche-specific branches.

## What is included

- six role pipeline: Scout, Extractor, Clustering, Opportunity, Skeptic, Experiment;
- deterministic scoring v1 with validation and stable content IDs;
- five JSON-compatible YAML niche configs;
- synthetic, explicitly labeled sample evidence;
- SQLite local persistence and PostgreSQL/pgvector production DDL;
- Streamlit dashboard with opportunity, risks, experiment and evidence trail;
- production-grade interactive web dashboard under `dashboard-web/`;
- JSON Schema contracts and automated tests;
- inert RSS/public API adapter stubs—no prohibited scraping.
- product sourcing and media-signal tracks for YouTube, TikTok and Shopee-compatible inputs;

See [MASTER_PRD.md](MASTER_PRD.md) for requirements and limitations.

## Repository map

```text
configs/niches/       five niche configurations
contracts/            external JSON data contracts
dashboard/app.py      Streamlit MVP
dashboard-web/        interactive Sites control center
data/sample/          synthetic evidence fixtures
docs/                 source authorization and adapter setup
data/runtime/         generated SQLite DB and latest snapshot
db/                   PostgreSQL/pgvector schema
src/opportunity_intel shared engine and CLI
tests/                deterministic/unit/integration tests
```

## Quick start

Requires Python 3.11+.

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m opportunity_intel.cli run --all
streamlit run dashboard/app.py
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m opportunity_intel.cli run --all
streamlit run dashboard/app.py
```

Open the Streamlit URL printed in the terminal (normally `http://localhost:8501`).

The same pipeline command also refreshes `dashboard-web/app/snapshot.json`. To run
the richer dashboard locally, open `dashboard-web/`, install its dependencies and
start its development script. Rebuild it after each new pipeline snapshot.

Run only the reference niche:

```bash
python -m opportunity_intel.cli run --niche seller_packing_os
```

Run official, credential-gated source adapters in addition to fixtures:

```bash
python -m opportunity_intel.cli run --all --live-sources
```

Run tests:

```bash
python -m pytest
```

The core test suite also works without installing third-party packages:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

In Windows PowerShell use `$env:PYTHONPATH='src'` before that command.

## PostgreSQL/pgvector option

The demo writes to `data/runtime/oia.db`. For the production-shaped database schema:

```bash
cp .env.example .env
# Replace POSTGRES_PASSWORD in .env before starting PostgreSQL.
docker compose up -d postgres
```

On Windows PowerShell, use `Copy-Item .env.example .env`. This creates PostgreSQL 16 with pgvector and initializes `db/postgres_schema.sql`. The MVP does not yet write through a PostgreSQL repository; the DDL is ready for that adapter. The Compose service refuses to start until a local password is provided, and `.env` is excluded from Git.

## Add a niche

1. Copy a config under `configs/niches/` and set a unique snake-case `id`.
2. Define actors, vocabulary, clusters and offer templates.
3. Add properly licensed/consented evidence through an adapter.
4. Run the pipeline and review all evidence/risk output manually.

Config files use the JSON subset of YAML so the core engine runs with only Python's standard library. PyYAML remains installed for future richer YAML syntax.

## Source safety

Adapters are the compliance boundary. Before enabling a source, document its terms, authorization, rate limit, retention and attribution. Official adapters remain inert without their corresponding credentials. See the PRD source policy before enabling them.

The sourcing extension includes official/authorized adapters for YouTube Data API,
TikTok Display API and a Shopee seller catalog. They return no network data until
the corresponding environment credentials are present. See
`docs/SOURCE_ADAPTERS.md` before enabling any source.
