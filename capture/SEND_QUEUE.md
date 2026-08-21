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

## 0. MCRC sub quote requests — CLAIMED session-x15cat 2026-08-20T02:55Z (sending now)
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

## Completed
- 18-email batch: sent 8/18. CASS: sent by Andrew 8/17.
