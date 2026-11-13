"""USAJOBS Search API (official). Requires a free API key:
   https://developer.usajobs.gov/apirequest/  ->  env USAJOBS_API_KEY, USAJOBS_EMAIL
Federal applications themselves are submitted manually through USAJOBS/Login.gov
(the executor routes them to NEEDS_HUMAN_ACTION with the tailored packet ready).
"""
import os

from .base import SourceError, http


def fetch(e: dict, terms: dict):
    key, email = os.environ.get("USAJOBS_API_KEY"), os.environ.get("USAJOBS_EMAIL")
    if not key:  # key kept with the private data (gitignored), registered to the portal-account email
        from ..config import home
        f = home() / "usajobs_key.txt"
        key = f.read_text().strip() if f.exists() else None
    if key and not email:
        from ..evidence import profile
        email = profile().get("account_email")
    if not key or not email:
        raise SourceError("USAJOBS_API_KEY / USAJOBS_EMAIL not set — source skipped")
    hdr = {"Authorization-Key": key, "User-Agent": email, "Host": "data.usajobs.gov"}
    for q in e.get("queries") or terms.get("usajobs_queries", []):
        data = http("GET", "https://data.usajobs.gov/api/search",
                    params={"Keyword": q, "ResultsPerPage": 100, "WhoMayApply": "public", "DatePosted": 30},
                    headers=hdr).json()
        for it in data.get("SearchResult", {}).get("SearchResultItems", []):
            d = it["MatchedObjectDescriptor"]
            rem = (d.get("PositionRemuneration") or [{}])[0]
            yearly = rem.get("RateIntervalCode") == "PA"
            det = d.get("UserArea", {}).get("Details", {})
            yield {
                "source_job_id": d["PositionID"], "employer": d.get("OrganizationName") or "U.S. Government",
                "title": d["PositionTitle"], "location": d.get("PositionLocationDisplay", ""),
                "country": "united states" if "United States" in str(d.get("PositionLocation")) else None,
                "description": "\n\n".join(filter(None, [d.get("QualificationSummary"), det.get("JobSummary"),
                                                        " ".join(det.get("MajorDuties") or []),
                                                        det.get("Requirements"), det.get("Education"),
                                                        det.get("SecurityClearance") and
                                                        f"Security clearance: {det.get('SecurityClearance')}"])),
                "posted_date": (d.get("PublicationStartDate") or "")[:10],
                "job_url": d.get("PositionURI"), "apply_url": (d.get("ApplyURI") or [d.get("PositionURI")])[0],
                "ats": "usajobs", "_partial": True,
                "salary_min": float(rem["MinimumRange"]) if yearly and rem.get("MinimumRange") else None,
                "salary_max": float(rem["MaximumRange"]) if yearly and rem.get("MaximumRange") else None,
                "salary_currency": "USD" if yearly else None, "salary_period": "year" if yearly else None,
            }
