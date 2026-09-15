const {Document, Packer, Paragraph, TextRun, AlignmentType, Table, TableRow, TableCell, WidthType} = require('docx');
const fs = require('fs');
const FONT = "Times New Roman", SIZE = 22; // 11pt
const P = (text, opts={}) => new Paragraph({alignment: opts.center ? AlignmentType.CENTER : AlignmentType.LEFT, spacing: {after: opts.tight ? 40 : 140}, children: [new TextRun({text, font: FONT, size: SIZE, bold: !!opts.bold, italics: !!opts.i})]});
const H = (t) => new Paragraph({spacing: {before: 200, after: 100}, children: [new TextRun({text: t, font: FONT, size: SIZE, bold: true})]});
const B = (t) => new Paragraph({bullet: {level: 0}, spacing: {after: 60}, children: [new TextRun({text: t, font: FONT, size: SIZE})]});
const cell = (t, bold) => new TableCell({width:{size:50,type:WidthType.PERCENTAGE}, children:[new Paragraph({children:[new TextRun({text:t,font:FONT,size:20,bold:!!bold})]})]});
const row = (a,b,bold) => new TableRow({children:[cell(a,bold), cell(b,bold)]});

const d = new Document({sections:[{properties:{page:{size:{width:12240,height:15840}}}, children:[
P("Capability Statement — Sources Sought 19AQMM26N0003", {center:true, bold:true}),
P("INL Mexico — Interdiction & Hidden Compartment Training and Mentoring", {center:true, bold:true}),
P("Pacific Research Group LLC — SBA-certified SDVOSB", {center:true}),
P(""),
H("1. Contact Information"),
P("Company: Pacific Research Group LLC (single-member LLC, California)", {tight:true}),
P("UEI: J585TLDV1CH1  ·  CAGE: 1Z9B6  ·  SAM.gov: Active", {tight:true}),
P("Point of Contact: Andrew O'Donnell, Managing Director", {tight:true}),
P("Email: Andrew@pacificresearchllc.com  ·  Phone: (650) 213-2381", {tight:true}),
P("Business size/status: Small business; SBA-certified SDVOSB (VetCert)", {tight:true}),

H("2. Credentials and Professional Experience"),
P("Pacific Research Group LLC (PRG) is an SDVOSB prime contractor whose model is the recruitment, credentialing, and program management of specialized subject-matter-expert instructors for U.S. Government requirements. PRG responds to this notice as a capable SDVOSB source that would perform as prime contractor and program manager, delivering instruction through a cadre of retired U.S. federal law-enforcement interdiction SMEs under PRG management. In the interest of accurate market research, PRG states its experience plainly:"),
B("Business in Mexico / SEDENA-SEMAR: PRG is a recently established entity and has not yet performed contracts in Mexico. PRG's Managing Director holds an MA in International Studies with Latin America regional training and in-country field experience in South America, and PRG's delivery model places a Mexico-based project manager and locally engaged bilingual legal SME on the program from day one."),
B("Interdiction and hidden-compartment training delivery: PRG would deliver instruction through named SME instructors recruited from retired U.S. Customs and Border Protection, HSI, DEA, and state criminal-interdiction backgrounds — the standard instructor pool for this discipline — each with documented law-enforcement interdiction service, instructor certification, and courtroom-testimony experience. PRG's role is the prime-contractor function: instructor vetting and credential documentation, curriculum management, scheduling, quality control, and Government reporting."),
B("Program management and interagency delivery: PRG's Managing Director is a U.S. military veteran who served in large-scale interagency operations — including medical and administrative operations supporting 25,000+ evacuees during Operation Allies Welcome under federal and CDC parameters — and has managed federally regulated, audit-ready program operations (multi-site NIH and industry clinical research; DoD healthcare technology management)."),
B("Train-the-trainer: PRG's instructor cadre model is built for certification-based delivery, and its QC framework (documented lesson standards, evaluator checklists, post-iteration corrective action) extends directly to train-the-trainer and the Option Year 3 quality-control/mentoring phase."),
P("Qualified Training Personnel matrix:"),
new Table({width:{size:100,type:WidthType.PERCENTAGE}, rows:[
row("Requirement","PRG capability", true),
row("SME instructors (multiple per course) — law enforcement, interdiction, hidden-compartment detection, courtroom testimony, certifications","Recruited retired CBP/HSI/DEA/state-interdiction instructors; credentials, service records, and instructor certifications documented per individual and submitted for Government review before assignment"),
row("Spanish-language materials, instructors, and/or interpreters","Bilingual instructors prioritized in recruitment; professional interpreter support and Spanish-language training materials produced under PRG QC"),
row("Mexico-based project management for recurring iterations over multiple years","Mexico-based (Mexico City) program manager engaged for the period of performance; PRG corporate PM and reporting from the U.S."),
row("Locally based legal subject-matter expert","Locally engaged, compliance-vetted Mexican attorney with criminal-procedure/evidentiary practice"),
row("Training kits for classroom use","Produced and maintained under PRG configuration control, Spanish-first with English masters"),
row("Modified vehicles (est. 5–7) with genuine or manufactured hidden compartments","Sourced and fabricated through PRG's instructor cadre and specialty vendors; maintained as Government-approved training aids with chain-of-custody documentation"),
]}),
P(""),
H("3. SOW vs. PWS Recommendation"),
P("PRG recommends a Performance Work Statement. The requirement's outcomes are measurable (certified students, certified Mexican instructors, field-audit results in the QC/mentoring phase), and a PWS with performance standards per iteration — certification pass rates, iteration completion, report timeliness — preserves the Government's flexibility across a multi-year, multi-site program while holding the contractor to results rather than prescribed methods."),
H("4. PSC and NAICS Recommendation"),
P("NAICS 611430 (Professional and Management Development Training; SBA size standard well above small-business thresholds relevant here) or 611519 (Other Technical and Trade Schools). PSC U008 (Education/Training — Training/Curriculum Development) or U099 (Education/Training — Other) for the combined delivery-and-development scope."),
H("5. Notional Pricing (nonbinding)"),
B("Recommended model: firm-fixed price per training iteration, with separate fixed-price CLINs for course development (one-time), train-the-trainer iterations, and QC/mentoring field visits, plus a cost-reimbursable travel CLIN at DSSR/GSA rates."),
B("Notional range, Basic Interdiction & Hidden Compartment Certification: $85,000–$130,000 per two-week iteration (multiple SME instructors, interpreter, materials, vehicle training aids amortized, Mexico PM support). Train-the-trainer iterations: $95,000–$140,000. QC/mentoring: $18,000–$28,000 per field visit cycle. All figures notional and nonbinding, per the notice."),
B("Cost-minimization recommendations: (a) staff Mexico-based PM and legal SME locally rather than rotating U.S. personnel — the largest single cost lever; (b) fabricate hidden-compartment training vehicles once in Mexico and retain them as Government training aids across all iterations rather than transporting vehicles; (c) schedule iterations back-to-back regionally to amortize instructor travel; (d) fixed-price-per-iteration CLINs to eliminate level-of-effort administration."),
P(""),
P("PRG confirms its interest in this requirement, supports an SDVOSB set-aside determination should market research warrant one, and is available for any follow-up questions at the contact above.", {}),
]}]});
Packer.toBuffer(d).then(b => {fs.writeFileSync("PRG_Capability_Statement_19AQMM26N0003.docx", b); console.log("wrote docx");});
