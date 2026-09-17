# PRG SBIR/STTR — screening gate (sbir-v1)

Run this gate FIRST on any SBIR/STTR notice, topic, or announcement,
before any analysis. Lead with one decision:

**GO / GO, CONDITIONAL / GO ON ELIGIBILITY / MONITOR–PREPOSITION /
NO-GO (THIS CYCLE) / NO-GO.**

For a NO-GO: name the gate that fired, one line, under 100 words.

This is the R&D-grant sibling of the capture-v3 contract gate in
`CLAUDE.md`. The aggregation model does not apply here — an STTR is not
a contract PRG primes and subcontracts out. It is a research award with
a mandatory 40/30 work split and a named PD/PI. So this gate asks a
different question and the two must not be run against each other.

The executable form of this document is `sbir_sttr_pipeline.py`. Keep
the two aligned when either changes, the same way `intl/GATE.md` and the
matcher's `--intl` mode are kept aligned.

---

## A. What "an opportunity" means here — get this right first

The NIH parent announcements are omnibus and always open:

| FON | Mechanism | Standard due dates |
| --- | --- | --- |
| **PA-27-100** | SBIR R43/R44 | Sep 5 2026 · Jan 5 2027 · Apr 5 2027 |
| **PA-27-102** | STTR R41/R42 | Sep 5 2026 · Jan 5 2027 · Apr 5 2027 |

*(Verified 2026-08-25 from each announcement's own Key Dates table,
fetched via grants.gov. The pipeline re-verifies both every run and
prints the URL it read them from; nothing here is copied forward on
faith.)*

**Finding those is not the task.** They are always there. Along with
PA-27-101 (SBIR Phase IIB) and PAR-27-098 (Commercialization Readiness),
they are the four documents the pipeline derives — from their own
"Companion Funding Opportunity" block, not from their titles — as the
omnibus set and excludes.

The real discovery targets are the things that carry a **signal about
what an institute actually intends to fund**:

1. **Notices of Special Interest (NOSIs)** and institute-specific PAs —
   an institute saying, in writing, what it wants under the parent.
2. **RFAs and topic-specific solicitations** with dedicated set-aside
   money and their own review panel.
3. **Contract-based SBIR topics** (PHS solicitations, DoD components),
   competed against a specific stated need rather than an open field.
4. **Announcements with a restricted eligibility field** — a mechanism
   only first-time PIs may enter thins the field more than any topical
   advantage PRG could build. See Gate 3.

And for every match, **surface the budget cap for that specific
institute**. The caps are not uniform under one parent: NCI allows
$700K Phase I / $2.5M Phase II, NHLBI $400K / $3M, NIMH $700K / $3M,
and eight components publish no figure at all beyond the SBA guideline.
`sbir_sttr_pipeline.py --ic-table` prints the current verified table.

---

## B. The six gates — cheapest first, stop at the first fail

### Gate 1 — Eligibility

US-owned for-profit small business, under 500 employees, work performed
in the US. PRG clears all three.

**Hard kills:**

- **Facility clearance** required at proposal time. PRG holds none.
- **GMP / cGMP manufacturing, clean room, fill-finish, IND-enabling.**
- **Applicant must operate a clinical site or a CLIA lab.** PRG has
  neither, and an STTR partner cannot supply what the *applicant* must
  hold.
- **Gated on a prior award** — Phase IIB, Phase II Bridge,
  Commercialization Readiness (SB1). PRG has no Phase I or Phase II.
- **A set-aside PRG is ineligible for** (8(a), HUBZone, WOSB/EDWOSB).
- **Bench- or animal-dominant scope.** This one has a nuance that
  matters: under STTR the *partnering institution may hold the lab*, so
  wet-lab language is not automatically fatal. It becomes fatal when
  (a) the mechanism is SBIR, so there is no partner to hold it, or
  (b) the scope is so bench-centric that PRG could not credibly supply
  its **mandatory 40% of the research effort**.

**Not a kill:** human-subjects work, clinical trial involvement, a
partner institution's IRB, or a topic that touches a laboratory
somewhere in the workplan.

### Gate 2 — Mechanism: STTR by default, SBIR by exception

The single most consequential fact about PRG's position:

> **SBIR** requires the PD/PI to be **primarily employed** (more than
> half time) by the small business at the time of award and throughout
> the project.
>
> **STTR** does not. Per PA-27-102: *"For the STTR program, the PD(s)/
> PI(s) may be employed with the SBC or the single, 'partnering'
> non-profit research institution as long as s/he has a formal
> appointment with or commitment to the applicant SBC… Each PD/PI must
> commit a minimum of 10% effort… Such a relationship does not
> necessarily involve a salary or other form of remuneration."*

Andrew is concurrently job searching for a full-time role. That rules
out the SBIR employment rule and leaves STTR fully available. So:

- **STTR (R41/R42) → pass.** Always flag which it is.
- **SBIR (R43/R44) → fail**, unless the work is genuinely
  solo-operator-shaped (software, analysis, curriculum, protocol,
  toolkit — no bench), in which case surface it **with the conflict
  named in the row**, never quietly.
- A dual **SBIR/STTR** notice passes on its STTR path.

Under STTR, PRG must perform **at least 40%** of the research effort and
the single partnering institution **at least 30%**. Budget the split
before promising anything.

### Gate 3 — Capability fit, 0 to 5, honest not generous

Scored against the operator profile in `sbir/PROFILE.md`. **At or below
2 is a kill.**

- **"Requires someone who has run trial operations at a site"** is a
  fit. Site activation, protocol deviations, accrual and retention,
  source data verification, risk-based monitoring, REDCap/OnCore/
  Medidata as the system of record, 21 CFR Part 11, the regulatory
  binder, coordinator burden. This is the thing almost no other
  applicant has, and it should be what the score is made of.
- **"Adjacent to healthcare" is not a fit** and scores nothing.
- Bench/discovery vocabulary actively pulls the score **down**, so a
  molecular topic cannot float to a 3 on health-literacy alone.

**The one exception — a restricted eligibility field.** An announcement
open only to first-time PIs, new entrepreneurs, or applicants who have
never held an NIH award survives Gate 3 even on a low fit score. This
is scored as a **niche, never as fit**: the fit number stays honest and
the digest says plainly that the row is there on eligibility rather than
on capability. A thin field is worth more to a first-time applicant than
a strong topic in a captured one.

### Gate 4 — Partner feasibility

For every STTR match, **name the specific academic department or center
that would plausibly host the PD/PI**, and state whether Stanford
Department of Medicine is a credible home for it.

| Work | Home | Stanford Dept of Medicine credible? |
| --- | --- | --- |
| Trial operations, site conduct | Dept of Medicine — Quantitative Sciences Unit / Spectrum CTSA | **Yes** — the department Andrew worked in |
| Clinical data, informatics | Dept of Medicine — Center for Biomedical Informatics Research | **Yes** — same department |
| Health services, implementation | Dept of Medicine — Primary Care & Population Health / Center for Population Health Sciences | **Yes** — same department |
| Device, clinical engineering | Bioengineering / Byers Center for Biodesign | **No** — outside the relationship; a real but unfunded 60–90 day cold build |
| Bench discovery | — | **Kill.** No path to that partner type, and PRG could not manage the science or supply 40% of it |

The asset PRG has that most applicants do not is a **real relationship
at Stanford Department of Medicine** plus hands-on knowledge of how
trial operations fail at the site level. Gate 4 exists to check that a
given opportunity actually lets PRG spend that asset.

### Gate 5 — Deadline feasibility

A **first** STTR carries work no repeat applicant has: standing up the
institutional partnership, getting a PD/PI to commit 10% effort, and
negotiating the **IP allocation agreement** the STTR program requires.

- **90+ days → ACTIONABLE.**
- **Under 90 days → NEXT CYCLE**, named and dated, never dropped. The
  standard cycle repeats every four months, so "next cycle" is a real
  plan, not a euphemism for no.
- **Closed → kill.**
- **Forecast** (NIH has stated intent but not published the NOFO) →
  **MONITOR–PREPOSITION.** There is nothing to write against yet, but
  the partner conversation should start now.

### Gate 6 — Competition and crowding

Never scoring, always informative. From NIH RePORTER, for the topic and
mechanism:

- **how many prior awards** in the last five fiscal years,
- **who keeps winning them** and how concentrated the top three are,
- **the named program officer** — the single most useful output of this
  gate, because the pre-application call is free and most applicants
  never make it.

| Label | Meaning |
| --- | --- |
| `CROWDED-CAPTURED` | 25+ awards, top-3 hold 45%+. A first-time applicant is buying a lottery ticket. Auto NO-GO. |
| `CROWDED-OPEN` | 25+ awards, no dominant winner. Competitive but enterable. |
| `CONTESTED` | 6–24 awards. |
| `THIN` | 1–5 awards. |
| `UNPROVEN` | none. Either genuinely new, or the institute does not fund this. Call the program officer and find out which. |

---

## C. Ranking and output

Rank by **fit score × deadline feasibility**, plus a bounded additive
credit for a restricted eligibility field — bounded so a niche row can
reach the page but never outrank a real fit. Cap the digest at 10.

Each surviving row carries: announcement number and exact title, the URL
each figure was verified from, mechanism, agency and institute, next due
date and days remaining, that institute's Phase I and Phase II caps, the
fit score with a one-sentence justification, the named plausible academic
partner, three candidate specific aims, the prior-award landscape with
the named program officer, and **one go/no-go with a single reason**.

---

## D. The two standing rules

**1. Never invent an announcement number, a deadline, or a budget cap.**
Every one of the three is copied from a primary source fetched in the
same run, and the URL it came from is printed beside it. Where a figure
cannot be verified the digest says so — an unresolved institute prints
the full verified spread across all participating components rather than
picking a plausible one, and an unfetchable cap prints `NOT VERIFIED`.

**2. When a source fails, say so in the digest.** Four of the eight
sources are routinely unavailable — SBIR.gov and DoD DSIP block this
network, Simpler.Grants.gov and SAM.gov need credentials. They are
probed every run and reported as holes in the sweep **above** the
ranking, so a partial sweep can never be read as a complete one.

**3. Flag foreign-affiliation screening language.** The 2026
reauthorization expanded that review, and PA-27-102 now states that NIH
**will not issue awards involving foreign subawards or subcontracts** at
all under this NOFO. PRG is clean on every part of this, but the
disclosure burden changes the workplan and the row should say so.
