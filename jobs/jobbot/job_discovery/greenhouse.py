"""Greenhouse public Job Board API (boards-api.greenhouse.io) — an official public feed."""
from .base import http


def fetch(e: dict, terms: dict):
    slug = e["slug"]
    data = http("GET", f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs", params={"content": "true"}).json()
    for j in data.get("jobs", []):
        yield {
            "source_job_id": j["id"], "employer": e["name"], "title": j["title"],
            "location": (j.get("location") or {}).get("name", ""),
            "description": j.get("content", ""),
            "posted_date": (j.get("first_published") or j.get("updated_at") or "")[:10],
            "job_url": j.get("absolute_url"), "apply_url": j.get("absolute_url"), "ats": "greenhouse",
        }
