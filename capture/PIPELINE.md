# PRG Capture Pipeline — live status board
> **Last updated: 2026-08-17 (Sunday)**

## 🎯 Active pursuits

| # | Pursuit | Stage | Deadline | Next action | Owner |
|---|---------|-------|----------|-------------|-------|
| 1 | **36C24E26Q0054** — VA GCP CRQA Monitoring · SDVOSB set-aside · IDIQ $20K min/$2M ceiling | PURSUE — sections drafted; CO confirmed email submission ("Correct," 8/14); Section 6 = neutral strategy; quals corrected to coordinator-truth | **Quote due Mon Aug 25, 10:00 ET** | ⚠️ DECISION: Lead monitor = hired CCRA / Andrew+training / both (rec: both). Then: CCRA picks from 73 applicants, 4 JAMA citations, docx assembly (Claude, review by 8/20) | Andrew decides → Claude assembles |
| 2 | **N323988871** — NMRC Fort Detrick BMET · $249.5K est / 30 mo | RFI SUBMITTED ✅ on time (8/14) | Watch SAM for the RFQ | Verify wage determination the day RFQ drops; BMET applicant screening | Claude watches |

## ✅ Closed out
- **36C26326Q1034** — VA NCO 23, BD Pyxis (CATO). CO confirmed sole
  source to CareFusion Solutions; notice description opens "NOTICE OF
  INTENT TO AWARD SOLE SOURCE." PRG conceded and withdrew (reply sent
  8/19). **Not pursuable.** Exposed the description-hydration defect —
  the matcher had been screening titles, not scopes; fixed 8/19.

## 🔧 Pre-award rails (PREAWARD_READINESS.md)
- SAM EBiz POC update — IN PROGRESS (Andrew, via update wizard)
- PIEE: blocked on CAGE group — call help desk **866-618-5988** AFTER SAM update processes; registration saved
- Tungsten/VA e-invoice portal — TODO (~20 min, any time)
- Payroll/insurance/QuickBooks — arrange-now, bind-at-award

## 📣 Recruiting
- CRQA posting: **73+ applicants (Indeed)** — screen for CCRA holders (bid-critical if path A/C)
- BMET posting: live on LinkedIn/Indeed/careers
- Careers page LIVE on pacificresearchllc.com ✅

## 🗓️ Week of Aug 18
Mon–Tue: monitor decision + CCRA shortlist + JAMA citations → Wed 8/20: full quote package for Andrew's review → Fri 8/22: final fixes → Sat–Sun 8/23–24: SUBMIT → Mon 8/25 10:00 ET deadline.

## 📤 Sent log — 2026-08-21 (domestic)

Non-binding correspondence, sent under the 8/20 amendment (`CLAUDE.md`
BIAS TO ACTION). No priced document was sent; none was built.

| Notice | Buyer | Scope | Sent to | Response due |
|---|---|---|---|---|
| 140G0226Q0150 | DOI | Oxford Instruments AZtec maintenance (H166) | Jennifer Rollin | 2026-08-21 12:00 MT — **made it with ~90 min to spare** |
| 36C25026Q0907 | VA | J065 GE Telemetry & Physiology | Janel Tate-Montgomery | 2026-08-24 09:00 ET |
| 36C261-27-AP-0240 | VA VISN 21 SF | Terumo System 1 heart-lung bypass maintenance — **SDVOSB set-aside under consideration** | Robert Clark | 2026-08-25 12:00 ET |
| 75N98026Q01027SSN | DOI | Leica PM / service agreement (J066) | Yvette Sornberger | 2026-08-25 14:30 ET |
| FTA Drug & Alcohol Compliance Audit Support | DOT/FTA | 49 CFR Part 40/655 grantee audits (NAICS 541611) | Cassandra Porter-Hickman, cc Crystal Zorich | 2026-09-08 17:00 ET |

Every one disclosed plainly where PRG lacks OEM authorization rather
than implying it. The Terumo response asks the one question that decides
the competition: whether VA will require the servicing technician to
hold OEM authorization — that requirement, not business size, sets how
many SDVOSBs can actually compete.

**PASS — NHGRI-08891** (Illumina DRAGEN throughput license + v4 server):
pure license and hardware resale, no services labor. Kill #1.

**Lost to the API quota:** 36C25926Q0750 (VA BioMed, SDVOSB, due today)
— its description never hydrated and the deadline passed before the
keyless fallback existed.

## ✅ Reconciled 2026-08-21 — the 8/17 send queue was already sent

`capture/SEND_QUEUE.md` sat in the repo asking the next session with
Outlook access to send 18 sources-sought responses plus one CASS draft.
**All 19 had already gone out on 2026-08-18** — the batch at 20:53–20:55
UTC, the CASS response at 01:11 UTC — and nobody stamped the JSON or
deleted the queue file afterward.

Verified against Outlook Sent Items, all 18 matched by solicitation
number; `capture/reports/ss_batch_2026-08-17.json` now carries a
`sent_at` on every entry. Queue file deleted, as its own last line
instructed once the batch was confirmed sent.

**What the stale file would have cost.** Processing it as written meant
19 duplicate emails, including a second copy of the BD PYXIS response to
Joshua Imdacha (36C26326Q1034) — the CO who had already written back to
explain that notice was a sole-source intent, not a competitive
solicitation. Two identical capability responses into a notice we were
already corrected on is not a clerical slip; it is the thing that makes
a CO stop reading PRG's mail.

This is exactly why the send gate is now the mailbox and not a repo
file (`CLAUDE.md`, BIAS TO ACTION amendment): a repo file records what a
session INTENDED to send, and goes stale the moment the send happens
somewhere else. Sent Items records what actually left.

Three of the 18 should never have gone at all — 36C26326Q1034 and
140D0426Q0851 were sole-source, W15QKN-26-Q-A171 an intent-to-award.
That is the defect the description-hydration fix and the non-competitive
gate now catch before drafting.
