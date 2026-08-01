#!/usr/bin/env python3
"""Render a tailored resume Markdown file to PDF (and a JSON model for docx).

Usage: python3 tools/resume_render.py tailored/<name>.md

RULES ENFORCED (do not regress):
- Em dashes and double hyphens are forbidden anywhere in resume text.
- A job/entry header is glued to its first bullet (flat KeepTogether only;
  nesting KeepTogether breaks ReportLab layout).
- A section header + rule is glued to the section's first content.
- Real TrueType fonts (Liberation Sans) are embedded; base-14 Helvetica is
  never used to draw glyphs (some viewers substitute slanted lookalikes).
"""
import json
import re
import sys

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, HRFlowable, ListFlowable, ListItem,
    KeepTogether,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

_FDIR = "/usr/share/fonts/truetype/liberation"
pdfmetrics.registerFont(TTFont("LiberationSans", f"{_FDIR}/LiberationSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("LiberationSans-Bold", f"{_FDIR}/LiberationSans-Bold.ttf"))
pdfmetrics.registerFontFamily("LiberationSans", normal="LiberationSans",
                              bold="LiberationSans-Bold")

DARK = HexColor("#000000")
RULE = HexColor("#000000")

S = {
    "name": ParagraphStyle("name", fontName="LiberationSans-Bold", fontSize=17,
                           leading=20, alignment=TA_CENTER, textColor=DARK, spaceAfter=2),
    "contact": ParagraphStyle("contact", fontName="LiberationSans", fontSize=9.5,
                              leading=12.5, alignment=TA_CENTER, textColor=DARK, spaceAfter=2),
    "headline": ParagraphStyle("headline", fontName="LiberationSans-Bold", fontSize=11.5,
                               leading=14.5, alignment=TA_CENTER, textColor=DARK,
                               spaceBefore=4, spaceAfter=4),
    "section": ParagraphStyle("section", fontName="LiberationSans-Bold", fontSize=11,
                              leading=13.5, textColor=DARK, spaceBefore=10, spaceAfter=1),
    "body": ParagraphStyle("body", fontName="LiberationSans", fontSize=9.8,
                           leading=12.6, textColor=DARK, spaceAfter=3),
    "jobtitle": ParagraphStyle("jobtitle", fontName="LiberationSans", fontSize=9.8,
                               leading=12.8, textColor=DARK, spaceBefore=6, spaceAfter=2),
    "bullet": ParagraphStyle("bullet", fontName="LiberationSans", fontSize=9.8,
                             leading=12.4, textColor=DARK),
    "edu": ParagraphStyle("edu", fontName="LiberationSans", fontSize=9.8,
                          leading=12.8, textColor=DARK, spaceAfter=2),
}
for _s in S.values():
    _s.bulletFontName = "LiberationSans"


def esc(t):
    t = t.replace(" | ", "\u00a0| ")  # bar binds to preceding word (master style)
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def md_bold(t):
    """Convert **x** to <b>x</b> after escaping."""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc(t))


def one_bullet(text):
    return ListFlowable(
        [ListItem(Paragraph(md_bold(text), S["bullet"]), leftIndent=14)],
        bulletType="bullet", start="•", bulletFontSize=9.8,
        bulletFontName="LiberationSans", leftIndent=14, spaceBefore=0, spaceAfter=1.5,
    )


def parse(md_path):
    """Parse the resume markdown into a simple document model."""
    lines = open(md_path).read().splitlines()
    model = {"name": None, "contact": None, "headline": None, "summary": None,
             "sections": []}
    cur = None
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("# ") and model["name"] is None:
            model["name"] = ln[2:].strip()
        elif ln.startswith("## ") and model["headline"] is None:
            model["headline"] = ln[3:].strip()
        elif ln.startswith("## "):
            cur = {"title": ln[3:].strip(), "items": []}
            model["sections"].append(cur)
        elif ln.startswith("### "):
            cur["items"].append({"type": "job", "text": ln[4:].strip()})
        elif ln.startswith("  - "):
            cur["items"].append({"type": "subline", "text": ln[4:].strip()})
        elif ln.startswith("- "):
            text = ln[2:].strip()
            if cur and cur["title"] in ("TECHNICAL SKILLS",):
                cur["items"].append({"type": "labelline", "text": text})
            elif cur and cur["title"] == "EDUCATION":
                cur["items"].append({"type": "eduline", "text": text})
            else:
                cur["items"].append({"type": "bullet", "text": text})
        elif ln.strip():
            if model["contact"] is None and model["name"] is not None:
                model["contact"] = ln.strip()
            elif model["headline"] is not None and model["summary"] is None and cur is None:
                model["summary"] = ln.strip()
            elif cur is not None:
                cur["items"].append({"type": "para", "text": ln.strip()})
        i += 1
    return model


def nowrap_dates(text):
    """Make the trailing date segment unbreakable so a year is never
    orphaned on its own line: the whole range wraps together or not at all."""
    segs = text.split(" | ")
    segs[-1] = segs[-1].replace(" ", "\u00a0")
    return " | ".join(segs)


AVAIL = 612 - 2 * 0.6 * 72  # page width minus margins, points


def job_para(text):
    """Job header on ONE line, always: bold title, auto-shrunk to fit."""
    text = nowrap_dates(text)
    parts = text.split(" | ", 1)
    title = parts[0]
    rest = (" | " + parts[1]) if len(parts) == 2 else ""
    size = 9.8
    while size > 7.5:
        w = (pdfmetrics.stringWidth(title, "LiberationSans-Bold", size)
             + pdfmetrics.stringWidth(rest.replace("\u00a0", " "), "LiberationSans", size))
        if w <= AVAIL - 10:
            break
        size -= 0.1
    st = ParagraphStyle(f"jt{size}", parent=S["jobtitle"], fontSize=size,
                        leading=size + 3)
    return Paragraph(f"<b>{esc(title)}</b>{esc(rest)}", st)


def build(model):
    story = [Paragraph(esc(model["name"]), S["name"]),
             Paragraph(esc(model["contact"]), S["contact"]),
             Paragraph(esc(model["headline"]), S["headline"]),
             Paragraph(esc(model["summary"]), S["body"])]
    for sec in model["sections"]:
        header = [Paragraph(f"<b>{esc(sec['title'])}</b>", S["section"]),
                  HRFlowable(width="100%", thickness=1.6, color=RULE,
                             spaceBefore=2, spaceAfter=5)]
        items = sec["items"]
        flows = []
        j = 0
        while j < len(items):
            it = items[j]
            if it["type"] == "job":
                # whole job block stays together: header + ALL its bullets
                head = [job_para(it["text"])]
                while j + 1 < len(items) and items[j + 1]["type"] == "bullet":
                    head.append(one_bullet(items[j + 1]["text"]))
                    j += 1
                flows.append(("group", head))
            elif it["type"] == "bullet":
                flows.append(("flow", one_bullet(it["text"])))
            elif it["type"] in ("labelline", "eduline"):
                style = S["edu"] if it["type"] == "eduline" else S["body"]
                flows.append(("flow", Paragraph(md_bold(it["text"]), style)))
            elif it["type"] == "subline":
                flows.append(("flow", Paragraph(esc(it["text"]), S["edu"])))
            elif it["type"] == "para":
                flows.append(("flow", Paragraph(md_bold(it["text"]), S["body"])))
            j += 1
        # Glue section header (+rule) to the section's first content, flat.
        if flows:
            kind, first = flows[0]
            first_group = first if kind == "group" else [first]
            story.append(KeepTogether(header + first_group))
            for kind, f in flows[1:]:
                if kind == "group":
                    story.append(KeepTogether(f))
                else:
                    story.append(f)
        else:
            story.append(KeepTogether(header))
    return story


def main():
    md_path = sys.argv[1]
    text = open(md_path).read()
    assert "—" not in text and "--" not in text and "–" not in text, \
        "dash rule violated in source markdown"
    model = parse(md_path)
    out_pdf = md_path.rsplit(".", 1)[0] + ".pdf"
    out_json = md_path.rsplit(".", 1)[0] + ".json"
    doc = SimpleDocTemplate(out_pdf, pagesize=letter,
                            leftMargin=0.6 * inch, rightMargin=0.6 * inch,
                            topMargin=0.55 * inch, bottomMargin=0.55 * inch,
                            title=f"{model['name']} - Resume", author=model["name"])
    doc.build(build(model))
    json.dump(model, open(out_json, "w"), indent=1)
    print("written:", out_pdf)
    print("written:", out_json)


if __name__ == "__main__":
    main()
