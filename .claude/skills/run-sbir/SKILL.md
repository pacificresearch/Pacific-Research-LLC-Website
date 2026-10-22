---
name: run-sbir
description: Run the full PRG SBIR/STTR capture cycle end to end — sweep NIH and grants.gov for small-business R&D opportunities, apply the six gates in sbir/GATE.md, verify every announcement number, deadline and budget cap against a primary source, and produce the ranked digest with a go/no-go on each. Use when Andrew says "run sbir", "run the sbir system", "/run-sbir", "check STTR", or asks for the SBIR/STTR run or digest.
---

# Run the SBIR/STTR system

One command for the R&D-grant lane, the way `/run-international` is one
command for the overseas lane. This is a **separate system** from the
contract capture pipeline — do not run `capture/WORKFLOW.md` or the
capture-v3 gate against an SBIR/STTR announcement, and do not run this
gate against a solicitation.

Read `sbir/GATE.md` and `sbir/PROFILE.md` before interpreting anything.

---

## Steps

### 1. Self-test, then sweep

```
python3 sbir_sttr_pipeline.py --selftest
python3 sbir_sttr_pipeline.py
```

If the self-test fails, **stop and fix it before reporting anything.**
A gate that mis-scores silently is worse than no run.

### 2. Report the source health FIRST

Before the ranking, state which sources came back and which did not.
SBIR.gov and DoD DSIP are normally blocked from this network, and
Simpler.Grants.gov and SAM.gov need credentials. Four of nine missing is
the normal state, and it must be said out loud every time:

> "This sweep covers NIH and grants.gov. SBIR.gov cross-agency topics
> and DoD DSIP were unreachable, so no non-NIH topic was screened."

Never present a partial sweep as complete. Never quietly drop a source.

### 3. Read the kill ledger, not just the shortlist

The ledger names the gate that fired on every screened-out candidate.
Scan it for a row that looks mis-scored — a real opportunity killed at
Gate 3 for lack of vocabulary, or an administrative notice that got
gated as though it were an opportunity. Those are pipeline bugs, and
they are fixed in `sbir_sttr_pipeline.py`, not worked around by hand.

### 4. Verify the three numbers by hand on anything actionable

For every row Andrew might actually act on, re-check against the primary
source the digest cites:

- the **announcement number and exact title**,
- the **next due date** — and remember that grants.gov's `responseDate`
  is the LAST cycle date on an NIH omnibus, not the next one,
- **that institute's** Phase I and Phase II cap
  (`python3 sbir_sttr_pipeline.py --ic-table`).

**Never state one of these three from memory.** If it cannot be
verified, say so in the report.

### 5. Update the board

Add or move any row Andrew is working in `sbir/PIPELINE.md`, and append
a dated line to its log.

### 6. Report, and stop at the engagement gate

Lead with the decision on each surviving row, one reason each. Then say
what the next action is.

**⛔ The gate: nothing outward-facing goes without Andrew.** Consistent
with the standing carve-outs in `CLAUDE.md`:

- **Do not email a program officer.** Draft the call agenda or the
  email and hand it over. The PO call is the highest-yield hour in this
  pipeline and it is Andrew's to make.
- **Do not contact a prospective academic partner**, and do not name any
  Stanford investigator, department, or center as a partner in any
  document until they have agreed in writing. Same rail as
  `intl/COMPLIANCE_RAILS.md` Rail 2 — the partner map says who PRG would
  *ask*, not who has said yes.
- **Do not submit an application** or any registration that makes a
  binding eligibility declaration.

Everything internal — the digest, the analysis, the drafts, the board,
repo work — just do it. That is the standing bias-to-action order and it
applies here in full.

---

## Other modes

```
python3 sbir_sttr_pipeline.py --institute-scan PA-27-102
```
Ranks every participating institute by verified budget cap and by how
crowded and how PRG-shaped its actual STTR portfolio is. Use this when
the question is "which institute should I aim at", not "what is open".

```
python3 sbir_sttr_pipeline.py --explain PAR-27-040
```
Full gate trace for one announcement — the fastest way to answer "why
did the pipeline kill this?"

```
python3 sbir_sttr_pipeline.py --all
```
Ignore the seen-list and show the standing shortlist, not just what
changed.

---

## The two things that must never happen

1. **Never invent an announcement number, a deadline, or a budget cap.**
   Every one of the three carries the URL it was read from. Where the
   run could not verify a figure it prints `NOT VERIFIED`, and so should
   you.

2. **Never let a failed source disappear.** If a source did not return
   data, the report says which one and what was therefore not screened.
