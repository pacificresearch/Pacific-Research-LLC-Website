# PRG Capture Workflow (v1)

This is the operating procedure for every solicitation PRG pursues. When
SAM.gov documents are uploaded to a session, run this pipeline in order.
Each opportunity is one folder in `capture/opportunities/` moving through
states:

**SCREEN → PURSUE → SUBMIT → MONITOR → WIN or LOSS**

Templates for every stage live in `capture/templates/`. Reusable content
(capability statements, past performance, resumes, boilerplate) lives in
`capture/library/` — always assemble from the library first, write from
scratch second, and file improved content back into the library after
every bid.

---

## Stage 0 — SCREEN

Apply the capture-v3 screening gate in `CLAUDE.md` (hard kills, lead-time
rules) before doing anything else.

- **PASS** → state the kill criterion, stop. Do not create a folder, do
  not draft documents.
- **Survivor** → create the opportunity folder:

```
capture/opportunities/YYYY-MM-DD_<agency-short>_<notice-id>/
  00_screening.md          # gate decision, role, fulfillment model, margin band
  01_solicitation/         # every SAM attachment, amendments as they arrive
  02_compliance_matrix.md
  03_proposal/             # capability statement, volumes, forms
  04_pricing.md
  05_staffing/             # job postings, contingent offers, sub quotes
  06_submission_checklist.md
  07_award/                # created only on win
  99_debrief.md            # created on loss (or win — always debrief)
```

Record in `00_screening.md`: pursuit decision, assigned fulfillment model
(founder-delivered / professional services / staffing / value-added
supply / trade-sub management), target margin band, response deadline,
Q&A deadline, site-visit date if any.

## Stage 1 — PURSUE

Four tracks run in parallel. The compliance matrix comes first because
every other document is checked against it.

### 1a. Compliance matrix (template: `01_compliance_matrix.md`)
Shred the solicitation: every "shall/must/will", all submission
instructions (format, page limits, file naming, delivery method, due
date/time with timezone), required forms and fill-ins, reps & certs,
evaluation factors and their weights, wage determinations, place of
performance, period of performance, clauses needing flow-down to subs.
Nothing gets submitted until every row is CLOSED.

### 1b. Proposal documents (template: `02_capability_statement.md`, `03_technical_volume.md`)
Generate ONLY the documents the solicitation asks for, in the format it
asks for, mapped row-by-row to the compliance matrix and evaluation
factors. Pull from `capture/library/` and tailor; never submit generic
boilerplate. Quote the PWS/SOW's own language back when describing
approach.

### 1c. Pricing (template: `04_pricing_worksheet.md`)
Build the number bottom-up: labor from the wage determination (SCA/DBA)
plus fringe/H&W, sub quotes, materials, overhead, then margin checked
against the band for the fulfillment model (CLAUDE.md). Verify the
limitation on subcontracting (50% services cap — W2 hires and
similarly-situated subs count as PRG) and the nonmanufacturer rule on
set-aside supply buys BEFORE finalizing. Flag working-capital exposure:
estimated float = (payroll + sub payments) carried before first
government payment.

### 1d. Sourcing (templates: `05_job_posting_contingent.md`, `06_subcontractor_tracker.md`)
Route by fulfillment model:
- **W2/1099 hires** → generate contingent job postings (ready-to-paste
  text + structured fields for LinkedIn/Indeed/an ATS). All pre-award
  postings MUST state "contingent upon contract award." Collect resumes
  and signed contingent-offer or letter-of-intent commitments for key
  personnel named in the proposal.

  **Automated distribution — careers page (v1 automation):** every
  posting is also published to `pacificresearchllc.com/careers` with
  schema.org `JobPosting` JSON-LD markup. Google for Jobs indexes these
  automatically (free organic distribution), and Indeed/board crawlers
  pick up structured careers pages. Claude generates the posting file
  and the careers-page update in the same pass; deploy goes out with the
  website. Applications land at Andrew@pacificresearchllc.com via the
  page's apply link. Manual paste to LinkedIn/Indeed remains for paid
  visibility; an ATS with API syndication is the v2 upgrade if posting
  volume justifies a subscription.
- **Trade subs / staffing firms / distributors** → run the subcontractor
  tracker: identify 3+ candidates, collect quotes, NDA/teaming agreement,
  COI, and confirm they accept the flow-down clauses from the matrix.

## Stage 2 — SUBMIT

Run `07_submission_checklist.md`: every compliance-matrix row closed,
every amendment acknowledged, files named and formatted per instructions,
signatures in place (SF1449/SF33 blocks), submitted ahead of deadline
with delivery confirmation saved to `01_solicitation/`.

Email channel: all CO correspondence and email submissions go from
**Andrew@pacificresearchllc.com (Outlook)**. Claude drafts the
submission email (subject line per solicitation instructions, attachments
listed, professional cover text); Andrew reviews and sends. If the
Microsoft 365 connector is linked, draft directly in Outlook; otherwise
output the email as paste-ready text in the opportunity folder.

## Stage 3 — MONITOR

Until award decision:
- Watch SAM for amendments and Q&A responses on this notice ID. An
  amendment triggers: re-run the delta through the compliance matrix,
  acknowledge the amendment, revise and resubmit if already submitted.
- Keep contingent hires and subs warm — status update at least every 2
  weeks; commitments go stale.

## Stage 4a — WIN (template: `08_win_day_setup.md`)

Day-one setup, all of it:
1. `07_award/` folder — signed award doc, contract number, CO/COR
   contacts, funded amount, CLIN structure.
2. **Project calendar** — dedicated calendar per contract seeded from the
   contract: PoP start/end, every deliverable due date, reporting
   cadence, invoice schedule, option-year decision dates minus 90 days.
3. **Get-paid setup** — WAWF or IPP registration per the contract's
   payment office, capture payment terms, set invoice-submission
   reminders.
4. **Staffing goes live** — flip contingent postings to live requisitions
   or execute the subcontract agreements; onboard against the contract
   start date.
5. QC plan, deliverable templates, kickoff request to the CO/COR.

## Stage 4b — LOSS (template: `09_loss_debrief.md`)

Always request a debrief (it's a right on most awards — 3 days to
request on FAR 15; ask regardless on simplified acquisitions). Log price
delta vs. winner if disclosed, weaknesses cited, and what changes. File
any reusable proposal content into `capture/library/`. Losses feed the
library and the pricing model — a lost bid with a filed debrief is paid
market research.

---

## Standing rules

- The library compounds or the system doesn't work: after EVERY bid, win
  or lose, file improved capability statements, boilerplate sections,
  and pricing actuals back into `capture/library/`.
- Sub-$250K simplified acquisitions are strategic past-performance
  builders — pursue at lower margin thresholds.
- Never let a proposal document make a claim the compliance matrix can't
  trace to a solicitation requirement or evaluation factor.
