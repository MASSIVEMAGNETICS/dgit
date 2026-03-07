#!/usr/bin/env python3
# =============================================================================
# VICTOR COMMAND CENTER — DATABASE STORAGE
# =============================================================================

import sqlite3
import json
from pathlib import Path
from typing import List, Optional, Any
from datetime import datetime, timezone

from backend.config import config
from backend.models.repo import RepoSummary, RepoMetadata, RepoStatus
from backend.models.query import QueryRequest, QueryResponse


class Database:
    """SQLite-backed persistence layer for repos and query history."""

    def __init__(self, db_path: Optional[Path] = None):
        self._path = db_path or config.database_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def init_db(self) -> None:
        """Create tables if they don't exist."""
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS repos (
                    name        TEXT PRIMARY KEY,
                    metadata    TEXT NOT NULL,
                    structure   TEXT,
                    scan_ts     TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS queries (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_text  TEXT NOT NULL,
                    intent      TEXT,
                    summary     TEXT,
                    results     TEXT,
                    created_at  TEXT NOT NULL
                );
            """)

    # ------------------------------------------------------------------
    # Repo CRUD
    # ------------------------------------------------------------------

    def save_repo(self, repo_summary: RepoSummary) -> None:
        """Insert or replace a repo summary."""
        metadata_json = repo_summary.metadata.model_dump_json()
        structure_json = repo_summary.structure.model_dump_json() if repo_summary.structure else None
        scan_ts = repo_summary.scan_timestamp.isoformat()

        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO repos (name, metadata, structure, scan_ts)
                VALUES (?, ?, ?, ?)
                """,
                (repo_summary.metadata.name, metadata_json, structure_json, scan_ts),
            )

    def get_repo(self, name: str) -> Optional[RepoSummary]:
        """Retrieve a single repo by name."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT metadata, structure, scan_ts FROM repos WHERE name = ?", (name,)
            ).fetchone()

        if not row:
            return None
        return self._row_to_summary(row)

    def list_repos(self) -> List[RepoSummary]:
        """Return all stored repos."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT metadata, structure, scan_ts FROM repos ORDER BY name"
            ).fetchall()
        return [self._row_to_summary(r) for r in rows]

    def delete_repo(self, name: str) -> bool:
        """Delete a repo by name. Returns True if a row was deleted."""
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM repos WHERE name = ?", (name,))
        return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # Query history
    # ------------------------------------------------------------------

    def save_query(self, query_request: QueryRequest, query_response: QueryResponse) -> None:
        """Persist a query and its response."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO queries (query_text, intent, summary, results, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    query_request.query,
                    query_response.intent,
                    query_response.summary,
                    json.dumps(query_response.results),
                    query_response.timestamp.isoformat(),
                ),
            )

    def get_query_history(self, limit: int = 50) -> List[dict]:
        """Return the most recent queries."""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, query_text, intent, summary, results, created_at
                FROM queries ORDER BY id DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()

        history = []
        for row in rows:
            results_raw = row[4]
            try:
                results = json.loads(results_raw) if results_raw else []
            except Exception:
                results = []
            history.append({
                'id': row[0],
                'query': row[1],
                'intent': row[2],
                'summary': row[3],
                'results': results,
                'created_at': row[5],
            })
        return history

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._path))
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _row_to_summary(row: Any) -> RepoSummary:
        from backend.models.repo import RepoStructure
        metadata = RepoMetadata.model_validate_json(row[0])
        structure = RepoStructure.model_validate_json(row[1]) if row[1] else None
        scan_ts = datetime.fromisoformat(row[2])
        return RepoSummary(metadata=metadata, structure=structure, scan_timestamp=scan_ts)
