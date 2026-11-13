"""Job discovery: official/public ATS feeds first, browser never used for discovery.

Each adapter yields raw dicts consumed by job_normalization.normalize().
Sources and employers are configured in jobs/employers.yaml (committed, no PII).

Not automated (by design):
  * LinkedIn — its User Agreement prohibits scraping/automated access. Use
    LinkedIn yourself; paste URLs into `jobbot add-url` and the system applies
    through the employer's own ATS.
  * Indeed web — blocks automated access; Indeed results arrive through the
    Indeed connector in a Claude session and are imported with `jobbot import`.
"""
from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor

from .. import application_tracker as db
from ..config import load_config, load_yaml
from ..job_normalization import normalize
from .base import relevant_title
from . import ashby, bigtech, greenhouse, icims, reliefweb, lever, smartrecruiters, un_careers, usajobs, workday, oracle_hcm

log = logging.getLogger("jobbot.discovery")

ADAPTERS = {
    "greenhouse": greenhouse.fetch,
    "lever": lever.fetch,
    "ashby": ashby.fetch,
    "workday": workday.fetch,
    "smartrecruiters": smartrecruiters.fetch,
    "usajobs": usajobs.fetch,
    "un_careers": un_careers.fetch,
    "icims": icims.fetch,
    "bigtech": bigtech.fetch,
    "reliefweb": reliefweb.fetch,
    "oracle": oracle_hcm.fetch,
}


def search_terms() -> dict:
    return load_yaml("search.yaml", {})


def run(only: list[str] | None = None, limit_employers: int | None = None) -> dict:
    """Incremental discovery across every configured employer/source."""
    cfg = load_config()
    reg = load_yaml("employers.yaml", {}) or {}
    terms = search_terms()
    excluded = {e.lower() for e in cfg["employers"].get("exclude", [])}
    stats = {"fetched": 0, "relevant": 0, "new": 0, "dupes": 0, "closed": 0, "errors": {}}
    from .web_search import load_discovered
    entries = [e for e in reg.get("employers", []) + load_discovered() if e.get("enabled", True)]
    for extra in cfg["employers"].get("include", []):
        if isinstance(extra, dict):
            entries.append(extra)
    if limit_employers:
        entries = entries[:limit_employers]
    sel = {o.lower() for o in (only or [])}  # ATS names ("workday") or employer names ("PATH")
    entries = [e for e in entries if not (sel and e["ats"].lower() not in sel and e["name"].lower() not in sel)
               and e["name"].lower() not in excluded
               and e["ats"] in ADAPTERS]

    def one(e):
        fn = ADAPTERS[e["ats"]]
        src = f'{e["ats"]}:{e.get("slug") or e.get("tenant") or e["name"]}'
        local = {"fetched": 0, "relevant": 0, "new": 0, "dupes": 0, "closed": 0}
        try:
            seen, full_enumeration, n = set(), True, 0
            for raw in fn(e, terms):
                n += 1
                local["fetched"] += 1
                full_enumeration = full_enumeration and not raw.pop("_partial", False)
                if not relevant_title(raw["title"], terms):
                    seen.add(str(raw["source_job_id"]))
                    continue
                local["relevant"] += 1
                raw.setdefault("source", src)
                job = normalize(raw)
                seen.add(job["source_job_id"])
                _, new = db.upsert_job(job)
                local["new" if new else "dupes"] += 1
            if full_enumeration and e["ats"] in ("greenhouse", "lever", "ashby"):
                local["closed"] += db.mark_inactive(src, seen)
            db.source_ok(src, n)
            return src, local, None
        except Exception as ex:  # one bad source never stops the run
            log.warning("source %s failed: %s", src, ex)
            db.source_error(src, str(ex))
            return src, local, str(ex)[:200]

    with ThreadPoolExecutor(max_workers=cfg.get("discovery_workers", 8)) as ex:
        for src, local, err in ex.map(one, entries):
            for k, v in local.items():
                stats[k] += v
            if err:
                stats["errors"][src] = err
    return stats


def import_records(records: list[dict], source: str = "import") -> dict:
    """Import jobs found elsewhere (Indeed connector, LinkedIn URLs you pasted, a CSV)."""
    stats = {"new": 0, "dupes": 0, "skipped": 0}
    for r in records:
        if not r.get("title") or not r.get("employer"):
            stats["skipped"] += 1
            continue
        r.setdefault("source", source)
        r.setdefault("source_job_id", r.get("job_url") or r.get("apply_url") or f'{r["employer"]}|{r["title"]}')
        jid, new = db.upsert_job(normalize(r))
        stats["new" if new else "dupes"] += 1
    return stats
