#!/usr/bin/env python3
"""Tier 1 partner vetting and sourcing from public sources (no API key needed).

Checks, per capture/PARTNER_VETTING.md:
  - SBA certification directory (search.certifications.sba.gov): active
    SDVOSB/VOSB/other certs, SAM status as SBA extracts it (code "A" = active),
    principal(s), the firm's own published email and website.
  - SAM.gov public search, exclusions: any active exclusion on the firm's UEI.

A check that cannot run is UNVERIFIED, never CLEAR.

Usage:
  python3 capture/tools/vet_partner.py vet "FIRM NAME" [UEI]
  python3 capture/tools/vet_partner.py source "search term" [regex-the-profile-must-match]
  python3 capture/tools/vet_partner.py opps "keyword" [title-regex] [min-response-date YYYY-MM-DD]
"""
import json
import os
import re
import ssl
import sys
import urllib.parse
import urllib.request

_CA = "/root/.ccr/ca-bundle.crt"
CTX = ssl.create_default_context(cafile=_CA) if os.path.exists(_CA) else ssl.create_default_context()

SBA_FILTERS = {
    "location": {"states": [], "zipCodes": [], "counties": [], "districts": [], "msas": []},
    "sbaCertifications": {"activeCerts": [], "isPreviousCert": False, "operatorType": "Or"},
    "naics": {"codes": [], "isPrimary": False, "operatorType": "Or"},
    "selfCertifications": {"certifications": [], "operatorType": "Or"},
    "keywords": {"list": [], "operatorType": "Or"},
    "lastUpdated": {"date": {"label": "Anytime", "value": "anytime"}},
    "samStatus": {"isActiveSAM": False},
    "qualityAssuranceStandards": {"qas": []},
    "bondingLevels": {"constructionIndividual": "", "constructionAggregate": "",
                      "serviceIndividual": "", "serviceAggregate": ""},
    "businessSize": {"relationOperator": "at-least", "numberOfEmployees": ""},
    "annualRevenue": {"relationOperator": "at-least", "annualGrossRevenue": ""},
    "entityDetailId": "",
}


def sba_search(term):
    body = dict(SBA_FILTERS, searchProfiles={"searchTerm": term})
    req = urllib.request.Request(
        "https://search.certifications.sba.gov/_api/v2/search",
        data=json.dumps(body).encode(), method="POST",
        headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=90, context=CTX)).get("results", [])


def sam_search(index, q, size=25, page=0, active_only=False):
    params = {"index": index, "q": q, "page": page, "size": size, "mode": "search"}
    if active_only:
        params["is_active"] = "true"
    req = urllib.request.Request(
        "https://sam.gov/api/prod/sgs/v1/search/?" + urllib.parse.urlencode(params),
        headers={"Accept": "application/hal+json"})
    return json.load(urllib.request.urlopen(req, timeout=90, context=CTX)).get("_embedded", {}).get("results", [])


def exclusions(uei):
    return [r.get("title") for r in sam_search("ei", uei, size=10)
            if r.get("_type") == "exclusion" and r.get("ueiSam") == uei and r.get("isActive")]


def active_certs(rec):
    return sorted((c["name"], c.get("exitDate")) for c in (rec.get("certs") or []) if c.get("active"))


def vet(name, uei=None):
    try:
        hits = sba_search(name)
    except Exception as e:  # noqa: BLE001
        return {"firm": name, "result": "UNVERIFIED", "why": f"SBA search failed: {e}"}
    rec = next((r for r in hits if uei and r.get("uei") == uei), None) or \
        next((r for r in hits if (r.get("legal_business_name") or "").upper() == name.upper()), None)
    if not rec:
        return {"firm": name, "result": "UNVERIFIED", "why": "not found in the SBA directory"}
    uei = rec.get("uei")
    try:
        exc = exclusions(uei)
    except Exception as e:  # noqa: BLE001
        return {"firm": name, "uei": uei, "result": "UNVERIFIED", "why": f"SAM exclusion search failed: {e}"}
    flags = []
    if exc:
        flags.append(f"SAM exclusion: {exc}")
    if rec.get("sam_extract_code") != "A":
        flags.append(f"SAM not active per SBA extract (code {rec.get('sam_extract_code')})")
    if not rec.get("email"):
        flags.append("no published email")
    return {
        "firm": rec.get("legal_business_name"), "uei": uei, "cage": rec.get("cage_code"),
        "certs": active_certs(rec), "sam_extract": rec.get("sam_extract_code"),
        "principals": rec.get("current_principals"), "email": rec.get("email"),
        "website": rec.get("website"), "city": rec.get("city"), "state": rec.get("state"),
        "exclusions": exc or "none",
        "result": "FLAG" if flags else "CLEAR", "flags": flags,
        "sources": ["search.certifications.sba.gov", "sam.gov public search (exclusions)"],
    }


def source(term, must=None, want=("SDVOSB", "VOSB")):
    out = []
    for r in sba_search(term):
        certs = {c for c, _ in active_certs(r)}
        if want and not certs & set(want):
            continue
        if not r.get("email") or r.get("sam_extract_code") != "A":
            continue
        text = " ".join([r.get("legal_business_name") or "", r.get("capabilities_narrative") or "",
                         " ".join(r.get("keywords") or [])])
        if must and not re.search(must, text, re.I):
            continue
        out.append({k: r.get(k) for k in ("legal_business_name", "uei", "city", "state", "current_principals",
                                          "email", "website", "year_established", "naics_primary")}
                   | {"certs": sorted(certs), "narrative": (r.get("capabilities_narrative") or "")[:300]})
    return out


def opps(q, title_rx=None, min_date="0000"):
    out = []
    for page in (0, 1):
        for r in sam_search("opp", q, size=100, page=page, active_only=True):
            rd = (r.get("responseDate") or "")[:10]
            if not rd or rd < min_date:
                continue
            if title_rx and not re.search(title_rx, r.get("title") or "", re.I):
                continue
            out.append({"response": rd, "type": (r.get("type") or {}).get("value"),
                        "number": r.get("solicitationNumber"), "title": r.get("title"), "id": r.get("_id")})
    return out


if __name__ == "__main__":
    cmd, *args = sys.argv[1:] or ["help"]
    if cmd == "vet":
        print(json.dumps(vet(*args), indent=1))
    elif cmd == "source":
        print(json.dumps(source(*args), indent=1))
    elif cmd == "opps":
        print(json.dumps(opps(*args), indent=1))
    else:
        print(__doc__)
