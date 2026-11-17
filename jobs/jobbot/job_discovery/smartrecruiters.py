"""SmartRecruiters public Posting API (api.smartrecruiters.com/v1/companies/{id}/postings)."""
from .base import http, relevant_title


def fetch(e: dict, terms: dict):
    base = f"https://api.smartrecruiters.com/v1/companies/{e['slug']}/postings"
    offset = 0
    while True:
        data = http("GET", base, params={"limit": 100, "offset": offset}).json()
        items = data.get("content", [])
        for p in items:
            if not relevant_title(p.get("name", ""), terms):
                continue
            d = http("GET", f"{base}/{p['id']}").json()
            secs = ((d.get("jobAd") or {}).get("sections") or {})
            desc = "\n\n".join((secs.get(k) or {}).get("text", "") for k in
                               ("companyDescription", "jobDescription", "qualifications", "additionalInformation"))
            loc = p.get("location") or {}
            yield {
                "source_job_id": p["id"], "employer": e["name"], "title": p["name"],
                "location": ", ".join(filter(None, [loc.get("city"), loc.get("region"), loc.get("country")]))
                            + (" (remote)" if loc.get("remote") else ""),
                "country": loc.get("country"), "description": desc, "posted_date": (p.get("releasedDate") or "")[:10],
                "job_url": d.get("postingUrl") or f"https://jobs.smartrecruiters.com/{e['slug']}/{p['id']}",
                "apply_url": d.get("applyUrl") or d.get("postingUrl"), "ats": "smartrecruiters",
            }
        offset += 100
        if offset >= data.get("totalFound", 0) or not items:
            break
