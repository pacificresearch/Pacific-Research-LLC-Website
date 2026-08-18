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
    BULL("Site visit report, Summary for Investigator, attachments, and supporting documents: delivered to the SMART PM group within seven business days of the last day on site (PWS 5.1.5.2), 100% on time; rework at no cost to the Government."),
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
    BULL(`Named CRQA monitor(s): [MONITOR NAME(S) — senior CRQA(s), each meeting every PWS 7.3 element: 7.3.2 credential (degree/licensure/CCRA), documented GCP training (7.3.3), monitoring/HSP training or CCRA (7.3.4), 10+ years GCP clinical-trial monitoring of research sites (7.3.5), and 5+ years monitoring/auditing federally funded research (7.3.6) with the trial-by-trial listing at 7.3.6.1; contingent offer executed; full documentation enclosed in Qualification Support Docs]${redacted ? " [redact names]" : ""}. Performs monitoring visits from the first task order.`),
    BULL(`Program management and single point of accountability: ${lead(redacted)} — ACRP-certified with documented GCP and human subjects protection training and extensive site-side GCP clinical research operations experience across multi-site federal (NIH) and industry protocols. Manages scheduling, credential currency, deliverable timeliness tracking, and escalation; administrative quality review (completeness, format, grammar, timeliness) of deliverables before release. Monitoring findings and reports are authored and owned by the named CRQA monitors.`),
    BULL("Credential-verified bench: an active national recruiting pipeline (public careers page and national job boards) with 70+ applicants to date, screened against the full PWS 7.3 qualification set as the application gate; additional qualified monitors are engaged as task-order volume requires."),
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
    P("Per the solicitation (Attachment 2 Section VI; PWS 7.3.6.2; Q&A #11), the references below cover the proposed monitor's delivery of GCP monitoring and auditing services for federally funded research. The Government will contact references directly; no narratives are provided. Only the first three references are listed."),
    H("Reference 1 — [Proposed monitor's federal monitoring engagement]"),
    P("[Organization / trial sponsor and funding source (e.g., NIH institute, VA) · POC name, title, email, phone · Contract/study identifier · Period of performance · Scope: # sites monitored, visit types and frequency, duration — from the HIRED monitor's own engagement history]"),
    H("Reference 2 — [Proposed monitor's federal monitoring engagement]"),
    P("[Same fields]"),
    H("Reference 3 — [Proposed monitor's federal monitoring engagement]"),
    P("[Same fields]"),
    H("Offeror entity statement"),
    P("Pacific Research Group LLC was recently established and has not yet performed Federal contracts as an entity; to the extent entity-level past performance is considered separately from the referenced monitor experience above, PRG respectfully requests treatment consistent with FAR 15.305(a)(2)(iv), under which an offeror without a record of relevant past performance may not be evaluated favorably or unfavorably. As additional objective, independently verifiable evidence of the team's clinical research operations delivery: co-authorship on four peer-reviewed JAMA publications arising from multi-site trials supported operationally by PRG's Managing Director [JAMA CITATIONS 1–4 — authors, title, year, DOI]; management of operational data for more than 1,500 participants across multi-site federal (NIH) and industry protocols; and formal service as an “Honest Broker” for pharmaceutical clinical systems data governance."),
    P("The proposed monitors' qualifications and certifications are documented in Section 2 Qualification Support Docs."),
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

// ---- Section 2 Technical narrative (S2 + S3 redacted) — 10-pg limit incl cover + TOC ----
async function technical(redacted) {
  const sec = redacted ? "Section 3 Redacted Technical" : "Section 2 Technical";
  const who = name(redacted);
  const pb = new Paragraph({children: [], pageBreakBefore: true});
  const d = doc([
    // Cover (1 pg — labels only, no narrative)
    P("", {}), P("", {}), P("", {}),
    P("Quote — Solicitation 36C24E26Q0054", {center:true, bold:true}),
    P("Good Clinical Practice (GCP) Clinical Research Quality Associate (CRQA) Monitoring Services", {center:true, bold:true}),
    P(sec, {center:true, bold:true}),
    P(redacted ? "" : "Pacific Research Group LLC · UEI J585TLDV1CH1 · CAGE 1Z9B6", {center:true}),
    new Paragraph({children: [], pageBreakBefore: true}),
    // TOC (1 pg — headings only)
    P("Table of Contents", {bold:true}),
    P("1. Understanding of the Requirement", {tight:true}),
    P("2. Technical Approach — General Scope (PWS 4.0)", {tight:true}),
    P("3. Task 1 — CRQA Visits with Pre- and Post-Work (PWS 5.1; CLIN x001)", {tight:true}),
    P("4. Task 2 — CRQA Visits without Pre- and Post-Work (PWS 5.2; CLIN x001)", {tight:true}),
    P("5. Task 3 — GCP Program Quality Support (PWS 5.3; CLIN x002)", {tight:true}),
    P("6. Deliverables and Timeliness (PWS 5.4)", {tight:true}),
    P("7. Qualifications and Experience (PWS 7.0)", {tight:true}),
    new Paragraph({children: [], pageBreakBefore: true}),
    // 1. Understanding
    H("1. Understanding of the Requirement"),
    P(`The VA Cooperative Studies Program's Site Monitoring, Auditing and Resource Team (SMART), co-located with the CSP Clinical Research Pharmacy Coordinating Center in Albuquerque, safeguards GCP compliance across a portfolio of ongoing multi-site trials — more than 15 protocols actively monitored, spanning therapeutic areas from Alzheimer's disease to urinary tract infection — conducted at VA and affiliated facilities. This requirements contract supplements SMART's authorized staffing with qualified contract CRQAs who execute study-specific monitoring plans developed by the Chief of Monitoring: site initiation and routine visits delivered on-site (with portal-to-portal travel) or as virtual equivalents, off-site review of key critical data, and GCP Program Quality Support (PQS), all under SMART SOPs and Approved Methods and Procedures (AMPs).`),
    P(`${who} understands success is measured not by visits completed but by audit-ready documentation: findings communicated to the SMART study lead immediately upon discovery when serious, reports delivered within seven business days of the last day on site, and corrective actions driven to documented closure. We also understand the operational realities — an estimated 3:1 off-site/on-site visit mix that shifts with each study's monitoring plan and FDA-regulated status, schedules set by SMART leadership, VA credentialing and NACI background investigation requirements governing access, and monitors who must arrive fluent in each trial's protocol, operations manual, and the full reference set in PWS 3.0 (ICH E6(R2), 45 CFR 46, 38 CFR 16, 21 CFR 312/812, FDA Form 1572 requirements, CSP Investigator Guidelines, CSP global SOPs, and SMART SOPs/AMPs).`),
    // 2. General scope
    H("2. Technical Approach — General Scope (PWS 4.0)"),
    BULL("Named, PWS 7.3-qualified CRQAs assigned per task order, identified with full supporting documentation within 30 days of notification (PWS 4.2), drawn from a credential-verified monitor bench sized to surge with task-order volume."),
    BULL("Each monitor is onboarded to the specific trial before the first visit: the study's integrated monitoring plan, protocol and operations manual, SMART SOP/AMP alignment, and completion of all VA/CSP/SMART-required training (PWS 5.3.7)."),
    BULL("Scheduling discipline: visits approved by the monitoring study Lead, coordinated directly with site coordinators and investigators, announced through the SMART PM email group using the provided templates, and documented so invoiced quantities trace to the CLIN block structure (pre/post package, on-site day, portal-to-portal travel leg)."),
    // 3. Task 1
    H("3. Task 1 — CRQA Visits with Pre- and Post-Work (PWS 5.1; CLIN x001)"),
    P(`Site initiation visits (PWS 5.1.1): scheduled after the Investigator's Meeting and conducted to the CRQA Monitoring Plan with the support of the Lead CRQA. The evaluation covers, at minimum, every element of PWS 5.1.1.2 — protocol procedures including inclusion/exclusion criteria, the informed consent process, screening, randomization, investigational product accountability, UAE/SAE reporting, source document review and verification, CRF completion and QA procedures, IRB policies, regulatory document completion, site correspondence, and un-blinding procedures for blinded studies — plus trial-specific items. The monitor verifies the regulatory file inventory of PWS 5.1.1.3 (current IRB approvals for protocol and consents, IRB membership documentation, investigator agreements, financial disclosures, CVs, indemnity agreements, and GCP/HIPAA/HSP training records) and confirms the study management documents of PWS 5.1.1.4 are complete and filed in the Essential Document Binder.`),
    P(`Routine monitoring visits (PWS 5.1.2): one to four days, at the frequency SMART leadership determines from accrual, enrollment, protocol complexity and risk, site record-keeping proficiency, and prior corrective actions. ${who} staffs to the Government's stated expectation of hiring the appropriate number of monitors to meet the visit demand.`),
    P(`Visit preparation (PWS 5.1.3): after Lead approval, the monitor coordinates dates directly with the site coordinator and investigator, develops the tentative agenda, identifies documents for review, requests the site announcement letter through the SMART PM email group using the provided template, and assembles all working materials — correspondence, prior monitoring documents, and the study's integrated monitoring plan — before travel.`),
    P(`Visit conduct (PWS 5.1.4): the monitor reviews subject and investigator records for GCP and VA/CSP policy compliance; checks protocol compliance; reviews the Essential Documents Binder; conducts informed consent and HIPAA review; verifies CRF data against source documents; reviews source documents and the electronic medical record for AEs, SAEs, and unidentified SAEs; checks CRF accuracy, legibility, and submission to the Data Coordinating Center; complies with VA privacy and data security policy throughout; provides immediate feedback to the CSP Director and SMART leadership of significant or serious noncompliance upon discovery, while still on site; delivers GCP guidance, training, and re-education as needed; determines follow-up actions; conducts the exit interview; and assists with CAPA development and implementation.`),
    P(`Reports and summary letters (PWS 5.1.5): using Government-provided templates, the monitor completes the site visit report, Summary for Investigator, attachments, and supporting documents, and posts them to the SMART SharePoint site (or as directed) within seven business days of the last day on site. All QA visit logs and scanned documents go to SMART and the Study Lead Monitor. Reports are grammatically correct, accurate, and audit-ready; the monitor follows up with the study lead monitor until report approval and distribution, and rework is at no cost to the Government.`),
    // 4. Task 2
    H("4. Task 2 — CRQA Visits without Pre- and Post-Work (PWS 5.2; CLIN x001)"),
    P(`Support visits (PWS 5.2.1): at the request of the Lead CRQA or SMART leadership, ${redacted ? "the offeror's" : "PRG's"} monitors support another CRQA's site visits — second-monitor support or new-monitor training — performing on-site actions and travel without responsibility for pre- or post-work. Meeting support (PWS 5.2.2): monitors attend or present at study kickoff, annual, and program meetings, and attend in-house or virtual training, at SMART's direction. Each such engagement is invoiced per the CLIN block structure: on-site days and travel legs only.`),
    // 5. Task 3
    H("5. Task 3 — GCP Program Quality Support (PWS 5.3; CLIN x002, hourly, no travel)"),
    P(`PQS work is performed remotely on an hourly basis at SMART's direction: creating study-specific site visit tools (5.3.1); developing GCP tools for participating sites (5.3.2); designing casebook-derived data organization for patient files (5.3.3); developing source-documentation requirements and guidance for key study data (5.3.4); off-site records review of key critical data in support of risk-based integrated monitoring — informed consent and HIPAA review, EHR eligibility and compliance review, EDC/CRF review, endpoint and safety data review, and follow-up determination (5.3.5); study orientation (5.3.6); and completion of all VA, CSP, and SMART-required training (5.3.7).`),
    P(`Sponsor's Designated Representative duties (PWS 5.3.8): where assigned, the SDR finalizes and approves reports before distribution, completes the SDR form, requests follow-up letters through the SMART PM group, evaluates investigator corrective action responses for acceptability and completeness — revising at no cost to the Government until accurate — consults with the CSP Coordinating Center PM or QA Nurse Specialist as needed, directs monitor follow-up to verify site action items, and documents resolution and closeout of each visit.`),
    // 6. Deliverables
    H("6. Deliverables and Timeliness (PWS 5.4)"),
    BULL("Site visit report, Summary for Investigator, attachments, supporting documents: within seven business days of the last day on site, to the SMART PM group via SharePoint, using Government templates."),
    BULL("Serious or significant noncompliance: immediate notification to SMART leadership upon discovery, while still on site."),
    BULL("QA visit logs and scanned site documents: delivered with the report package to SMART and the Study Lead Monitor."),
    BULL("Monitor identification with full PWS 7.3 documentation: within 30 days of task-order notification."),
    BULL("Internal tracking: every deliverable is logged with its due date at visit scheduling; the deliverable tracker is reviewed twice weekly and any at-risk date is escalated to the Government before it is missed."),
    // 7. Quals
    H("7. Qualifications and Experience (PWS 7.0)"),
    P(`Named CRQA monitor(s) — [MONITOR NAME(S)${redacted ? " — redacted" : ""}]: each proposed monitor meets every element of PWS 7.3 with enclosed documentation — current CV (7.3.1); qualifying degree, licensure, or ACRP CCRA certification (7.3.2); documented GCP training from a nationally recognized provider (7.3.3); documented monitoring and human subjects protection training or CCRA certification (7.3.4); more than ten years of GCP clinical-trial monitoring of clinical research sites, documented trial-by-trial in the CV (7.3.5); and more than five years delivering GCP monitoring or auditing services for federally funded research, with the sponsor-by-sponsor listing of trials, site counts, visit frequency, and durations required by 7.3.6.1 [MONITOR'S FEDERAL TRIAL LISTING]. Medical record and chart review experience, including the specific EHR systems and access tools used (7.3.7), and Microsoft Office and Adobe proficiency demonstrated by example (7.3.8) are documented in each CV.`),
    P(`Program management: ${lead(redacted)} provides the single point of accountability for scheduling, credential currency, deliverable timeliness, and escalation — ACRP-certified, with documented GCP and human subjects protection training and extensive site-side GCP clinical research operations experience across multi-site federal (NIH) and industry protocols, including direct response to sponsor monitors' findings and data queries: deep familiarity with the monitored side of every item in a CRQA monitoring plan. Monitoring visits, findings, and reports are performed and owned exclusively by the named PWS 7.3-qualified monitors.`),
    P("Supporting documentation for every element above — CVs, degree and certification copies, GCP/HSP/monitoring training certificates, and the federal trial listings — is enclosed as Section 2 Qualification Support Docs, excluded from this section's page count. Full copies are provided; no links."),
  ]);
  await save(d, sec.replaceAll(" ", "_") + ".docx");
}

(async () => {
  await certifying(false); await certifying(true);
  await qaplan(false); await qaplan(true);
  await staffing(false); await staffing(true);
  await gfp(); await pastperf(); await admin();
  await technical(false); await technical(true);
})();
