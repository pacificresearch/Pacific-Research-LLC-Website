# Invoice template + limitation-on-subcontracting tracker

Two things that must stay in lockstep: what you bill, and the evidence
that the way you performed it was compliant. Track them in one place or
you will reconstruct the second one under audit pressure.

## Part 1 — Invoice

Build the invoice **from the contract's own required fields**, checked
against diff-checklist row 15. Missing a required field is the most
common reason a government invoice is rejected, and a rejected invoice
restarts the payment clock.

| Field | Value |
|---|---|
| Contractor | Pacific Research Group LLC |
| UEI / CAGE | J585TLDV1CH1 / 1Z9B6 |
| Remit-to (must match SAM EFT) | |
| Contract number | |
| Task/delivery order number | |
| Invoice number (sequential, never reused) | |
| Invoice date | |
| Billing period | from – to |
| Payment office | |
| CO / COR | |

| CLIN | Description | Unit | Qty this period | Unit price | Amount |
|---|---|---|---|---|---|
| | | | | | |
| | | | **Period total** | | |

| Cumulative | Amount |
|---|---|
| Billed to date | |
| Contract value / ceiling | |
| Remaining | |

**Attachments per contract requirements:** deliverable acceptance
evidence, timesheets, receipts for reimbursables, subcontractor invoices.

### Submission checklist
- [ ] Submitted through the system the contract names (WAWF/PIEE, IPP,
      agency portal) — not by email unless the contract says email
- [ ] Every required field populated
- [ ] Amounts tie to accepted deliverables, not to work merely performed
- [ ] Invoice number sequential and unused
- [ ] Submission confirmation saved to `07_award/`
- [ ] Payment follow-up date on the calendar

## Part 2 — Limitation on subcontracting tracker

Applies to set-aside awards. For **services**, at least **50%** of the
amount paid by the government must be spent on employees of PRG or of
**similarly situated entities** (other SDVOSB/VOSB concerns on an
SDVOSB set-aside).

**What counts toward PRG's half:** PRG W2 employees; similarly-situated
subcontractors. **What does not:** subcontractors and 1099 contractors
that are not similarly situated. This is measured over the **period of
performance**, so track it every invoice period rather than discovering
it at the end.

| Period | Total billed | PRG employees | Similarly-situated subs | **Compliant share** | % | Other subs | Cumulative % |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

- [ ] Cumulative compliant share ≥ 50% — if it is drifting below, fix
      the staffing mix now, not at closeout
- [ ] Similarly-situated status **verified in SAM** at the time of
      subcontracting, and re-verified if the sub's status could lapse
- [ ] Supporting payroll and sub-payment records retained

**Compliance is certified, not estimated.** If you signed a Certificate
of Compliance at bid time, this table is how you prove it.
