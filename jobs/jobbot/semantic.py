"""Optional semantic layer: Claude reads the posting against the evidence library.

Runs through the Claude Code CLI in headless mode (`claude -p`), which uses the
account you are already logged into — no API key. If the CLI is missing, not
logged in, or returns anything that fails validation, the deterministic score stands.

Claude's output may LOWER eligibility (it can find a mandatory requirement the regexes
missed) but can never raise a deterministic `fail` to pass.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess

PROMPT = """You are screening a job posting for one specific candidate. Use ONLY the candidate evidence
below; never assume a skill, credential, language, clearance or years of experience that is not listed.

Return ONLY a JSON object, no prose, with exactly these keys:
{{"qualifications_fit": <0-100>, "interview_likelihood": <0-100>,
  "mandatory_requirements": [{{"requirement": "...", "met": "yes"|"no"|"unclear", "evidence": "candidate evidence id or 'none'"}}],
  "preferred_gaps": ["..."],
  "emphasize": ["evidence ids most relevant to this posting, best first, max 6"],
  "one_line_rationale": "..."}}

Rules: always say "the candidate"; never use gendered pronouns. A requirement is mandatory only if the posting marks it required/minimum/must. Site-based clinical
research coordination is NOT sponsor/CRO monitoring experience. Founder/Managing Director of a new
firm (2026-present) is real experience but not years of people management at scale.

CANDIDATE EVIDENCE (id: text):
{evidence}

JOB: {title} — {employer} — {location}
POSTING:
{posting}
"""


def available() -> bool:
    return shutil.which("claude") is not None


def assess(job: dict, evidence_lines: list[str], timeout: int = 180) -> dict | None:
    if not available():
        return None
    prompt = PROMPT.format(evidence="\n".join(evidence_lines)[:12000], title=job["title"], employer=job["employer"],
                           location=job.get("location") or "", posting=(job.get("description") or "")[:14000])
    try:
        # no tools, minimal system prompt, no session files: ~1 cent per posting
        out = subprocess.run(["claude", "-p", "--output-format", "json", "--tools", "",
                              "--system-prompt", "You are a meticulous recruiter. You return strict JSON only.",
                              "--no-session-persistence"],
                             input=prompt, capture_output=True, text=True, timeout=timeout)
    except (subprocess.TimeoutExpired, OSError):
        return None
    if out.returncode != 0:
        return None
    try:
        envelope = json.loads(out.stdout)
        text = envelope.get("result", "") if isinstance(envelope, dict) else str(envelope)
    except json.JSONDecodeError:
        text = out.stdout
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    return validate(data)


def validate(d: dict) -> dict | None:
    try:
        fit = float(d["qualifications_fit"])
        inter = float(d["interview_likelihood"])
        reqs = [r for r in d.get("mandatory_requirements", []) if isinstance(r, dict) and r.get("met") in
                ("yes", "no", "unclear")]
    except (KeyError, TypeError, ValueError):
        return None
    if not (0 <= fit <= 100 and 0 <= inter <= 100):
        return None
    return {"qualifications_fit": fit, "interview_likelihood": inter, "mandatory_requirements": reqs,
            "preferred_gaps": [str(x) for x in d.get("preferred_gaps", [])][:10],
            "emphasize": [str(x) for x in d.get("emphasize", [])][:6],
            "one_line_rationale": str(d.get("one_line_rationale", ""))[:300]}


def blend(det: dict, sem: dict, elig: dict) -> tuple[dict, dict]:
    """Average semantic and deterministic fit/interview; semantic 'no' on a mandatory item -> fail."""
    from .job_scoring import WEIGHTS
    sub = dict(det["subscores"])
    sub["fit"] = round((sub["fit"] + sem["qualifications_fit"]) / 2)
    sub["interview"] = round((sub["interview"] + sem["interview_likelihood"]) / 2)
    elig = dict(elig)
    reasons = list(elig["eligibility_reasons"])
    for r in sem["mandatory_requirements"]:
        if r["met"] == "no":
            reasons.append({"check": "semantic_mandatory", "outcome": "fail", "detail": r["requirement"][:200],
                            "evidence": "Claude review"})
        elif r["met"] == "unclear":
            reasons.append({"check": "semantic_mandatory", "outcome": "review", "detail": r["requirement"][:200],
                            "evidence": "Claude review"})
    elig["eligibility_reasons"] = reasons
    if any(r["outcome"] == "fail" for r in reasons):
        elig["eligibility"] = "fail"
    elif elig["eligibility"] == "pass" and any(r["outcome"] == "review" for r in reasons):
        elig["eligibility"] = "review"
    total = 0.0 if elig["eligibility"] == "fail" else sum(WEIGHTS[k] * v for k, v in sub.items())
    out = dict(det, subscores=sub, score=round(total, 1))
    return out, elig
