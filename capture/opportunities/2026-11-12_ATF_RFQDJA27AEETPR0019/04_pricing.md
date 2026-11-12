# Pricing Worksheet — RFQDJA27AEETPR0019 · NCETR Instructor Services BPA

**Fulfillment model:** professional services (1099 credentialed instructor
SMEs, PRG primes and manages) → **target margin band 30–50%, floor 22%.**

**Status: NOT SUBMISSION-READY. No rate is quotable yet.** The structure,
the wrap chain and the decision arithmetic below are complete and checked.
Three inputs are missing, each named with the source it must come from.
Nothing here is an invented rate, and no number below may be copied into a
quote until §6 closes.

## 0. What the Government is buying, priced

A **fixed full-day rate per labor category, per ordering period** — 6
categories × 5 ordering periods = 30 CLIN lines, each QTY 1 / UNIT DAY.
Billing is actual time worked.

The day rate **must absorb** (RFQ §6, matrix D7):
- instruction, range activities, course development
- **travel time** and preparation time
- local travel (not reimbursable)

Reimbursed **outside** the rate as ODC under the FTR: travel, lodging,
per diem.

Half-day orders bill at full day rate ÷ 2 (matrix D8) — so the full-day
rate must stay viable when halved.

## 1. Direct labor — REQUIRED INPUT, NOT HELD

| CLIN | Labor category | Source required | Held? |
|---|---|---|---|
| 0001 | Explosives Specialist | Signed 1099 day-rate quote | ❌ |
| 0002 | Fire/Arson Specialist | Signed 1099 day-rate quote | ❌ |
| 0003 | Exercise Support Specialist | Signed 1099 day-rate quote | ❌ |
| 0004 | Technical Operations Specialist | Signed 1099 day-rate quote | ❌ |
| 0005 | NCD Academy Canine Trainer | Signed 1099 day-rate quote | ❌ |
| 0006 | NORT Canine Trainer | Signed 1099 day-rate quote | ❌ |

**Wage determination: UNRESOLVED and blocking.** FAR 52.222-41 Service
Contract Labor Standards is incorporated (RFQ p.1171) but no WD is
attached to the solicitation. If SCA applies, a WD rate + H&W fringe sets
a hard floor under every category. If the instructors are exempt
professionals under 29 CFR 541, it does not. **CO question drafted at
`03_proposal/co_question_draft.md`; questions due 2026-11-18. ⛔ not sent.**

Permitted rate sources per CLAUDE.md: wage determination, signed quote,
GS grade/step/locality, or BLS SOC. A BLS SOC anchor was attempted this
run and could not be retrieved (`api.bls.gov` returned the unregistered
daily-threshold error, and `www.bls.gov` returned 403). It must be pulled
with a registered key, or substituted by the signed quotes above.

## 2. Wrap chain — verified

**W2 path** (if PRG employs an instructor rather than contracting one):

    base salary × 1.2348 (FICA/FUTA/SUTA/WC + fringe)
                ÷ 1,879 productive hours
                × 1.12 overhead
                × 1.10 G&A
                = burdened hourly

Sanity check, confirmed arithmetically this run:
`1.2348 × 1.12 × 1.10 ÷ 1,879 = 0.00080962`; reciprocal = **1,235.16**.
So **base ÷ 1,235 = burdened hourly** ✓ (chain is internally consistent).
Day rate = burdened hourly × 8.

**1099 path** (the model for this BPA — no PRG fringe or payroll tax):

    sub day rate × 1.12 overhead × 1.10 G&A = PRG cost/day
                 = sub day rate × 1.232

**Price = cost ÷ (1 − margin).**

## 3. Margin sensitivity — arithmetic on an unknown, NOT a quote

What PRG would have to charge per day at each possible sub rate. The
left column is a variable, not a market estimate.

| Sub day rate (unknown) | PRG cost/day (×1.232) | Price at 22% floor | Price at 35% target |
|---|---|---|---|
| $600 | $739.20 | $947.69 | $1,137.23 |
| $800 | $985.60 | $1,263.59 | $1,516.31 |
| $1,000 | $1,232.00 | $1,579.49 | $1,895.38 |
| $1,200 | $1,478.40 | $1,895.38 | $2,274.46 |
| $1,500 | $1,848.00 | $2,369.23 | $2,843.08 |

Read it the other way to size a recruiting target: a day rate PRG judges
defensible as reasonable, ÷ 1.232 ÷ (1 ÷ (1 − margin)), is the most PRG
can pay an SME and hold that margin.

## 4. Why margin survives here — the structural finding

On most set-aside buys PRG's management margin is competed away by a
vertically integrated competitor. **Not on this one.** RFQ §6:

> "Though price is not rated, price reasonableness will be determined by
> the contracting officer in accordance with FAR 12.204."

Award is Acceptable/Unacceptable on technical capability, per labor
category, with past performance neutral if absent. PRG is therefore not
required to be the low bidder — only technically acceptable and
*reasonable*. That is the condition under which the aggregation model
actually clears its margin band, and it is the reason this notice was
selected over the higher-ranked VA trade notice (see run report).

Consequence for pricing strategy: price inside the band and make
reasonableness trivially easy for the CO to confirm — show the basis.
Do not shave margin to buy a score that does not exist.

## 5. Compliance checks

- [x] **Limitation on subcontracting** — FAR 52.219-14, 50% services cap.
      SB set-aside: sole-proprietor 1099 SMEs are similarly-situated small
      business concerns, so the cap is **not binding** on this structure.
      Confirm each SME's small-business status at agreement signing.
- [x] **Nonmanufacturer rule** — n/a, services.
- [ ] **Price ≥ cost at the 22% floor** — cannot be evaluated until §1 closes.
- [ ] **CLIN structure matches the schedule exactly** — 30 lines, 6
      categories × 5 ordering periods, QTY 1 / UNIT DAY. Build from the
      RFQ table verbatim.
- [ ] **Half-day viability** — confirm the rate holds when halved (D8).
- [ ] **Escalation across ordering periods 2–5** — the schedule prices each
      ordering period separately; decide escalation and state the basis.

## 6. Gate — all three must close before a quote exists

1. **SCA/WD answer from the CO** (question due 2026-11-18) — sets or
   removes the cost floor.
2. **At least one signed 1099 day-rate quote per category PRG intends to
   bid.** Bid no category without one.
3. **An identified, qualified, residency-eligible SME per bid category**,
   agreed in writing before being named anywhere (CLAUDE.md honesty rail).

If a category cannot close all three by ~2026-11-25, **drop that
category** and bid the rest. Ratings are per-category, so a dropped
category costs nothing on the others.

If no category closes, the answer is **no-bid this window and on-ramp in
the 2027-10-15 → 2027-10-31 window**, not a thinner margin.
**PRG DOES NOT PERFORM AT A LOSS.**

## 7. Working capital

| Item | Amount |
|---|---|
| Monthly burn (1099 instructor payments) | Order-driven; no standing bench cost between BPA calls |
| Payment terms (matrix D5) | Prompt Payment Act — 30 days from receipt of a proper invoice |
| Float carried before first payment | ~1 order cycle of SME payments + ODC travel outlay |
| Covered by | Mirror 1099 terms to pay-when-paid or net-45 so the float is not all on PRG |

A BPA carries no guaranteed volume — there is no standing payroll between
calls, which is the main working-capital advantage of this structure over
a staffed services contract.
