# PRG SBIR/STTR — sources, and what each one is actually good for

Probed 2026-08-25 from the pipeline's own network. The pipeline re-probes
every source on every run and prints the result at the top of the digest,
so this file is the explanation, not the status.

---

## Working

### 1. Grants.gov Search2 — `https://api.grants.gov/v1/api/search2`
Keyless, POST JSON. **The authoritative record for an announcement
number, its exact title, and its dates.**

Two things worth knowing:

- The documented host `https://grants.gov/api/common/search2` returns
  the HTML search page. The working endpoint is `api.grants.gov/v1/api/`.
- `responseDate` on an NIH omnibus is the **last** cycle date, not the
  next one. PA-27-101 reports `Apr 05, 2029` while its next deadline is
  Sep 5 2026. The pipeline parses the NOFO's own Key Dates table instead
  and only falls back to `responseDate` for single-deadline
  opportunities.

Companions: `fetchOpportunity` (full synopsis, eligibility text,
contacts, attachment folders) and the attachment download at
`https://grants.gov/grantsws/rest/opportunity/att/download/{id}`.

**That attachment is the most valuable single fetch in the system.** It
is the complete NOFO, and the IC-by-IC budget table lives inside it.
Parsing it is what makes it possible to print a budget cap with a URL
next to it instead of a remembered number.

### 2. NIH Guide search API — `https://search.grants.nih.gov/guide/api/data`
Keyless GET. The discovery surface for NOSIs, PAs, PARs and RFAs.
Returns `docnum`, `title`, `doctype`, `ac` (activity codes),
`primaryIC`, `reldate`, `expdate`, `parentFOA`.

Three behaviours found by probing, all handled in code:

- **Page size is capped at 25** server-side no matter what `size` asks
  for. `from` paging works, so the pipeline pages.
- **`sort=reldate:desc` is the working sort syntax.** `sortField`,
  `sortby`, and `orderBy` are all silently ignored, which is worse than
  an error because the result still looks sorted.
- **Only `doctype` filters server-side.** `activityCode`, `primaryIC`
  and any date parameter are ignored, so those are applied client-side.

This index is also where the two-letter IC code map comes from
(`NOT-DK-…` → NIDDK): the pipeline harvests docnum/primaryIC pairs from
the index itself rather than carrying a hand-typed table.

### 3. NIH Guide weekly RSS — `.../guide/newsfeed/fundingopps.xml`
Catches a notice the week it posts, before the search index necessarily
surfaces it against the lane's keywords.

### 4. NIH RePORTER v2 — `https://api.reporter.nih.gov/v2/projects/search`
Keyless POST. **Award intelligence, not opportunity discovery**, exactly
as intended. Gate 6 runs on it: crowding, repeat winners, and the named
program officer.

Two traps:

- **`advanced_text_search` `operator`.** `"and"` requires every term, so
  a six-word lane phrase matched 0 of NCI's 250 STTR rows; `"or"` matched
  240 of 250. Neither number means anything. The institute scan pulls
  each portfolio once and classifies it against the gate's own
  vocabulary instead.
- **One row per project-YEAR.** A Phase I, its Phase II, and every
  non-competing continuation come back as separate rows sharing a core
  number. Counting rows turns a 114-project institute into 182 and
  inflates every concentration figure. The pipeline dedupes to distinct
  projects.

### 5. NIH notice pages — `https://grants.nih.gov/grants/guide/notice-files/{DOC}.html`
Fetchable and used for NOSI full text. Note that the sibling
`pa-files/` path 404s from this network even with a browser
user-agent, so PA/PAR/RFA text is pulled through grants.gov attachments
instead.

---

## Not available — probed every run, reported as holes in the sweep

### 6. SBIR.gov — `https://api.www.sbir.gov/public/api/topics`
**HTTP 403.** Confirmed 2026-08-25; the `www.sbir.gov/topics` page 403s
too. This was flagged in advance and it is real. The consequence is
specific and it is stated at the top of every digest: **cross-agency
topic search does not run**, so any non-NIH topic that exists only on
sbir.gov is not screened. This is not silently skipped and the digest
never claims cross-agency coverage without it.

### 7. DoD SBIR/STTR — `defensesbirsttr.mil` and DSIP `dodsbirsttr.mil`
**HTTP 403 / an HTML block page on a 200.** DoD topics are not swept.
Check the DoD opportunities page by hand before treating any digest as
cross-agency. (A block page returned with a 200 status is why the
pipeline checks content-type before parsing: otherwise it surfaces as a
bare `JSONDecodeError` and reads like a bug in our code.)

### 8. Simpler.Grants.gov — `https://api.simpler.grants.gov/v1/opportunities/search`
**HTTP 401.** Needs an API key; request one at
`https://wiki.simpler.grants.gov/product/api` and set
`SIMPLER_GRANTS_API_KEY`. Lowest-priority gap of the four: it indexes
the same opportunities as Search2, which does run.

### 9. SAM.gov Opportunities v2
Needs `SAM_API_KEY` (the same key the contract matcher uses). Without
it, **contract-based SBIR topics — PHS solicitations and DoD component
buys — are not swept.** Grant-based NIH coverage is unaffected. Setting
the key in the scheduled job's secrets closes this one.

---

## The rule this file exists to serve

A source that fails is a **finding**, not an error to swallow. Every run
prints a source-health table above the ranking, and when anything is
missing the digest states that the sweep is incomplete and names what
was not covered. Four of nine unavailable is the normal state of this
system, and the output has to say so every single time.
