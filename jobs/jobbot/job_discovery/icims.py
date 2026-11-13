"""iCIMS public career portals (jobs-<company>.icims.com / careers-<company>.icims.com).

Listing pages (?ss=1&in_iframe=1&pr=N) give job links + titles; each posting page carries a
schema.org JobPosting JSON-LD block (title, description, location, dates, salary). Read-only,
low volume, same as any visitor. Employer entry: {ats: icims, host: jobs-jhpiego.icims.com, name: Jhpiego}
"""
from __future__ import annotations

import html
import json
import re

from .base import http, relevant_title

LINK = re.compile(r'href="(https://[^"]+?\.icims\.com/jobs/(\d+)/[^"]+?/job)\?[^"]*"[^>]*?title="[^"]*?-\s*([^"]+)"', re.S)
LDJSON = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
COUNTRY = {"US": "united states", "USA": "united states"}


def _text(h: str) -> str:
    h = re.sub(r"<(br|/p|/li|/h\d)[^>]*>", "\n", h or "", flags=re.I)
    return html.unescape(re.sub(r"<[^>]+>", " ", h)).replace("\xa0", " ").strip()


def listing(host: str, max_pages: int = 25):
    seen = set()
    for pr in range(max_pages):
        page = http("GET", f"https://{host}/jobs/search", params={"ss": 1, "in_iframe": 1, "pr": pr}).text
        found = 0
        for url, jid, title in LINK.findall(page):
            if jid in seen:
                continue
            seen.add(jid)
            found += 1
            yield url, jid, html.unescape(title).strip()
        if not found:
            return


def posting(url: str) -> dict | None:
    page = http("GET", url, params={"in_iframe": 1}).text
    for block in LDJSON.findall(page):
        try:
            d = json.loads(block)
        except ValueError:
            continue
        if d.get("@type") == "JobPosting":
            return d
    return None


def fetch(e: dict, terms: dict):
    for url, jid, title in listing(e["host"]):
        if not relevant_title(title, terms):
            continue  # only open postings whose title could fit
        d = posting(url)
        if not d:
            continue
        locs = d.get("jobLocation") or []
        locs = locs if isinstance(locs, list) else [locs]
        addr = (locs[0].get("address") if locs else {}) or {}
        cc = (addr.get("addressCountry") or "").upper()
        city = ", ".join(x for x in (addr.get("addressLocality"), addr.get("addressRegion"))
                         if x and x != "UNAVAILABLE")
        remote = (d.get("jobLocationType") or "").upper() == "TELECOMMUTE"
        sal = ((d.get("baseSalary") or {}).get("value") or {}) if isinstance(d.get("baseSalary"), dict) else {}
        unit = (sal.get("unitText") or "").lower()
        yield {
            "source_job_id": jid, "employer": e["name"], "title": d.get("title") or title,
            "location": (city or cc) + (" (remote)" if remote else ""),
            "country": COUNTRY.get(cc, cc.lower()) if cc else "",
            "description": _text(d.get("description", "")),
            "posted_date": (d.get("datePosted") or "")[:10],
            "job_url": d.get("url") or url, "apply_url": (d.get("url") or url).rstrip("/") + "/login",
            "ats": "icims",
            "salary_min": sal.get("minValue") if unit == "year" else None,
            "salary_max": sal.get("maxValue") if unit == "year" else None,
            "salary_currency": (d.get("baseSalary") or {}).get("currency") if isinstance(d.get("baseSalary"), dict) else None,
            "salary_period": "year" if unit == "year" else None,
        }
