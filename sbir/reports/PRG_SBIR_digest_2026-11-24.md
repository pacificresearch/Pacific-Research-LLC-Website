# PRG SBIR/STTR digest — 2026-11-24

Pipeline `sbir_sttr_pipeline.py` (sbir-v1). Gate doc: `sbir/GATE.md`.
Default mechanism is **STTR** — Andrew is job searching, so the SBIR
primarily-employed rule cannot be satisfied. SBIR appears only where
the work is solo-operator-shaped, and always flagged as a conflict.

## Source health — read this before the ranking

| Source | Status | Detail |
| --- | --- | --- |
| Parent NOFO PA-27-102 | **FAILED** | full-announcement attachment unavailable — IC budget caps CANNOT be verified this run |
| Parent NOFO PA-27-100 | **FAILED** | full-announcement attachment unavailable — IC budget caps CANNOT be verified this run |
| Omnibus exclusion set | **OK** | PA-27-100, PA-27-102 — derived from the parents' own Companion Funding Opportunity block, not from titles |
| IC-code harvest | **OK** | 751 record(s) — 3 quer(ies) over 48 page(s), released within 900 days |
| IC-code map | **OK** | 24 two-letter IC code(s) resolved from the NIH Guide index itself (accumulated across runs); unresolved codes yield a cap RANGE, never a guessed institute |
| NIH Guide search API | **OK** | 669 record(s) — 8 quer(ies) over 128 page(s), released within 900 days |
| Administrative notices | **OK** | 22 SBIR/STTR notice(s) were policy, rescission, correction or webinar announcements rather than funding opportunities, and were not gated: NOT-OD-27-017 (Notice of Change: Updates to SBIR and STTR Foreign Risk Noti); NOT-GM-26-014 (Notice of Informational Webinar on the NIGMS Small Business ); NOT-OD-26-090 (Notice of Information: Implementation of HHS Annual SBIR and); NOT-HL-26-005 (Notice to Rescind NOT-HL-24-008 "NHLBI Announces New Policie); NOT-OD-26-076 (Notice to Rescind NOT-OD-24-077 "Technical and Business Assi) |
| grants.gov Search2 | **OK** | 701 record(s) — 9 keyword page(s) |
| NIH Guide weekly RSS | **OK** | 3 record(s) |
| SBIR.gov cross-agency topics | **FAILED** | HTTP 403 Forbidden — cross-agency topic search UNAVAILABLE this run; any non-NIH topic that exists only on sbir.gov was not swept |
| DoD DSIP open topics | **FAILED** | JSON decode: expected JSON, got text/html (61140 bytes) — the endpoint answered with an HTML page, which is what a block or a WAF challenge looks like |
| Simpler.Grants.gov API | **NO-CREDENTIAL** | no SIMPLER_GRANTS_API_KEY in env — this source returns 401 without one. Request a key at https://wiki.simpler.grants.gov/product/api . Not fatal: it indexes the same opportunities as Search2, which ran. |
| SAM.gov Opportunities v2 | **NO-CREDENTIAL** | no SAM_API_KEY in env — contract-based SBIR topics (PHS solicitations, DoD component buys) were NOT swept. Grant-based NIH coverage is unaffected. |
| Seen-list | **OK** | no NEW or CHANGED survivor this run — showing the standing shortlist unchanged so the digest is never silently empty |

> **This sweep is incomplete.** 6 source(s) did not return data: Parent NOFO PA-27-102, Parent NOFO PA-27-100, SBIR.gov cross-agency topics, DoD DSIP open topics, Simpler.Grants.gov API, SAM.gov Opportunities v2. Anything that exists only there was not screened. Do not read the ranking below as cross-agency coverage.

## Ranked shortlist — 1 of 1 survivor(s)

### 1. PAR-27-040 — Small Business Transition Grant for New Entrepreneurs (Parent R41/R42 Clinical Trial Optional)

- **Verified against**: https://grants.gov/search-results-detail/362577
- **Mechanism**: SBIR/STTR | **Agency**: NIH | **Institute**: not resolved | **Stage**: FORECAST
  - forecast: NIH has stated intent to publish; the NOFO does not exist yet, so the date below is NIH's estimate, not a published deadline
- **Restricted eligibility field** ("never been an independent pd/pi"): PD/PI must never have led an NIH research grant — Andrew qualifies, and it removes every established small-business PI from the field
- **Restricted eligibility field** ("transition grant"): transition-to-entrepreneurship mechanism; the field is first-timers, not incumbents
- **Next due date**: 2027-01-05 (42 day(s) out) — NEXT CYCLE
  - due date read from: https://grants.gov/search-results-detail/362577
- **Phase I cap**: NOT VERIFIED | **Phase II cap**: NOT VERIFIED
  - source: the parent announcement's budget table could not be fetched this run, so no cap was copied from a primary source. Nothing is being guessed in its place — re-run, or read the cap off the NOFO by hand.
- **Fit**: 0.0/5 — clears the bar on general health-research literacy only
- **Partner**: Stanford Department of Medicine — Quantitative Sciences Unit / Spectrum Clinical & Translational Research Unit (CTSA)
  - Stanford Dept of Medicine credible: **YES** — the announcement is not yet topic-specific, so this is the default home PRG would pitch: This is the department Andrew worked in; the CTSA hub is chartered to host exactly this kind of trial-operations methods work and routinely signs STTR partner letters.
- **PI rule**: STTR: PD/PI may be employed by the partnering non-profit research institution, so long as the PI holds a formal appointment with or commitment to PRG (no salary required) and commits >=10% effort. Compatible with Andrew taking a full-time role.

**Three candidate specific aims:**

1. Aim 1. Characterize the site-level failure modes the topic targets by structured retrospective review of 20-30 trials at the partner institution, coding deviations, screen failures, and startup delays against a taxonomy Andrew built from Stanford Dept of Medicine operations.
2. Aim 2. Build and instrument the intervention against that taxonomy, using REDCap/OnCore as the system of record so the intervention rides existing site infrastructure rather than asking coordinators to adopt a parallel tool.
3. Aim 3. Test feasibility in a single-arm pilot at 2-3 partner-institution study teams, with predefined thresholds on coordinator burden (time-on-task), data-quality (query rate, SDV findings), and cycle time to site activation.

- **Prior-award landscape**: 4 distinct SBIR/STTR project(s) FY2021-FY2026 (4 project-year rows), THIN. Top firms: Serinus Biosciences Inc (1), Laborecom Therapeutics Inc. (1), Persista Bio Inc (1). Top-3 concentration 75%.
- **Program officer(s)**: Kadir Aslan (1), Coralie Isabelle Poizat (1), Guillermo Arreaza-Rubin (1)
  - reproduce: https://reporter.nih.gov/search — criteria: activity R41/R42/R43/R44, FY2021-2026, text "transition entrepreneurs"
- **Novelty**: UNCHANGED (first seen 2026-08-25)

> **MONITOR-PREPOSITION** — forecast only — NIH has announced its intent but not published the NOFO, so there is nothing to write against yet. PD/PI must never have led an NIH research grant — Andrew qualifies, and it removes every established small-business PI from the field. Watch for the NOFO and start the partner conversation now.

## Kill ledger — 25 candidate(s) screened out

| Doc | Gate | Reason |
| --- | --- | --- |
| PAR-27-098 | G1 | gated on a prior SBIR/STTR award PRG does not hold ("commercialization readiness") |
| PA-27-101 | G1 | gated on a prior SBIR/STTR award PRG does not hold ("phase iib") |
| NOT-OD-26-037 | G3 | capability fit 0.0/5 — no site-level trial-operations demand in the text |
| NOT-AT-25-004 | G3 | capability fit 0.0/5 — no site-level trial-operations demand in the text |
| NOT-GM-25-012 | G3 | capability fit 0.0/5 — no site-level trial-operations demand in the text |
| PAR-26-001 | G2 | SBIR requires Andrew to be primarily employed by PRG, which the concurrent job search rules out, and the work is not solo-operator-shaped |
| NOT-OD-25-004 | G3 | capability fit 0.0/5 — no site-level trial-operations demand in the text |
| NOT-OD-24-155 | G3 | capability fit 0.0/5 — no site-level trial-operations demand in the text |
| NOT-OD-24-154 | G3 | capability fit 0.0/5 — no site-level trial-operations demand in the text |
| NOT-OD-24-153 | G2 | SBIR requires Andrew to be primarily employed by PRG, which the concurrent job search rules out, and the work is not solo-operator-shaped |
| NOT-OD-24-152 | G2 | SBIR requires Andrew to be primarily employed by PRG, which the concurrent job search rules out, and the work is not solo-operator-shaped |
| NOT-DA-24-037 | G3 | capability fit 0.5/5 — no site-level trial-operations demand in the text |
| NOT-DA-24-036 | G2 | SBIR requires Andrew to be primarily employed by PRG, which the concurrent job search rules out, and the work is not solo-operator-shaped |
| NOT-OD-24-147 | G3 | capability fit 0.0/5 — no site-level trial-operations demand in the text |
| NOT-OD-24-149 | G3 | capability fit 0.0/5 — no site-level trial-operations demand in the text |
| FOR-CA-25-086 | G1 | gated on a prior SBIR/STTR award PRG does not hold ("phase iib") |
| FOR-CA-25-087 | G5 | closed 390 day(s) ago |
| TEMP-30794 | G2 | SBIR requires Andrew to be primarily employed by PRG, which the concurrent job search rules out, and the work is not solo-operator-shaped |
| PAR-27-039 | G2 | SBIR requires Andrew to be primarily employed by PRG, which the concurrent job search rules out, and the work is not solo-operator-shaped |
| HHS-2027-ACL-NIDILRR-BISA-0308 | G2 | SBIR requires Andrew to be primarily employed by PRG, which the concurrent job search rules out, and the work is not solo-operator-shaped |
| HHS-2027-ACL-NIDILRR-BISB-0309 | G2 | SBIR requires Andrew to be primarily employed by PRG, which the concurrent job search rules out, and the work is not solo-operator-shaped |
| FOR-NS-25-017 | G2 | not an SBIR/STTR mechanism |
| 26-510 | G3 | capability fit 0.0/5 — no site-level trial-operations demand in the text |
| 26-511 | G3 | capability fit 0.0/5 — no site-level trial-operations demand in the text |
| NOT-OD-27-017 | G3 | capability fit 0.0/5 — no site-level trial-operations demand in the text |

## NIH Guide — posted this week (unfiltered, for eyeball)

- [Notice to Rescind NOT-CA-21-096, "Notice of Information: Guidance Regarding Minimum Level of Effort for NCI-Funded Awards"](http://grants.nih.gov/grants/guide/notice-files/NOT-CA-27-002.html)
- [Notice of Office of Data Science Strategy (ODSS) Participation in PA-25-080 "NIH Support for Conferences and Scientific Meetings (](http://grants.nih.gov/grants/guide/notice-files/NOT-OD-27-012.html)
- [Notice of Change: Updates to SBIR and STTR Foreign Risk Notification and Mitigation Process](http://grants.nih.gov/grants/guide/notice-files/NOT-OD-27-017.html)

## Run metadata

- **run date**: 2026-11-24
- **elapsed**: 78.8s
- **candidates discovered**: 26
- **scored**: 26
- **unverifiable (no primary source)**: 0
- **survivors**: 1
- **killed**: 25
- **RePORTER window**: FY2021-FY2026
- **seen-list**: /home/runner/work/Pacific-Research-LLC-Website/Pacific-Research-LLC-Website/sbir/state/seen.json

---

_Every announcement number, due date, and budget cap above was copied from a primary source fetched during this run, and the URL it came from is printed beside it. Anything the run could not verify says NOT VERIFIED rather than carrying a guess._
