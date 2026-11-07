"""Workday career sites — the public JSON endpoint the career site itself uses.

Search is keyword-driven (one request per query, paged), then the posting detail is
fetched only for titles that pass the relevance filter. Low volume, rate limited.
"""
import re
from datetime import date, timedelta

from .base import SourceError, http, relevant_title


def _posted(s: str | None) -> str | None:
    if not s:
        return None
    s = s.lower()
    if "today" in s:
        return date.today().isoformat()
    if "yesterday" in s:
        return (date.today() - timedelta(days=1)).isoformat()
    m = re.search(r"(\d+)\+?\s*days", s)
    return (date.today() - timedelta(days=int(m.group(1)))).isoformat() if m else None


def fetch(e: dict, terms: dict):
    t, n, site = e["tenant"], e["wd"], e["site"]
    base = f"https://{t}.{n}.myworkdayjobs.com/wday/cxs/{t}/{site}"
    queries = e.get("queries") or terms.get("workday_queries", [])
    max_pages = e.get("max_pages", 2)
    max_details = e.get("max_details", 60)
    seen, details = set(), 0
    for q in queries:
        for page in range(max_pages):
            try:
                data = http("POST", base + "/jobs", json={"appliedFacets": {}, "limit": 20, "offset": page * 20,
                                                           "searchText": q}, min_interval=1.2).json()
            except SourceError:
                raise
            posts = data.get("jobPostings") or []
            for p in posts:
                path = p.get("externalPath")
                if not path or path in seen:
                    continue
                seen.add(path)
                if not relevant_title(p.get("title", ""), terms):
                    continue
                if details >= max_details:
                    return
                details += 1
                try:
                    d = http("GET", base + path, min_interval=1.2).json().get("jobPostingInfo", {})
                except Exception:
                    continue
                yield {
                    "source_job_id": d.get("jobReqId") or path, "employer": e["name"], "title": d.get("title") or p["title"],
                    "location": d.get("location") or p.get("locationsText", ""),
                    "country": (d.get("country") or {}).get("descriptor"),
                    "description": d.get("jobDescription", ""),
                    "posted_date": d.get("startDate") or _posted(p.get("postedOn")),
                    "job_url": d.get("externalUrl"), "apply_url": (d.get("externalUrl") or "") + "/apply",
                    "ats": "workday", "_partial": True,
                }
            if len(posts) < 20:
                break
