#!/usr/bin/env python3
"""Render the Stanford RPM tailored resume to a clean professional PDF.

PAGINATION RULES (do not regress):
- A job/entry header must NEVER appear at the bottom of a page separated
  from its bullets: the header is glued to its first bullet via KeepTogether.
- A section header + underline rule must NEVER be orphaned: they are glued
  to the section's first content flowable via KeepTogether.
- Bullet lists may break between bullets, never mid-bullet-from-header.
"""
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

# Embed real fonts so viewers never substitute a slanted/oblique lookalike.
# Liberation Sans is metrically compatible with Helvetica/Arial.
_FDIR = "/usr/share/fonts/truetype/liberation"
pdfmetrics.registerFont(TTFont("LiberationSans", f"{_FDIR}/LiberationSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("LiberationSans-Bold", f"{_FDIR}/LiberationSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("LiberationSans-Italic", f"{_FDIR}/LiberationSans-Italic.ttf"))
pdfmetrics.registerFont(TTFont("LiberationSans-BoldItalic", f"{_FDIR}/LiberationSans-BoldItalic.ttf"))
pdfmetrics.registerFontFamily("LiberationSans", normal="LiberationSans",
                              bold="LiberationSans-Bold", italic="LiberationSans-Italic",
                              boldItalic="LiberationSans-BoldItalic")

DARK = HexColor("#1a1a1a")
RULE = HexColor("#444444")

styles = {
    "name": ParagraphStyle("name", fontName="LiberationSans-Bold", fontSize=16,
                           leading=19, alignment=TA_CENTER, textColor=DARK,
                           spaceAfter=2),
    "contact": ParagraphStyle("contact", fontName="LiberationSans", fontSize=9,
                              leading=12, alignment=TA_CENTER, textColor=DARK,
                              spaceAfter=2),
    "headline": ParagraphStyle("headline", fontName="LiberationSans-Bold", fontSize=11,
                               leading=14, alignment=TA_CENTER, textColor=DARK,
                               spaceBefore=4, spaceAfter=4),
    "section": ParagraphStyle("section", fontName="LiberationSans-Bold", fontSize=10.5,
                              leading=13, textColor=DARK, spaceBefore=10,
                              spaceAfter=1),
    "body": ParagraphStyle("body", fontName="LiberationSans", fontSize=9.2,
                           leading=12.2, alignment=TA_JUSTIFY, textColor=DARK,
                           spaceAfter=3),
    "jobtitle": ParagraphStyle("jobtitle", fontName="LiberationSans", fontSize=9.4,
                               leading=12.4, textColor=DARK, spaceBefore=6,
                               spaceAfter=2),
    "bullet": ParagraphStyle("bullet", fontName="LiberationSans", fontSize=9.2,
                             leading=12.0, alignment=TA_JUSTIFY, textColor=DARK),
    "edu": ParagraphStyle("edu", fontName="LiberationSans", fontSize=9.2,
                          leading=12.4, textColor=DARK, spaceAfter=2),
}

for _s in styles.values():
    _s.bulletFontName = "LiberationSans"


def one_bullet(text, space_after=1.5):
    return ListFlowable(
        [ListItem(Paragraph(text, styles["bullet"]), leftIndent=14)],
        bulletType="bullet", start="•", bulletFontSize=9.2, bulletFontName="LiberationSans",
        leftIndent=14, spaceBefore=0, spaceAfter=space_after,
    )


def section(story, title, first_flowables):
    """Section header + rule glued to the section's first content."""
    header = [
        Paragraph(f"<b>{title}</b>", styles["section"]),
        HRFlowable(width="100%", thickness=0.8, color=RULE,
                   spaceBefore=1, spaceAfter=4),
    ]
    flat = []
    for f in first_flowables:
        if isinstance(f, KeepTogether):
            flat.extend(f._content)
        else:
            flat.append(f)
    story.append(KeepTogether(header + flat))


def job(story, title, items, first=False):
    """Job header glued to its first bullet; remaining bullets may flow.

    Returns the flowables when first=True so the caller can glue them into
    the section header group instead of appending directly.
    """
    head = KeepTogether([Paragraph(title, styles["jobtitle"]), one_bullet(items[0])])
    rest = [one_bullet(t) for t in items[1:]]
    if first:
        return [head] + rest[:0], rest  # glue only header+first bullet to section
    story.append(head)
    story.extend(rest)
    return None


story = []
story.append(Paragraph("Andrew O'Donnell", styles["name"]))
story.append(Paragraph(
    "Los Angeles, CA | aodhan.o@outlook.com | 650.213.2381 | linkedin.com/in/andrewdavidodonnell/",
    styles["contact"]))
story.append(Paragraph("SPONSORED RESEARCH OPERATIONS PROFESSIONAL", styles["headline"]))

story.append(Paragraph(
    "Research operations professional with 8+ years of experience, including 4+ years within the Stanford "
    "University School of Medicine supporting sponsored projects funded by NIH and industry sponsors. Direct "
    "experience partnering with principal investigators, sponsors, and CROs on the regulatory, administrative, "
    "and financial dimensions of funded clinical trials, including budgeting, billing, and feasibility management; "
    "interpretation of protocol, institutional, and sponsor requirements; and sustained audit readiness under "
    "FDA regulations (21 CFR) and ICH GCP. ACRP-Certified Project Manager with a record of advising and "
    "training research staff, driving process improvement, and communicating complex compliance requirements "
    "clearly to faculty-led teams.", styles["body"]))

section(story, "CORE COMPETENCIES", [Paragraph(
    "Sponsored Project Operations (Federal &amp; Industry) | Pre-Award Support: Budgeting &amp; Feasibility | "
    "Post-Award Support: Billing, Compliance &amp; Audit Readiness | Principal Investigator &amp; Sponsor Liaison | "
    "Policy &amp; Protocol Interpretation | Regulatory Compliance (FDA 21 CFR, ICH GCP, HIPAA, Human Subjects "
    "Protections) | Clinical Trial Management | Process Improvement | Cross-Functional Team Coordination | "
    "Staff Training, Onboarding &amp; Mentoring | Analytical &amp; Written Communication | Data Quality &amp; "
    "Query Resolution", styles["body"])])

section(story, "TECHNICAL SKILLS", [Paragraph(
    "<b>Research Systems:</b> CTMS - OnCore, Oracle Siebel | EDC - Medidata Rave, REDCap | eTMF | eConsent | "
    "ePRO/eCOA | Epic | IRT | Cerner | Safety Reporting - AE/SAE, CTCAE", styles["body"])])
story.append(Paragraph(
    "<b>Analytics &amp; Reporting:</b> Excel (Advanced Functions) | SAS | SPSS | R | Python | Smartsheet",
    styles["body"]))
story.append(Paragraph(
    "<b>Collaboration:</b> Microsoft Office Suite | Teams | Zoom | Slack | Adobe Acrobat Sign | SharePoint | "
    "Box | DocuSign | Jira | Confluence | Google Workspace", styles["body"]))

stanford_bullets = [
    "Served as liaison between principal investigators, sponsors, and CROs on regulatory, "
    "administrative, and financial matters across concurrent NIH (federally sponsored) and industry clinical "
    "trials (Phase II-IV), supporting seamless trial execution and audit readiness.",
    "Supported budgeting, billing, and feasibility management for funded studies, applying university, "
    "hospital, and sponsor requirements to financial and operational decisions.",
    "Interpreted and explained protocol, institutional, and sponsor requirements to study teams and served as "
    "the escalation point for study procedures and documentation standards.",
    "Ensured regulatory compliance for multi-site NIH-sponsored projects under ICH GCP and FDA regulations "
    "(21 CFR); maintained HIPAA-compliant consent processes as designated Honest Broker for Gilead "
    "GS-US-685-6819, working directly with trial leadership.",
    "Served as day-to-day lead supervising junior staff members.",
    "Drove process improvement in data operations: optimized REDCap/OnCore databases with validation rules, "
    "queries, and dashboards, achieving 90%+ on-time query resolution; executed clinical operations for "
    "1,500+ participants with the site consistently ranked among the top enrollment sites nationally.",
]
stanford_title = ("<b>Clinical Research Coordinator Associate</b> | Stanford University Department of "
                  "Medicine, Palo Alto, CA | Nov 2021 - Feb 2026")
section(story, "EXPERIENCE",
        [KeepTogether([Paragraph(stanford_title, styles["jobtitle"]),
                       one_bullet(stanford_bullets[0])])])
story.extend(one_bullet(t) for t in stanford_bullets[1:])

job(story,
    "<b>Technical Operations Manager (Contract)</b> | International SOS (Iqarus), Fort Lee, VA | "
    "Aug 2021 - Sep 2021",
    [
        "Led biomedical operations at the first U.S. haven site for Operation Allies Welcome, coordinating "
        "with Army Public Health and federal interagency partners to achieve 100% compliance with CDC "
        "vaccination and screening requirements for 25K+ evacuees.",
        "Redesigned high-throughput COVID-19 testing and vaccination workflows, cutting average processing "
        "time per patient from 30 to approximately 18 minutes (40% faster), and trained staff and interagency "
        "partners on the new workflows.",
        "Supervised biomedical and technical personnel across daily shift operations, directing task "
        "assignment, readiness, and escalation of clinical support issues.",
    ])

job(story,
    "<b>Healthcare Technology Manager | 4A2x5</b> | U.S. Air Force, Various Locations | "
    "Sep 2017 - Sep 2025, ADT - Reserve",
    [
        "Maintained 98%+ preventive-maintenance compliance across 200+ biomedical devices valued at $2M+, "
        "sustaining Joint Commission and DoD accreditation readiness.",
        "Led HTM for the 752nd Medical Squadron during Global Medic 2019, supervising 6 biomedical personnel "
        "and ensuring operational readiness of mobile medical infrastructure in a multinational mass-casualty "
        "exercise.",
        "Supervised and trained airmen in equipment maintenance and safety procedures, building "
        "cross-disciplinary teams and achieving zero equipment-related incidents.",
    ])

job(story,
    "<b>Emergency Department Technician | RCET</b> | Children's Hospital of Orange County, Santa Ana, CA | "
    "Jan 2018 - Oct 2021",
    [
        "Delivered frontline care in a top-ranked Level I pediatric trauma center across 20K+ annual "
        "emergency encounters; precepted and trained new emergency department technicians.",
    ])

cert_bullets = [
    "Association of Clinical Research Professionals - Project Manager (ACRP-PM), Certified Professional (ACRP-CP)",
    "CITI Good Clinical Practice (GCP) | HIPAA | Aerosol Transmissible Diseases | DOT Shipping",
    "Google Advanced Data Analytics | Stanford Online AI in Healthcare | Interprofessional Healthcare Informatics",
    "AAMI Certified Biomedical Equipment Technician (CBET)",
    "NREMT Registry No. E3767060 | CPT I Registry No. CPT 02270029 | American Heart Association BLS, ACLS, PALS",
]
section(story, "LICENSES AND CERTIFICATIONS", [one_bullet(cert_bullets[0])])
story.extend(one_bullet(t) for t in cert_bullets[1:])

pub_bullets = [
    "JAMA. 2023. Higher-dose fluvoxamine and time to sustained recovery in outpatients with COVID-19: The "
    "ACTIV-6 randomized clinical trial. ClinicalTrials.gov: NCT04885530.",
    "JAMA. 2024. Nirmatrelvir-ritonavir and symptoms in adults with post-acute sequelae of SARS-CoV-2 "
    "infection: The STOP-PASC randomized clinical trial. ClinicalTrials.gov: NCT05576662.",
    "JAMA Network Open. 2024. Effect of montelukast versus placebo on time to sustained recovery in "
    "outpatients with COVID-19: The ACTIV-6 randomized clinical trial. ClinicalTrials.gov: NCT04885530.",
    "JAMA Internal Medicine. 2025. Metformin and time to sustained recovery in adults with COVID-19: The "
    "ACTIV-6 randomized clinical trial. ClinicalTrials.gov: NCT04885530.",
]
section(story, "PUBLICATIONS", [
    Paragraph("Contributor to four peer-reviewed publications from federally and industry-sponsored trials:",
              styles["body"]),
    one_bullet(pub_bullets[0]),
])
story.extend(one_bullet(t) for t in pub_bullets[1:])

section(story, "EDUCATION", [KeepTogether([
    Paragraph("<b>MA, International Studies</b> | Chapman University, Orange, CA", styles["edu"]),
    Paragraph("Graduate Fellowship Award (2x) | Sigma Iota Rho Honor Society", styles["edu"]),
])])
story.append(KeepTogether([
    Paragraph("<b>BA, Classics</b> | California State University Long Beach, Long Beach, CA", styles["edu"]),
    Paragraph("Eta Sigma Phi Honor Society", styles["edu"]),
]))
story.append(Paragraph(
    "<b>Certificate in Pre-Medicine and General Sciences with Distinction</b> | UCLA Extension, Los Angeles, CA",
    styles["edu"]))

out = "/home/user/Pacific-Research-LLC-Website/tailored/ODonnell_Andrew_Resume_Stanford_RPM_200255.pdf"
doc = SimpleDocTemplate(out, pagesize=letter,
                        leftMargin=0.65 * inch, rightMargin=0.65 * inch,
                        topMargin=0.55 * inch, bottomMargin=0.55 * inch,
                        title="Andrew O'Donnell - Resume",
                        author="Andrew O'Donnell")
doc.build(story)
print("written:", out)
