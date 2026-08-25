# PRG SBIR/STTR — workflow (sbir-v1)

**SCREEN → VERIFY → ENGAGE → PARTNER → SUBMIT → MONITOR → WIN/LOSS**

The contract lane's pipeline (`capture/WORKFLOW.md`) does not transfer.
An STTR is not a contract PRG primes and subcontracts out; it is a
research award with a named PD/PI, a mandatory 40/30 work split, and an
IP allocation agreement to negotiate. Different gate, different clock,
different documents.

---

## 0. Run it

```
python3 sbir_sttr_pipeline.py                     # full run, writes the digest
python3 sbir_sttr_pipeline.py --dry-run           # print only, persist nothing
python3 sbir_sttr_pipeline.py --all               # include UNCHANGED rows
python3 sbir_sttr_pipeline.py --ic-table          # verified IC budget caps
python3 sbir_sttr_pipeline.py --institute-scan    # which institute to aim at
python3 sbir_sttr_pipeline.py --explain PA-27-102 # gate trace for one FON
python3 sbir_sttr_pipeline.py --selftest          # offline gate assertions
```

Digests land in `sbir/reports/`. The seen-list is `sbir/state/seen.json`
and is committed — it is what makes a repeat run surface only what is
NEW or CHANGED. `sbir/state/nofo_cache.json` is not committed; it is
rebuilt in one run.

**Read the source-health table at the top of every digest before reading
the ranking.** Four of the eight sources are routinely unavailable and
the digest says which. A partial sweep must never be read as complete.

---

## 1. SCREEN

`sbir/GATE.md`, six gates, cheapest first, stop at the first fail. The
pipeline does this and records the gate that fired on every candidate in
the kill ledger, so a screen-out is auditable rather than invisible.

Then read the ledger, not just the shortlist. The kill reasons are where
a mis-scored row shows up.

## 2. VERIFY — before anything is written

Three numbers get checked by hand against a primary source before a
single hour goes into an application:

1. **The announcement number and its exact title.** From grants.gov or
   the NIH Guide, not from the digest, not from memory.
2. **The next due date**, and whether it is a standard cycle date or a
   one-off. NIH standard receipt dates are Sep 5 / Jan 5 / Apr 5 for
   this program, and grants.gov's own `responseDate` field is the LAST
   cycle date, not the next one. That trap is handled in code and should
   still be checked by eye.
3. **That institute's Phase I and Phase II cap.** They are not uniform:
   `--ic-table` prints the verified table, and the spread runs from the
   bare SBA guideline to $700K Phase I / $3M Phase II.

## 3. ENGAGE — call the program officer

The single highest-yield hour in this whole pipeline, and the one most
applicants skip.

Gate 6 names the PO who signed the most awards in PRG's lane at that
institute. Call before writing, not after. Ask three things:

- Is this idea responsive to what the institute wants under the parent?
- Would the institute consider a budget above the SBA guideline for it,
  and under which waiver?
- Is there a NOSI or an upcoming reissue that would be a better home?

Nothing about this call is binding and none of it is a commitment. Log
it in `sbir/PIPELINE.md` with the date and what was said.

## 4. PARTNER — the long pole, start it first

For a first STTR this is the schedule driver and the reason Gate 5 wants
90+ days:

1. Identify the named PD/PI at the partner institution (see the partner
   map in `sbir/PROFILE.md`). Ask; do not assume.
2. Confirm the PD/PI will commit **at least 10% effort** and hold a
   formal appointment with or commitment to PRG. It need not carry a
   salary, but it must be a real, documented relationship.
3. Route through the institution's **Office of Technology Licensing /
   sponsored projects**. The **IP allocation agreement** is required and
   is what takes the weeks.
4. Model the **40% PRG / 30% institution** split in the budget before
   promising scope to anyone.
5. Nothing names a partner in any document until they have agreed in
   writing. Same rail as `intl/COMPLIANCE_RAILS.md` Rail 2.

## 5. SUBMIT

Registrations first, because they gate everything and they are slow:
SAM (active — PRG has this), eRA Commons, SBA Company Registry, and an
ORCID linked to the PD/PI's eRA Commons profile. NIH warns registration
can take six weeks and that being late is not an excuse.

Applications are due **5:00 PM local time of the applicant
organization** on the due date.

Reuse from `capture/library/` where a variant exists — the company
profile, past performance, and the capability language are shared with
the contract lane. File improvements back after every submission.

## 6. MONITOR

Summary statement and score post to eRA Commons after review; council
review and earliest start date follow the cycle table in the
announcement. Log every state change in `sbir/PIPELINE.md`.

## 7. WIN / LOSS

**Win:** the STTR-specific version of `capture/templates/08_win_day_setup.md`
— plus the IP allocation agreement executed, the partner subaward
issued, and the 40/30 split tracked against actuals from month one.

**Loss:** request the summary statement, read the resubmission window
(the same cycle reopens in four months), and file reusable
specific-aims and approach language back to `capture/library/`. A first
STTR that scores but does not fund is a resubmission, not a loss.

---

## Scheduling

`.github/workflows/sbir-sttr-digest.yml` runs the pipeline weekly, commits
the digest and the updated seen-list, and opens a GitHub issue when
something NEW or CHANGED clears the gates — so the digest arrives rather
than needing to be polled. It runs `--selftest` first and fails the job
if the gate assertions break, so a scoring regression is loud.
