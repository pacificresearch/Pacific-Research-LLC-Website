"""Answer employer screening questions strictly from the evidence library.

Scope: questions of FACT about experience/education/skills ("Have you worked for a CRO?", "Do you have
a BA?", "Years of experience with GCP?") and short free-text prompts ("Briefly describe your EDC
experience"). Out of scope (always returned as None -> NEEDS_HUMAN_ACTION): legal/eligibility,
attestations, relatives/conflicts, personal circumstances, salary, anything the evidence doesn't settle.

Every answer carries the evidence ids it rests on and is cached in $JOBBOT_HOME/answer_cache.yaml, keyed
by the normalized question, so you can review or override any answer once and it applies everywhere.
"No" is a valid, honest answer and is given when the evidence shows the candidate lacks the thing.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess

import yaml

from .config import home
from .evidence import evidence_lines, fact_guard

OUT_OF_SCOPE = re.compile(r"\b(relatives?|family members?|conflicts? of interest|outside employment|acknowledg\w*|attest\w*|"
                          r"certif(y|ication)|agree|consent|signature|felony|convict\w*|criminal|disabilit\w*|veteran|"
                          r"gender|race|ethnic\w*|sponsor(ship)?|visa|authori[sz]ed|citizen\w*|clearance|salary|"
                          r"compensation|pay|currently live|reside|commute|relocat\w*|start date|notice period|referr\w*|"
                          r"how did you hear|age|birth|drug|background check|non-?compete|tell us about yourself|"
                          r"anything else)\b", re.I)
MOTIVATION = re.compile(r"excite|why (do|are|would) you|interest(ed|s)? (in|you)|motivat|passion|attract|what draws|"
                        r"why this (role|company|position)", re.I)
RESIDENCE = re.compile(r"(currently )?(live|living|reside|residing|located|based) in (the )?([a-z .,'-]+?)(\?|\*|✱|$)", re.I)
BAY = {"san francisco bay area", "bay area", "san francisco"}
SOCAL = {"southern california", "orange county", "los angeles", "socal", "california", "greater los angeles"}


def residence_answer(question: str, pr: dict) -> str | None:
    """'Do you currently live in X?' from the address on file."""
    m = RESIDENCE.search(question)
    if not m:
        return None
    place = m.group(4).strip(" ,.").lower()
    addr = pr.get("address") or {}
    here = {(addr.get("city") or "").lower(), (addr.get("state") or "").lower(), "orange county", "southern california",
            "socal", "greater los angeles", "los angeles area", "united states", "united states of america", "us",
            "u.s", "u.s.", "usa", "u.s.a", "america"}
    if place in here or (place in SOCAL and (addr.get("state") or "").lower() == "california"):
        return "Yes"
    return "No"

PROMPT = """Answer an employer's job-application screening question for ONE candidate, using ONLY the
candidate evidence below. Do not assume anything not stated. Site-based clinical research coordination
at an academic medical center is NOT working for a CRO, sponsor, pharma or biotech company. Founding a
small federal contracting firm in 2026 is real but recent experience.

Two kinds of questions:
1. FACTS about the candidate (experience, credentials, history): answer only if the evidence clearly settles
   it; "No" is correct when the evidence shows the candidate lacks it; otherwise "UNKNOWN".
2. LOW-STAKES ADMINISTRATIVE preferences (how did you hear, preferred contact channel, interview scheduling
   preference, talent-pool / future-opportunity opt-in, newsletter, preferred pronunciation, shift or
   schedule flexibility, willingness to complete assessments, etc.): use sensible judgment for a candidate
   who wants to keep the application moving — pick the neutral, efficient option. Never pick an option
   that asserts something untrue (e.g. "an employee referred me"). Basis may be ["judgment"].
Never answer legal attestations, consents, terms acceptance, conflicts of interest, or personal/legal status
questions — return "UNKNOWN" for those.
{choice_rule}
Return ONLY JSON: {{"answer": "...", "basis": ["evidence ids"], "confidence": 0.0-1.0}}

CANDIDATE EVIDENCE:
{evidence}

JOB: {title} at {employer}
QUESTION: {question}
"""


def _cache_file():
    return home() / "answer_cache.yaml"


def _norm(q: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", q.lower()).strip()[:200]


def cache() -> dict:
    f = _cache_file()
    return (yaml.safe_load(f.read_text()) or {}) if f.exists() else {}


def _save(d: dict) -> None:
    _cache_file().write_text(yaml.safe_dump(d, sort_keys=True, allow_unicode=True, width=120))


def answer(question: str, options: list[str], job: dict, timeout: int = 120) -> str | None:
    q = " ".join(question.split())
    from .evidence import profile
    res = residence_answer(q, profile())
    if res:
        return res
    bls = bls_answer(q, options)
    if bls:
        return bls
    key = _norm(q)
    c = cache()
    hit = c.get(key)
    if hit is None or hit.get("override") is None:  # an override on a (truncated) copy of the question wins
        ov = next((v for k, v in c.items() if v.get("override") is not None and len(k) >= 60
                   and (key.startswith(k[:120]) or k.startswith(key[:120]))), None)
        hit = ov or hit
    if hit and hit.get("override") is not None:
        return hit["override"]  # Andrew's own answer always wins
    if re.search(r"(if yes|please (describe|explain|specify|provide details))", q, re.I) and job.get("employer"):
        for v in c.values():
            if v.get("detail") and v.get("employer_first_seen", "").split()[0].lower() in job["employer"].lower():
                return v["detail"]
    if MOTIVATION.search(q) and not [o for o in options if o and not re.match(r"^(select|please select|select one|--)", o, re.I)]:
        return motivation_answer(job)  # free-text only; never pasted into a choice list
    if not q or OUT_OF_SCOPE.search(q):
        return None
    yesno = re.match(r"^(do|does|did|have|has|are|is|can|will|would|were)\b", q, re.I)
    if hit and hit.get("override") is not None:
        return hit["override"]
    if hit and hit.get("answer") not in (None, "UNKNOWN"):
        a = hit["answer"]
        if yesno and not options:
            m = re.match(r"^(yes|no)\b", a, re.I)
            if m:
                return m.group(1).title()
        elif not options or a in options:
            return a
    if not shutil.which("claude"):
        return None
    opts = [o for o in options if o and not re.match(r"^(select|please select|select one|--)", o, re.I)]
    if not opts and re.match(r"^(do|does|did|have|has|are|is|can|will|would|were)\b", q, re.I):
        opts = ["Yes", "No"]  # yes/no question rendered as a combobox: never type prose into it
    choice_rule = (f"The answer MUST be exactly one of these options: {opts}" if opts else
                   "Free-text: answer in 1-3 plain sentences (max 450 characters), first person, using only "
                   "documented facts and numbers from the evidence.")
    prompt = PROMPT.format(choice_rule=choice_rule, evidence="\n".join(evidence_lines())[:12000],
                           title=job.get("title", ""), employer=job.get("employer", ""), question=q)
    try:
        out = subprocess.run(["claude", "-p", "--output-format", "json", "--tools", "", "--no-session-persistence",
                              "--system-prompt", "You answer strictly from evidence and return JSON only."],
                             input=prompt, capture_output=True, text=True, timeout=timeout)
        text = json.loads(out.stdout).get("result", "")
        d = json.loads(re.search(r"\{.*\}", text, re.S).group(0))
    except Exception:
        return None
    ans = str(d.get("answer", "")).strip()
    basis = [str(b) for b in d.get("basis", [])][:6]
    conf = float(d.get("confidence", 0) or 0)
    ok = ans and ans != "UNKNOWN" and conf >= 0.7 and basis
    if ok and opts and ans not in opts:
        ok = False
    if ok and not opts and (len(ans) > 450 or fact_guard(ans, job.get("description", ""))):
        ok = False
    c[key] = {"question": q, "answer": ans if ok else "UNKNOWN", "basis": basis, "confidence": conf,
              "employer_first_seen": job.get("employer", ""), "override": None}
    _save(c)
    return ans if ok else None


def motivation_answer(job: dict) -> str | None:
    """'Why this role?' answered like the cover letter: posting focus <-> documented experience. No invented
    personal enthusiasm or connection; fact-guarded."""
    from .cover_letter_builder import _focus
    from .evidence import profile
    focus = _focus(job)
    pr = profile()
    jt = f"{job.get('title', '')} {job.get('description', '')}".lower()
    pts = sorted(pr["cover_points"], key=lambda p: -sum(2 for t in p["tags"] if t in jt))
    pts = [p for p in pts if p["id"] not in ("cp.pubs", "cp.ma")][:1]
    text = (f"The role's emphasis on {focus} lines up directly with my experience. " + (pts[0]["text"] if pts else "")).strip()
    if len(text) > 600 or fact_guard(text, job.get("description", "")):
        return None
    return text


BLS_RX = re.compile(r"\bBLS\b|basic life support|\bCPR\b", re.I)
BLS_CURRENT_RX = re.compile(r"\b(current|active|valid|currently (hold|have)|do you (hold|have|possess))\b", re.I)
BLS_WILLING_RX = re.compile(r"\b(willing|able|obtain|within \d+|upon hire|prior to start|by (your )?start)\b", re.I)


def bls_answer(q: str, options: list[str]) -> str | None:
    """Andrew 11/13: BLS is expired and will be renewed upon hire. Truthful either way:
    'can you obtain it' -> Yes; 'do you currently hold it' -> No / the renew-on-hire option."""
    if not BLS_RX.search(q) or re.search(r"\bACLS|PALS\b", q) and not BLS_RX.search(q.replace("ACLS", "")):
        return None
    opts = [o for o in options if o and not re.match(r"^(select|please select|--)", o, re.I)]
    if BLS_WILLING_RX.search(q):
        return next((o for o in opts if re.match(r"^yes\b", o, re.I)), "Yes")
    if BLS_CURRENT_RX.search(q) or opts:
        renew = next((o for o in opts if re.search(r"will (obtain|renew)|upon hire|willing|in progress|expired", o, re.I)), None)
        if renew:
            return renew
        if opts:
            return next((o for o in opts if re.match(r"^no\b", o, re.I)), None)
        return "No - BLS (AHA) previously held; will renew upon hire"
    return "AHA BLS previously held (expired); will renew upon hire"
