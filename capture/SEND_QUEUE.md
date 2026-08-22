# PENDING OUTBOUND — process FIRST in any session with Outlook access

## ⚠️ DEDUPE PROTOCOL (MANDATORY — multiple sessions are active, Andrew 8/19)
Before sending ANY item below:
1. `git pull` this branch and re-read this file. If the item is marked
   SENT or CLAIMED by another session within the last 30 min, SKIP it.
2. Search Outlook SENT ITEMS for the item's exact subject line. If a
   matching sent message exists, the item is already sent: mark it SENT
   here (with timestamp found), push, and do NOT send again.
3. To send: edit this file marking the item "CLAIMED <session> <UTC time>",
   commit AND push BEFORE sending. If the push is rejected (conflict),
   another session claimed it: pull and re-check, do not send.
4. After sending: mark "SENT <UTC time>", push immediately.

## 0. MCRC sub quote requests — UNCLAIMED (prior claim VOID: container restart before send; NOT sent as of 03:0xZ; Sent Items check confirmed nothing sent). Any session with Outlook: send per protocol.
Send the quote-request email in
`capture/opportunities/2026-08_MCRC_M9549226SS001/05_staffing/subcontractor_tracker.md`
as THREE separate emails (same subject/body) to:
1. info@dbl-eagle.com  2. sales@biggp.com  3. info@mercuryecs.com
Subject: Quote request: CAT6 port remediation, Quantico VA (government project)
(4th sub, Fredericksburg Technology, has no public email: Andrew calls
(540) 403-8324 or uses fxbgtech.com contact form.)
Mark the tracker's "Quote req sent" boxes and delete this section after sending.

## 1. MCRC ROM reply (M9549226SS001) — DRAFT READY, awaiting Andrew
- Reply draft in Andrew's Drafts (to Endicott + Galloway, USMC MCRC),
  in-thread on Jeff Endicott's 8/19 email. ROM $32K–$42K / $37K planning
  figure, FFP, full SOW scope + assumptions + honest new-entrant
  corporate-experience statement.
- Andrew declined the automated send → HE reviews and presses Send (or
  tells Claude to edit and send). RFI deadline: **Aug 24, 5 PM ET.**

## 2. INL Mexico RFI (19AQMM26N0003) — DRAFT READY, needs manual attachment
- Draft in Andrew's Drafts, to ModrakER@state.gov, exact subject per
  notice. Outlook tools cannot attach files → Andrew attaches
  `PRG_Capability_Statement_19AQMM26N0003.docx` (delivered in chat; also
  at intl/opportunities/2026-08-28_INL-Mexico_19AQMM26N0003/03_response/),
  deletes the [ATTACH] placeholder line, sends. Deadline: **Aug 28, 4 PM CST.**

## 3. DoDEA RFI responses x2 (due Aug 28, 12:00 PM ET) — PDFs READY, need manual attachment
- Email A to: shunika.crockett@dodea.edu, emani.gray@dodea.edu
  Subject: Sources Sought DODEAHQ-SS-001 - DoDEA TMC Italy - SDVOSB Response of Pacific Research Group LLC
  Attach: intl/opportunities/2026-08-28_DoDEA_Italy_TMC/03_response/PRG_Response_DODEAHQ-SS-001.pdf
- Email B to: shunika.crockett@dodea.edu, michael.hosea@dodea.edu
  Subject: Sources Sought DODEAHQ-SS-002 - DoDEA Pacific East Japan - SDVOSB Response of Pacific Research Group LLC
  Attach: intl/opportunities/2026-08-28_DoDEA_Japan_FAM/03_response/PRG_Response_DODEAHQ-SS-002.pdf
- Body (both, HTML): short cover: attached capability statement, PWS feedback, and ROM pricing per the notice; PRG (UEI J585TLDV1CH1, CAGE 1Z9B6), an SBA-certified SDVOSB, confirms interest and supports set-aside consideration. Signature block standard.
- Outlook tools cannot attach: create DRAFTS with body+recipients, Andrew attaches PDFs (delivered in chat 8/21) and sends.

## 4. Canberra pre-quote conference link request (late but send ASAP)
- To: cnbgsoprocurement@state.gov
- Subject: RFQ 19AS2026Q0031 - Pre-Quotation Conference Link Request - Pacific Research Group LLC
- Body (short): PRG (UEI J585TLDV1CH1, CAGE 1Z9B6), an SBA-certified SDVOSB,
  intends to quote and respectfully requests the Teams link for the August 26
  pre-quotation conference and any supplemental information, acknowledging the
  request window has passed. Standard signature. No attachment needed — can
  send fully automated.

## 5. Canberra CO clarification question (no attachment — fully automatable)
- To: cnbgsoprocurement@state.gov
- Subject: RFQ 19AS2026Q0031 - Clarification Question - Pacific Research Group LLC
- Body: per intl/opportunities/2026-09-11_Canberra_19AS2026Q0031/05_staffing/teaming_outreach.md
## 6. Canberra teaming outreach x3 (verify org contact emails first, then send)
- Per teaming_outreach.md: USSC, AIIA, ANU NSC — same body, adapted greeting

## Completed
- 18-email batch: sent 8/18. CASS: sent by Andrew 8/17.
