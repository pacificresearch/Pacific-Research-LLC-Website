---
name: run-international
description: Run the full PRG International capture cycle end to end — screen overseas SAM notices with the --intl matcher, apply intl/GATE.md, draft tailored responses for survivors, price and assemble anything biddable, update the board, and stop at the send gate. Use when Andrew says "run international system", "run the international system", "/run-international", or asks for the international capture run.
---

# Run International System

One command, the whole cycle: **SCREEN → GATE → DRAFT → PRICE → SEND → REPORT.**

Work through it in order. Do not ask permission between steps — Andrew's
bias-to-action standing order applies (`CLAUDE.md`). The only stop is
step 7.

---

## 1. Screen

```
python3 samgov_opportunity_matcher.py --intl --days 7 --limit 100 --narrow \
  --no-recompetes --no-grants --no-sbir --no-reliefweb --no-excel --no-report \
  > intl/reports/PRG_INTL_report_$(date +%F).md
```

`--narrow` is deliberate: the wide-net set-aside sweep is almost all
domestic and costs minutes for no international yield. `--intl` adds the
State/foreign-assistance posting offices, which is where the volume is.

**Check the hydration line in stderr.** Descriptions are fetched before
screening. If it reports 0 retrieved, the screen is running on titles
only — STOP and fix that before trusting anything downstream.

If `api.sam.gov` is unreachable, STOP and say so. Never fabricate a report.

## 2. Gate

Apply `intl/GATE.md` to every notice. It runs BEFORE `capture/WORKFLOW.md`.

Three outcomes:
- **PASS** — name the kill criterion, one line, move on. No folder.
- **REGISTER–PREPOSITION** — the expected majority early on. Log to the
  registration backlog in `intl/PIPELINE.md`. This is a productive
  outcome, not a dry day; report it as one.
- **Survivor** — opportunity folder per `intl/WORKFLOW.md` Stage 0,
  using `intl/templates/00_screening_intl.md`.

Kill #11 check on every UN-system notice: above US $500K PRG cannot
register at UNGM Level 2 until it turns three. Eligibility PASS, not a
judgment call.

## 3. Draft responses — pre-RFP notices

For every notice the matcher marks **`respond_recommended: True`**
(NOT merely "not disqualified" — that conflation is what sent three bad
responses on 8/17):

Use `capture/templates/14_sources_sought_response.md`.
- **Under 200 words.**
- Answer the notice's own questions, in its words and order.
- Only capability that bears on THIS scope.
- No FAR 9.104-1 recital, no SAM-registration sentence, no reflex
  set-aside advocacy, no credentials the scope doesn't call for.

**Set-aside posture** (`intl/GATE.md` §A) — this is the one real edge:
- **U.S. government overseas buy** → ask the CO to consider a set-aside
  under **FAR 19.000(b)(1)(ii)**, noting overseas awards count toward
  the agency's small-business goals. Cite the paragraph.
- **UN / multilateral / development bank** → no US preference exists.
  SDVOSB is one credibility line, never a claim of entitlement.

## 4. Price anything biddable

Solicitations that survive: `intl/PRICING.md`. Build bottom-up —
local wage data, DSSR per-diem for the actual post on the actual date,
DBA rated for that country, country-risk margin band. Then the three
checks: limitation on subcontracting, working-capital float on the
*practical* payment lag, and the 10% FX stress test.

Pricing authority is delegated — build the number and present it
finished. Never block on input.

## 5. Compliance rails

Every surviving pursuit gets the nine rails from
`intl/COMPLIANCE_RAILS.md` as compliance-matrix rows. Two gate the
pursuit itself, not the submission:
- **Rail 1 sanctions** — legal kill, no override, verified live.
- **Rail 2 FCPA vetting** — closes before any local partner is NAMED in
  a document.

High-threat post → the mandatory six-line RISK block, all six answered.
An unanswered line is a hold, not a guess.

## 6. Update the board

Refresh `intl/PIPELINE.md`: active pursuits, registration backlog and
its blockers, roster counts, recently done. Commit everything and push
to the working branch.

## 7. SEND, THEN REPORT

Andrew's 8/20 amendment (`CLAUDE.md` BIAS TO ACTION): the run does not
stop at a report. **The line is price, not email.**

**Send now, no approval:** sources sought and RFI responses, capability
statements, expressions of interest, questions to a CO or UN procurement
officer, FAR 19.000(b)(1)(ii) set-aside asks, and any non-binding
registration correspondence. Reply on the recipient's own thread with
`outlook_create_reply_draft` when answering something they wrote;
`outlook_send_mail` only to open a genuinely new conversation. Never
`send_mail` with "RE:" — it looks like a reply and starts a second
thread. Mark each one sent in the batch record.

**⛔ Stage, do not send:** anything committing PRG to a price — quotes,
RFQ responses, cost volumes, signed certificates of compliance. Build it
complete and submission-ready, every form filled, no placeholders, so
Andrew's approval is one look and one send. Save as an Outlook draft and
put a copy in the opportunity folder.

**⛔ Also still gated:** external job-board postings, binding portal
registrations (UNGM, bank), and naming any local partner or expert
before their Rail 2 vetting closes.

Then report:

```
PRG INTERNATIONAL — <date>
  Screened: N notices → M international → K survivors
  SENT: N
    <sol> — <buyer, country> — <what went out> — <deadline local / ET>
  ⛔ STAGED, awaiting your go: <sol>, <price>, <margin>
  REGISTER–PREPOSITION: N — blocked on <registration>
  PASS: N (top kill: <criterion>)
  Registration backlog: next <X>, blocker <Y>
```

If Andrew has recorded a dollar ceiling in `CLAUDE.md`, quotes at or
under it are sent rather than staged, and reported under SENT.

---

## Honesty rules — absolute in this lane

Never claim in-country presence, an office, a local entity, prior work
in a country, or a language PRG does not have. **PRG holds no working
foreign language** (Andrew, 8/19 — English only). Local partners supply
presence and language, and are **named as partners**.

Never argue with a contracting officer (`CLAUDE.md`). Concede cleanly,
take corrections once, pivot to the lane PRG can truthfully serve.
