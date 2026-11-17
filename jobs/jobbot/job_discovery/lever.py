"""Lever public Postings API (api.lever.co/v0/postings) — an official public feed."""
from datetime import datetime, timezone

from .base import http


def fetch(e: dict, terms: dict):
    data = http("GET", f"https://api.lever.co/v0/postings/{e['slug']}", params={"mode": "json"}).json()
    for j in data:
        cats = j.get("categories") or {}
        sal = j.get("salaryRange") or {}
        desc = "\n\n".join(filter(None, [j.get("openingPlain"), j.get("descriptionBodyPlain") or j.get("descriptionPlain")]
                                  + [f"{l.get('text')}\n{l.get('content')}" for l in j.get("lists", [])]
                                  + [j.get("additionalPlain")]))
        interval = (sal.get("interval") or "").lower()
        yield {
            "source_job_id": j["id"], "employer": e["name"], "title": j["text"],
            "location": cats.get("location", "") + (" (remote)" if j.get("workplaceType") == "remote" else ""),
            "country": j.get("country"), "description": desc,
            "posted_date": datetime.fromtimestamp(j.get("createdAt", 0) / 1000, timezone.utc).date().isoformat(),
            "job_url": j.get("hostedUrl"), "apply_url": j.get("applyUrl"), "ats": "lever",
            "salary_min": sal.get("min") if "year" in interval else None,
            "salary_max": sal.get("max") if "year" in interval else None,
            "salary_currency": sal.get("currency"), "salary_period": "year" if "year" in interval else None,
        }
