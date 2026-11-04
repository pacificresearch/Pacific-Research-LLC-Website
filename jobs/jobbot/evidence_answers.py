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

OUT_OF_SCOPE = re.compile(r"relative|family member|conflict of interest|outside employment|acknowledg|attest|certif|"
                          r"agree|consent|signature|felony|convict|criminal|disabilit|veteran|gender|race|ethnic|"
                          r"sponsor|visa|authori[sz]ed|citizen|clearance|salary|compensation|pay|currently live|"
                          r"reside|commute|relocat|start date|notice|referr|how did you hear|age|birth|drug|"
                          r"background check|non-?compete|excite|why (do|are|would) you|interest(ed|s)? (in|you)|"
                          r"motivat|passion|attract|what draws|tell us about yourself|cover letter|anything else", re.I)
RESIDENCE = re.compile(r"(currently )?(live|reside|located|based) in (the )?([a-z .,'-]+?)(\?|\*|$)", re.I)
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
            "socal", "greater los angeles", "los angeles area"}
    if place in here or (place in SOCAL and (addr.get("state") or "").lower() == "california"):
        return "Yes"
    return "No"

PROMPT = """Answer an employer's job-application screening question for ONE candidate, using ONLY the
candidate evidence below. Do not assume anything not stated. Site-based clinical research coordination
at an academic medical center is NOT working for a CRO, sponsor, pharma or biotech company. Founding a
small federal contracting firm in 2026 is real but recent experience.

If the evidence clearly settles the question, answer it; "No" is correct when the evidence shows the
candidate lacks it. If it does not clearly settle it, answer "UNKNOWN".
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
    if not q or OUT_OF_SCOPE.search(q):
        return None
    key = _norm(q)
    c = cache()
    hit = c.get(key)
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
    ok = ans and ans != "UNKNOWN" and conf >= 0.75 and basis
    if ok and opts and ans not in opts:
        ok = False
    if ok and not opts and (len(ans) > 450 or fact_guard(ans, job.get("description", ""))):
        ok = False
    c[key] = {"question": q, "answer": ans if ok else "UNKNOWN", "basis": basis, "confidence": conf,
              "employer_first_seen": job.get("employer", ""), "override": None}
    _save(c)
    return ans if ok else None
