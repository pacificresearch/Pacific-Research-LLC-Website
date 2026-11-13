"""Oracle Recruiting Cloud (HCM Candidate Experience) career sites — Providence, UCSF, Stanford, Cedars-Sinai,
Mayo Clinic, Mount Sinai, Vanderbilt University (Andrew 11/13: hospital systems / academic medical centers).

Uses the public REST endpoints the career site itself calls. Read-only, keyword search, low volume.
Employer entry: {ats: oracle, host: evac.fa.us2.oraclecloud.com, site: CX_1, name: Providence}
No executor adapter yet: these jobs are prepared as packets.
"""
from __future__ import annotations

import html
import re

from .base import http, relevant_title


def _text(h: str) -> str:
    h = re.sub(r"<(br|/p|/li|/div|/h\d)[^>]*>", "\n", h or "", flags=re.I)
    return re.sub(r"[ \t]+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).replace("\xa0", " ").strip()


def fetch(e: dict, terms: dict):
    host, site = e["host"], e.get("site", "CX_1")
    api = f"https://{host}/hcmRestApi/resources/latest"
    queries = e.get("queries") or terms.get("workday_queries", [])
    seen, details = set(), 0
    for q in queries:
        for page in range(e.get("max_pages", 2)):
            data = http("GET", f"{api}/recruitingCEJobRequisitions",
                        params={"onlyData": "true", "expand": "requisitionList",
                                "finder": f'findReqs;siteNumber={site},keyword="{q}",limit=25,offset={page * 25}'},
                        min_interval=1.0).json()
            items = (data.get("items") or [{}])[0].get("requisitionList") or []
            for r in items:
                jid = str(r.get("Id"))
                if jid in seen or not relevant_title(r.get("Title", ""), terms):
                    continue
                seen.add(jid)
                if details >= e.get("max_details", 60):
                    continue
                details += 1
                d = (http("GET", f"{api}/recruitingCEJobRequisitionDetails",
                          params={"expand": "all", "onlyData": "true",
                                  "finder": f'ById;Id="{jid}",siteNumber={site}'}, min_interval=1.0).json()
                     .get("items") or [{}])[0]
                flex = "\n".join(f"{f.get('Prompt')}: {f.get('Value')}" for f in d.get("requisitionFlexFields") or []
                                 if f.get("Value") not in (None, ""))
                desc = "\n\n".join(filter(None, [_text(d.get("ExternalDescriptionStr")),
                                                 _text(d.get("ExternalResponsibilitiesStr")),
                                                 _text(d.get("ExternalQualificationsStr")), flex]))
                wp = (r.get("WorkplaceType") or "").lower()
                url = f"https://{host}/hcmUI/CandidateExperience/en/sites/{site}/job/{jid}"
                yield {"source_job_id": jid, "employer": e["name"], "title": r.get("Title", ""),
                       "location": (r.get("PrimaryLocation") or "") + (" (remote)" if "remote" in wp else
                                                                      " (hybrid)" if "hybrid" in wp else ""),
                       "country": "united states" if r.get("PrimaryLocationCountry") == "US"
                       else (r.get("PrimaryLocationCountry") or "").lower(),
                       "description": desc, "posted_date": r.get("PostedDate") or "", "ats": "oracle",
                       "job_url": url, "apply_url": url}
            if len(items) < 25:
                break
