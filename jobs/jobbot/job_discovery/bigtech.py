"""Big-tech career sites (Andrew 11/13: 20% big tech). Public search feeds, read-only, low volume.

Employer entry: {ats: bigtech, site: amazon|microsoft, name: Amazon}
Applying on these sites needs the candidate's own sign-in (Amazon/Microsoft accounts, 2FA), so these jobs
are prepared as packets for Andrew, never auto-submitted.
"""
from __future__ import annotations

import html
import re
from datetime import datetime, timezone

from .base import http, relevant_title

QUERIES = ["clinical research", "clinical operations", "clinical program manager", "health program manager",
           "clinical trial", "healthcare program manager", "medical device", "health research",
           "clinical specialist", "public health", "biomedical"]


def _text(h: str) -> str:
    h = re.sub(r"<(br|/p|/li|/div|/h\d)[^>]*>", "\n", h or "", flags=re.I)
    return html.unescape(re.sub(r"<[^>]+>", " ", h)).replace("\xa0", " ").strip()


def _amazon(e, terms):
    seen = set()
    for q in QUERIES:
        data = http("GET", "https://www.amazon.jobs/en/search.json",
                    params={"base_query": q, "result_limit": 50, "country": "USA"}).json()
        for j in data.get("jobs", []):
            if j["id"] in seen or not relevant_title(j["title"], terms):
                continue
            seen.add(j["id"])
            desc = "\n\n".join(filter(None, [_text(j.get("description")), "Basic qualifications:\n" +
                                              _text(j.get("basic_qualifications")), "Preferred qualifications:\n" +
                                              _text(j.get("preferred_qualifications"))]))
            company = j.get("company_name") or "Amazon"
            yield {"source_job_id": str(j["id"]), "employer": "Amazon" if "amazon" in company.lower() else company,
                   "title": j["title"], "location": j.get("normalized_location") or j.get("location") or "",
                   "country": "united states" if j.get("country_code") == "USA" else (j.get("country_code") or "").lower(),
                   "description": desc, "posted_date": "", "ats": "bigtech",
                   "job_url": "https://www.amazon.jobs" + j.get("job_path", ""),
                   "apply_url": j.get("url_next_step") or "https://www.amazon.jobs" + j.get("job_path", "")}


def _microsoft(e, terms):
    seen = set()
    base = "https://apply.careers.microsoft.com/api/pcsx"
    for q in QUERIES:
        data = http("GET", f"{base}/search", params={"domain": "microsoft.com", "query": q, "start": 0,
                                                     "num": 50, "location": "United States"}).json()
        for p in (data.get("data") or {}).get("positions", []):
            if p["id"] in seen or not relevant_title(p["name"], terms):
                continue
            seen.add(p["id"])
            d = (http("GET", f"{base}/position_details", params={"position_id": p["id"], "domain": "microsoft.com",
                                                                 "hl": "en"}).json().get("data") or {})
            url = d.get("publicUrl") or f"https://apply.careers.microsoft.com{p.get('positionUrl', '')}"
            locs = p.get("locations") or []
            yield {"source_job_id": str(p["id"]), "employer": "Microsoft", "title": p["name"],
                   "location": "; ".join(locs)[:200] + (" (remote)" if p.get("workLocationOption") == "remote" else ""),
                   "country": "united states" if "US" in (p.get("standardizedLocations") or []) else "",
                   "description": _text(d.get("jobDescription", "")),
                   "posted_date": datetime.fromtimestamp(p.get("postedTs", 0), timezone.utc).date().isoformat(),
                   "ats": "bigtech", "job_url": url, "apply_url": url}


SITES = {"amazon": _amazon, "microsoft": _microsoft}


def fetch(e: dict, terms: dict):
    yield from SITES[e["site"]](e, terms)
