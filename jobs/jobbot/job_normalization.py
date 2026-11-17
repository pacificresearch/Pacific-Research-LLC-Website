"""Normalize raw postings from any source into one schema; dedupe fingerprint."""
from __future__ import annotations

import hashlib
import html
import json
import re

US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA",
    "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK",
    "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC", "PR"}
US_STATE_NAMES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut", "delaware", "florida",
    "georgia", "hawaii", "idaho", "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana", "maine",
    "maryland", "massachusetts", "michigan", "minnesota", "mississippi", "missouri", "montana", "nebraska",
    "nevada", "new hampshire", "new jersey", "new mexico", "new york", "north carolina", "north dakota", "ohio",
    "oklahoma", "oregon", "pennsylvania", "rhode island", "south carolina", "south dakota", "tennessee", "texas",
    "utah", "vermont", "virginia", "washington", "west virginia", "wisconsin", "wyoming", "district of columbia"}
COUNTRIES = [
    "united kingdom", "england", "scotland", "ireland", "france", "germany", "switzerland", "italy", "spain",
    "portugal", "netherlands", "belgium", "denmark", "sweden", "norway", "finland", "austria", "poland",
    "czech", "hungary", "romania", "bulgaria", "greece", "turkey", "israel", "india", "china", "japan",
    "korea", "taiwan", "singapore", "malaysia", "thailand", "vietnam", "philippines", "indonesia",
    "australia", "new zealand", "canada", "mexico", "brazil", "argentina", "chile", "peru", "colombia",
    "costa rica", "panama", "guatemala", "uruguay", "ecuador", "bolivia", "kenya", "uganda", "tanzania",
    "nigeria", "ghana", "ethiopia", "south africa", "rwanda", "malawi", "zambia", "mozambique", "senegal",
    "egypt", "jordan", "lebanon", "iraq", "afghanistan", "pakistan", "bangladesh", "nepal", "ukraine",
    "serbia", "croatia", "slovakia", "lithuania", "latvia", "estonia", "haiti", "dominican republic",
    "sierra leone", "liberia", "drc", "democratic republic of the congo", "south sudan", "sudan", "somalia",
    "yemen", "syria", "myanmar", "cambodia", "laos", "sri lanka", "united arab emirates", "saudi arabia",
    "qatar", "geneva", "hong kong", "puerto rico"]
ALIASES = {"uk": "united kingdom", "gbr": "united kingdom", "deu": "germany", "che": "switzerland",
           "bra": "brazil", "ind": "india", "chn": "china", "jpn": "japan", "can": "canada", "mex": "mexico",
           "usa": "united states", "us": "united states", "geneva": "switzerland", "hong kong": "china"}


def html_to_text(s: str | None) -> str:
    if not s:
        return ""
    s = html.unescape(html.unescape(s))
    s = re.sub(r"(?i)<\s*(br|/p|/li|/h\d|/div)\s*/?>", "\n", s)
    s = re.sub(r"(?i)<li[^>]*>", "\n• ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"[ \t\xa0]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n\n", s)
    return s.strip()


def norm_title(t: str) -> str:
    t = t.lower()
    t = re.sub(r"\(.*?\)|\[.*?\]", " ", t)
    t = re.sub(r"\b(remote|hybrid|onsite|on-site|req\w*\s*#?\d+|r\d{5,})\b", " ", t)
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def classify_location(loc: str | None, country_hint: str | None = None) -> tuple[str, int]:
    """Return (country, remote_flag). Country is 'united states' or a lowercase country name or ''."""
    l = (loc or "").lower()
    remote = 1 if re.search(r"\bremote\b|\bvirtual\b|work from home|anywhere", l) else 0
    hint = (country_hint or "").lower().strip()
    if hint:
        hint = ALIASES.get(hint, hint)
        if hint in ("united states", "united states of america"):
            return "united states", remote
        return hint, remote
    if re.search(r"\b(united states|usa|u\.s\.)\b", l):
        return "united states", remote
    for c in COUNTRIES:
        if re.search(rf"\b{re.escape(c)}\b", l):
            return ALIASES.get(c, c), remote
    toks = set(re.findall(r"\b[A-Z]{2}\b", loc or ""))
    if toks & US_STATES or any(n in l for n in US_STATE_NAMES):
        return "united states", remote
    if remote and not l.replace("remote", "").strip(" ,-/"):
        return "united states", remote  # bare "Remote" on US boards
    return "", remote


_MONEY = r"(?:US\$|USD\s*|\$|€|£|EUR\s*|GBP\s*|CHF\s*)\s?(\d{1,3}(?:[,.]\d{3})+|\d+(?:\.\d+)?)\s*([kK])?"


def parse_salary(text: str | None) -> dict:
    """Extract an ADVERTISED range from posting text. Returns {} when none is stated."""
    if not text:
        return {}
    t = text.replace("–", "-").replace("—", "-")
    m = re.search(_MONEY + r"\s*(?:-|to)\s*" + _MONEY + r"(?:\s*(?:per|/|a)\s*(hour|hr|year|yr|annum|annually|month))?",
                  t, re.I)
    if not m:
        return {}

    def num(v, k):
        x = float(re.sub(r"[,.]", "", v)) if re.fullmatch(r"\d{1,3}(?:[,.]\d{3})+", v) else float(v)
        return x * 1000 if k else x

    lo, hi = num(m.group(1), m.group(2)), num(m.group(3), m.group(4))
    if lo > hi:
        lo, hi = hi, lo
    period = (m.group(5) or "").lower()
    cur = "EUR" if "€" in m.group(0) or "EUR" in m.group(0) else "GBP" if "£" in m.group(0) or "GBP" in m.group(0) \
        else "CHF" if "CHF" in m.group(0) else "USD"
    if period in ("hour", "hr") or hi < 300:
        lo, hi, period = lo * 2080, hi * 2080, "year(hourly x2080)"
    elif period == "month" or hi < 30000:
        lo, hi, period = lo * 12, hi * 12, "year(monthly x12)"
    else:
        period = "year"
    if hi < 15000 or hi > 2_000_000:
        return {}
    return {"salary_min": round(lo), "salary_max": round(hi), "salary_currency": cur,
            "salary_period": period, "salary_label": "advertised"}


def fingerprint(employer: str, title: str, location: str | None) -> str:
    loc = re.sub(r"[^a-z]+", " ", (location or "").lower()).strip()
    loc = " ".join(sorted(set(loc.split())))[:80]
    key = f"{re.sub(r'[^a-z0-9]+', '', employer.lower())}|{norm_title(title)}|{loc}"
    return hashlib.sha1(key.encode()).hexdigest()


def normalize(raw: dict) -> dict:
    """raw: keys from an adapter. Produces the DB job dict."""
    desc = raw.get("description") or ""
    if ("<" in desc and ">" in desc) or "&lt;" in desc:
        desc = html_to_text(desc)
    country, remote = classify_location(raw.get("location"), raw.get("country"))
    sal = {k: raw.get(k) for k in ("salary_min", "salary_max", "salary_currency", "salary_period") if raw.get(k)}
    if sal.get("salary_min") or sal.get("salary_max"):
        sal["salary_label"] = "advertised"
    else:
        sal = parse_salary(desc)
    job = {
        "source": raw["source"], "source_job_id": str(raw["source_job_id"]),
        "employer": raw["employer"].strip(), "title": re.sub(r"\s+", " ", raw["title"]).strip(),
        "location": (raw.get("location") or "").strip(), "country": country, "remote": remote,
        "description": desc[:60000], "posted_date": raw.get("posted_date"),
        "job_url": raw.get("job_url"), "apply_url": raw.get("apply_url") or raw.get("job_url"),
        "ats": raw.get("ats") or raw["source"].split(":")[0],
        "raw_json": json.dumps({k: v for k, v in raw.items() if k != "description"}, default=str)[:20000],
        **{"salary_min": None, "salary_max": None, "salary_currency": None, "salary_period": None,
           "salary_label": "unknown"}, **sal,
    }
    job["fingerprint"] = fingerprint(job["employer"], job["title"], job["location"])
    return job
