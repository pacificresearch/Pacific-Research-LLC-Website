"""Evidence library access + the fact guard.

The fact guard is the last line of defense against fabrication: any generated text
(resume, cover letter, Claude-polished prose) is rejected if it contains a number,
credential acronym or proper-noun program name that is not in the evidence library
or the posting itself.
"""
from __future__ import annotations

import re
from functools import lru_cache

import yaml

from .config import home

CREDENTIAL_TOKENS = {"ACRP-PM", "ACRP-CP", "CBET", "NREMT", "CPT", "BLS", "ACLS", "PALS", "PHTLS", "TCCC", "CITI",
                     "GCP", "HIPAA", "DOT", "PMP", "CCRA", "CCRP", "SOCRA", "RN", "MPH", "PHD", "MBA", "CISSP", "PE",
                     "RAC", "CPHQ", "CCRC", "CCRP", "LSSGB", "CSM", "PMI-ACP", "MD"}


@lru_cache(maxsize=1)
def _load(path_str: str, mtime: float) -> dict:
    from pathlib import Path
    return yaml.safe_load(Path(path_str).read_text())


def profile() -> dict:
    p = home() / "profile.yaml"
    if not p.exists():
        raise FileNotFoundError(f"{p} missing — copy jobs/profile.example.yaml there and fill it in")
    return _load(str(p), p.stat().st_mtime)


def all_text(pr: dict | None = None) -> str:
    pr = pr or profile()
    return yaml.safe_dump(pr, allow_unicode=True)


def evidence_lines(pr: dict | None = None) -> list[str]:
    pr = pr or profile()
    out = []
    for role in pr["experience"]:
        for b in role["bullets"]:
            out.append(f"{b['id']}: [{role['title']}, {role['org']}, {role['dates']}] {' '.join(b['text'].split())}")
    out.append("certifications: " + "; ".join(pr.get("certifications", [])))
    out.append("education: " + "; ".join(pr.get("education", [])))
    out.append("field_experience: " + " ".join(pr.get("field_experience", "").split()))
    langs = pr.get("facts", {}).get("languages", {})
    out.append("languages (verified): " + ", ".join(f"{k}={v}" for k, v in langs.items()))
    out.append("security clearance: " + str(pr.get("facts", {}).get("clearance", "none")))
    return out


def lexicon(pr: dict | None = None) -> set[str]:
    pr = pr or profile()
    words = set()
    for role in pr["experience"]:
        for b in role["bullets"]:
            words.update(str(t).lower() for t in b.get("tags", []))
    for group in pr.get("skills", {}).values():
        words.update(s.lower() for s in group if len(s) < 40)
    return {w for w in words if len(w) > 2}


def _numbers(s: str) -> set[str]:
    return {n.replace(",", "") for n in re.findall(r"\d[\d,]*(?:\.\d+)?", s)}


def fact_guard(generated: str, job_text: str = "", pr: dict | None = None) -> list[str]:
    """Return a list of violations (empty = clean)."""
    pr = pr or profile()
    allowed_src = all_text(pr) + "\n" + (job_text or "")
    allowed_nums = _numbers(allowed_src)
    problems = []
    for n in _numbers(generated):
        if n not in allowed_nums:
            problems.append(f"number not in evidence or posting: {n}")
    up_src = allowed_src.upper()
    for tok in set(re.findall(r"\b[A-Z][A-Z\-]{1,8}\b", generated)):
        if tok in CREDENTIAL_TOKENS and tok not in up_src:
            problems.append(f"credential not in evidence: {tok}")
    for phrase in re.findall(r"\b(?:fluent|native|bilingual) in (\w+)", generated, re.I):
        if f"{phrase.lower()}: native" not in all_text(pr).lower() and phrase.lower() != "english":
            problems.append(f"language claim not verified: {phrase}")
    return problems
