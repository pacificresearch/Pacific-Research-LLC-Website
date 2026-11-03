"""Weighted 0-100 match score + category assignment.

Weights (fixed by the operating spec):
  30% qualifications/experience fit   20% interview likelihood
  15% compensation/benefits           15% career advancement
  10% employer quality                10% geography/lifestyle/work arrangement

A good total never overrides eligibility == fail (enforced in pipeline + here: total capped at 0).
Optional semantic layer (semantic.py) refines fit + interview likelihood for the top of each pool.
"""
from __future__ import annotations

import re
from datetime import date

WEIGHTS = {"fit": 0.30, "interview": 0.20, "comp": 0.15, "advancement": 0.15, "employer": 0.10, "geo": 0.10}

# Rough market bands, used ONLY when no salary is advertised; always labeled "estimated".
ESTIMATE_BANDS = [
    (r"director", (150000, 210000)), (r"senior .*manager|sr\.? .*manager|manager ii|lead", (130000, 175000)),
    (r"clinical trial manager|clinical project manager|clinical study manager", (125000, 165000)),
    (r"program manager|project manager|operations manager", (110000, 150000)),
    (r"senior cra|sr\.? cra|cra ii|clinical research associate ii", (100000, 135000)),
    (r"\bcra\b|clinical research associate", (85000, 115000)),
    (r"senior clinical research coordinator|clinical research supervisor", (85000, 115000)),
    (r"coordinator|associate|analyst|specialist|officer", (70000, 100000)),
]

SENIORITY = [
    (r"\b(director|principal)\b", 85), (r"\b(senior|sr\.?|lead|staff|manager ii|iii)\b.*\bmanager\b", 92),
    (r"\bmanager\b|\bchief of party\b|\bhead\b", 88), (r"\b(lead|supervisor|senior|sr\.?)\b", 75),
    (r"\b(specialist|analyst|officer|associate ii|cra ii)\b", 55),
    (r"\b(coordinator|associate|assistant)\b", 30),
]


INTL_SCOPE = re.compile(r"global health|international development|humanitarian|country office|low- and middle-income|"
                        r"\blmics?\b|usaid|overseas|field office|in-country|international (programs?|operations|travel)|"
                        r"emergency response|refugee|resettlement|migration")
DOMAIN = re.compile(r"health|clinical|medical|biomed|bio\w*|pharma|patient|life science|device|research|trial|"
                    r"public|humanitarian|global|hospital|care\b|disease|vaccine|lab|diagnostic|therapeut|science|"
                    r"defense|federal|government|army|navy|air force|va\b|dod")


def domain_relevant(job: dict) -> bool:
    """A non-clinical title only counts as 'fit' when the work itself is health/research/federal-health."""
    t = job["title"].lower()
    if DOMAIN.search(t):
        return True
    d = (job.get("description") or "").lower()[:6000]
    return len(re.findall(r"clinical|patient|health|medical|biomedical|trial|research", d)) >= 8


def categorize(job: dict, terms: dict) -> str:
    t = job["title"].lower()
    emp = job["employer"].lower()
    intl_emp = any(x in emp for x in terms.get("international_employers", []))
    if job.get("country") not in ("united states", "") or intl_emp:
        return "C"
    if len(INTL_SCOPE.findall((job["title"] + " " + (job.get("description") or "")[:8000]).lower())) >= 3:
        return "C"  # US-based role with meaningful international responsibilities
    if re.search(r"clinical (research|trial|study|operations|project)|\bcra\b|clinical monitor|study start|"
                 r"site (activation|management)|research (operations|program) manager|ecoa|eclinical", t):
        return "A"
    return "B"


def family_for(job: dict, category: str) -> str:
    t = (job["title"] + " " + (job.get("description") or "")[:6000]).lower()
    if category == "A":
        return "clinical"
    if category == "C":
        return "international"
    if len(INTL_SCOPE.findall(t)) >= 2:
        return "international"
    if len(re.findall(r"clinical (trial|research|stud|site|operations)|\bsite\b|protocol|\bgcp\b|investigator|enrollment", t)) >= 6:
        return "clinical"
    return "program"


def _kw_score(text: str, words: list[str]) -> float:
    hits = sum(1 for w in words if w in text)
    return min(100.0, 100.0 * hits / max(6, len(words) * 0.35))


def salary_view(job: dict) -> dict:
    lo, hi = job.get("salary_min"), job.get("salary_max")
    if lo or hi:
        usd = (job.get("salary_currency") or "USD").upper()
        fx = {"USD": 1.0, "EUR": 1.08, "GBP": 1.27, "CHF": 1.12}.get(usd, None)
        if fx is None:
            return {"label": "advertised", "min": lo, "max": hi, "currency": usd, "usd_mid": None}
        mid = ((lo or hi) + (hi or lo)) / 2 * fx
        return {"label": "advertised", "min": lo, "max": hi, "currency": usd, "usd_mid": mid}
    t = job["title"].lower()
    if job.get("country") in ("", "united states"):
        for rx, band in ESTIMATE_BANDS:
            if re.search(rx, t):
                return {"label": "estimated", "min": band[0], "max": band[1], "currency": "USD",
                        "usd_mid": sum(band) / 2, "basis": "internal title band (not employer data)"}
    return {"label": "unknown", "usd_mid": None}


def score(job: dict, elig: dict, cfg: dict, terms: dict, tiers: dict, evidence_lexicon: set[str]) -> dict:
    category = categorize(job, terms)
    title = job["title"].lower()
    text = (job["title"] + "\n" + (job.get("description") or "")).lower()

    # --- fit: category vocabulary + overlap with documented evidence + title targets
    cat_kw = terms.get("category_keywords", {}).get(category, [])
    fit = 0.45 * _kw_score(text, cat_kw) + 0.40 * _kw_score(text, sorted(evidence_lexicon)) + 15
    if re.search(r"infectious|covid|vaccine|nih|decentralized|pragmatic|platform trial|post-acute", text):
        fit += 8
    if re.search(r"biomedical|medical device|healthcare technology|equipment", text) and category != "A":
        fit += 5
    if not domain_relevant(job):
        fit *= 0.55  # generic PM/ops roles outside health/research/federal-health are not a fit
    if re.search(r"\b(sales|marketing|human resources|hr\b|payroll|it infrastructure|infrastructure modernization|"
                 r"real estate|facilities|legal)\b", title):
        fit *= 0.6
    fit = min(fit, 100)

    # --- interview likelihood
    interview = 62.0
    seniority = next((v for rx, v in SENIORITY if re.search(rx, title)), 55)
    if seniority >= 85 and re.search(r"director|principal", title):
        interview -= 18
    for r in elig["eligibility_reasons"]:
        if r["outcome"] == "review":
            interview -= 10 if r["check"] == "specialized_experience" else 6
    if job.get("posted_date"):
        try:
            age = (date.today() - date.fromisoformat(job["posted_date"][:10])).days
            interview += 10 if age <= 7 else 4 if age <= 14 else -6 if age <= 45 else -15
        except ValueError:
            pass
    if re.search(r"veteran|military|vevraa|dod|va\b|federal", text):
        interview += 6
    if fit >= 75:
        interview += 8
    interview = max(5, min(interview, 100))

    # --- compensation
    sal = salary_view(job)
    s = cfg["salary"]
    mid = sal.get("usd_mid")
    intl = category == "C"
    if mid is None:
        comp = 50
    elif intl:
        comp = 90 if mid >= s["target_min"] else 75 if mid >= s["floor_usd"] else 55 if mid >= s["international_floor_usd"] else 25
    else:
        comp = 100 if mid >= s["target_max"] else 88 if mid >= s["target_min"] else 65 if mid >= s["floor_usd"] else 20
    if sal["label"] == "estimated":
        comp = 50 + (comp - 50) * 0.5  # estimates move the needle half as much

    # --- advancement
    advancement = seniority
    if re.search(r"clinical research coordinator", title) and not re.search(r"senior|sr|lead|supervis|manager|iii", title):
        advancement = 20  # entry-level CRC: not the direction

    # --- employer quality
    employer = {1: 90, 2: 75, 3: 60}.get(tiers.get(job["employer"], 3), 60)

    # --- geography
    loc = (job.get("location") or "").lower()
    g = cfg["geography"]
    geo = g["other_us_score"]
    if intl:
        geo = g["international"]["default"]
        for k, v in g["international"]["preferred"].items():
            if k in loc or k == (job.get("country") or ""):
                geo = v
                break
    else:
        for tier in g["tiers"]:
            if any(m in loc for m in tier["match"]) or (tier["name"] == "Remote US" and job.get("remote")):
                geo = max(geo, tier["score"])

    sub = {"fit": round(fit), "interview": round(interview), "comp": round(comp), "advancement": round(advancement),
           "employer": employer, "geo": geo}
    total = sum(WEIGHTS[k] * v for k, v in sub.items())
    if elig["eligibility"] == "fail":
        total = 0.0
    return {"category": category, "family": family_for(job, category), "score": round(total, 1),
            "subscores": sub, "salary": sal}
