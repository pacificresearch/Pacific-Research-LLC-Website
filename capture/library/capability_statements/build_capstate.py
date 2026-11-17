#!/usr/bin/env python3
"""Build PRG capability statements (one page, PDF + Markdown) from one source.

    python3 capture/library/capability_statements/build_capstate.py            # all variants
    python3 capture/library/capability_statements/build_capstate.py general    # one variant

Identity facts come from capture/library/company_profile.md and SAM.gov. Change
them in COMPANY below and in company_profile.md together. Every experience line
is the Managing Director's individual record and is labelled that way: PRG has
no federal contract performance to cite yet, and no variant may imply it does.

To tailor for a notice: copy a variant, reorder COMPETENCIES so the notice's own
nouns come first, set `for_notice`, rebuild. Keep it to one page.
Requires Playwright (Chromium) for the PDF; the Markdown is written regardless.
"""
import base64
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
LOGO = os.path.join(ROOT, "site", "assets", "logo-mark-256.png")

COMPANY = {
    "name": "Pacific Research Group LLC",
    "poc": "Andrew O'Donnell, Managing Director",
    "phone": "(650) 213-2381",
    "email": "Andrew@pacificresearchllc.com",
    "web": "pacificresearchllc.com",
    "address": "2827 E Coolidge Ave, Orange, CA 92867",
    "uei": "J585TLDV1CH1",
    "cage": "1Z9B6",
    "sam": "Active through June 15, 2027",
    "cert": "SBA-certified SDVOSB and VOSB (VetCert), May 26, 2026 to May 26, 2029",
    "entity": "Single-member LLC, California",
    "naics_primary": "541714",
    "naics": "541611, 541618, 541690, 541990, 541720, 541380, 541511, 541512, 541519, 518210, "
             "541612, 541620, 541930, 611430, 611710, 621112, 621999, 624230",
    "psc": "R408, R499, R707, R425, Q999",
}

# The Managing Director's individual record. Metrics are quoted from company_profile.md.
EXPERIENCE = {
    "research": ("Clinical research operations",
                 "Multi-site NIH- and industry-sponsored protocols, including work with the Stanford University "
                 "Department of Medicine. 1,500+ participants managed; at least 90% on-time data-query resolution. "
                 "ACRP-CP and ACRP-PM certified."),
    "oaw": ("Operation Allies Welcome",
            "Mass medical intake and enrollment for 25,000+ evacuees in a federal interagency operation run to "
            "CDC requirements."),
    "bmet": ("U.S. Air Force biomedical equipment (4A2X5)",
             "98% preventive-maintenance and accreditation compliance across a $2M+ biomedical asset inventory, "
             "to Joint Commission and DoD standards. AAMI CBET certified."),
    "workflow": ("Clinical workflow redesign",
                 "40% reduction in patient processing time through redesign of clinical intake and data workflows."),
    "data": ("Data governance and platforms",
             "Formal Honest Broker for clinical data systems. Epic, Cerner, REDCap, OnCore CTMS, Medidata; "
             "SAS, SPSS, R and Python."),
}

VARIANTS = {
    "general": {
        "file": "capstate_general",
        "title": "Capability Statement",
        "tagline": "Healthcare, research and technical program management",
        "about": "Pacific Research Group LLC (PRG) is a Service-Disabled Veteran-Owned Small Business that primes "
                 "federal health, research and technical service requirements and manages them end to end: contract "
                 "management, quality control, staffing, invoicing and compliance, under one accountable point of "
                 "contact. Work is delivered by the Managing Director and by qualified personnel and specialty "
                 "partners recruited against each requirement.",
        "competencies": [
            ("Clinical research operations", "study coordination, recruitment and retention, regulatory and GCP compliance, data management"),
            ("Healthcare technology management", "biomedical equipment maintenance programs and accreditation readiness"),
            ("Healthcare operations and performance improvement", "workflow assessment and redesign, measurement, dashboards, training"),
            ("Medical readiness operations", "high-throughput intake, testing and vaccination operations, interagency coordination"),
            ("Program management, analytics and technical writing", "schedules, QC plans, reporting, statistical analysis"),
        ],
        "differentiators": [
            "Eligible for SDVOSB set-asides and VA Veterans First contracting.",
            "One accountable program manager and prime-level quality control on all work, including subcontracted work.",
            "Managing Director credentials across research, clinical and technical fields: ACRP-CP, ACRP-PM, AAMI CBET, NREMT.",
            "Compliance built in: HIPAA, 21 CFR Part 11, ICH GCP, OSHA.",
            "Says plainly what it performs itself and what it brings through a teaming partner.",
        ],
        "experience": ["research", "oaw", "bmet", "workflow", "data"],
        "role": None,
    },
    "clinical_research": {
        "file": "capstate_541715_clinical_research",
        "title": "Capability Statement: Clinical and Population Health Research Support",
        "tagline": "Research operations, site coordination and data management",
        "about": "Pacific Research Group LLC (PRG) is a Service-Disabled Veteran-Owned Small Business that supports "
                 "clinical and population health research: project management, site coordination and monitoring, "
                 "participant recruitment and retention, regulatory and human-subjects compliance, and data "
                 "management. PRG is small under NAICS 541714 and 541715.",
        "competencies": [
            ("Project management and site coordination", "plans, schedules, milestones, site and subcontract coordination, progress reporting"),
            ("Participant recruitment and retention", "screening, enrollment, follow-up and retention tracking against protocol targets"),
            ("Protocol implementation and regulatory compliance", "IRB submissions, informed consent, GCP and 21 CFR 50, 56 and 312 record keeping"),
            ("Site monitoring and quality assurance", "source verification, case report form review, corrective action follow-up"),
            ("Data collection, management and analysis", "REDCap, OnCore CTMS and Medidata; SAS, SPSS, R and Python"),
        ],
        "differentiators": [
            "Managing Director is ACRP-CP and ACRP-PM certified, with multi-site NIH and industry protocol experience.",
            "Formal Honest Broker experience in clinical data governance; HIPAA and 21 CFR Part 11 practice.",
            "Decentralized and hybrid study operations, including remote data capture and follow-up.",
            "One accountable program manager and prime-level quality control on all work.",
            "Adds certified small-business participation to a larger research team.",
        ],
        "experience": ["research", "data", "oaw", "workflow"],
        "role": "On large multi-study requirements PRG participates as a small-business team member or subcontractor. "
                "On separable task areas (coordination, monitoring, recruitment, data management) PRG can perform as prime.",
    },
    "healthcare_operations": {
        "file": "capstate_541611_healthcare_operations",
        "title": "Capability Statement: Healthcare Operations and Performance Improvement",
        "tagline": "Program management, measurement and sustainment for health systems",
        "about": "Pacific Research Group LLC (PRG) is a Service-Disabled Veteran-Owned Small Business that manages "
                 "healthcare operations and improvement programs: program management, current-state assessment, "
                 "performance measurement, training support and sustainment, under one accountable point of contact. "
                 "PRG is small under NAICS 541611.",
        "competencies": [
            ("Program management", "schedules, deliverables, risk tracking and a single point of contact for the facility"),
            ("Readiness and current-state assessment", "clinical and administrative workflow review, baselines, gap analysis"),
            ("Performance measurement and reporting", "outcome and process measures, dashboards, benefit validation, executive reporting"),
            ("Training support and standard work", "curricula packaging, job aids, standard work documents, sustainment materials"),
            ("Access and patient-flow improvement support", "intake, throughput and wait-time workflows"),
        ],
        "differentiators": [
            "Eligible for SDVOSB set-asides and VA Veterans First contracting.",
            "Managing Director has worked inside DoD medical facilities, a federal interagency medical operation and an academic medical center.",
            "Accreditation-readiness background to Joint Commission and DoD standards.",
            "Teams with certified SDVOSB specialty firms for senior Lean and HRO coaching, so the team meets limitations on subcontracting.",
            "One accountable program manager and prime-level quality control on all work.",
        ],
        "experience": ["workflow", "bmet", "oaw", "research"],
        "role": "PRG performs program management, measurement and training support itself and brings senior Lean and "
                "high-reliability coaching through qualified teaming partners. No partner is named until an agreement is signed.",
    },
}

EXPERIENCE_NOTE = ("PRG is a recently established firm with no federal contract performance to cite yet. "
                   "The record below is the individual experience of its Managing Director, a U.S. Air Force veteran.")


def _e(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def html(v):
    c = COMPANY
    logo = "data:image/png;base64," + base64.b64encode(open(LOGO, "rb").read()).decode() if os.path.exists(LOGO) else ""
    comp = "".join(f"<li><b>{_e(a)}:</b> {_e(b)}</li>" for a, b in v["competencies"])
    diff = "".join(f"<li>{_e(d)}</li>" for d in v["differentiators"])
    exp = "".join(f"<li><b>{_e(EXPERIENCE[k][0])}.</b> {_e(EXPERIENCE[k][1])}</li>" for k in v["experience"])
    role = f'<h2>How PRG participates</h2><p>{_e(v["role"])}</p>' if v.get("role") else ""
    notice = f'<p class="for">Prepared for {_e(v["for_notice"])}</p>' if v.get("for_notice") else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{_e(c['name'])} {_e(v['title'])}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700&display=swap">
<style>
@page {{ size: Letter; margin: 0 }}
:root {{ --navy:#0B1F33; --navy2:#14365C; --blue:#1F6FBF; --ink:#1b2430; --muted:#55606e; --tint:#eef3f9; --line:#cfd8e3 }}
* {{ box-sizing: border-box }}
html, body {{ margin:0; padding:0 }}
body {{ font-family:"Public Sans", Inter, "Helvetica Neue", Arial, sans-serif; color:var(--ink); font-size:9.05pt; line-height:1.33;
  width:8.5in; height:11in; display:flex; flex-direction:column; -webkit-print-color-adjust:exact; print-color-adjust:exact }}
header {{ background:var(--navy); color:#fff; padding:0.26in 0.5in 0.22in; display:flex; gap:0.22in; align-items:center }}
header img {{ width:0.74in; height:0.74in; border-radius:50%; background:#fff; padding:2px; flex:none }}
header .name {{ font-size:20pt; font-weight:700; letter-spacing:.01em; line-height:1.1 }}
header .title {{ font-size:10.5pt; font-weight:600; margin-top:3px; color:#cfe0f5 }}
header .tag {{ font-size:9pt; color:#a9c2e0; margin-top:2px }}
header .badge {{ margin-left:auto; text-align:right; font-size:8.6pt; line-height:1.45; color:#dbe7f5; flex:none }}
header .badge b {{ display:block; font-size:10pt; color:#fff; font-weight:700 }}
main {{ flex:1; display:grid; grid-template-columns: 1fr 2.45in; min-height:0 }}
.body {{ padding:0.2in 0.3in 0.12in 0.5in }}
aside {{ background:var(--tint); padding:0.2in 0.4in 0.12in 0.28in; border-left:1px solid var(--line) }}
h2 {{ font-size:9pt; letter-spacing:.09em; text-transform:uppercase; color:var(--navy2); margin:0 0 5px; padding-bottom:3px; border-bottom:1.5px solid var(--blue); font-weight:700 }}
.body h2:not(:first-child), aside h2:not(:first-child) {{ margin-top:9px }}
p {{ margin:0 0 4px }}
ul {{ margin:0; padding-left:14px }}
li {{ margin-bottom:2.4px }}
.note {{ color:var(--muted); font-size:8.5pt }}
.for {{ font-weight:600; color:var(--navy2) }}
dl {{ margin:0 }}
dt {{ font-size:7.6pt; letter-spacing:.07em; text-transform:uppercase; color:var(--muted); font-weight:600; margin-top:7px }}
dt:first-child {{ margin-top:0 }}
dd {{ margin:1px 0 0; font-size:8.9pt; overflow-wrap:anywhere }}
footer {{ background:var(--navy2); color:#dbe7f5; font-size:8.4pt; padding:0.09in 0.5in; display:flex; justify-content:space-between; gap:12px }}
</style></head><body>
<header>{f'<img src="{logo}" alt="">' if logo else ''}
<div><div class="name">{_e(c['name'])}</div><div class="title">{_e(v['title'])}</div><div class="tag">{_e(v['tagline'])}</div></div>
<div class="badge"><b>SBA-certified SDVOSB</b>UEI {c['uei']}<br>CAGE {c['cage']}</div></header>
<main><div class="body">
{notice}<h2>Who we are</h2><p>{_e(v['about'])}</p>
<h2>Core competencies</h2><ul>{comp}</ul>
<h2>Differentiators</h2><ul>{diff}</ul>
<h2>Experience</h2><p class="note">{_e(EXPERIENCE_NOTE)}</p><ul>{exp}</ul>
{role}
</div><aside>
<h2>Company data</h2><dl>
<dt>Unique Entity ID</dt><dd>{c['uei']}</dd>
<dt>CAGE code</dt><dd>{c['cage']}</dd>
<dt>SAM.gov registration</dt><dd>{_e(c['sam'])}</dd>
<dt>Certification</dt><dd>{_e(c['cert'])}</dd>
<dt>Business size</dt><dd>Small business</dd>
<dt>Entity</dt><dd>{_e(c['entity'])}</dd>
<dt>Primary NAICS</dt><dd>{c['naics_primary']}</dd>
<dt>Other NAICS</dt><dd>{_e(c['naics'])}</dd>
<dt>PSC</dt><dd>{_e(c['psc'])}</dd></dl>
<h2>Contact</h2><dl>
<dt>Point of contact</dt><dd>{_e(c['poc'])}</dd>
<dt>Phone</dt><dd>{c['phone']}</dd>
<dt>Email</dt><dd style="font-size:8.1pt;white-space:nowrap">{c['email']}</dd>
<dt>Web</dt><dd>{c['web']}</dd>
<dt>Address</dt><dd>{_e(c['address'])}</dd></dl>
</aside></main>
<footer><span>{_e(c['name'])} · {c['phone']} · {c['email']}</span><span>UEI {c['uei']} · CAGE {c['cage']}</span></footer>
</body></html>"""


def markdown(v):
    c = COMPANY
    L = [f"# {c['name']} — {v['title']}", "",
         f"**SBA-certified SDVOSB / VOSB** | UEI {c['uei']} | CAGE {c['cage']} | {c['poc']}, {c['phone']}, {c['email']}", ""]
    if v.get("for_notice"):
        L += [f"Prepared for {v['for_notice']}", ""]
    L += ["## Who we are", v["about"], "", "## Core competencies"]
    L += [f"- **{a}:** {b}" for a, b in v["competencies"]]
    L += ["", "## Differentiators"] + [f"- {d}" for d in v["differentiators"]]
    L += ["", "## Experience", EXPERIENCE_NOTE, ""] + [f"- **{EXPERIENCE[k][0]}.** {EXPERIENCE[k][1]}" for k in v["experience"]]
    if v.get("role"):
        L += ["", "## How PRG participates", v["role"]]
    L += ["", "## Company data",
          f"- SAM.gov registration: {c['sam']}", f"- Certification: {c['cert']}", f"- Entity: {c['entity']}",
          f"- Primary NAICS {c['naics_primary']}; other NAICS {c['naics']}", f"- PSC {c['psc']}",
          f"- {c['address']} · {c['web']}", ""]
    return "\n".join(L)


PDF_JS = """
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  for (const f of process.argv.slice(2)) {
    const p = await b.newPage();
    await p.goto('file://' + f, { waitUntil: 'networkidle' });
    const over = await p.evaluate(() => document.querySelector('main').scrollHeight - document.querySelector('main').clientHeight);
    await p.pdf({ path: f.replace(/\\.html$/, '.pdf'), format: 'Letter', printBackground: true, pageRanges: '1' });
    console.log(f.split('/').pop().replace('.html', '.pdf'), over > 1 ? 'OVERFLOWS ONE PAGE by ' + over + 'px' : 'fits one page');
    await p.close();
  }
  await b.close();
})();
"""


def main():
    want = sys.argv[1:] or list(VARIANTS)
    pages = []
    for key in want:
        v = VARIANTS[key]
        open(os.path.join(HERE, v["file"] + ".md"), "w", encoding="utf-8").write(markdown(v))
        h = os.path.join(HERE, v["file"] + ".html")
        open(h, "w", encoding="utf-8").write(html(v))
        pages.append(h)
    js = os.path.join(HERE, "_pdf.js")
    open(js, "w").write(PDF_JS)
    try:
        subprocess.run(["node", js] + pages, check=True)
    except (OSError, subprocess.CalledProcessError) as e:
        print("PDF step failed (Markdown and HTML were still written):", e)
    finally:
        os.remove(js)
        for h in pages:
            os.remove(h)


if __name__ == "__main__":
    main()
