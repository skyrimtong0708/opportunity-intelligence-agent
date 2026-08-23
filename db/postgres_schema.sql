CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS niches (
  id text PRIMARY KEY,
  name text NOT NULL,
  config jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS evidence (
  id text PRIMARY KEY,
  niche_id text NOT NULL REFERENCES niches(id),
  source_type text NOT NULL,
  source_name text NOT NULL,
  source_url text NOT NULL,
  title text NOT NULL,
  content text NOT NULL,
  observed_at timestamptz NOT NULL,
  collected_at timestamptz NOT NULL DEFAULT now(),
  engagement integer NOT NULL DEFAULT 0 CHECK (engagement >= 0),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  content_hash text GENERATED ALWAYS AS (encode(digest(lower(trim(content)), 'sha256'), 'hex')) STORED,
  embedding vector(1536),
  UNIQUE (niche_id, source_url, content_hash)
);

CREATE TABLE IF NOT EXISTS pain_points (
  id text PRIMARY KEY,
  niche_id text NOT NULL REFERENCES niches(id),
  evidence_id text NOT NULL REFERENCES evidence(id),
  statement text NOT NULL,
  actor text NOT NULL,
  workaround text NOT NULL,
  purchase_trigger text NOT NULL,
  frequency numeric(4,2) NOT NULL CHECK (frequency BETWEEN 0 AND 10),
  severity numeric(4,2) NOT NULL CHECK (severity BETWEEN 0 AND 10),
  willingness_to_pay numeric(4,2) NOT NULL CHECK (willingness_to_pay BETWEEN 0 AND 10),
  confidence numeric(4,3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  tags text[] NOT NULL DEFAULT '{}',
  embedding vector(1536)
);

CREATE TABLE IF NOT EXISTS clusters (
  id text PRIMARY KEY,
  niche_id text NOT NULL REFERENCES niches(id),
  label text NOT NULL,
  description text NOT NULL,
  pain_point_ids text[] NOT NULL,
  evidence_count integer NOT NULL,
  keywords text[] NOT NULL DEFAULT '{}',
  embedding vector(1536)
);

CREATE TABLE IF NOT EXISTS opportunities (
  id text PRIMARY KEY,
  niche_id text NOT NULL REFERENCES niches(id),
  cluster_id text NOT NULL REFERENCES clusters(id),
  title text NOT NULL,
  problem text NOT NULL,
  target_customer text NOT NULL,
  proposed_offer text NOT NULL,
  business_model text NOT NULL,
  evidence_ids text[] NOT NULL,
  dimensions jsonb NOT NULL,
  score numeric(4,2) NOT NULL CHECK (score BETWEEN 0 AND 10),
  score_version text NOT NULL,
  risks jsonb NOT NULL DEFAULT '[]'::jsonb,
  experiment jsonb NOT NULL DEFAULT '{}'::jsonb,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS product_candidates (
  id text PRIMARY KEY,
  niche_id text NOT NULL REFERENCES niches(id),
  source_type text NOT NULL,
  source_name text NOT NULL,
  source_url text NOT NULL,
  title text NOT NULL,
  supplier_name text NOT NULL,
  marketplace text NOT NULL,
  price numeric(14,2) NOT NULL CHECK (price >= 0),
  currency text NOT NULL,
  min_order_quantity integer NOT NULL CHECK (min_order_quantity >= 1),
  shipping_origin text NOT NULL,
  rating numeric(3,2),
  review_count integer NOT NULL DEFAULT 0,
  sold_count integer NOT NULL DEFAULT 0,
  problem_tags text[] NOT NULL DEFAULT '{}',
  dimensions jsonb NOT NULL,
  sourcing_score numeric(4,2) NOT NULL CHECK (sourcing_score BETWEEN 0 AND 10),
  score_version text NOT NULL,
  linked_opportunity_ids text[] NOT NULL DEFAULT '{}',
  risks jsonb NOT NULL DEFAULT '[]'::jsonb,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  collected_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS media_signals (
  id text PRIMARY KEY,
  niche_id text NOT NULL REFERENCES niches(id),
  platform text NOT NULL,
  source_type text NOT NULL,
  source_url text NOT NULL,
  title text NOT NULL,
  description text NOT NULL,
  creator text NOT NULL,
  published_at timestamptz NOT NULL,
  query text NOT NULL,
  view_count bigint NOT NULL DEFAULT 0,
  like_count bigint NOT NULL DEFAULT 0,
  comment_count bigint NOT NULL DEFAULT 0,
  relevance_score numeric(4,2) NOT NULL CHECK (relevance_score BETWEEN 0 AND 10),
  problem_tags text[] NOT NULL DEFAULT '{}',
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  collected_at timestamptz NOT NULL DEFAULT now(),
  embedding vector(1536)
);

CREATE INDEX IF NOT EXISTS evidence_niche_observed_idx ON evidence(niche_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS opportunity_niche_score_idx ON opportunities(niche_id, score DESC);
CREATE INDEX IF NOT EXISTS product_niche_score_idx ON product_candidates(niche_id, sourcing_score DESC);
CREATE INDEX IF NOT EXISTS media_niche_score_idx ON media_signals(niche_id, relevance_score DESC);
CREATE INDEX IF NOT EXISTS evidence_embedding_hnsw_idx ON evidence USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS pain_embedding_hnsw_idx ON pain_points USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS media_embedding_hnsw_idx ON media_signals USING hnsw (embedding vector_cosine_ops);
