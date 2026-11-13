"""UN Secretariat careers (careers.un.org) public job-opening list.

The site sits behind a CDN that blocks some datacenter networks; from a home
connection it normally answers. A 403 is recorded in source health, not bypassed.
UN applications are filed manually in Inspira (account + PHP form) — the executor
routes them to NEEDS_HUMAN_ACTION with the tailored cover letter/PHP text ready.
"""
from .base import http


def fetch(e: dict, terms: dict):
    r = http("POST", "https://careers.un.org/api/public/opening/jo/list/filteredV2/en",
             json={"filterConfig": {"keyword": ""}, "pagination": {"page": 0, "itemPerPage": 200,
                                                                   "sortBy": "startDate", "sortDirection": -1}})
    data = r.json().get("data", {})
    for j in data.get("list", []):
        loc = ", ".join(filter(None, [(j.get("dutyStation") or [{}])[0].get("description") if j.get("dutyStation")
                                      else None]))
        yield {
            "source_job_id": j.get("jobId"), "employer": "United Nations Secretariat" if not j.get("dept")
            else f"United Nations — {j['dept'].get('name', '')}".strip(" —"),
            "title": j.get("postingTitle") or j.get("jobTitle", ""), "location": loc,
            "description": " ".join(filter(None, [j.get("jobFamily", {}).get("name") if isinstance(j.get("jobFamily"), dict)
                                                  else None, j.get("level")])),
            "posted_date": (j.get("startDate") or "")[:10],
            "job_url": f"https://careers.un.org/jobSearchDescription/{j.get('jobId')}?language=en",
            "apply_url": f"https://careers.un.org/jobSearchDescription/{j.get('jobId')}?language=en",
            "ats": "inspira", "_partial": True,
        }
