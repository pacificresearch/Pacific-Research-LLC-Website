"""SQLite cache: identical API requests are never paid for twice inside the refresh window."""
from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Optional

log = logging.getLogger("prg.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS api_cache (
  key TEXT PRIMARY KEY, source TEXT, url TEXT, params TEXT,
  retrieved_at TEXT, expires_at TEXT, payload TEXT);
CREATE TABLE IF NOT EXISTS listings (id TEXT PRIMARY KEY, cbsa TEXT, retrieved_at TEXT, payload TEXT);
CREATE TABLE IF NOT EXISTS property_records (id TEXT PRIMARY KEY, retrieved_at TEXT, payload TEXT);
CREATE TABLE IF NOT EXISTS rental_comps (key TEXT PRIMARY KEY, retrieved_at TEXT, payload TEXT);
CREATE TABLE IF NOT EXISTS economic_data (key TEXT PRIMARY KEY, source TEXT, retrieved_at TEXT, payload TEXT);
CREATE TABLE IF NOT EXISTS web_research (key TEXT PRIMARY KEY, query TEXT, retrieved_at TEXT, payload TEXT);
CREATE TABLE IF NOT EXISTS api_calls (ts TEXT, source TEXT, endpoint TEXT, cached INTEGER, status INTEGER);
CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, started_at TEXT, finished_at TEXT, summary TEXT);
"""


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Cache:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._lock = threading.Lock()
        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    @staticmethod
    def make_key(source: str, url: str, params: Optional[dict] = None) -> str:
        blob = json.dumps({"s": source, "u": url, "p": params or {}}, sort_keys=True, default=str)
        return hashlib.sha256(blob.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            row = self.conn.execute("SELECT payload, expires_at FROM api_cache WHERE key=?", (key,)).fetchone()
        if not row:
            return None
        payload, expires_at = row
        if expires_at and datetime.fromisoformat(expires_at) < _now():
            return None
        return json.loads(payload)

    def put(self, key: str, source: str, url: str, params: Optional[dict], payload: Any, ttl_hours: float) -> None:
        now = _now()
        with self._lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO api_cache VALUES (?,?,?,?,?,?,?)",
                (key, source, url, json.dumps(params or {}, default=str), now.isoformat(),
                 (now + timedelta(hours=ttl_hours)).isoformat(), json.dumps(payload, default=str)))
            self.conn.commit()

    def cached(self, source: str, url: str, params: Optional[dict], ttl_hours: float,
               fetch: Callable[[], Any], endpoint: str = "") -> tuple[Any, bool]:
        """Return (payload, was_cached). fetch() is only called on a miss."""
        key = self.make_key(source, url, params)
        hit = self.get(key)
        if hit is not None:
            self.log_call(source, endpoint or url, cached=True, status=200)
            return hit, True
        payload = fetch()
        if payload is not None:
            self.put(key, source, url, params, payload, ttl_hours)
        return payload, False

    def log_call(self, source: str, endpoint: str, cached: bool, status: int) -> None:
        with self._lock:
            self.conn.execute("INSERT INTO api_calls VALUES (?,?,?,?,?)",
                              (_now().isoformat(), source, endpoint, int(cached), status))
            self.conn.commit()

    def call_counts(self, since: Optional[str] = None) -> dict:
        q = "SELECT source, cached, COUNT(*) FROM api_calls"
        args: tuple = ()
        if since:
            q += " WHERE ts >= ?"
            args = (since,)
        q += " GROUP BY source, cached"
        out: dict = {}
        with self._lock:
            for source, cached, n in self.conn.execute(q, args):
                out.setdefault(source, {"live": 0, "cached": 0})
                out[source]["cached" if cached else "live"] += n
        return out

    def store(self, table: str, key: str, payload: Any, extra: Optional[dict] = None) -> None:
        cols = {"key" if table != "listings" and table != "property_records" else "id": key,
                "retrieved_at": _now().isoformat(), "payload": json.dumps(payload, default=str)}
        cols.update(extra or {})
        names = ",".join(cols)
        with self._lock:
            self.conn.execute(f"INSERT OR REPLACE INTO {table} ({names}) VALUES ({','.join('?'*len(cols))})",
                              tuple(cols.values()))
            self.conn.commit()

    def record_run(self, run_id: str, started_at: str, finished_at: str, summary: dict) -> None:
        with self._lock:
            self.conn.execute("INSERT OR REPLACE INTO runs VALUES (?,?,?,?)",
                              (run_id, started_at, finished_at, json.dumps(summary, default=str)))
            self.conn.commit()
