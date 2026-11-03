"""SQLite tracking database + the application state machine.

Invariants enforced here (not in callers):
  * one application row per job (UNIQUE job_id)            -> no duplicate applications
  * one job row per fingerprint (employer+title+location)    -> cross-source dedupe
  * every status change is validated against TRANSITIONS and logged to `events`
  * a submit click is recorded (attempts.submit_clicked=1) and committed BEFORE the
    click happens; recovery never re-clicks submit on such an application
  * SUBMITTED requires confirmation evidence
"""
from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone

from .config import path

STATUSES = [
    "DISCOVERED", "SCREENED", "QUALIFIED", "MATERIALS_READY", "AWAITING_APPROVAL",
    "SUBMITTING", "SUBMITTED", "CONFIRMATION_PENDING", "NEEDS_HUMAN_ACTION",
    "FAILED", "REJECTED", "INTERVIEW", "OFFER",
]

TRANSITIONS: dict[str, set[str]] = {
    "DISCOVERED": {"SCREENED", "REJECTED"},
    "SCREENED": {"QUALIFIED", "REJECTED", "SCREENED"},
    "QUALIFIED": {"MATERIALS_READY", "REJECTED", "NEEDS_HUMAN_ACTION", "SCREENED"},
    "MATERIALS_READY": {"AWAITING_APPROVAL", "SUBMITTING", "NEEDS_HUMAN_ACTION", "REJECTED", "MATERIALS_READY"},
    "AWAITING_APPROVAL": {"SUBMITTING", "REJECTED", "NEEDS_HUMAN_ACTION", "MATERIALS_READY", "AWAITING_APPROVAL"},
    "SUBMITTING": {"SUBMITTED", "CONFIRMATION_PENDING", "NEEDS_HUMAN_ACTION", "FAILED", "AWAITING_APPROVAL"},
    "CONFIRMATION_PENDING": {"SUBMITTED", "NEEDS_HUMAN_ACTION", "FAILED", "REJECTED", "INTERVIEW"},
    "NEEDS_HUMAN_ACTION": {"AWAITING_APPROVAL", "SUBMITTED", "REJECTED", "FAILED", "MATERIALS_READY", "SUBMITTING"},
    "FAILED": {"MATERIALS_READY", "NEEDS_HUMAN_ACTION", "REJECTED", "AWAITING_APPROVAL"},
    "SUBMITTED": {"INTERVIEW", "REJECTED", "OFFER"},
    "INTERVIEW": {"OFFER", "REJECTED", "INTERVIEW"},
    "OFFER": set(),
    "REJECTED": {"SCREENED"},  # re-screen only when the rejection came from our own screen
}

COUNTS_AS_SUBMITTED = {"SUBMITTED", "INTERVIEW", "OFFER"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY,
  fingerprint TEXT NOT NULL UNIQUE,
  source TEXT NOT NULL, source_job_id TEXT NOT NULL,
  employer TEXT NOT NULL, title TEXT NOT NULL,
  location TEXT, country TEXT, remote INTEGER DEFAULT 0,
  salary_min REAL, salary_max REAL, salary_currency TEXT, salary_period TEXT,
  salary_label TEXT DEFAULT 'unknown',
  description TEXT, posted_date TEXT,
  job_url TEXT, apply_url TEXT, ats TEXT,
  first_seen TEXT, last_seen TEXT, active INTEGER DEFAULT 1, last_verified TEXT,
  also_seen_on TEXT DEFAULT '[]', raw_json TEXT,
  UNIQUE(source, source_job_id)
);
CREATE TABLE IF NOT EXISTS assessments (
  job_id INTEGER PRIMARY KEY REFERENCES jobs(id),
  category TEXT, family TEXT,
  eligibility TEXT, eligibility_reasons TEXT, confidence REAL,
  score REAL, subscores TEXT, semantic TEXT, scored_at TEXT
);
CREATE TABLE IF NOT EXISTS applications (
  id INTEGER PRIMARY KEY,
  job_id INTEGER NOT NULL UNIQUE REFERENCES jobs(id),
  status TEXT NOT NULL, category TEXT,
  resume_path TEXT, resume_sha TEXT, resume_family TEXT,
  cover_path TEXT, cover_sha TEXT,
  approved_at TEXT, approved_note TEXT,
  submitted_at TEXT, confirmation TEXT, confirmation_evidence TEXT,
  follow_up_date TEXT, needs_action TEXT, notes TEXT,
  status_reason TEXT, attempts INTEGER DEFAULT 0,
  created_at TEXT, updated_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_app_status ON applications(status);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY, application_id INTEGER, ts TEXT,
  from_status TEXT, to_status TEXT, reason TEXT
);
CREATE TABLE IF NOT EXISTS attempts (
  id INTEGER PRIMARY KEY, application_id INTEGER, started_at TEXT, finished_at TEXT,
  mode TEXT, submit_clicked INTEGER DEFAULT 0, outcome TEXT, error TEXT,
  evidence_dir TEXT, field_log TEXT
);
CREATE TABLE IF NOT EXISTS emails (
  id INTEGER PRIMARY KEY, message_id TEXT UNIQUE, received TEXT, sender TEXT,
  subject TEXT, classification TEXT, application_id INTEGER, snippet TEXT,
  needs_attention INTEGER DEFAULT 0, handled INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS runs (
  id INTEGER PRIMARY KEY, started_at TEXT, finished_at TEXT, phase TEXT,
  status TEXT, stats TEXT, error TEXT
);
CREATE TABLE IF NOT EXISTS source_health (
  source TEXT PRIMARY KEY, last_ok TEXT, last_error TEXT, last_error_at TEXT, last_count INTEGER
);
"""

_local = threading.local()


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def today() -> str:
    return datetime.now().astimezone().date().isoformat()


def connect() -> sqlite3.Connection:
    con = getattr(_local, "con", None)
    dbfile = str(path("jobbot.sqlite"))
    if con is None or getattr(_local, "dbfile", None) != dbfile:
        con = sqlite3.connect(dbfile, timeout=30, isolation_level=None)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA foreign_keys=ON")
        con.executescript(SCHEMA)
        _local.con, _local.dbfile = con, dbfile
    return con


def reset_connection() -> None:
    con = getattr(_local, "con", None)
    if con is not None:
        con.close()
    _local.con = None


@contextmanager
def tx():
    con = connect()
    try:
        con.execute("BEGIN IMMEDIATE")
        yield con
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise


# ---------------------------------------------------------------- settings
def get_settings() -> dict:
    out = {}
    for r in connect().execute("SELECT key, value FROM settings"):
        out[r["key"]] = json.loads(r["value"])
    return out


def set_setting(key: str, value) -> None:
    with tx() as con:
        con.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (key, json.dumps(value)))


# ---------------------------------------------------------------- jobs
def upsert_job(job: dict) -> tuple[int, bool]:
    """Insert or refresh a normalized job. Returns (job_id, is_new).

    Dedupe order: exact (source, source_job_id) -> fingerprint (same opening seen on
    another board). A cross-source duplicate is recorded in also_seen_on, never re-inserted.
    """
    ts = now()
    with tx() as con:
        r = con.execute("SELECT id FROM jobs WHERE source=? AND source_job_id=?",
                        (job["source"], job["source_job_id"])).fetchone()
        if r is None:
            r = con.execute("SELECT id, also_seen_on FROM jobs WHERE fingerprint=?", (job["fingerprint"],)).fetchone()
            if r is not None:
                seen = set(json.loads(r["also_seen_on"] or "[]"))
                seen.add(f'{job["source"]}:{job["source_job_id"]}')
                con.execute("UPDATE jobs SET also_seen_on=?, last_seen=?, active=1 WHERE id=?",
                            (json.dumps(sorted(seen)), ts, r["id"]))
                return r["id"], False
            cols = ["fingerprint", "source", "source_job_id", "employer", "title", "location", "country", "remote",
                    "salary_min", "salary_max", "salary_currency", "salary_period", "salary_label", "description",
                    "posted_date", "job_url", "apply_url", "ats", "raw_json"]
            vals = [job.get(c) for c in cols]
            cur = con.execute(
                f"INSERT INTO jobs({','.join(cols)},first_seen,last_seen,active) VALUES({','.join('?'*len(cols))},?,?,1)",
                vals + [ts, ts])
            jid = cur.lastrowid
            con.execute("INSERT INTO applications(job_id,status,created_at,updated_at) VALUES(?,?,?,?)",
                        (jid, "DISCOVERED", ts, ts))
            return jid, True
        # refresh mutable fields of a known posting
        con.execute("""UPDATE jobs SET last_seen=?, active=1, description=COALESCE(?,description),
                       salary_min=COALESCE(?,salary_min), salary_max=COALESCE(?,salary_max),
                       salary_label=CASE WHEN ? IS NOT NULL THEN ? ELSE salary_label END,
                       apply_url=COALESCE(?,apply_url) WHERE id=?""",
                    (ts, job.get("description"), job.get("salary_min"), job.get("salary_max"),
                     job.get("salary_min"), job.get("salary_label"), job.get("apply_url"), r["id"]))
        return r["id"], False


def mark_inactive(source: str, seen_ids: set[str], employer: str | None = None) -> int:
    """Postings from a fully-enumerated source that disappeared are closed."""
    q = "SELECT id, source_job_id FROM jobs WHERE source=? AND active=1"
    args: list = [source]
    if employer:
        q += " AND employer=?"
        args.append(employer)
    n = 0
    with tx() as con:
        for r in con.execute(q, args).fetchall():
            if r["source_job_id"] not in seen_ids:
                con.execute("UPDATE jobs SET active=0 WHERE id=?", (r["id"],))
                n += 1
    return n


def job(job_id: int) -> sqlite3.Row | None:
    return connect().execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()


def save_assessment(job_id: int, a: dict) -> None:
    with tx() as con:
        con.execute("""INSERT INTO assessments(job_id,category,family,eligibility,eligibility_reasons,confidence,
                       score,subscores,semantic,scored_at) VALUES(?,?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(job_id) DO UPDATE SET category=excluded.category, family=excluded.family,
                       eligibility=excluded.eligibility, eligibility_reasons=excluded.eligibility_reasons,
                       confidence=excluded.confidence, score=excluded.score, subscores=excluded.subscores,
                       semantic=COALESCE(excluded.semantic, assessments.semantic), scored_at=excluded.scored_at""",
                    (job_id, a.get("category"), a.get("family"), a.get("eligibility"),
                     json.dumps(a.get("eligibility_reasons", [])), a.get("confidence"), a.get("score"),
                     json.dumps(a.get("subscores", {})),
                     json.dumps(a["semantic"]) if a.get("semantic") else None, now()))
        con.execute("UPDATE applications SET category=? WHERE job_id=?", (a.get("category"), job_id))


# ---------------------------------------------------------------- applications
class TransitionError(RuntimeError):
    pass


def app_by_job(job_id: int) -> sqlite3.Row:
    return connect().execute("SELECT * FROM applications WHERE job_id=?", (job_id,)).fetchone()


def app(app_id: int) -> sqlite3.Row:
    return connect().execute("SELECT * FROM applications WHERE id=?", (app_id,)).fetchone()


def transition(app_id: int, to: str, reason: str = "", **fields) -> None:
    if to not in TRANSITIONS:
        raise TransitionError(f"unknown status {to}")
    with tx() as con:
        r = con.execute("SELECT status FROM applications WHERE id=?", (app_id,)).fetchone()
        if r is None:
            raise TransitionError(f"no application {app_id}")
        frm = r["status"]
        if to not in TRANSITIONS[frm]:
            raise TransitionError(f"illegal transition {frm} -> {to} (app {app_id})")
        if to == "SUBMITTED" and not (fields.get("confirmation") or fields.get("confirmation_evidence")):
            row = con.execute("SELECT confirmation, confirmation_evidence FROM applications WHERE id=?",
                              (app_id,)).fetchone()
            if not (row["confirmation"] or row["confirmation_evidence"]):
                raise TransitionError("SUBMITTED requires confirmation evidence")
        sets = {"status": to, "updated_at": now(), "status_reason": reason, **fields}
        con.execute(f"UPDATE applications SET {','.join(k + '=?' for k in sets)} WHERE id=?",
                    list(sets.values()) + [app_id])
        con.execute("INSERT INTO events(application_id,ts,from_status,to_status,reason) VALUES(?,?,?,?,?)",
                    (app_id, now(), frm, to, reason))


def update_app(app_id: int, **fields) -> None:
    if "status" in fields:
        raise TransitionError("use transition() to change status")
    fields["updated_at"] = now()
    with tx() as con:
        con.execute(f"UPDATE applications SET {','.join(k + '=?' for k in fields)} WHERE id=?",
                    list(fields.values()) + [app_id])


def start_attempt(app_id: int, mode: str) -> int:
    with tx() as con:
        cur = con.execute("INSERT INTO attempts(application_id,started_at,mode) VALUES(?,?,?)", (app_id, now(), mode))
        con.execute("UPDATE applications SET attempts=attempts+1 WHERE id=?", (app_id,))
        return cur.lastrowid


def mark_submit_clicked(attempt_id: int) -> None:
    """Durably record intent BEFORE clicking submit (idempotency barrier)."""
    with tx() as con:
        con.execute("UPDATE attempts SET submit_clicked=1 WHERE id=?", (attempt_id,))


def finish_attempt(attempt_id: int, outcome: str, error: str | None = None, evidence_dir: str | None = None,
                   field_log: list | None = None) -> None:
    with tx() as con:
        con.execute("UPDATE attempts SET finished_at=?, outcome=?, error=?, evidence_dir=?, field_log=? WHERE id=?",
                    (now(), outcome, error, evidence_dir, json.dumps(field_log) if field_log is not None else None,
                     attempt_id))


def ever_clicked_submit(app_id: int) -> bool:
    r = connect().execute("SELECT 1 FROM attempts WHERE application_id=? AND submit_clicked=1", (app_id,)).fetchone()
    return r is not None


def recover() -> list[str]:
    """Crash recovery: resolve applications left mid-flight by a dead process."""
    notes = []
    for r in connect().execute("SELECT id FROM applications WHERE status='SUBMITTING'").fetchall():
        if ever_clicked_submit(r["id"]):
            transition(r["id"], "CONFIRMATION_PENDING", "recovered after crash: submit was clicked; verify, never resubmit")
            notes.append(f"app {r['id']}: SUBMITTING -> CONFIRMATION_PENDING")
        else:
            transition(r["id"], "AWAITING_APPROVAL", "recovered after crash before submit click")
            notes.append(f"app {r['id']}: SUBMITTING -> AWAITING_APPROVAL")
    with tx() as con:
        con.execute("UPDATE attempts SET finished_at=?, outcome='aborted' WHERE finished_at IS NULL", (now(),))
        con.execute("UPDATE runs SET finished_at=?, status='aborted' WHERE finished_at IS NULL", (now(),))
    return notes


def submitted_today(category: str | None = None) -> int:
    # employer-confirmed submissions only; a later employer rejection still counts as a submission
    q = ("SELECT COUNT(*) FROM applications WHERE submitted_at IS NOT NULL AND confirmation IS NOT NULL "
         "AND substr(submitted_at,1,10)=?")
    args: list = [datetime.now(timezone.utc).date().isoformat()]
    if category:
        q += " AND category=?"
        args.append(category)
    return connect().execute(q, args).fetchone()[0]


def employer_submissions_today(employer: str) -> int:
    return connect().execute(
        """SELECT COUNT(*) FROM applications a JOIN jobs j ON j.id=a.job_id
           WHERE j.employer=? AND a.status IN ('SUBMITTING','SUBMITTED','CONFIRMATION_PENDING')
           AND substr(a.updated_at,1,10)=?""",
        (employer, datetime.now(timezone.utc).date().isoformat())).fetchone()[0]


def source_ok(source: str, count: int) -> None:
    with tx() as con:
        con.execute("""INSERT INTO source_health(source,last_ok,last_count) VALUES(?,?,?)
                       ON CONFLICT(source) DO UPDATE SET last_ok=excluded.last_ok, last_count=excluded.last_count""",
                    (source, now(), count))


def source_error(source: str, err: str) -> None:
    with tx() as con:
        con.execute("""INSERT INTO source_health(source,last_error,last_error_at) VALUES(?,?,?)
                       ON CONFLICT(source) DO UPDATE SET last_error=excluded.last_error,
                       last_error_at=excluded.last_error_at""", (source, err[:500], now()))


def pipeline_rows(status: str | None = None, category: str | None = None, q: str | None = None,
                  limit: int = 500) -> list[sqlite3.Row]:
    sql = """SELECT a.*, j.employer, j.title, j.location, j.country, j.salary_min, j.salary_max, j.salary_label,
             j.salary_currency, j.apply_url, j.job_url, j.source, j.ats, j.posted_date, j.active,
             s.score, s.confidence, s.eligibility, s.eligibility_reasons, s.family, s.subscores
             FROM applications a JOIN jobs j ON j.id=a.job_id LEFT JOIN assessments s ON s.job_id=j.id WHERE 1=1"""
    args: list = []
    if status:
        sql += " AND a.status=?"
        args.append(status)
    if category:
        sql += " AND a.category=?"
        args.append(category)
    if q:
        sql += " AND (j.employer LIKE ? OR j.title LIKE ? OR j.location LIKE ?)"
        args += [f"%{q}%"] * 3
    sql += " ORDER BY COALESCE(s.score,0) DESC LIMIT ?"
    args.append(limit)
    return connect().execute(sql, args).fetchall()
