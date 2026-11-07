"""Web-search discovery: find employer job boards through search engines, then read them through
their official public feeds.

Search results are used only to learn WHICH employers have relevant openings and WHERE their ATS
board lives (job-boards.greenhouse.io/<slug>, jobs.lever.co/<slug>, jobs.ashbyhq.com/<slug>,
<tenant>.<wd>.myworkdayjobs.com/<site>, jobs.smartrecruiters.com/<id>). Each verified board is added
to $JOBBOT_HOME/employers_discovered.yaml and is then enumerated every day by the normal adapters, so
coverage compounds. Aggregators that re-post other companies' jobs are excluded.

Search backends:
  * a Claude session with WebSearch: Claude runs SEARCH_QUERIES and calls `harvest(urls)`
    (`python -m jobbot harvest urls.txt`);
  * unattended on your Mac: `claude -p` with the WebSearch tool (search_with_claude()).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess

import yaml

from ..config import home
from .base import http

AGGREGATORS = {"jobgether", "leverdemo-60", "jobboardio", "remotehunter", "dice", "hirebasis", "talentify",
               "jobot", "cynet", "insight-global", "kforce", "teksystems"}

SEARCH_QUERIES = [
    'site:job-boards.greenhouse.io "clinical trial manager"',
    'site:job-boards.greenhouse.io "clinical operations manager"',
    'site:job-boards.greenhouse.io "clinical project manager"',
    'site:job-boards.greenhouse.io "clinical research" manager California',
    'site:jobs.lever.co "clinical operations"',
    'site:jobs.lever.co "clinical trial manager"',
    'site:jobs.lever.co "global health"',
    'site:jobs.ashbyhq.com "clinical operations"',
    'site:myworkdayjobs.com "clinical trial manager"',
    'site:myworkdayjobs.com "clinical research manager"',
    'site:myworkdayjobs.com "global health" program',
    'site:myworkdayjobs.com "health security"',
    'site:jobs.smartrecruiters.com "clinical operations"',
    '"clinical trial manager" remote greenhouse OR lever',
    '"global health program manager" careers',
    '"medical device" "program manager" Irvine careers',
    # Andrew 11/6: more remote and international
    'site:job-boards.greenhouse.io "clinical trial manager" remote',
    'site:jobs.lever.co "clinical project manager" remote',
    'site:myworkdayjobs.com "clinical operations" "remote"',
    'site:myworkdayjobs.com "global health" "program manager"',
    'site:myworkdayjobs.com "international programs" manager',
    'site:job-boards.greenhouse.io "global health"',
    'site:jobs.lever.co "international development"',
    '"global clinical operations" manager remote careers',
    '"humanitarian" "program manager" health careers greenhouse OR lever OR workday',
    '"global health security" program manager careers',
]

PATTERNS = [
    ("greenhouse", re.compile(r"(?:job-boards|boards)(?:\.eu)?\.greenhouse\.io/(?:embed/job_board\?for=)?([a-z0-9_-]+)", re.I)),
    ("lever", re.compile(r"jobs\.(?:eu\.)?lever\.co/([a-z0-9_.-]+)", re.I)),
    ("ashby", re.compile(r"jobs\.ashbyhq\.com/([a-z0-9_.%-]+)", re.I)),
    ("workday", re.compile(r"https?://([a-z0-9-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([A-Za-z0-9_-]+)", re.I)),
    ("smartrecruiters", re.compile(r"(?:jobs|careers)\.smartrecruiters\.com/([A-Za-z0-9_-]+)", re.I)),
]


def parse(url: str) -> dict | None:
    for ats, rx in PATTERNS:
        m = rx.search(url)
        if not m:
            continue
        if ats == "workday":
            tenant, wd, site = m.group(1).lower(), m.group(2).lower(), m.group(3)
            if site.lower() in ("job", "jobs", "details", "en-us"):
                return None
            return {"ats": "workday", "tenant": tenant, "wd": wd, "site": site, "name": tenant}
        slug = m.group(1).strip("/").lower() if ats != "smartrecruiters" else m.group(1)
        if slug in AGGREGATORS or slug in ("embed", "jobs", "job", "search"):
            return None
        return {"ats": ats, "slug": slug, "name": slug}
    return None


def _verify(e: dict) -> tuple[bool, str, int]:
    """Confirm the board exists and get the employer's display name and posting count."""
    try:
        if e["ats"] == "greenhouse":
            d = http("GET", f"https://boards-api.greenhouse.io/v1/boards/{e['slug']}").json()
            n = len(http("GET", f"https://boards-api.greenhouse.io/v1/boards/{e['slug']}/jobs").json().get("jobs", []))
            return True, d.get("name") or e["slug"], n
        if e["ats"] == "lever":
            j = http("GET", f"https://api.lever.co/v0/postings/{e['slug']}", params={"mode": "json"}).json()
            return isinstance(j, list), e["slug"].replace("-", " ").title(), len(j) if isinstance(j, list) else 0
        if e["ats"] == "ashby":
            j = http("GET", f"https://api.ashbyhq.com/posting-api/job-board/{e['slug']}").json()
            return True, e["slug"].replace("-", " ").title(), len(j.get("jobs", []))
        if e["ats"] == "workday":
            j = http("POST", f"https://{e['tenant']}.{e['wd']}.myworkdayjobs.com/wday/cxs/{e['tenant']}/{e['site']}/jobs",
                     json={"appliedFacets": {}, "limit": 1, "offset": 0, "searchText": ""}).json()
            return True, e["tenant"].replace("-", " ").title(), j.get("total", 0)
        if e["ats"] == "smartrecruiters":
            j = http("GET", f"https://api.smartrecruiters.com/v1/companies/{e['slug']}/postings", params={"limit": 1}).json()
            return j.get("totalFound", 0) > 0, e["slug"], j.get("totalFound", 0)
    except Exception:
        return False, "", 0
    return False, "", 0


def _relevant_count(e: dict) -> int:
    from ..config import load_yaml
    from .base import relevant_title
    from . import ashby, greenhouse, lever, smartrecruiters, workday
    terms = load_yaml("search.yaml", {})
    if e["ats"] == "workday":
        return 1  # keyword-searched per query anyway
    fn = {"greenhouse": greenhouse.fetch, "lever": lever.fetch, "ashby": ashby.fetch,
          "smartrecruiters": smartrecruiters.fetch}[e["ats"]]
    try:
        return sum(1 for r in fn(e, terms) if relevant_title(r["title"], terms))
    except Exception:
        return 0


def _key(e: dict) -> str:
    ident = e.get("slug") or (f"{e['tenant']}/{e.get('site', '')}" if e.get("tenant") else e.get("name", ""))
    return f"{e['ats']}:{ident}".lower()


def registry_file():
    return home() / "employers_discovered.yaml"


def load_discovered() -> list[dict]:
    f = registry_file()
    return (yaml.safe_load(f.read_text()) or {}).get("employers", []) if f.exists() else []


def harvest(urls: list[str], names: dict | None = None) -> dict:
    """Parse URLs -> ATS boards, verify each, append new ones to the discovered registry."""
    from ..config import load_yaml
    known = {_key(e) for e in (load_yaml("employers.yaml", {}) or {}).get("employers", []) if e.get("ats")}
    disc = load_discovered()
    known |= {_key(e) for e in disc}
    stats = {"urls": len(urls), "boards": 0, "added": [], "rejected": []}
    seen = set()
    for u in urls:
        e = parse(u)
        if not e or _key(e) in seen:
            continue
        seen.add(_key(e))
        stats["boards"] += 1
        if _key(e) in known:
            continue
        ok, name, n = _verify(e)
        if not ok or n == 0:
            stats["rejected"].append(_key(e))
            continue
        rel = _relevant_count(e)
        if rel == 0:  # same-name company in another industry, or nothing in our lane
            stats["rejected"].append(_key(e) + " (no relevant titles)")
            continue
        e["name"] = (names or {}).get(_key(e)) or name
        e["tier"] = 2
        e["found_via"] = u[:200]
        disc.append(e)
        known.add(_key(e))
        stats["added"].append(f"{e['name']} ({e['ats']}, {n} postings)")
    registry_file().write_text(yaml.safe_dump({"employers": disc}, sort_keys=False, allow_unicode=True))
    return stats


def search_with_claude(queries: list[str] | None = None, timeout: int = 600) -> list[str]:
    """Unattended search through Claude Code's WebSearch tool (uses your Claude login)."""
    if not shutil.which("claude"):
        return []
    q = "\n".join(queries or SEARCH_QUERIES)
    prompt = ("Run a web search for EACH query below. Collect every result URL that points to an employer job "
              "board or job posting on greenhouse.io, lever.co, ashbyhq.com, myworkdayjobs.com, myworkdaysite.com "
              "or smartrecruiters.com. Return ONLY a JSON array of URL strings, nothing else.\n\n" + q)
    try:
        out = subprocess.run(["claude", "-p", "--output-format", "json", "--tools", "WebSearch",
                              "--allowedTools", "WebSearch", "--no-session-persistence"],
                             input=prompt, capture_output=True, text=True, timeout=timeout)
        text = json.loads(out.stdout).get("result", "")
        m = re.search(r"\[.*\]", text, re.S)
        return [u for u in json.loads(m.group(0)) if isinstance(u, str)] if m else []
    except Exception:
        return []
