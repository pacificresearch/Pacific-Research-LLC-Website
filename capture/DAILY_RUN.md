# Daily Capture Run — procedure for the scheduled session

> **Send cadence (Andrew, 8/21): 4 + 4 + 4.** This file is the MORNING
> block — the only one that sweeps SAM. Two send-only blocks follow it,
> MIDDAY at 19:00 UTC and SIGN-OFF at 00:00 UTC, working this report and
> the open backlog rather than re-sweeping (the keyed API's daily quota
> does not survive three sweeps). Target four non-binding responses per
> block, drawn from real supply — never padded. See `CLAUDE.md`, DAILY
> SEND CADENCE.

A scheduled Routine fires a fresh cloud session every morning. That
session follows this procedure end-to-end and finishes with an
executive notification to Andrew. Human approval gates are marked ⛔ —
the run PREPARES those actions but never executes them.

## 1. Setup
- If `capture/WORKFLOW.md` is missing from the default branch, fetch and
  check out `claude/system-design-discussion-x15cat` (pre-merge state).
- Verify `api.sam.gov` is reachable. If the egress proxy blocks it
  (HTTP 403 CONNECT), STOP and notify: "Network policy still blocks
  api.sam.gov — allow it in the environment settings at
  claude.ai/code." Do not fabricate a report.

## 2. Generate the report
```
python3 samgov_opportunity_matcher.py --days 3 --limit 100 \
  > capture/reports/PRG_report_YYYY-MM-DD.md
```
**Descriptions are hydrated automatically.** SAM's search endpoint
returns a URL in place of the notice body for 100% of notices, so the
run fetches each description before screening (cached across runs in
`~/.prg_desc_cache.json`). If the hydration line reports 0 retrieved,
the screen is running on titles only — STOP and fix it rather than
trusting the output.
(`SAM_API_KEY` env var overrides the built-in key.) Commit the report.
Look back 3 days so weekend/holiday gaps self-heal; dedupe against
notice IDs already present in `capture/reports/` and
`capture/opportunities/`.

## 3. Screen and select — VOLUME MODE (Andrew's standing order 8/17)
FIRST: for every pre-RFP notice (sources sought / RFI / presolicitation)
the matcher marks **`respond_recommended: True`**, draft a tailored
capability response the SAME DAY into its opportunity folder using
**`capture/templates/14_sources_sought_response.md`** — under 200 words,
answering only what the notice asks, in the notice's own words and
order. No FAR 9.104-1 recital, no SAM-registration sentence, no reflex
set-aside advocacy, and no credentials that do not bear on this scope
(Andrew, 8/19). Download notice attachments and follow any prescribed
format. Queue each as an Outlook draft when the connector is available;
notify Andrew of ALL pending sends. Never send a generic blast — the
8/17 batch sent one identical 118-word credential dump to a concrete
notice, a bat-removal notice, a staffing notice, and a software
subscription. Every response cites the notice's own scope language. Solicitations (biddable) still get ranked and selected below.
**Volume mode is gated on `respond_recommended`, NOT on "survived the
gate."** Those are different tests and conflating them is what sent three
of the 18 responses in the 2026-08-17 batch to notices PRG could never
win — including 36C26326Q1034, whose description opens "NOTICE OF INTENT
TO AWARD SOLE SOURCE ... THIS NOTICE IS NOT A REQUEST FOR COMPETITIVE
QUOTES." The contracting officer wrote back to correct us. A response
sent into a sole-source or intent-to-award notice costs credibility with
the exact CO we are trying to build a relationship with.

Before any batch send, confirm for every notice: `respond_recommended`
is True, `noncompetitive` is False, and the description was actually
retrieved (see step 2 — a notice screened on its title alone has not
been screened).

- Apply the CLAUDE.md capture-v3 gate to every notice in the report.
- Rank survivors by the report's weighted priority score, adjusted for:
  days of runway remaining, sub-$250K past-performance value, and
  recurring/follow-on potential.
- Select ONE opportunity as **CURRENT CONTRACT UNDER CONSIDERATION**.
  (Others stay listed in the report as backlog.) If nothing survives,
  the notification says so — that is a valid, cheap outcome.

## 4. Prepare the selected opportunity (per capture/WORKFLOW.md)
- Create the opportunity folder; write `00_screening.md`.
- Pull attachments from SAM if reachable; build the compliance matrix
  as far as the available documents allow.
- Draft proposal skeleton docs from `capture/library/`.
- Write the CO email, addressed to the CO of record, from
  Andrew@pacificresearchllc.com. **What happens next depends on whether
  it commits PRG to a price** (`CLAUDE.md` BIAS TO ACTION amendment,
  8/20):
  - **Non-binding — SEND IT.** Sources sought and RFI responses,
    capability statements, questions, clarification and extension
    requests, interested-vendor list requests, set-aside asks. Send on
    the CO's own thread, then report what went out. No advance approval.
    **First check Sent Items** — `outlook_email_search(folderName="Sent
    Items", query="<notice number>")`. Andrew runs other sessions and
    the Routines fire into fresh ones; the shared mailbox is the only
    ledger they all see. A hit means skip it and say so in the report,
    never send a second copy. Search by notice number, not subject, and
    look back an extra day (Sent Items filters on local time).
  - **⛔ Priced — STAGE IT.** Quote covers, RFQ responses, anything with
    a cost volume or a signed certificate of compliance. Save as an
    Outlook DRAFT (or `03_proposal/co_email_draft.md` if the connector
    is unavailable), complete and submission-ready with every form
    filled and no placeholders, and notify Andrew leading with the
    number and the margin. A quote is a binding offer.
- If fulfillment needs hires: generate contingent job postings + the
  careers-page snippet per `05_job_posting_contingent.md`, insert into
  `site/careers/index.html`. LinkedIn/Indeed paste text goes in
  `05_staffing/`. ⛔ Andrew pastes to LinkedIn/Indeed.
- Commit everything to a branch `capture/YYYY-MM-DD-<notice-id>`, push,
  open a draft PR titled "Capture: <notice id> <short title>".

## 5. Update the pipeline board
Refresh `capture/PIPELINE.md`: stages, deadlines, next actions, recently-done. This board is Andrew's single view of everything — keep it current and honest every run.

## 6. Notify (the run's final message — reaches Andrew by push + email)
Lead with: **CURRENT CONTRACT UNDER CONSIDERATION: <title> (<notice
id>)** — agency, response deadline, pursuit role, fulfillment model,
estimated value/margin band. Then **SENT TODAY** — one line per piece of
non-binding correspondence that actually went out (notice id, CO, what
it was). Then, as a short checklist, the ⛔ actions still waiting on
Andrew:
1. Approve and send the staged quote — lead with the number and margin
2. Post the prepared LinkedIn/Indeed text
3. Approve/adjust anything flagged in the compliance matrix
Then one line each for backlog survivors and the PASS count. No filler.

## Standing boundaries
- **Replying to a CO: use the reply tools, not `send_mail`.** Find their
  message and reply into the conversation so the exchange stays threaded
  on their end (`capture/WORKFLOW.md` Stage 2). `send_mail` with "RE:"
  in the subject starts a second thread. New conversations only.
- **Non-binding CO correspondence goes out on its own** — sources
  sought, RFIs, capability statements, questions, set-aside asks. Send
  them, then report them.
- ⛔ NEVER auto-submit a quote, an RFQ response, or anything else that
  commits PRG to a price, and NEVER publish a job posting to an external
  board. Stage those complete and notify. The careers page ships only
  via draft PR that Andrew merges.
- Amendments/updates on opportunities already in `capture/opportunities/`
  take priority over new selections — check them first (step 3).
- One selected contract at a time unless Andrew has said otherwise in
  the opportunity folder's `00_screening.md`.
