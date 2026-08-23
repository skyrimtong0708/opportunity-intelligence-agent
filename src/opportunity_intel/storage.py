from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .pipeline import PipelineResult


SQLITE_SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS evidence (
  id TEXT PRIMARY KEY, niche_id TEXT NOT NULL, source_type TEXT NOT NULL,
  source_name TEXT NOT NULL, source_url TEXT NOT NULL, title TEXT NOT NULL,
  content TEXT NOT NULL, observed_at TEXT NOT NULL, payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pain_points (
  id TEXT PRIMARY KEY, niche_id TEXT NOT NULL, evidence_id TEXT NOT NULL,
  statement TEXT NOT NULL, payload_json TEXT NOT NULL,
  FOREIGN KEY (evidence_id) REFERENCES evidence(id)
);
CREATE TABLE IF NOT EXISTS clusters (
  id TEXT PRIMARY KEY, niche_id TEXT NOT NULL, label TEXT NOT NULL,
  evidence_count INTEGER NOT NULL, payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS opportunities (
  id TEXT PRIMARY KEY, niche_id TEXT NOT NULL, cluster_id TEXT NOT NULL,
  title TEXT NOT NULL, score REAL NOT NULL, score_version TEXT NOT NULL,
  payload_json TEXT NOT NULL, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (cluster_id) REFERENCES clusters(id)
);
CREATE TABLE IF NOT EXISTS product_candidates (
  id TEXT PRIMARY KEY, niche_id TEXT NOT NULL, marketplace TEXT NOT NULL,
  title TEXT NOT NULL, sourcing_score REAL NOT NULL, source_url TEXT NOT NULL,
  payload_json TEXT NOT NULL, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS media_signals (
  id TEXT PRIMARY KEY, niche_id TEXT NOT NULL, platform TEXT NOT NULL,
  title TEXT NOT NULL, relevance_score REAL NOT NULL, source_url TEXT NOT NULL,
  payload_json TEXT NOT NULL, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_evidence_niche ON evidence(niche_id);
CREATE INDEX IF NOT EXISTS idx_opportunities_niche_score ON opportunities(niche_id, score DESC);
CREATE INDEX IF NOT EXISTS idx_products_niche_score ON product_candidates(niche_id, sourcing_score DESC);
CREATE INDEX IF NOT EXISTS idx_media_niche_score ON media_signals(niche_id, relevance_score DESC);
"""


class SqliteRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, result: PipelineResult) -> None:
        conn = sqlite3.connect(self.path)
        try:
            conn.executescript(SQLITE_SCHEMA)
            for item in result.evidence:
                data = item.to_dict()
                conn.execute(
                    "INSERT OR REPLACE INTO evidence VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (item.id, item.niche_id, item.source_type, item.source_name, item.source_url,
                     item.title, item.content, item.observed_at, json.dumps(data, ensure_ascii=False)),
                )
            for item in result.pain_points:
                conn.execute(
                    "INSERT OR REPLACE INTO pain_points VALUES (?, ?, ?, ?, ?)",
                    (item.id, item.niche_id, item.evidence_id, item.statement,
                     json.dumps(item.to_dict(), ensure_ascii=False)),
                )
            for item in result.clusters:
                conn.execute(
                    "INSERT OR REPLACE INTO clusters VALUES (?, ?, ?, ?, ?)",
                    (item.id, item.niche_id, item.label, item.evidence_count,
                     json.dumps(item.to_dict(), ensure_ascii=False)),
                )
            for item in result.opportunities:
                conn.execute(
                    """INSERT INTO opportunities(id,niche_id,cluster_id,title,score,score_version,payload_json)
                       VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
                       score=excluded.score, payload_json=excluded.payload_json, updated_at=CURRENT_TIMESTAMP""",
                    (item.id, item.niche_id, item.cluster_id, item.title, item.score,
                    item.score_version, json.dumps(item.to_dict(), ensure_ascii=False)),
                )
            for item in result.product_candidates:
                conn.execute(
                    """INSERT INTO product_candidates(id,niche_id,marketplace,title,sourcing_score,source_url,payload_json)
                       VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET sourcing_score=excluded.sourcing_score,
                       payload_json=excluded.payload_json, updated_at=CURRENT_TIMESTAMP""",
                    (item.id, item.niche_id, item.marketplace, item.title, item.sourcing_score,
                     item.source_url, json.dumps(item.to_dict(), ensure_ascii=False)),
                )
            for item in result.media_signals:
                conn.execute(
                    """INSERT INTO media_signals(id,niche_id,platform,title,relevance_score,source_url,payload_json)
                       VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET relevance_score=excluded.relevance_score,
                       payload_json=excluded.payload_json, updated_at=CURRENT_TIMESTAMP""",
                    (item.id, item.niche_id, item.platform, item.title, item.relevance_score,
                     item.source_url, json.dumps(item.to_dict(), ensure_ascii=False)),
                )
            conn.commit()
        finally:
            conn.close()


def write_snapshot(results: dict[str, PipelineResult], path: str | Path) -> None:
    payload = {
        niche_id: {
            "evidence": [x.to_dict() for x in result.evidence],
            "pain_points": [x.to_dict() for x in result.pain_points],
            "clusters": [x.to_dict() for x in result.clusters],
            "opportunities": [x.to_dict() for x in result.opportunities],
            "product_candidates": [x.to_dict() for x in result.product_candidates],
            "media_signals": [x.to_dict() for x in result.media_signals],
        }
        for niche_id, result in results.items()
    }
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
