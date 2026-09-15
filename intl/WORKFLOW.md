# PRG International — capture workflow (v1)

The operating procedure for every international pursuit. Same pipeline
as the domestic system, different rails.

**SCREEN → PURSUE → SUBMIT → MONITOR → WIN or LOSS**

**One library, two systems.** Reusable content lives in
`capture/library/` — the SAME library the domestic system uses. File
international variants alongside domestic ones (`company_profile_intl.md`,
`past_performance_oaw.md`), never in a second library. The library
compounds or neither system works.

Templates specific to this lane live in `intl/templates/`; domestic
templates in `capture/templates/` are used unchanged wherever they fit
(compliance matrix, submission checklist, loss debrief).

---

## The business model — the lane

PRG primes and owns the customer relationship, contract management, QC,
invoicing, and compliance. Andrew travels to post — embassies, missions,
project sites — to source, vet, hire, and manage **local experts and
local firms** who execute the work.

**Founder travel is a feature, not an overrun.** It is the differentiator
against remote-managed competitors and it is budgeted into every pricing
model as a direct cost, priced at DSSR rates. Never absorb it into
overhead and never leave it out to look cheap.

Decision standard, unchanged:
**WIN → SOURCE (locally) → PERFORM → CONTROL → INVOICE → COLLECT → PROFIT.**

---

## Stage 0 — SCREEN

Apply `intl/GATE.md` before anything else.

- **PASS** → state the kill criterion, stop. No folder, no documents.
- **REGISTER–PREPOSITION** → no opportunity folder; add a line to the
  registration backlog in `intl/PIPELINE.md` naming the exact
  registration that was missing. This is the most common early outcome
  and it is a productive one.
- **Survivor** → create the opportunity folder:

```
intl/opportunities/YYYY-MM-DD_<country>_<buyer>_<notice-id>/
  00_screening.md          # gate decision, role, fulfillment model,
                           # margin band, RISK block if high-threat,
                           # registration status
  01_solicitation/         # tender docs, amendments, clarifications
  02_compliance_matrix.md  # incl. the 9 mandatory intl rails
  03_proposal/
  04_pricing.md            # local wages + DSSR travel + country-risk margin
  05_sourcing/             # local partner quotes, expert CVs, NDAs,
                           # FCPA vetting files, teaming agreements
  06_submission_checklist.md
  07_award/                # on win
  99_debrief.md            # always
```

`00_screening.md` records: pursuit decision, country and post, buyer
regime (**U.S. government overseas** vs **UN/multilateral/bank** — this
drives the whole set-aside posture, see `intl/GATE.md` §A), fulfillment
model, target margin band, response deadline in **local time AND ET**,
site-visit or pre-bid conference date, and the registration PRG must
already hold.

## Stage 1 — PURSUE

Five tracks. The compliance matrix comes first because everything else
is checked against it.

### 1a. Compliance matrix (`capture/templates/01_compliance_matrix.md`)
Shred the tender exactly as domestically — every shall/must, submission
format, page limits, file naming, delivery method, deadline **with
timezone**, forms, reps and certs, evaluation criteria and weights,
place of performance, period of performance, flow-downs.

**Then add the nine international rails from `intl/GATE.md` §E as rows.**
They are requirements like any other and nothing submits until they are
CLOSED. Two of them gate the pursuit rather than the document:
sanctions screening (§1) and FCPA vetting (§2) must close **before any
local partner is named in a proposal**, not before submission.

### 1b. Proposal documents
Assemble from `capture/library/` and tailor. Quote the tender's own scope
language back. Set-aside posture per `intl/GATE.md` §A — advocacy on U.S.
overseas buys, one credibility line in UN/bank lanes.

### 1c. Pricing (`intl/PRICING.md`) — DELEGATED AUTHORITY
Same standing order as domestic (8/17): Claude prices independently from
data and presents the finished number with the package. Never block a
bid waiting on pricing input. International build-up is in
`intl/PRICING.md`: local-market wage data, DSSR per-diem and travel,
DBA insurance rated for the post, security and life support, country-risk
margin band, FX and payment-lag working capital.

### 1d. Sourcing — local experts and local firms (`intl/experts/`)
This is the international analog of the careers page, and it compounds
the same way the library does.

- **Individual local experts** → `intl/experts/ROSTER.md` plus a folder
  per expert with CV, rate, availability, languages, vetting status,
  NDA. Built from every pursuit whether or not PRG wins.
- **Local firms / subcontractors** → `capture/templates/06_subcontractor_tracker.md`,
  plus `intl/templates/local_partner_teaming.md` for the teaming terms
  that differ overseas (currency, flow-downs, duty of care, anti-bribery).
- **Every** agent, partner, and hire clears
  `intl/templates/fcpa_vetting_checklist.md` and signs
  `intl/templates/fcpa_rep_letter.md` before being named in a proposal
  or paid a dollar. No exceptions, no "we'll do it after award."
- Job postings still run through the existing careers page
  (`site/careers/`) with the location field set to the post, plus
  per-country channels as paste-ready text in `05_sourcing/`. All
  pre-award postings say **contingent upon contract award.**

### 1e. Travel and access
Confirm before committing to a delivery date: visa category and lead
time, passport validity and blank pages, vaccination requirements, post
entry/clearance procedures (country clearance / eCC where applicable),
and whether the trip needs an invitation letter from the buyer. A
proposal that promises on-site presence PRG cannot lawfully achieve is
a false claim.

## Stage 2 — SUBMIT

`capture/templates/07_submission_checklist.md`, plus:
- Deadline converted to local time at the buyer's location AND ET, with
  the conversion written out. This is the single most common
  international submission failure.
- Portal submissions (UNGM, eConsultant2, bank e-procurement) are made
  well ahead — these portals cut off hard and support is slow. Save the
  submission receipt to `01_solicitation/`.
- Email correspondence from **Andrew@pacificresearchllc.com (Outlook)**.
  Claude drafts; ⛔ Andrew reviews and sends.

## Stage 3 — MONITOR

- Watch for amendments, clarifications, and Q&A on the buyer's own
  portal — UN and bank tenders post clarifications only on the portal,
  not by email. Check the portal, do not wait for a notification.
- Keep local partners and named experts warm — every 2 weeks. Overseas
  commitments go stale faster; local firms take other work.
- Track the currency. A large FX move between bid and award changes the
  margin on a local-currency contract; note it in the folder.

## Stage 4a — WIN (`capture/templates/08_win_day_setup.md`, plus)

1. `07_award/` — award doc, contract number, CO/COR or UN procurement
   officer, funded amount, currency, CLIN or deliverable structure.
2. **Project calendar** seeded from the contract, in the **post's
   timezone**, including travel windows and visa lead times.
3. **Get-paid setup** — WAWF/IPP for U.S. government; the buyer's own
   vendor-payment portal and bank details for UN/multilateral. Confirm
   the payment currency, the correspondent-bank path, and who eats the
   wire fees. Set invoice reminders against the real cycle, not the
   stated one.
4. **Insurance binds** — DBA policy in force **before anyone deploys.**
   Not after. Confirm coverage for local hires.
5. **Local hires execute** — contracts in the correct classification for
   that country's labor law, FCPA rep letters countersigned, onboarding
   against the contract start date.
6. QC plan, deliverable templates, kickoff request.

## Stage 4b — LOSS

`capture/templates/09_loss_debrief.md`. Always request the debrief —
U.S. buyers owe one; UN and bank buyers usually give a shorter
"unsuccessful bidder" briefing on request and it is still worth having.
Log the winner, the price delta if disclosed, and whether a local-firm
prime beat PRG on presence. File reusable content to `capture/library/`
and any vetted local expert to `intl/experts/` — **a lost bid that
leaves behind three vetted local experts was not a loss.**

---

## Standing rules

- **Honesty is absolute and this lane makes it easy to break.** Never
  claim in-country presence, an office, a local entity, prior work in a
  country, or a language PRG does not have. The true story is strong:
  MA in International Studies; field experience in Brazil, Peru, and
  China; Operation Allies Welcome (25K+ evacuees, interagency/CDC
  compliance); a U.S. veteran-owned firm with a documented management
  system. Local partners supply local presence and are **named as
  partners.** "Through our teaming partner [Firm], PRG will…" is
  accurate; "PRG's Lima office" is a lie.
- Every response cites the tender's own scope language.
- Set-aside posture per `intl/GATE.md` §A. Advocate on U.S. overseas
  buys; one credibility line in UN/multilateral lanes; never claim
  entitlement.
- Anti-bribery vetting before naming, before paying. The travel-and-
  hire-locally model's #1 legal risk is an agent PRG did not vet.
- No pursuit in a high-threat post without all six RISK lines answered.
- The library compounds; the expert roster compounds. File after every
  bid, win or lose.
