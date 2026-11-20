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
    "poc": "Andrew O'Donnell, Founder and Managing Director",
    "phone": "(650) 213-2381",
    "email": "Andrew@pacificresearchllc.com",
    "web": "pacificresearchllc.com",
    "address": "2827 E Coolidge Ave, Orange, CA 92867 (Greater Los Angeles)",
    "uei": "J585TLDV1CH1",
    "cage": "1Z9B6",
    "sam": "Active through June 15, 2027",
    "cert": "SBA-certified SDVOSB and VOSB (VetCert), May 26, 2026 to May 26, 2029",
    "entity": "California LLC",
    "naics_primary": "541714",
    "naics": "541611, 541618, 541690, 541990, 541720, 541380, 541511, 541512, 541519, 518210, "
             "541612, 541620, 541930, 611430, 611710, 621112, 621999, 624230",
    "psc": "R408, R499, R707, R425, Q999",
}


# ---------------------------------------------------------------------------------------------
# v2 (2026-11-20): leads with the buyer's outcome and the strongest numbers; the no-federal-
# performance disclosure stays, attached to the numbers it qualifies. Every figure is the founder's
# individual record from company_profile.md / CLAUDE.md. PRG has no federal contract performance
# and no variant may imply it does.
# ---------------------------------------------------------------------------------------------
PROOF = {
    "evac": ("25,000+", "evacuees through mass medical intake, a federal interagency operation run to CDC requirements"),
    "part": ("1,500+", "participants managed across multi-site NIH and industry research protocols"),
    "pm": ("98%", "preventive-maintenance and accreditation compliance on $2M+ of biomedical assets, to Joint Commission and DoD standards"),
    "flow": ("40%", "reduction in patient processing time through clinical workflow redesign"),
    "query": ("90%+", "of data queries resolved on time across multi-site studies"),
    "jama": ("4", "peer-reviewed JAMA publications"),
    "countries": ("3", "countries of field experience: Brazil, Peru and China"),
}

FOUNDER = {
    "name": "Andrew O'Donnell, Founder and Managing Director",
    "education": "MA, International Studies · BA, Classics",
    "certs": "ACRP-CP · ACRP-PM · AAMI CBET · NREMT · CPT-I · BLS/ACLS/PALS · PHTLS/TCCC",
    "record": "U.S. Air Force veteran (biomedical equipment, 4A2X5) · Level I trauma center · "
              "formal Honest Broker for clinical data systems · 4 JAMA publications",
}

DISCLOSURE = ("Founder track record: the individual experience of PRG's founder. PRG was established in 2026 "
              "and has no federal contract performance yet.")

ENGAGE = [
    ("Prime", "SDVOSB set-asides and sole-source awards"),
    ("Teammate or subcontractor", "SDVOSB participation for your team and subcontracting plan"),
    ("Mentor-protégé joint venture", "pairing a mentor's past performance with our certification"),
    ("Early engagement", "sources-sought and market-research responses, before the solicitation"),
]

DELIVER = ("PRG owns contract management, quality control, compliance and invoicing, and staffs each requirement "
           "with vetted personnel and specialty partners. A partner is named only under a written agreement.")

VARIANTS = {
    "general": {
        "file": "capstate_general",
        "title": "Capability Statement",
        "headline": "Veteran-owned operator for federal health, research and crisis programs",
        "tagline": "Clinical research · healthcare operations · crisis and international programs · analytics",
        "proof": ["evac", "part", "pm", "flow"],
        "pillars": [
            ("Clinical research operations", "Study coordination, recruitment and retention, GCP and regulatory compliance, and data management on multi-site NIH and industry protocols."),
            ("Healthcare operations and readiness", "Accreditation readiness, biomedical equipment programs, workflow redesign and performance measurement for VA, DoD and health systems."),
            ("Crisis, humanitarian and international programs", "Mass medical intake, evacuee operations and interagency coordination, with international program support grounded in an MA in International Studies."),
            ("Analytics and program management", "Dashboards, statistical analysis and executive reporting in SAS, SPSS, R and Python; REDCap, OnCore, Medidata, Epic and Cerner."),
        ],
        "naics_show": "541611, 541690, 541990, 541720, 624230",
    },
    "clinical_research": {
        "file": "capstate_541715_clinical_research",
        "title": "Capability Statement: Clinical and Population Health Research Support",
        "headline": "Veteran-owned research operations for federal clinical and population health studies",
        "tagline": "Site coordination · recruitment and retention · regulatory compliance · data management",
        "proof": ["part", "query", "jama", "flow"],
        "pillars": [
            ("Project management and site coordination", "Plans, schedules, milestones, site and subcontract coordination, and progress reporting to the sponsor."),
            ("Recruitment and retention", "Screening, enrollment, follow-up and retention tracking against protocol targets, including decentralized and hybrid studies."),
            ("Regulatory compliance and monitoring", "IRB submissions, informed consent, GCP record keeping, source verification, HIPAA and 21 CFR Part 11 practice."),
            ("Data collection, management and analysis", "REDCap, OnCore CTMS and Medidata; Honest Broker governance; SAS, SPSS, R and Python."),
        ],
        "naics_show": "541715 (small), 541714, 541720, 541690",
    },
    "healthcare_operations": {
        "file": "capstate_541611_healthcare_operations",
        "title": "Capability Statement: Healthcare Operations and Performance Improvement",
        "headline": "Veteran-owned program management for health system readiness and improvement",
        "tagline": "Assessment · measurement · training support · accreditation readiness · sustainment",
        "proof": ["pm", "flow", "evac", "part"],
        "pillars": [
            ("Program management", "Schedules, deliverables, risk tracking and a single point of contact for the facility."),
            ("Readiness and current-state assessment", "Clinical and administrative workflow review, baselines and gap analysis, to Joint Commission and DoD standards."),
            ("Performance measurement and reporting", "Outcome and process measures, dashboards, benefit validation and executive reporting."),
            ("Training support and sustainment", "Curricula packaging, job aids, standard work and sustainment materials; access and patient-flow improvement support."),
        ],
        "naics_show": "541611, 541618, 611430, 541990",
    },
    "nimhd": {
        "file": "capstate_nimhd_75N94027R00005",
        "title": "Capability Statement: NIMHD Population Health and Clinical Research",
        "headline": "Veteran-owned research operations for NIMHD population health and clinical research",
        "tagline": "Study coordination · site and subcontract management · recruitment and retention · compliance · data and statistics",
        "for_notice": "NIH NIMHD Division of Intramural Research, Sources Sought 75N94027R00005 (NAICS 541715)",
        "proof": ["part", "query", "evac", "jama"],
        "pillars": [
            ("Study coordination and project management", "Plans, schedules, milestones and progress reporting across multiple concurrent studies, with one accountable point of contact."),
            ("Site and subcontract management", "Coordination and oversight of research sites and subcontractors, with prime-level quality control on all work."),
            ("Recruitment and retention", "Screening, enrollment, follow-up and retention tracking against protocol targets, including decentralized and hybrid operations."),
            ("Regulatory compliance and site monitoring", "IRB submissions, informed consent, GCP record keeping, source verification, HIPAA and 21 CFR Part 11 practice."),
            ("Data management and statistical analysis", "REDCap, OnCore CTMS and Medidata; SAS, SPSS, R and Python; Honest Broker data governance."),
        ],
        "participation": "On a five-year multi-study requirement, PRG participates as a small-business team member or performs separable task areas as prime. It does not claim to perform the full scope alone; no partner is named until an agreement is signed.",
        "naics_show": "541715 (small), 541714, 541720, 541690",
    },
    "crisis_international": {
        "file": "capstate_crisis_international",
        "title": "Capability Statement: Crisis, Humanitarian and International Programs",
        "headline": "Veteran-owned operator for medical crisis response and international programs",
        "tagline": "Evacuee and refugee operations · emergency medicine · monitoring and evaluation · program management",
        "proof": ["evac", "part", "countries", "pm"],
        "pillars": [
            ("Mass medical operations", "High-throughput intake, screening, enrollment and case tracking for evacuee and refugee populations, with CDC and interagency coordination."),
            ("Emergency and crisis readiness", "Emergency medicine and trauma-care experience (NREMT, TCCC, PHTLS) applied to preparedness, surge planning and medical equipment readiness."),
            ("Monitoring, evaluation and analytics", "Study design, data collection, statistical analysis and reporting backed by clinical research and an MA in International Studies."),
            ("International program management", "Planning, staffing and oversight of overseas programs through vetted local partners, named only under written agreement. No in-country presence is claimed."),
        ],
        "naics_show": "624230, 541611, 541720, 541690",
    },
}


def _e(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def html(v):
    c = COMPANY
    logo = "data:image/png;base64," + base64.b64encode(open(LOGO, "rb").read()).decode() if os.path.exists(LOGO) else ""
    proof = "".join(f'<div class="stat"><b>{_e(PROOF[k][0])}</b><span>{_e(PROOF[k][1])}</span></div>' for k in v["proof"])
    pill = "".join(f'<div class="cap"><b>{_e(a)}</b>{_e(b)}</div>' for a, b in v["pillars"])
    eng = "".join(f'<div class="way"><b>{_e(a)}</b>{_e(b[0].upper() + b[1:])}</div>' for a, b in ENGAGE)
    notice = f'<p class="for">Prepared for {_e(v["for_notice"])}</p>' if v.get("for_notice") else ""
    f = FOUNDER
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{_e(c['name'])} {_e(v['title'])}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700;800&display=swap">
<style>
@page {{ size: Letter; margin: 0 }}
:root {{ --navy:#0B1F33; --navy2:#14365C; --blue:#1F6FBF; --ink:#1b2430; --muted:#55606e; --tint:#eef3f9; --line:#cfd8e3; --gold:#C9A227 }}
* {{ box-sizing: border-box }}
html, body {{ margin:0; padding:0 }}
body {{ font-family:"Public Sans", Inter, "Helvetica Neue", Arial, sans-serif; color:var(--ink); font-size:9.3pt; line-height:1.42;
  width:8.5in; height:11in; display:flex; flex-direction:column; -webkit-print-color-adjust:exact; print-color-adjust:exact }}
header {{ background:var(--navy); color:#fff; padding:0.25in 0.5in 0.2in; display:flex; gap:0.2in; align-items:center; border-bottom:3px solid var(--gold) }}
header img {{ width:0.7in; height:0.7in; border-radius:50%; background:#fff; padding:2px; flex:none }}
header .name {{ font-size:10pt; font-weight:600; letter-spacing:.12em; text-transform:uppercase; color:#a9c2e0 }}
header .head {{ font-size:15.5pt; font-weight:800; line-height:1.15; margin-top:3px }}
header .tag {{ font-size:8.7pt; color:#a9c2e0; margin-top:4px }}
header .badge {{ margin-left:auto; text-align:right; font-size:8.4pt; line-height:1.45; color:#dbe7f5; flex:none }}
header .badge b {{ display:block; font-size:9.6pt; color:#fff; font-weight:700 }}
.band {{ display:grid; grid-template-columns:repeat(4,1fr); background:var(--tint); border-bottom:1px solid var(--line) }}
.stat {{ padding:0.14in 0.16in 0.1in; border-right:1px solid var(--line) }}
.stat:last-child {{ border-right:0 }}
.stat b {{ display:block; font-size:21pt; font-weight:800; color:var(--navy2); line-height:1 }}
.stat span {{ display:block; font-size:7.7pt; line-height:1.3; color:var(--muted); margin-top:3px }}
.disc {{ font-size:7.6pt; color:var(--muted); padding:5px 0.5in 6px; border-bottom:1px solid var(--line); font-style:italic }}
main {{ flex:1; display:grid; grid-template-columns: 1fr 2.3in; min-height:0 }}
.body {{ padding:0.2in 0.3in 0.12in 0.5in }}
aside {{ background:var(--tint); padding:0.2in 0.34in 0.12in 0.26in; border-left:1px solid var(--line) }}
h2 {{ font-size:8.6pt; letter-spacing:.09em; text-transform:uppercase; color:var(--navy2); margin:0 0 5px; padding-bottom:3px; border-bottom:1.5px solid var(--blue); font-weight:700 }}
.body h2:not(:first-child), aside h2:not(:first-child) {{ margin-top:12px }}
p {{ margin:0 0 5px }}
.cap {{ margin:0 0 6px }}
.cap b {{ display:block; color:var(--navy2); font-weight:700 }}
.ways {{ display:grid; grid-template-columns:1fr 1fr; gap:6px 14px }}
.way b {{ display:block; color:var(--navy2); font-weight:700 }}
.way {{ font-size:8.9pt }}
.for {{ font-weight:600; color:var(--navy2) }}
.fnd b {{ color:var(--navy2) }}
.fnd div {{ margin-bottom:3px }}
dl {{ margin:0 }}
dt {{ font-size:7.2pt; letter-spacing:.07em; text-transform:uppercase; color:var(--muted); font-weight:600; margin-top:6px }}
dt:first-child {{ margin-top:0 }}
dd {{ margin:1px 0 0; font-size:8.6pt; overflow-wrap:anywhere }}
footer {{ background:var(--navy2); color:#dbe7f5; font-size:8.2pt; padding:0.08in 0.5in; display:flex; justify-content:space-between; gap:12px }}
</style></head><body>
<header>{f'<img src="{logo}" alt="">' if logo else ''}
<div><div class="name">{_e(c['name'])}</div><div class="head">{_e(v['headline'])}</div><div class="tag">{_e(v['tagline'])}</div></div>
<div class="badge"><b>SBA-certified SDVOSB</b>UEI {c['uei']}<br>CAGE {c['cage']}</div></header>
<div class="band">{proof}</div>
<div class="disc">{_e(DISCLOSURE)}</div>
<main><div class="body">
{notice}<h2>What we do</h2>{pill}
<h2>How PRG works with you</h2><div class="ways">{eng}</div><p style="margin-top:6px">{_e(v.get("participation", DELIVER))}</p>
<h2>Founder</h2><div class="fnd"><div><b>{_e(f['name'])}</b></div><div><b>Education:</b> {_e(f['education'])}</div><div><b>Credentials:</b> {_e(f['certs'])}</div><div>{_e(f['record'])}</div></div>
</div><aside>
<h2>Company data</h2><dl>
<dt>Unique Entity ID</dt><dd>{c['uei']}</dd>
<dt>CAGE code</dt><dd>{c['cage']}</dd>
<dt>SAM.gov registration</dt><dd>{_e(c['sam'])}</dd>
<dt>Certification</dt><dd>{_e(c['cert'])}</dd>
<dt>Business size</dt><dd>Small business</dd>
<dt>Primary NAICS</dt><dd>{c['naics_primary']}</dd>
<dt>Relevant NAICS</dt><dd>{_e(v.get('naics_show', '541611, 541690, 541990'))}</dd>
<dt>PSC</dt><dd>{_e(c['psc'])}</dd></dl>
<h2>Contact</h2><dl>
<dt>Point of contact</dt><dd>{_e(c['poc'])}</dd>
<dt>Phone</dt><dd>{c['phone']}</dd>
<dt>Email</dt><dd style="font-size:8pt;white-space:nowrap">{c['email']}</dd>
<dt>Web</dt><dd>{c['web']}</dd>
<dt>Address</dt><dd>{_e(c['address'])}</dd></dl>
</aside></main>
<footer><span>{_e(c['name'])} · {c['phone']} · {c['email']}</span><span>UEI {c['uei']} · CAGE {c['cage']}</span></footer>
</body></html>"""


def markdown(v):
    c = COMPANY; f = FOUNDER
    L = [f"# {c['name']} — {v['title']}", "", f"**{v['headline']}**", "",
         f"**SBA-certified SDVOSB / VOSB** | UEI {c['uei']} | CAGE {c['cage']} | {c['poc']}, {c['phone']}, {c['email']}", ""]
    if v.get("for_notice"):
        L += [f"Prepared for {v['for_notice']}", ""]
    L += ["## Track record at a glance"] + [f"- **{PROOF[k][0]}** {PROOF[k][1]}" for k in v["proof"]] + ["", f"*{DISCLOSURE}*", "", "## What we do"]
    L += [f"- **{a}:** {b}" for a, b in v["pillars"]]
    L += ["", "## How PRG works with you"] + [f"- **{a}:** {b}" for a, b in ENGAGE] + ["", DELIVER, "", "## Founder",
          f"**{f['name']}**", f"- Education: {f['education']}", f"- Credentials: {f['certs']}", f"- {f['record']}", "",
          "## Company data", f"- SAM.gov registration: {c['sam']}", f"- Certification: {c['cert']}",
          f"- Primary NAICS {c['naics_primary']}; all NAICS on the SAM registration: {c['naics']}", f"- PSC {c['psc']}",
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
