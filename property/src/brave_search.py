"""Brave Search (optional). Produces RESEARCH LEADS with source tiering — never facts. A human/agent verifies."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional
from urllib.parse import urlparse

from .config import api_keys
from .database import Cache
from .http_client import HttpError, get_json

log = logging.getLogger("prg.brave")
URL = "https://api.search.brave.com/res/v1/web/search"

# Source priority per the brief: government > EDA > company/SEC > BLS/Census/FHFA/FRED > local business press > other
TIERS = [
    (1, lambda h: h.endswith(".gov") or ".gov." in h or h.endswith(".mil")),
    (2, lambda h: any(t in h for t in ["edc", "chamber", "econdev", "economicdevelopment", "-eda.", "edp.", "growth"])),
    (3, lambda h: "sec.gov" in h or "prnewswire" in h or "businesswire" in h or "globenewswire" in h or "/press" in h),
    (4, lambda h: any(t in h for t in ["bls.gov", "census.gov", "fhfa.gov", "stlouisfed.org"])),
    (5, lambda h: any(t in h for t in ["bizjournals", "news", "times", "post", "gazette", "herald", "tribune", "journal", "wral", "wbir", "abc", "nbc", "cbs", "fox", "npr", "publicradio"])),
]
SEO_BLOGS = ["zillow.com/blog", "realtor.com/advice", "biggerpockets", "roofstock", "mashvisor", "noradarealestate", "rentometer", "awning.com", "doorloop", "stessa", "propertyclub", "homeguide", "sofi", "bankrate"]


def available() -> bool:
    return bool(api_keys().get("BRAVE_SEARCH_API_KEY"))


def tier_of(url: str) -> int:
    h = urlparse(url).netloc.lower()
    if any(b in url.lower() for b in SEO_BLOGS):
        return 9
    for t, fn in TIERS:
        if fn(h):
            return t
    return 6


def search(cache: Cache, ttl: float, query: str, budget: dict, count: int = 8, freshness: Optional[str] = None) -> List[dict]:
    key = api_keys().get("BRAVE_SEARCH_API_KEY")
    if not key:
        return []
    params = {"q": query, "count": count}
    if freshness:
        params["freshness"] = freshness   # e.g. "py" past year

    def fetch():
        if budget["used"] >= budget["max"]:
            log.warning("Brave budget exhausted")
            return None
        budget["used"] += 1
        try:
            data = get_json(URL, params, headers={"X-Subscription-Token": key, "Accept": "application/json"})
        except HttpError as e:
            log.warning("Brave failed: %s", e)
            return None
        cache.log_call("brave", "web/search", cached=False, status=200)
        return data

    data, _ = cache.cached("brave", URL, params, ttl, fetch, endpoint="web/search")
    results = []
    for r in (data or {}).get("web", {}).get("results", []):
        results.append({"title": r.get("title"), "url": r.get("url"), "description": r.get("description"),
                        "age": r.get("age") or r.get("page_age"), "tier": tier_of(r.get("url", "")), "query": query})
    results.sort(key=lambda x: x["tier"])
    return results


QUERY_TEMPLATES = {
    "catalysts": ["{city} {state} economic development announcement jobs investment 2025 2026",
                  "{city} {state} new plant OR factory OR \"data center\" OR hospital construction announced",
                  "{city} {state} site:*.gov economic development project"],
    "relocation": ["{city} {state} relocation incentive program grant remote worker",
                   "{city} {state} down payment assistance program first-time homebuyer grant"],
    "landlord_law": ["{city} {state} rental registration license inspection ordinance landlord",
                     "{state} landlord tenant law eviction timeline security deposit limit rent control"],
    "tax_rules": ["{county} county {state} assessor reassessment after sale property tax",
                  "{county} county {state} treasurer property tax bill lookup"],
    "employers": ["{city} {state} largest employers list"],
}


def research_leads(cache: Cache, ttl: float, market: dict, budget: dict) -> Dict[str, List[dict]]:
    """Run the query templates for a market and return tiered leads per topic (empty if no key)."""
    out: Dict[str, List[dict]] = {}
    if not available():
        return out
    for topic, qs in QUERY_TEMPLATES.items():
        leads = []
        for q in qs:
            leads += search(cache, ttl, q.format(**market), budget)
        seen, dedup = set(), []
        for l in leads:
            if l["url"] in seen:
                continue
            seen.add(l["url"])
            dedup.append(l)
        out[topic] = dedup[:12]
    return out
