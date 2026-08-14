# Daily Capture Run — procedure for the scheduled session

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
(`SAM_API_KEY` env var overrides the built-in key.) Commit the report.
Look back 3 days so weekend/holiday gaps self-heal; dedupe against
notice IDs already present in `capture/reports/` and
`capture/opportunities/`.

## 3. Screen and select
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
- Draft the CO email (RFI response, question submission, or quote cover
  — whatever the notice stage calls for), addressed to the CO of
  record, from Andrew@pacificresearchllc.com. If the Microsoft 365
  connector is available, save it as an Outlook DRAFT; otherwise write
  it to `03_proposal/co_email_draft.md`. ⛔ Andrew reviews and sends.
- If fulfillment needs hires: generate contingent job postings + the
  careers-page snippet per `05_job_posting_contingent.md`, insert into
  `site/careers/index.html`. LinkedIn/Indeed paste text goes in
  `05_staffing/`. ⛔ Andrew pastes to LinkedIn/Indeed.
- Commit everything to a branch `capture/YYYY-MM-DD-<notice-id>`, push,
  open a draft PR titled "Capture: <notice id> <short title>".

## 5. Notify (the run's final message — reaches Andrew by push + email)
Lead with: **CURRENT CONTRACT UNDER CONSIDERATION: <title> (<notice
id>)** — agency, response deadline, pursuit role, fulfillment model,
estimated value/margin band. Then, as a short checklist, the ⛔ actions
waiting on Andrew:
1. Send the drafted CO email (link/location of draft)
2. Post the prepared LinkedIn/Indeed text
3. Approve/adjust anything flagged in the compliance matrix
Then one line each for backlog survivors and the PASS count. No filler.

## Standing boundaries
- ⛔ NEVER auto-send email to a contracting officer, submit a quote, or
  publish a job posting to an external board. Prepare + notify only.
  The careers page ships only via draft PR that Andrew merges.
- Amendments/updates on opportunities already in `capture/opportunities/`
  take priority over new selections — check them first (step 3).
- One selected contract at a time unless Andrew has said otherwise in
  the opportunity folder's `00_screening.md`.
