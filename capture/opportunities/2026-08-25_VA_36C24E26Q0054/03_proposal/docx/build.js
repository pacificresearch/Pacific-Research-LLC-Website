const {Document, Packer, Paragraph, TextRun, AlignmentType, HeadingLevel, Table, TableRow, TableCell, WidthType, BorderStyle} = require('docx');
const fs = require('fs');

const FONT = "Times New Roman", SIZE = 24; // 12pt = 24 half-points
const P = (text, opts={}) => new Paragraph({
  alignment: opts.center ? AlignmentType.CENTER : AlignmentType.LEFT,
  spacing: {after: opts.tight ? 60 : 160},
  children: [new TextRun({text, font: FONT, size: SIZE, bold: !!opts.bold, italics: !!opts.i})]
});
const H = (text) => new Paragraph({spacing: {before: 240, after: 120}, children: [new TextRun({text, font: FONT, size: SIZE, bold: true})]});
const BULL = (text) => new Paragraph({bullet: {level: 0}, spacing: {after: 80}, children: [new TextRun({text, font: FONT, size: SIZE})]});
const PAGE = {size: {width: 12240, height: 15840}}; // US Letter, default 1" margins

function doc(children) {
  return new Document({sections: [{properties: {page: PAGE}, children}]});
}
async function save(d, name) {
  const buf = await Packer.toBuffer(d);
  fs.writeFileSync(name, buf);
  console.log("wrote", name);
}

const CO_HEADER = (section, redacted) => [
  P(`Solicitation 36C24E26Q0054 — Good Clinical Practice (GCP) Clinical Research Quality Associate (CRQA) Monitoring Services`, {center:true, bold:true}),
  P(section, {center:true, bold:true}),
  P(redacted ? "" : "Pacific Research Group LLC · UEI J585TLDV1CH1 · CAGE 1Z9B6", {center:true, tight:true}),
];

const name = (r) => r ? "[OFFEROR]" : "Pacific Research Group LLC";
const lead = (r) => r ? "the proposed Lead CRQA" : "Andrew O'Donnell, Managing Director";

// ---- Certifying Statement (S2 + S3 redacted) ----
async function certifying(redacted) {
  const sec = redacted ? "Section 3 Redacted Certifying Statement" : "Section 2 Certifying Statement";
  const d = doc([
    ...CO_HEADER(sec, redacted),
    P(""),
    P("CERTIFYING STATEMENT", {center:true, bold:true}),
    P(""),
    P(`${name(redacted)} hereby certifies that all employees, contractors, and subcontractor personnel performing under any contract resulting from solicitation 36C24E26Q0054 will, for the entire life of the contract including all option periods, hold the same or better qualifications and certifications as those proposed in the technical quote, including without limitation the qualifications specified in Performance Work Statement section 7.3 (degree, licensure, or ACRP certification; documented Good Clinical Practice training; and documented clinical research monitoring and human subjects protection training). Any personnel added during contract performance will meet or exceed these same standards and will be submitted with supporting documentation for Government review prior to performing work.`),
    P(""),
    P("Signature: _________________________________"),
    P(redacted ? "[Authorized Representative]" : "Andrew O'Donnell, Managing Director"),
    P("Date: ____________________"),
    ...(redacted ? [] : [P("UEI J585TLDV1CH1 · CAGE 1Z9B6", {tight:true})]),
  ]);
  await save(d, sec.replaceAll(" ", "_") + ".docx");
}

// ---- QA Plan (S2 + S3) ----
async function qaplan(redacted) {
  const sec = redacted ? "Section 3 Redacted QA Plan" : "Section 2 QA Plan";
  const d = doc([
    ...CO_HEADER(sec, redacted),
    H("1. Purpose and Alignment"),
    P(`This draft Quality Assurance Plan governs CRQA monitoring services under solicitation 36C24E26Q0054. It aligns to the Performance Work Statement and QASP, SMART Standard Operating Procedures and Approved Methods and Procedures, and ICH E6(R2). The objective is that every visit is executed to the study-specific CRQA Monitoring Plan and every deliverable is audit-ready on first submission.`),
    H("2. Quality Standards and Targets"),
    BULL("Visit conduct: 100% adherence to the CRQA Monitoring Plan and SMART SOPs."),
    BULL("Routine visit report and investigator summary: delivered within 10 calendar days of the last visit day, 100% on time."),
    BULL("Report quality: complete, accurate, audit-ready; at least 95% accepted without rework; 100% reviewed by the Lead CRQA before release during the base year."),
    BULL("Monitor credentials: PWS 7.3 documentation current for every monitor, tracked with 90-day advance expiration alerts."),
    BULL("Scheduling: visits confirmed through SMART-designated channels; changes documented per PWS 6.2.3.2."),
    H("3. Quality Control Method"),
    P("Pre-visit: checklist verification that credentials are current, the monitoring plan and prior findings are reviewed, and site logistics are confirmed. In-visit: standardized working papers per SMART AMPs. Post-visit: Lead CRQA review of 100% of reports before submission during the base year; sampling relaxes only with Government concurrence. Monthly internal trend review of findings, timeliness, and site feedback, with corrective actions logged with owner and due date."),
    H("4. Deficiency Handling"),
    P(`Any missed standard receives root-cause analysis within 5 business days, a corrective action, and verification at the next deliverable. Repeat deficiencies escalate to ${redacted ? "executive management" : "the Managing Director"} with a process change. The Government hears of any at-risk deliverable from ${name(redacted)} first, before the due date.`),
    H("5. Records"),
    P("Visit files, reports, credential documentation, and QC checklists are retained per VHA Directive 1907.01 and CSP/SMART records requirements and are available to the Government on request."),
  ]);
  await save(d, sec.replaceAll(" ", "_") + ".docx");
}

// ---- Staffing Plan (S2 + S3) — 2 page limit ----
async function staffing(redacted) {
  const sec = redacted ? "Section 3 Redacted Staffing Plan" : "Section 2 Staffing Plan";
  const d = doc([
    ...CO_HEADER(sec, redacted),
    H("1. Staffing Model"),
    P(`${name(redacted)} staffs this requirement with a two-tier structure sized to SMART's stated workload of 8 to 12 actively monitored trials per year within a 25-trial portfolio.`),
    BULL(`Primary CRQA: [CANDIDATE NAME — CCRA-certified; contingent offer executed; certificates enclosed in Qualification Support Docs]${redacted ? " [redact name]" : ""}. Performs monitoring visits from the first task order.`),
    BULL(`Second monitor and single point of accountability: ${lead(redacted)} — ACRP-certified with documented GCP, human subjects protection, and clinical monitoring training [course certificate enclosed], and extensive site-side GCP operations experience across multi-site federal (NIH) and industry protocols. Quality-reviews every deliverable before release and serves as escalation and scheduling POC.`),
    BULL("Credential-verified bench: an active national recruiting pipeline (public careers page and national job boards) with 70+ applicants to date, screened against PWS 7.3 as the application gate; additional monitors are engaged as task-order volume requires."),
    H("2. Task-Order Response (PWS 4.2 — 30 days)"),
    P("Days 0–3: confirm scope and monitoring plan. Days 3–10: match monitor(s) from the bench and verify credential currency. Days 10–20: trial-specific onboarding (protocol, operations manual, SMART SOPs/AMPs). Days 20–30: readiness check by the Lead reviewer and submission of monitor identification with full PWS 7.3 documentation to SMART."),
    H("3. Continuity and Quality of Staffing"),
    BULL("Credential expiration tracking with 90-day alerts; no monitor performs with lapsed credentials, consistent with the Certifying Statement."),
    BULL("A cross-briefed backup monitor is designated for each active study, with a documented handover protocol for any transition."),
    BULL("VA credentialing and PIV processing initiated at assignment and tracked to completion before the first site visit."),
    BULL(`Limitations on subcontracting (VAAR 852.219-75): W2 monitors${redacted ? "" : " and any similarly-situated SDVOSB subcontractors"} constitute the required performance share, tracked each invoice period.`),
  ]);
  await save(d, sec.replaceAll(" ", "_") + ".docx");
}

// ---- Section 4 GFP ----
async function gfp() {
  const d = doc([
    ...CO_HEADER("Section 4 Government Property", false),
    H("1. Government Property Proposed for Rent-Free Use"),
    P("None. Pacific Research Group LLC will perform using contractor-furnished equipment. Remote monitoring activities use Government-provided system access (accounts and remote connectivity) as directed by SMART, which constitutes access rather than accountable Government property."),
    H("2. Dates of Use"),
    P("Not applicable; no Government property is requested."),
    H("3. Property Management System and Practices"),
    P("Notwithstanding the above, PRG maintains a property management practice aligned to the principles of FAR 52.245-1 and customary commercial practice (ASTM E2452): item identification and records, physical control, reporting of loss or damage within 24 hours, and return or disposition per Contracting Officer direction. These practices apply to any Government access credentials, tokens, or property incidentally furnished during performance."),
  ]);
  await save(d, "Section_4_Government_Property.docx");
}

// ---- Section 6 Past Performance (neutral) ----
async function pastperf() {
  const d = doc([
    ...CO_HEADER("Section 6 Past Performance", false),
    P(""),
    P("Pacific Research Group LLC was recently established and has not yet performed Federal contracts as an entity; accordingly, PRG has no entity-level past performance references to provide and respectfully requests treatment consistent with FAR 15.305(a)(2)(iv), under which an offeror without a record of relevant past performance may not be evaluated favorably or unfavorably on this factor."),
    P("In lieu of contract references, PRG offers the following objective, independently verifiable evidence of the proposed monitoring team's delivery of clinical research operations and GCP-governed trial support for federally funded and industry-sponsored research:"),
    BULL("[JAMA CITATION 1 — authors, title, JAMA, year, DOI]"),
    BULL("[JAMA CITATION 2]"),
    BULL("[JAMA CITATION 3]"),
    BULL("[JAMA CITATION 4]"),
    BULL("Management of operational data for more than 1,500 participants across multi-site federal (NIH) and industry protocols, including at the Stanford University Department of Medicine."),
    BULL("Formal service as an “Honest Broker” for pharmaceutical clinical systems data governance."),
    P("The proposed monitors' qualifications and certifications (ACRP; GCP; human subjects protection; clinical monitoring training) are documented in Section 2 Qualification Support Docs."),
  ]);
  await save(d, "Section_6_Past_Performance.docx");
}

// ---- Section 1 Administrative ----
async function admin() {
  const d = doc([
    ...CO_HEADER("Section 1 Administrative", false),
    H("1. Representations and Certifications"),
    P("Pacific Research Group LLC's representations and certifications are complete and current in the System for Award Management (SAM.gov) under UEI J585TLDV1CH1 (CAGE 1Z9B6). Registration status: Active. PRG is an SBA-certified Service-Disabled Veteran-Owned Small Business."),
    H("2. Acknowledgment of Amendments"),
    P("Signed SF30 first pages acknowledging Amendment 0001 and Amendment 0002 are enclosed with this section as separate attachments. [ATTACH: signed SF30 page 1 for each amendment]"),
    H("3. Unique Entity Identifier"),
    P("UEI: J585TLDV1CH1. PRG is registered in SAM at time of quote submission and will maintain active registration through award, in accordance with the solicitation."),
    H("4. VAAR 852.219-75 — VA Notice of Limitations on Subcontracting: Certificate of Compliance"),
    P("The entire clause with all offeror fill-ins completed, including insertion of “Pacific Research Group LLC” in the [Insert Name of Offeror] brackets, is enclosed with this section as a separate attachment. [ATTACH: completed 852.219-75 certificate — REJECTION IF INCOMPLETE]"),
    H("5. Point of Contact"),
    P("Andrew O'Donnell, Managing Director · Andrew@pacificresearchllc.com · (650) 213-2381"),
  ]);
  await save(d, "Section_1_Administrative.docx");
}

(async () => {
  await certifying(false); await certifying(true);
  await qaplan(false); await qaplan(true);
  await staffing(false); await staffing(true);
  await gfp(); await pastperf(); await admin();
})();
