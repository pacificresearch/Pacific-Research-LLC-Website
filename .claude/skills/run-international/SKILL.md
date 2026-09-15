---
name: run-international
description: Run the full PRG International capture cycle end to end — screen overseas SAM notices with the --intl matcher, apply intl/GATE.md, draft tailored responses for survivors, price and assemble anything biddable, update the board, and stop at the send gate. Use when Andrew says "run international system", "run the international system", "/run-international", or asks for the international capture run.
---

# Run International System

One command, the whole cycle: **SCREEN → GATE → DRAFT → PRICE → REPORT → ⛔ SEND GATE.**

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

## 7. ⛔ SEND GATE — stop here

Report to Andrew and stop. Do not send.

Sending to a contracting officer is one of the four carve-outs Andrew
set (`CLAUDE.md`), because a quote is a binding offer and a response is
outward-facing. Present:

```
INTERNATIONAL RUN — <date>
  Screened: N notices → M international → K survivors
  Responses drafted: N  (⛔ awaiting your go)
    <sol> — <buyer, country> — <deadline local / ET>
  Biddable priced: N — <sol>, <price>, <margin>
  REGISTER–PREPOSITION: N — blocked on <registration>
  PASS: N (top kill: <criterion>)
  Registration backlog: next <X>, blocker <Y>
```

**On "send":** reply on the CO's own thread with
`outlook_create_reply_draft` when responding to something they wrote;
`outlook_send_mail` only to open a new conversation. Never `send_mail`
with "RE:" — it looks like a reply and starts a second thread.

Then mark sent in the batch record, update the board, and confirm the
full sent list.

---

## Honesty rules — absolute in this lane

Never claim in-country presence, an office, a local entity, prior work
in a country, or a language PRG does not have. **PRG holds no working
foreign language** (Andrew, 8/19 — English only). Local partners supply
presence and language, and are **named as partners**.

Never argue with a contracting officer (`CLAUDE.md`). Concede cleanly,
take corrections once, pivot to the lane PRG can truthfully serve.
