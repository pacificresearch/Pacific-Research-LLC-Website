"""Ashby public Job Posting API (api.ashbyhq.com/posting-api) — an official public feed."""
from .base import http


def fetch(e: dict, terms: dict):
    data = http("GET", f"https://api.ashbyhq.com/posting-api/job-board/{e['slug']}",
                params={"includeCompensation": "true"}).json()
    for j in data.get("jobs", []):
        if j.get("isListed") is False:
            continue
        addr = ((j.get("address") or {}).get("postalAddress") or {})
        comp = (j.get("compensation") or {})
        lo = hi = cur = None
        for t in comp.get("summaryComponents") or []:
            if t.get("compensationType") == "Salary" and (t.get("interval") or "").endswith("YEAR"):
                lo, hi, cur = t.get("minValue"), t.get("maxValue"), t.get("currencyCode")
        yield {
            "source_job_id": j["id"], "employer": e["name"], "title": j["title"],
            "location": (j.get("location") or "") + (" (remote)" if j.get("isRemote") else ""),
            "country": addr.get("addressCountry"), "description": j.get("descriptionPlain") or j.get("descriptionHtml"),
            "posted_date": (j.get("publishedAt") or "")[:10], "job_url": j.get("jobUrl"),
            "apply_url": j.get("applyUrl"), "ats": "ashby",
            "salary_min": lo, "salary_max": hi, "salary_currency": cur, "salary_period": "year" if lo else None,
        }
