"""Tailored resume generation (DOCX = editable, PDF = submitted), from evidence only.

Three baseline families — clinical, program, international — each with its own headline,
summary, skill emphasis and bullet variants (all copied from your own documents).
A per-job derivative re-ranks bullets and skills against the posting. Text is never
invented: the builder only selects, orders and picks among documented variants.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer
from xml.sax.saxutils import escape

from .config import path
from .evidence import fact_guard, profile

FAMILIES = ("clinical", "program", "international")
PER_ROLE = {"clinical": {"prg": 3, "stanford": 6, "iqarus": 2, "choc": 2, "usaf": 2},
            "program": {"prg": 5, "stanford": 5, "iqarus": 3, "choc": 1, "usaf": 3},
            "international": {"prg": 3, "stanford": 4, "iqarus": 4, "choc": 2, "usaf": 3}}
FAMILY_TAG_BOOST = {
    "clinical": {"clinical trials", "gcp", "regulatory", "decentralized", "enrollment", "edc", "redcap", "sponsor", "irb",
                 "data quality", "protocol adherence", "training"},
    "program": {"cross-functional", "budget", "p&l", "federal", "medical devices", "milestones", "process improvement",
                "stakeholder", "vendor", "operations", "leadership", "procurement"},
    "international": {"humanitarian", "interagency", "multinational", "field operations", "public health", "refugee",
                      "partnerships", "logistics", "capacity building", "emergency response", "stakeholder"},
}
SKILL_ORDER = {"clinical": ["clinical", "leadership", "data", "program", "tools"],
               "program": ["program", "leadership", "clinical", "data", "tools"],
               "international": ["program", "leadership", "clinical", "data", "tools"]}


def _tokens(s: str) -> set[str]:
    return set(re.findall(r"[a-z][a-z0-9&+\-/]{2,}", s.lower()))


def _relevance(text: str, tags: list[str], job_text: str, job_tokens: set[str], family: str) -> float:
    jt = job_text.lower()
    tags = [str(t) for t in tags]
    tag_hits = sum(2.0 for t in tags if t.lower() in jt)
    boost = sum(1.0 for t in tags if t in FAMILY_TAG_BOOST[family])
    overlap = len(_tokens(text) & job_tokens) * 0.15
    return tag_hits + boost + overlap


def select(job: dict, family: str, emphasize: list[str] | None = None) -> dict:
    """Return the structured, tailored resume content (all strings from the evidence library)."""
    if family not in FAMILIES:
        raise ValueError(family)
    pr = profile()
    job_text = f"{job.get('title', '')}\n{job.get('description', '')}"
    jtok = _tokens(job_text)
    emphasize = set(emphasize or [])
    roles = []
    for role in pr["experience"]:
        scored = []
        for b in role["bullets"]:
            text = (b.get("variants") or {}).get(family) or b["text"]
            # a different family's variant can win when it matches the posting's language better
            for fam, v in (b.get("variants") or {}).items():
                if len(_tokens(v) & jtok) > len(_tokens(text) & jtok) + 3:
                    text = v
            s = _relevance(text, b.get("tags", []), job_text, jtok, family) + (6 if b["id"] in emphasize else 0)
            scored.append((s, b["id"], " ".join(text.split())))
        k = PER_ROLE[family].get(role["id"], 3)
        top = sorted(scored, key=lambda x: -x[0])[:k]
        roles.append({**{x: role[x] for x in ("title", "org", "location", "dates")},
                      "bullets": [{"id": i, "text": t, "score": round(s, 2)} for s, i, t in top]})
    skills = []
    for group in SKILL_ORDER[family]:
        items = pr["skills"].get(group, [])
        skills += sorted(items, key=lambda x: -len(_tokens(x) & jtok))
    seen, ordered = set(), []
    for s in skills:
        if s.lower() not in seen:
            seen.add(s.lower())
            ordered.append(s)
    return {"family": family, "contact": pr["contact"], "headline": pr["headlines"][family],
            "summary": " ".join(pr["summaries"][family].split()), "roles": roles, "skills": ordered[:26],
            "certifications": pr["certifications"], "publications": pr["publications"],
            "education": pr["education"],
            "field_experience": " ".join(pr["field_experience"].split()) if family == "international" else None}


def _contact_line(c: dict) -> str:
    return " | ".join(x for x in (c.get("location"), c.get("email"), c.get("phone"), c.get("linkedin")) if x)


def write_docx(r: dict, out: Path) -> None:
    d = Document()
    st = d.styles["Normal"]
    st.font.name, st.font.size = "Calibri", Pt(10.5)
    for s in d.sections:
        s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = Pt(46)
    p = d.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(r["contact"]["name"])
    run.bold, run.font.size = True, Pt(16)
    p = d.add_paragraph(_contact_line(r["contact"]))
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = d.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run(r["headline"]).bold = True

    def h(t):
        para = d.add_paragraph()
        rr = para.add_run(t.upper())
        rr.bold, rr.font.size = True, Pt(11)

    h("Professional Summary")
    d.add_paragraph(r["summary"])
    h("Core Competencies")
    d.add_paragraph(" | ".join(r["skills"]))
    h("Experience")
    for role in r["roles"]:
        para = d.add_paragraph()
        para.add_run(f"{role['title']} | {role['org']}, {role['location']}").bold = True
        para.add_run(f" | {role['dates']}")
        for b in role["bullets"]:
            d.add_paragraph(b["text"], style="List Bullet")
    if r.get("field_experience"):
        h("Global Field Experience")
        d.add_paragraph(r["field_experience"])
    h("Licenses and Certifications")
    for c in r["certifications"]:
        d.add_paragraph(c, style="List Bullet")
    h("Publications")
    for c in r["publications"]:
        d.add_paragraph(c, style="List Bullet")
    h("Education")
    for c in r["education"]:
        d.add_paragraph(c)
    d.save(out)


def write_pdf(r: dict, out: Path) -> None:
    base = ParagraphStyle("b", fontName="Helvetica", fontSize=9.6, leading=12.2)
    name = ParagraphStyle("n", parent=base, fontName="Helvetica-Bold", fontSize=15, leading=18, alignment=TA_CENTER)
    center = ParagraphStyle("c", parent=base, alignment=TA_CENTER)
    head = ParagraphStyle("h", parent=base, fontName="Helvetica-Bold", fontSize=10.5, spaceBefore=7, spaceAfter=2)
    role_st = ParagraphStyle("r", parent=base, spaceBefore=4)
    e = lambda s: escape(s)
    flow = [Paragraph(e(r["contact"]["name"]), name), Paragraph(e(_contact_line(r["contact"])), center),
            Paragraph(f"<b>{e(r['headline'])}</b>", center), Spacer(1, 4),
            Paragraph("PROFESSIONAL SUMMARY", head), Paragraph(e(r["summary"]), base),
            Paragraph("CORE COMPETENCIES", head), Paragraph(e(" | ".join(r["skills"])), base),
            Paragraph("EXPERIENCE", head)]

    def bullets(items):
        return ListFlowable([ListItem(Paragraph(e(t), base), leftIndent=10) for t in items], bulletType="bullet",
                            start="•", leftIndent=10, bulletFontSize=8)

    for role in r["roles"]:
        flow.append(Paragraph(f"<b>{e(role['title'])} | {e(role['org'])}, {e(role['location'])}</b> | "
                              f"{e(role['dates'])}", role_st))
        flow.append(bullets([b["text"] for b in role["bullets"]]))
    if r.get("field_experience"):
        flow += [Paragraph("GLOBAL FIELD EXPERIENCE", head), Paragraph(e(r["field_experience"]), base)]
    flow += [Paragraph("LICENSES AND CERTIFICATIONS", head), bullets(r["certifications"]),
             Paragraph("PUBLICATIONS", head), bullets(r["publications"]),
             Paragraph("EDUCATION", head)] + [Paragraph(e(x), base) for x in r["education"]]
    doc = SimpleDocTemplate(str(out), pagesize=LETTER, leftMargin=0.6 * inch, rightMargin=0.6 * inch,
                            topMargin=0.5 * inch, bottomMargin=0.5 * inch, title=f"{r['contact']['name']} Resume",
                            author=r["contact"]["name"])
    doc.build(flow)


def _slug(s: str, n: int = 40) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "", s.title())[:n]


def file_stem(name: str, title: str, suffix: str = "") -> str:
    """Andrew 11/7: 'AO_' + the job title, e.g. AO_Manager_Clinical_Operations (+ '_Cover_Letter')."""
    initials = "".join(w[0] for w in name.replace("'", "").split() if w[:1].isalpha()).upper()
    t = "_".join(re.findall(r"[A-Za-z0-9]+", title))[:60].strip("_")
    return f"{initials}_{t}{suffix}"


def build(app_id: int, job: dict, family: str, emphasize: list[str] | None = None) -> dict:
    r = select(job, family, emphasize)
    flat = "\n".join([r["summary"], *r["skills"], *[b["text"] for role in r["roles"] for b in role["bullets"]]])
    problems = fact_guard(flat, job.get("description", ""))
    if problems:
        raise ValueError(f"fact guard rejected resume: {problems}")
    folder = path("materials", f"app_{app_id:05d}", "x").parent
    last = r["contact"]["name"].split()[-1].replace("'", "")
    first = r["contact"]["name"].split()[0]
    stem = file_stem(r["contact"]["name"], job["title"])
    pdf, docx = folder / f"{stem}.pdf", folder / f"{stem}.docx"
    write_pdf(r, pdf)
    write_docx(r, docx)
    sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
    (folder / "resume_manifest.json").write_text(json.dumps(
        {"family": family, "pdf": pdf.name, "docx": docx.name, "sha256": sha,
         "bullets": [b["id"] for role in r["roles"] for b in role["bullets"]], "skills": r["skills"]}, indent=2))
    return {"pdf": str(pdf), "docx": str(docx), "sha256": sha, "family": family}


def build_baselines() -> list[str]:
    """The three untailored family baselines (for review and manual applications)."""
    out = []
    for fam in FAMILIES:
        generic = {"title": "", "description": "", "employer": "Baseline"}
        r = select(generic, fam)
        folder = path("materials", "baselines", "x").parent
        pr = profile()
        last = pr["contact"]["name"].split()[-1].replace("'", "")
        stem = f"{last}_{pr['contact']['name'].split()[0]}_Resume_{fam.title()}_Baseline"
        write_pdf(r, folder / f"{stem}.pdf")
        write_docx(r, folder / f"{stem}.docx")
        out.append(str(folder / f"{stem}.pdf"))
    return out
