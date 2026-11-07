"""Employer-specific cover letters (200-350 words) from documented achievements only.

Structure: specific opening (employer + exact title + the posting's own focus) -> 2-3
documented achievements chosen for relevance -> connection to the organization's work
as the POSTING describes it (never an invented personal motivation) -> close.
Optional Claude polish is accepted only if it passes the fact guard and word-count check.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from datetime import date

from docx import Document
from docx.shared import Pt
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from xml.sax.saxutils import escape

from .config import path
from .evidence import fact_guard, profile

FOCUS = [
    (r"decentralized|remote trial|dct|virtual trial", "decentralized and hybrid trial delivery"),
    (r"infectious|vaccine|covid|antiviral", "infectious disease research"),
    (r"study start.?up|site activation", "study start-up and site activation"),
    (r"site monitoring|monitoring visit|clinical monitor|\bcra\b", "site monitoring and data quality"),
    (r"laborator|\blabs?\b|central lab|bioanalytic", "laboratory project delivery"),
    (r"site (operations|network|management)|research site", "research site operations"),
    (r"medical device|biomedical|medtech", "medical technology programs"),
    (r"humanitarian|refugee|emergency|crisis", "humanitarian health operations"),
    (r"global health|international|country office", "global health programs"),
    (r"health security|biosecurity|biodefense|preparedness|pandemic", "health security and preparedness"),
    (r"federal|government|dod|\bva\b|hhs", "federal health programs"),
    (r"partnership|alliance", "partnership development"),
    (r"program manag|project manag", "program delivery"),
    (r"clinical operations|clinical trial", "clinical trial operations"),
]


def needed(job: dict, category: str, score: float) -> tuple[bool, str]:
    t = (job.get("description") or "").lower()
    if re.search(r"cover letter (is )?(required|must)|(must|please) (include|submit|attach) a cover letter", t):
        return True, "required by employer"
    if re.search(r"cover letter", t):
        return True, "requested/encouraged in posting"
    if category == "C":
        return True, "international role"
    if re.search(r"manager|director|lead|chief", job["title"].lower()) and score >= 85:
        return True, "senior and competitive"
    if category == "B":
        return True, "explains transition beyond site-level research"
    return False, "not needed"


def _focus(job: dict) -> str:
    t = f"{job['title']} {job.get('description', '')[:4000]}".lower()
    for rx, phrase in FOCUS:
        if re.search(rx, t):
            return phrase
    return "this work"


def _mission_sentence(job: dict) -> str | None:
    """A sentence the employer wrote about itself — referenced, not paraphrased into a claim about Andrew."""
    for s in re.split(r"(?<=[.!?])\s+", job.get("description") or ""):
        s = s.strip()
        if 60 < len(s) < 220 and re.search(r"\b(our mission|we are|we're|is dedicated|our goal|we help|we work)\b", s, re.I):
            return s
    return None


def compose(job: dict, family: str, emphasize: list[str] | None = None) -> str:
    pr = profile()
    jt = f"{job['title']} {job.get('description', '')}".lower()
    prior = {"clinical": {"cp.activ6": 5, "cp.data": 3, "cp.oaw": 1},
             "program": {"cp.prg": 3, "cp.oaw": 3, "cp.usaf": 3, "cp.activ6": 2},
             "international": {"cp.oaw": 5, "cp.activ6": 2, "cp.usaf": 1}}[family]
    sem_map = {"su.": "cp.activ6", "oaw.": "cp.oaw", "usaf.": "cp.usaf", "prg.": "cp.prg"}
    emph_cp = {v for e in (emphasize or [])[:3] for k, v in sem_map.items() if e.startswith(k)}

    def weight(p):
        hits = sum(2 for t in p["tags"] if re.search(rf"\b{re.escape(t)}\b", jt))
        return hits + prior.get(p["id"], 0) + (3 if p["id"] in emph_cp else 0)

    pts = sorted(pr["cover_points"], key=lambda p: -weight(p))
    chosen = [p for p in pts if p["id"] not in ("cp.pubs", "cp.ma")][:2]
    extra = []
    if any(p["id"] == "cp.activ6" for p in chosen):
        extra.append(next(p for p in pr["cover_points"] if p["id"] == "cp.pubs"))
    if family == "international" or job.get("country") not in ("", "united states"):
        extra.append(next(p for p in pr["cover_points"] if p["id"] == "cp.ma"))
    focus = _focus(job)
    employer, title = job["employer"], job["title"]
    opening = (f"I am applying for the {title} position at {employer}. The role's emphasis on {focus} matches the work "
               f"I have done across Stanford University's Department of Medicine, the U.S. Air Force Reserve, and a "
               f"federal humanitarian medical operation.")
    body1 = " ".join(p["text"] for p in chosen + extra[:1])
    mission = _mission_sentence(job)
    p3 = (f"Your posting describes the organization this way: “{mission}” I would bring the same operational "
          f"discipline to that work: clear tracking, practical fixes when handoffs break, and steady coordination "
          f"across investigators, sponsors, partners, and field teams." if mission else
          f"I would bring the same operational discipline to {employer}: clear tracking, practical fixes when handoffs "
          f"break, and steady coordination across investigators, sponsors, partners, and field teams.")
    tail = " ".join(p["text"] for p in extra[1:])
    close = (f"I hold ACRP Project Manager and Certified Professional credentials and an MA in International Studies. "
             f"I would welcome the chance to discuss how I can contribute to the {title} role.")
    paras = [opening, body1, p3] + ([tail] if tail else []) + [close]
    return "\n\n".join(paras)


def polish_with_claude(draft: str, job: dict, timeout: int = 120) -> str | None:
    if not shutil.which("claude"):
        return None
    prompt = (f"Edit this cover letter for natural flow and concision (200-330 words). Do NOT add any fact, number, "
              f"credential, motivation, personal connection or claim that is not already in the draft. Keep the "
              f"employer name and job title exactly. Return only the letter body paragraphs.\n\nDRAFT:\n{draft}")
    try:
        out = subprocess.run(["claude", "-p", "--tools", "", "--no-session-persistence",
                              "--system-prompt", "You are a careful editor. You never add facts."],
                             input=prompt, capture_output=True, text=True, timeout=timeout)
    except (subprocess.TimeoutExpired, OSError):
        return None
    text = out.stdout.strip()
    return text if out.returncode == 0 and text else None


def words(s: str) -> int:
    return len(re.findall(r"\b\w[\w'\-]*\b", s))


def build(app_id: int, job: dict, family: str, emphasize: list[str] | None = None, polish: bool = False) -> dict:
    body = compose(job, family, emphasize)
    used = "template"
    if polish:
        cand = polish_with_claude(body, job)
        if cand and not fact_guard(cand, job.get("description", "")) and 200 <= words(cand) <= 350 \
                and job["employer"] in cand:
            body, used = cand, "claude-polished"
    problems = fact_guard(body, job.get("description", ""))
    if problems:
        raise ValueError(f"fact guard rejected cover letter: {problems}")
    n = words(body)
    pr = profile()
    c = pr["contact"]
    folder = path("materials", f"app_{app_id:05d}", "x").parent
    last = c["name"].split()[-1].replace("'", "")
    from .resume_builder import file_stem
    stem = file_stem(c["name"], job["title"], "_Cover_Letter")
    header = [c["name"], " | ".join(x for x in (c["location"], c["email"], c["phone"]) if x),
              date.today().strftime("%B %-d, %Y"), "", f"Hiring Team, {job['employer']}", f"Re: {job['title']}", "",
              "Dear Hiring Team,"]
    footer = ["Sincerely,", c["name"]]
    # PDF
    st = ParagraphStyle("b", fontName="Helvetica", fontSize=10.5, leading=14.5, spaceAfter=8)
    flow = [Paragraph(escape(h) if h else "&nbsp;", st) for h in header]
    flow += [Paragraph(escape(p), st) for p in body.split("\n\n")] + [Spacer(1, 4)]
    flow += [Paragraph(escape(f), st) for f in footer]
    pdf = folder / f"{stem}.pdf"
    SimpleDocTemplate(str(pdf), pagesize=LETTER, leftMargin=inch, rightMargin=inch, topMargin=0.9 * inch,
                      bottomMargin=0.9 * inch, title="Cover Letter", author=c["name"]).build(flow)
    # DOCX + plain text (for paste-in fields)
    d = Document()
    d.styles["Normal"].font.size = Pt(11)
    for h in header:
        d.add_paragraph(h)
    for p in body.split("\n\n"):
        d.add_paragraph(p)
    for f in footer:
        d.add_paragraph(f)
    docx = folder / f"{stem}.docx"
    d.save(docx)
    txt = folder / "cover_letter.txt"
    txt.write_text("Dear Hiring Team,\n\n" + body + "\n\nSincerely,\n" + c["name"] + "\n")
    return {"pdf": str(pdf), "docx": str(docx), "txt": str(txt), "words": n, "method": used,
            "sha256": hashlib.sha256(pdf.read_bytes()).hexdigest()}
