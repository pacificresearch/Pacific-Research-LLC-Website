# PRG pricing system — domestic

**Standing order (Andrew, 8/20): PRG does not perform at a loss. Ever.**

A price below the floor in §4 is not a stretch, an investment, or a
past-performance play. It is a no-bid. Walking away from a contract PRG
cannot profit on is a *good* outcome and gets reported as one.

This file is how PRG builds a number when Andrew does not already know
what the work costs — which is most of the time, across most of these
NAICS codes. It replaces guessing with a chain: **every price traces to
a rate somebody publishes, a quote somebody signed, or a stated
assumption.** Nothing is invented.

International pricing adds country risk, DSSR travel, DBA insurance and
withholding tax on top of this — see `intl/PRICING.md`. The wrap chain
below is shared by both lanes.

---

## 1. The wrap chain — how a salary becomes a billable rate

One formula, used every time, so two bids priced a month apart are
comparable.

```
                     annual base salary
        × 1.2348     fringe        (see §2)
        ÷ 1,879      productive hours per FTE-year (see §2)
        × 1.12       overhead      (see §2)
        × 1.10       G&A           (see §2)
        ─────────────────────────────────────
        = fully burdened cost per BILLABLE hour
```

**Shortcut, accurate to a cent:**

> **burdened hourly cost = annual base salary ÷ 1,235**
>
> **fully burdened annual cost = annual base salary × 1.52**

$105,000 base → $85.01/billable hour. $75,000 → $60.73. $140,000 →
$113.36. Use the shortcut to sanity-check in seconds; use the full chain
in the worksheet so a CO can audit it.

Then: **price = burdened cost ÷ (1 − margin)**. Not cost × (1 + margin)
— that understates. At $85.01 cost and a 19% margin the rate is
$85.01 ÷ 0.81 = $104.95, call it $105.

---

## 2. Where each factor comes from — and when to change it

| Factor | PRG standing value | Source | Change it when |
|---|---|---|---|
| **Fringe** | **23.5% of base** | FICA 7.65% + FUTA/SUTA + workers' comp + $1,000/mo health/dental/vision | **SCA-covered work: replace with the wage determination's H&W rate outright** — the WD governs, not this number. High-wage roles: FICA caps out, so 23.5% is conservative (fine). |
| **Productive hours** | **1,879** | 2,087 standard − 88 holiday (11 federal days) − 120 PTO (3 weeks) | Contract specifies different holidays, or the role is part-time/intermittent. Never use 2,080 — that bills PTO and holidays to the client, and they aren't billable. |
| **Overhead** | **12%** | Recruiting, background investigations (~$230 ea), role credentialing and training, laptop/VPN/software, GL + professional liability, unbillable admin | A contract demands something unusual — clearances, specialty insurance, government-furnished-equipment gaps, a second site. Price the delta explicitly rather than nudging the percentage. |
| **G&A** | **10%** | PRG contract management, QC review of every deliverable, COR interface, invoicing (WAWF/Tungsten), accounting | Rarely. This is what PRG the prime actually does; it is the value-add the aggregation model sells. |

**PRG has no DCAA-approved indirect rates.** These are commercial-format
rates, which is correct for the simplified-acquisition and commercial-item
work PRG is bidding. If a solicitation demands certified cost or pricing
data or an approved accounting system, that is a separate qualification
question — flag it in the compliance matrix.

---

## 3. Get the labor rate from a published source — never from feel

In priority order. Cite which one was used, in the worksheet.

1. **Wage determination** (SCA/DBA work). Binding, not a benchmark.
   Pull the exact WD number and revision from the solicitation. Use its
   H&W in place of PRG fringe.
2. **A signed sub or staffing-firm quote** for that exact scope.
3. **GS scale + locality** for the labor category the PWS describes, when
   the buyer is effectively replacing a federal position — the VA GCP
   monitor was priced off GS-13 Step 1 Rest-of-US. This is the best
   available proxy for what the government thinks the work is worth.
4. **BLS OES** median-to-75th percentile for the SOC code and metro.
5. **Live market evidence** — actual applicants' salary expectations for
   the posting PRG ran. Weakest as a sole basis, strongest as a check on
   1–4. If 73 applicants all want $120K and the build says $105K, the
   build is wrong.

**Then close the loop before submitting:** confirm the assumed salary
against a real, willing candidate. A rate built on a salary nobody will
accept is a loss waiting for the award.

---

## 4. THE FLOOR — the walk-away line

Margin here means **(price − fully burdened cost) ÷ price**.

| Fulfillment model | Target band | **FLOOR — no-bid below** | Why the floor sits there |
|---|---|---|---|
| Founder-delivered | 40–60% | **30%** | Andrew's hours are PRG's scarcest asset; below 30% the contract costs more in opportunity than it returns |
| Professional services (FFP by deliverable) | 30–50% | **22%** | Scope creep on deliverable-based work routinely runs +20% over estimate; 22% absorbs that and still lands above zero |
| Staffing / LOE | 15–30% | **12%** | Hours are specified by the contract, so cost error is small (±5%) — but only if the CLIN is truly LOE. If PRG owns the outcome regardless of hours, price it as professional services instead |
| Value-added supply | 10–20% | **8%** | Only with a **written price hold from the distributor through the acceptance period.** Without one, the floor is 15% |
| Trade-sub management | 8–15% | **6%** | Only with a **firm written sub quote, valid past the award date, with the flow-downs accepted.** Without one, the floor is 15% |

**Below the floor, the answer is PASS.** Not a thinner margin, not a
learning bid. Write the no-bid line into the report: *"<notice> — priced
at $X, floor is $Y, no-bid."* That is a finding, not a failure.

**One exception, and it is narrow:** a sub-$50K simplified acquisition
whose real return is the CPARS record may go to the floor exactly — but
never below it, and never on a multi-year vehicle where a bad rate sets
the option-year baseline.

---

## 5. The six ways this work actually loses money

Check each one before a price leaves the folder. Most losses are not
thin margins — they are a cost that was never in the build.

1. **Firm-fixed-price on hours PRG does not control.** If the government
   sets the pace and the CLIN is FFP, the downside is unbounded. Either
   get an LOE/hours cap in writing, or price the realistic high case,
   or no-bid. This is the most common way small primes die.
2. **Flat option years against an escalating wage determination.** SCA
   WDs revise annually. Bidding years 2–5 at year-1 rates books a loss
   in year 3. **Escalate option years 3%/yr minimum**, more if the WD
   history says so. Check the WD's own revision history.
3. **ODCs left out of the build.** Travel, background investigations,
   credentialing and training, equipment, licenses, specialty insurance,
   shipping. Each one is small; together they are the margin. If the
   solicitation says travel is reimbursed at cost, price it at zero
   margin — but *price it*, and never leave a travel CLIN blank when the
   schedule wants a number.
4. **The limitation on subcontracting rewriting the cost base.** If the
   build assumes 60% of services subbed cheap, the 50% cap forces work
   in-house at PRG's higher loaded rate and the margin evaporates.
   Compute the compliant split *first*, then price it.
5. **Sub quotes that expire before award.** A quote good for 30 days
   against a 90-day award cycle means the sub reprices and PRG eats the
   delta. Get validity through the acceptance period plus 30 days, in
   writing, or carry a contingency for the gap.
6. **Working-capital float.** Net-30 from *invoice acceptance* is really
   45–75 days from doing the work, while payroll runs biweekly. This is
   not a margin problem — it is a solvency problem, and it can end PRG
   on a contract that is profitable on paper. Compute months of float ×
   monthly burn, and confirm the cash or credit exists **before** bidding.
   Mirror terms downstream: pay subs after PRG is paid, or net-45.

---

## 6. Before any number leaves the folder

All of these, every time. The worksheet
(`capture/templates/04_pricing_worksheet.md`) carries them as checkboxes.

- [ ] Every labor rate cites a §3 source by name — WD number, quote,
      GS grade/step/locality, or BLS SOC.
- [ ] Salary assumption confirmed against a real candidate, or flagged
      as unconfirmed in the notification.
- [ ] Productive hours are 1,879, not 2,080.
- [ ] Option years escalated, not flat.
- [ ] Every ODC in §5.3 either priced or explicitly marked N/A.
- [ ] Limitation-on-subcontracting split computed and ≥ 50% PRG.
- [ ] Sub quotes valid through acceptance + 30 days.
- [ ] Working-capital float computed and covered.
- [ ] **Margin ≥ the §4 floor for this model.** If not → PASS, and say so.
- [ ] Price checked against any stated ceiling, NTE, or IDIQ maximum —
      **the ceiling binds harder than the margin band.** A price above it
      is non-responsive no matter how good the margin looks.
- [ ] CLIN structure matches the solicitation's schedule exactly, unit
      for unit. Read the unit definition; "100 visits or 475 blocks"
      means the priced unit is a block.

---

## 7. How the price is presented to Andrew

Never a bare number. Always:

1. **The recommendation** — one line: unit price, total, margin.
2. **The build** — the wrap chain with the actual figures, so it can be
   audited in thirty seconds.
3. **The sensitivity table** — price at three or four salary/rate
   assumptions, with the margin at each, so the shape of the risk is
   visible.
4. **The floor** — what the no-bid number is, and how much headroom the
   recommendation has above it.
5. **The open assumptions** — anything not yet confirmed, named plainly.

Then it stages and waits. A quote is a binding offer: submitted, it
commits PRG to perform at that number for the acceptance period. Priced
documents do not auto-send (`CLAUDE.md`, BIAS TO ACTION amendment) until
Andrew records a dollar ceiling for autonomous sending.

---

## 8. Worked example — VA 36C24E26Q0054 (GCP monitoring)

The reference build. Full detail in
`capture/opportunities/2026-08-25_VA_36C24E26Q0054/04_pricing.md`.

| Step | Basis | Value |
|---|---|---|
| Base salary | GS-13 Step 1, Rest-of-US — the grade the PWS describes | $105,000 |
| Fringe | 23.5% | $24,652 |
| Productive hours | 2,087 − 88 − 120 | 1,879 |
| Direct cost/hour | $129,652 ÷ 1,879 | $69.00 |
| Overhead 12% | | $8.28 |
| G&A 10% | | $7.73 |
| **Burdened cost** | | **$85.01/hr** |
| Price at 19% margin | $85.01 ÷ 0.81 | **$105/hr** |
| Floor (professional services) | 22% → but ceiling-bound, see below | |

**What the example teaches:** the $2M IDIQ ceiling bound the price harder
than the margin band did. The build supported a higher rate; the ceiling
did not allow it. Check the ceiling before optimizing the margin.
