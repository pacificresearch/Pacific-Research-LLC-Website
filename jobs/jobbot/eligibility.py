"""Mandatory-requirement screen. Deterministic, conservative, explainable.

Outcomes:
  fail    an unmet MANDATORY legal/licensing/citizenship/clearance/credential/language/
          experience requirement was found. Never overridden by a good score.
  review  something mandatory might be unmet, or could not be verified -> human/semantic check
  pass    nothing blocking found

Facts come from profile.yaml `facts` (citizenship, clearance, languages, licenses, degrees,
years). Unknown facts are treated as NOT held: a requirement we cannot prove is a review/fail,
never an assumed pass.
"""
from __future__ import annotations

import re

LANGS = ["spanish", "portuguese", "french", "arabic", "mandarin", "chinese", "russian", "german", "italian",
         "japanese", "korean", "swahili", "amharic", "hindi", "urdu", "dari", "pashto", "farsi", "persian",
         "ukrainian", "turkish", "vietnamese", "tagalog", "haitian creole", "dutch", "polish"]
UN_OFFICIAL = {"arabic", "chinese", "english", "french", "russian", "spanish"}


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.;:!?])\s+|\n+", text) if s.strip()]


def _req_context(s: str) -> str:
    """Classify a sentence as required / preferred / neutral."""
    l = s.lower()
    if re.search(r"\b(preferred|desirable|desired|nice to have|a plus|an asset|advantage|bonus|ideally)\b", l):
        return "preferred"
    if re.search(r"\b(required|must|mandatory|essential|minimum|need to|is necessary|requirement)\b", l):
        return "required"
    return "neutral"


def screen(job: dict, facts: dict) -> dict:
    title = (job.get("title") or "")
    text = f"{title}\n{job.get('description') or ''}"
    low = text.lower()
    sents = _sentences(text)
    reasons: list[dict] = []

    def add(kind, outcome, detail, evidence=""):
        reasons.append({"check": kind, "outcome": outcome, "detail": detail, "evidence": evidence[:240]})

    citizen = {c.lower() for c in facts.get("citizenships", [])}
    clearance = (facts.get("clearance") or "none").lower()
    langs = {k.lower(): v for k, v in (facts.get("languages") or {}).items()}
    licenses = {l.lower() for l in facts.get("licenses", [])}
    degrees = {d.lower() for d in facts.get("degrees", [])}
    years = float(facts.get("years_professional", 0))

    # 1. security clearance --------------------------------------------------------
    if re.search(r"\bts/sci\b|\bts w/|\btop secret\b|polygraph|\bsci\b", title.lower()) and clearance in ("none", "", "unknown"):
        add("clearance", "fail", "title requires TS/SCI or polygraph; no active clearance", title)
    for s in sents:
        l = s.lower()
        if re.search(r"(secret|ts/sci|top secret|public trust|security clearance|\bclearance\b)", l):
            active = re.search(r"\b(active|current|existing|must (possess|hold|have)|required)\b", l)
            obtain = re.search(r"(ability|able|eligib\w*) to (obtain|receive|acquire|maintain)|obtain and maintain", l)
            if "public trust" in l and obtain:
                add("clearance", "pass", "public trust obtainable (US citizen)", s)
            elif obtain and not re.search(r"\bactive\b|\bcurrent\b", l):
                if facts.get("clearance_history"):
                    add("clearance", "pass", f"obtainable after hire; previously held {facts['clearance_history']}", s)
                else:
                    add("clearance", "review", "clearance must be obtained after hire — confirm eligibility", s)
            elif active and clearance in ("none", "", "unknown"):
                add("clearance", "fail", "active clearance required; profile lists none", s)
            break

    # 2. citizenship / nationality / work authorization ------------------------------
    for s in sents:
        l = s.lower()
        m = re.search(r"(?:must be|only|open to|restricted to|limited to)\s+(?:a\s+)?(?:citizens?|nationals?)\s+(?:of\s+)?"
                      r"(?:the\s+)?([a-z .]+?)(?:\s+(?:only|citizens?|nationals?))?[.,;]", l)
        m2 = re.search(r"(?:only\s+)?([a-z]+)\s+nationals\s+(?:only|are eligible|will be considered)", l)
        target = (m.group(1).strip() if m else m2.group(1).strip() if m2 else "")
        if target:
            us = target in ("united states", "u.s", "u.s.", "us", "american", "united states of america")
            if us and "united states" in citizen:
                add("citizenship", "pass", "U.S. citizenship requirement met", s)
            elif us or any(target.startswith(c) for c in citizen):
                add("citizenship", "pass" if any(target.startswith(c) for c in citizen) else "fail",
                    f"citizenship requirement: {target}", s)
            else:
                add("citizenship", "fail", f"restricted to {target} citizens/nationals", s)
            break
        if re.search(r"(right|authori[sz]ation|eligib\w+) to work in (the )?(?!united states|us\b|u\.s)([a-z ]+)", l) and \
                _req_context(s) == "required" and job.get("country") not in ("united states", ""):
            add("work_authorization", "fail" if not re.search(r"sponsor|visa (support|will be provided)", l) else "review",
                "requires existing right to work outside the US; no sponsorship stated", s)
            break
    if job.get("country") not in ("", "united states") and not any(r["check"] in ("citizenship", "work_authorization")
                                                                   for r in reasons):
        intl_org = re.search(r"\b(united nations|unicef|undp|unops|world health organization|icrc|ifrc|iom|"
                             r"red cross|international organization)\b", low)
        if intl_org:
            add("work_authorization", "pass", "international organization (visa/status handled by employer)")
        elif re.search(r"visa sponsorship|relocation (package|support|assistance)|we sponsor", low):
            add("work_authorization", "review", "outside US; sponsorship/relocation mentioned — confirm")
        else:
            add("work_authorization", "review", f"located in {job.get('country')}; local hire likely — a U.S. citizen "
                "would need a work permit the posting does not offer")

    # 3. mandatory foreign language ----------------------------------------------------
    for s in sents:
        l = s.lower()
        for lang in LANGS:
            if re.search(rf"\b{lang}\b", l) and re.search(r"fluen|proficien|native|command of|working knowledge|"
                                                          r"spoken and written|written and spoken|bilingual", l):
                held = langs.get(lang, "none")
                ctx = _req_context(s)
                if held in ("fluent", "native", "professional"):
                    add("language", "pass", f"{lang}: {held}", s)
                elif ctx == "required" or (ctx == "neutral" and re.search(r"\bfluen|bilingual", l)):
                    add("language", "fail" if held in ("none", "") else "review",
                        f"{lang} proficiency required; profile: {held or 'not verified'}", s)
                else:
                    add("language", "note", f"{lang} preferred (not mandatory)", s)
                break

    # 4. licensure / credentials ----------------------------------------------------------
    lic_rx = {
        "rn": r"\b(rn|registered nurse)\b.*(license|licensure|required)|(license|licensure).*\b(rn|registered nurse)\b",
        "md": r"\b(md|do|m\.d\.)\b.*(required|degree)|medical degree required|licensed physician",
        "pharmd": r"pharmd|licensed pharmacist",
        "pe": r"professional engineer|\bpe license",
        "ccrp_ccra": r"\b(ccra|ccrp|socra)\b.*(required|must)",
        "pmp": r"\bpmp\b.*(required|must)|(required|must).*\bpmp\b",
        "cpa": r"\bcpa\b",
    }
    for key, rx in lic_rx.items():
        for s in sents:
            if re.search(rx, s.lower()) and _req_context(s) == "required":
                if key not in licenses and not (key == "ccrp_ccra" and "acrp-cp" in licenses):
                    add("license", "fail" if key in ("rn", "md", "pharmd", "pe", "cpa") else "review",
                        f"required credential: {key.upper()}", s)
                break

    # 5. degree ---------------------------------------------------------------------------
    for s in sents:
        l = s.lower()
        if _req_context(s) != "required":
            continue
        if re.search(r"\b(phd|ph\.d|doctorate|doctoral)\b", l) and not re.search(r"\bor\b.*(master|equivalent|experience)", l):
            if not degrees & {"phd", "md"}:
                add("degree", "fail", "doctorate required", s)
            break
        if re.search(r"\b(mph|master'?s? (of|in) public health)\b", l) and not re.search(
                r"\bor\b|related field|equivalent", l) and "mph" not in degrees:
            add("degree", "review", "MPH specified (MA International Studies held)", s)
            break

    # 6. years of experience ------------------------------------------------------------------
    best_req = None
    for s in sents:
        l = s.lower()
        nums = [int(n) for n in re.findall(r"(\d{1,2})\s*\+?\s*(?:-\s*\d{1,2}\s*)?(?:years?|yrs)", l)]
        if not nums or "experience" not in l:
            continue
        ctx = _req_context(s)
        if ctx == "preferred":
            continue
        need = min(nums)  # "BA + 10 yrs or MA + 8 yrs" -> the most favorable path
        if best_req is None or need > best_req[0]:
            best_req = (need, s)
    if best_req:
        need, s = best_req
        if need > years + 2:
            add("experience", "fail", f"requires {need}+ years; profile documents {years:g}", s)
        elif need > years:
            add("experience", "review", f"requires {need}+ years; profile documents {years:g}", s)
        else:
            add("experience", "pass", f"{need} years required; {years:g} documented", s)

    # 7. specialized-experience traps (site coordination != sponsor monitoring) ----------------
    t = title.lower()
    if re.search(r"\bcra\b|clinical research associate|clinical monitor", t) and \
            re.search(r"(monitoring|independent(ly)? monitor|on-?site monitoring) experience", low):
        mon_years = facts.get("sponsor_monitoring_years", 0)
        add("specialized_experience", "review" if mon_years == 0 else "pass",
            "CRA role expects sponsor/CRO monitoring experience; profile shows site-side coordination "
            f"(monitoring years: {mon_years})")
    if re.search(r"clinical trial manager|\bctm\b|clinical study manager", t) and \
            re.search(r"(cro|sponsor|pharma\w*|biotech\w*)[- ]side|global trial|study management experience", low):
        add("specialized_experience", "review", "CTM role may require sponsor/CRO study-management experience")

    # 8. application deadline already passed (dead timeline) ----------------------------
    from datetime import date, datetime
    m = re.search(r"(?:apply by|deadline(?: to apply)?|closing date|close date|applications? (?:due|close[sd]?))"
                  r"[^.\n]{0,40}?((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.? \d{1,2}(?:st|nd|rd|th)?,? \d{4}"
                  r"|\d{4}-\d{2}-\d{2})", low)
    if m:
        raw = re.sub(r"(st|nd|rd|th),?", "", m.group(1)).replace(",", "").replace(".", "")
        dl = None
        for fmt in ("%B %d %Y", "%b %d %Y", "%Y-%m-%d"):
            try:
                dl = datetime.strptime(raw.title() if fmt != "%Y-%m-%d" else raw, fmt).date()
                break
            except ValueError:
                continue
        if dl and dl < date.today():
            soft = re.search(r"(may|will) continue to be accepted|until (the position is )?filled|best consideration|"
                             r"first consideration", low)
            add("deadline", "review" if soft else "fail",
                f"application deadline {dl.isoformat()} has passed" + (" (rolling after)" if soft else ""), m.group(0))
        elif dl and (dl - date.today()).days <= 2:
            add("deadline", "note", f"deadline {dl.isoformat()} — apply today")

    outcome = "pass"
    if any(r["outcome"] == "fail" for r in reasons):
        outcome = "fail"
    elif any(r["outcome"] == "review" for r in reasons):
        outcome = "review"
    # evidence quality: thin postings can't be verified well
    desc_len = len(job.get("description") or "")
    conf = 0.9 if desc_len > 2500 else 0.75 if desc_len > 800 else 0.45 if desc_len > 150 else 0.2
    if outcome == "review":
        conf -= 0.15
    return {"eligibility": outcome, "eligibility_reasons": reasons, "confidence": round(max(conf, 0.05), 2)}
