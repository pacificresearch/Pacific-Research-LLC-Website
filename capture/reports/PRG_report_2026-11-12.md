# PRG Domestic Capture Run — 2026-11-12

**Published report:** https://claude.ai/artifact/1w5Y8pgJY549Dp7KKgFf1c
**Notices screened:** 752 (6 core + 32 low-barrier NAICS, `--days 7`)
**Matcher:** `samgov_opportunity_matcher.py --days 7`, exit 0, 13:04:26 →
13:06:03 UTC (97 s)
**Repo state at run:** `main` @ `732dbab`
**Artifacts:** `/root/PRG_Executive_Report_2026-11-12.html`,
`/root/PRG_Contracts_2026-11-12.xlsx`

Coverage: 7 core-eligible, 97 low-barrier plays, 361 subcontracting/teaming
targets, 131 SDVOSB set-asides. Published pipeline value $176.2M across the
12 notices that stated a figure (a floor, not a total).

---

## SELECTED — current contract under consideration

**RFQDJA27AEETPR0019 — ATF/NCETR Instructor Services BPA. BID AS PRIME.**

| | |
|---|---|
| Agency | DOJ / ATF, National Center for Explosives Training and Research |
| Location | Huntsville, AL 35806 |
| Set-aside | 100% Small Business (NAICS 611430, PSC R499) |
| Vehicle | Multiple-award Firm-Fixed-Price BPA, FAR 13.303, 60 months / 5 ordering periods |
| Value | $500K simplified acquisition threshold |
| Quote window | opens **2026-11-16**, due **2026-11-30 17:00 ET** |
| Questions due | **2026-11-18** |
| Fulfillment | professional services — 1099 credentialed instructor SMEs, PRG primes |
| Folder | `capture/opportunities/2026-11-12_ATF_RFQDJA27AEETPR0019/` |

Why this one, over the three notices the matcher ranked above it:

- **Price is not rated.** RFQ §6: *"Though price is not rated, price
  reasonableness will be determined by the contracting officer in
  accordance with FAR 12.204."* Award is Acceptable/Unacceptable on
  technical capability **per labor category**. PRG's management margin is
  not competed away — rare, and the whole reason this is the selection.
- **No past performance is rated neutral**, and non-submittal explicitly
  does not affect award. A genuine first-contract opening.
- **Multiple award**, with annual on-ramp windows each Oct 15–31 through
  2030. Missing this window is recoverable.
- All seven capture-v3 hard kills checked and cleared — including #5: the
  Public Trust background investigations are *personnel* suitability
  (Tier 1/2/4, SF-85P), **not** a facility clearance at proposal.
- LoS 50% cap is **not binding**: on an SB set-aside, sole-proprietor 1099
  SMEs are similarly-situated small business concerns.

Six labor categories: Explosives Specialist, Fire/Arson Specialist,
Exercise Support Specialist, Technical Operations Specialist, NCD Academy
Canine Trainer, NORT Canine Trainer. Each accepts HS/GED + 15 years in
place of a degree, which widens the recruitable pool.

### Staged, not priced — and why

The compliance matrix is built and closed on every row that the
solicitation can close. **No quote exists and none could honestly be
produced today.** Three inputs are missing, each named with its source in
`04_pricing.md §6`:

1. **FAR 52.222-41 Service Contract Labor Standards is incorporated
   (RFQ p.1171) but no wage determination is attached.** If SCA applies, a
   WD sets a hard floor under all six categories; if the instructors are
   exempt professionals under 29 CFR 541, it does not. This is the
   blocking item. CO question drafted, **⛔ not sent** — questions due
   2026-11-18.
2. **No signed 1099 day-rate quote for any category.** Recruiting has not
   started.
3. **No identified SME per category.** Nothing and no one is named, per the
   written-agreement-first honesty rail.

A BLS SOC anchor was attempted as an interim citable source and could not
be retrieved (`api.bls.gov` unregistered daily threshold; `www.bls.gov`
403). Rather than invent a rate, `04_pricing.md` carries the verified wrap
chain and a margin sensitivity table over sub day rate as a variable.

Wrap chain verified this run: `1.2348 × 1.12 × 1.10 ÷ 1,879 = 0.00080962`,
reciprocal **1,235.16** — so `base ÷ 1,235 = burdened hourly` ✓.
1099 path: `sub day rate × 1.232 = PRG cost/day`; `price = cost ÷ (1 − margin)`.
Professional services band 30–50%, **floor 22%**.

---

## NO-BID — with the numbers

**36C25027Q0078 — VA Fire Suppression System Maintenance and Kitchen
Exhaust Cleaning. PASS.** Richard L. Roudebush VAMC, Indianapolis IN,
SDVOSB set-aside, due 2026-12-01 10:00 ET. The matcher ranked this #3
Green at priority 77 and labelled it *"founder-delivered, est. GM 40–60%,
PURSUE AS SUBCONTRACTOR"*. All three of those labels are wrong, and the
full solicitation says why.

Verified scope (base CY2027 + 4 option years, 12 MO per CLIN, Appendix B):
5 kitchen suppression systems (NFPA 17A / ANSUL R-102) + 5 Kidde IND-21
Hazmat dry chemical systems; 120 monthly unit inspections/yr; 20 unit
services/yr across 2 semiannual visits; 20 hood inspections and 20
complete NFPA 96 hood cleanings/yr; 4 grease-trap pump-outs/yr.

Two sourced facts kill it together:

1. **Award basis is "Price Alone"** (52.212-2 OCT 2025 DEVIATION, RFQ
   p.56). No technical factor, no past-performance factor.
2. **Limitation on subcontracting, Services box (i) checked**: PRG "will
   not pay more than 50% of the amount paid by the government to it to
   firms that are not listed in SBS as SDVOSBs or VOSBs."

And PRG can self-perform essentially none of it: **Kidde IND-21
maintenance "shall be performed by factory-authorized Kidde service
personnel with documented IND training"** (§4 Personnel Qualifications) —
an OEM authorization PRG cannot hold or hire into. NFPA 96 hood cleaning
needs certified cleaners; the grease trap needs a permitted waste
transporter and receiving facility. PRG's self-performable share is the
monthly visual inspections plus PM/QC/admin.

The arithmetic: to hold subcontract payments at or below 50% of the award
while subcontracting all credentialed work to non-SDVOSB firms, PRG's
price must be **at least 2× the subcontract cost of the technical work**.
A self-performing SDVOSB fire-protection contractor — and VA's 811310
SDVOSB pool in Indiana is populated with exactly those — bids its own
cost plus a normal margin, with no middle layer. On Price Alone, the
compliant PRG price loses by construction. The competitive price is
non-compliant with the 50% certification and lands below the 6%
trade-sub-management floor.

Compliant is uncompetitive; competitive is non-compliant. **PASS.**
Not a thinner margin — PRG does not perform at a loss.

Wage determination on file for reference if a similar Indianapolis notice
appears: **WD 2015-4787 rev 34, 8/12/2026** — Fire Extinguisher Repairer
(23310) $25.57/hr, Fire Alarm System Mechanic (23290) $27.23/hr, General
Maintenance Worker (23370) $23.81/hr, H&W $5.92/hr, 11 holidays, 2 weeks
vacation after 1 year.

### Also passed on this window

- **SPE7LX27U0564** (53--SEAL,ROPE,AIRCRAFT) and **SPE7M527U0075**
  (59--ADAPTER,CONNECTOR) — DLA DIBBS parts buys. Hard kill #1, pure
  resale with no services labor. The matcher mislabelled both
  "professional services".
- **F3G1EB6257AG01** (30 RS Mission Planning Software Tool, due
  2026-11-20) — 8 days out, below the 10-day minimum lead for a teaming
  play. **⏳ EXPIRING-SOON**, kept visible, not queued as ready-to-work.
- **36C25027Q0078 J061 Eaton Powerware** — OEM-authorization risk, Red.
- **2027_PROMISE** (NASA polar rover R&D) — no credible PRG path as prime.

---

## Outbound

**Nothing was sent. Step 5 was not performed.** Two independent reasons:

1. **It is gated.** CLAUDE.md's standing carve-outs and
   `capture/DAILY_RUN.md:173` — *"⛔ NEVER auto-send email to a
   contracting officer"* — both require Andrew. The scheduled prompt's
   step 5 instructs sending non-binding correspondence; the repo's own
   standing order overrides it. Prepare and notify, never auto-submit.
2. **No `mcp__Microsoft_365__` tools exist in this session**, which is the
   scheduled prompt's own stated condition for skipping the step. Outlook
   is reachable only under a differently-namespaced server, so the
   sent-items dedup check by notice number could not be run as specified.
   Never send unchecked.

One item is staged and ready for Andrew:
`2026-11-12_ATF_RFQDJA27AEETPR0019/03_proposal/co_question_draft.md`
— the SCA/WD clarification question. **Send by 2026-11-18** or the
pricing floor stays unresolved.

---

## Run notes

- `capture/PRICING.md` does not exist. The scheduled prompt cites that
  path; the domestic pricing doctrine actually lives in
  `capture/templates/04_pricing_worksheet.md`, with worked precedent in
  `capture/opportunities/*/04_pricing.md`. Prompt path should be corrected.
- The run took 97 s. The scheduled prompt treats a sub-2-minute run as
  suspect, but 752 notices were screened with full output — the duration
  heuristic is a weak proxy and fired a false positive here. The real
  signal is the screened count.
- SAM quota had been exhausted (HTTP 429, "exceeded your quota, access
  after 2026-Nov-12 00:00 UTC") when checked on 2026-11-11. It reset on
  schedule and this run went through cleanly.
- `capture/check_sam_key.py` reports **"SAM CREDENTIAL IS DEAD"** on a
  429, because every non-401/403 HTTP error falls through to the dead-key
  branch. A 429 is quota exhaustion, not a rejected key, and the renewal
  instructions it prints are wrong for that case. Needs its own branch.
