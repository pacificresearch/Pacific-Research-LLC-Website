# PRG Learning Log — the experiment record
> Operating hypothesis (Andrew, 8/19): **PRG can fulfill ANY government
> contract for a profit.** Every pursuit is a test. Every kill, loss, and
> win is data. This log records each falsification and the fix applied to
> the search/screening criteria. Review at every daily run; a lesson that
> doesn't change a gate rule, a matcher filter, or a pricing default
> isn't captured yet.

## Current refined hypothesis (v2)
PRG can profitably fulfill any government contract where (a) execution is
delegable to hireable/subcontractable experts, AND (b) no structural
barrier blocks the path — firm licensure, bonding, facility clearance,
contract-vehicle membership, or OEM authorization we cannot obtain.
The gate's kill list IS the accumulated falsification record of "ANY."

## Data → fixes applied

| # | Date | Observation (the failed test) | Fix applied |
|---|------|-------------------------------|-------------|
| 1 | 8/12 | Metabolon, Fastpak: sole-source/intent-to-award notices are decided before we respond | Gate: intent-to-sole-source = auto-PASS; matcher flags "intent to award/sole source" text |
| 2 | 8/13 | OEM-locked equipment maintenance (BD PYXIS class): manufacturer controls parts, firmware, certs; won't authorize a reseller-less SDVOSB | Gate kill #6 (ostensible subcontractor / unobtainable OEM auth). Sources-sought responses still sent (cheap set-aside advocacy) but BID decisions require an OEM-auth path check FIRST |
| 3 | 8/14 | NMRC: gut-feel estimate ($400–450K) was 2x the hidden SAT ceiling in PWS §2.0 | Pricing rule: read EVERY solicitation for budget signals (SAT, IGCE hints, vehicle ceilings) before numbers; delegated-pricing authority requires document-derived ceilings |
| 4 | 8/17 | "50 bids" order vs. reality: bids can't be mass-produced without fabricating prices; pre-RFP responses can be volume-produced | VOLUME MODE split: same-day responses to ALL surviving pre-RFP notices; bids remain researched one-by-one |
| 5 | 8/17 | Same-week-expiry solicitations produce rushed, non-compliant bids | APEX lead-time rules: biddable notice expiring <7 days = PASS, no exceptions |
| 6 | 8/18 | Forum feedback: $80–90K Senior BMET is under Maryland market | Confirmed by BLS data; kept deliberately as loss-leader (SAT-capped contract) but logged: posting salary must be checked against BLS 75th percentile, not median, for "Senior" titles |
| 7 | 8/18 | VA GCP PWS 7.3.5/7.3.6 nearly missed: 10-yr monitoring + 5-yr federal per named monitor buried in quals section | Compliance-matrix rule: personnel-qualification sections get line-by-line extraction BEFORE staffing decisions; founder-as-key-person claims re-checked against every quals row |
| 8 | 8/19 | Intl sweep: embassy commodity buys (vehicles, phones, parts) dominate volume but are pure resale; insurance requires underwriter licensure; A&E requires firm licensure | Intl gate: resale/underwriting/A&E auto-kills; matcher intl mode down-ranks "purchase/acquisition of" titles |
| 9 | 8/19 | M365 connector flaps repeatedly; sends missed their window twice | Durable SEND_QUEUE.md pattern: every outbound queued in-repo; any session with Outlook processes queue FIRST |
| 10 | 8/19 | MCRC ROM draft stated "completion within 2-3 weeks of award" with no crew under commitment (Andrew caught it) | Rule: pre-proposal communications state durations as "typically completed in X" market estimates; firm schedules ONLY at proposal, backed by a committed sub quote. Sub quotes (3) collected during PURSUE, before any bid |

| 11 | 9/15 | Scheduled runs reported SUCCEEDED for weeks while producing NO artifacts (no reports on main since 8/18; PIPELINE stale at 8/17); root cause: PR #13 never merged, so fresh sessions ran the obsolete main-branch system | Rules: (a) merge ops changes to MAIN same day — scheduled sessions only see main; (b) every scheduled run MUST commit its report + pipeline refresh, and a run without artifacts is a FAILED run regardless of status; (c) any session auditing the system checks last artifact date first |
| 12 | 9/15 | Matcher recorded a 502 gateway error as "0 records" for NAICS 561720 — silent coverage loss presented as a clean report (Andrew caught it) | Matcher fixed: 5xx retried 3x with backoff; unrecoverable failures tracked as FAILED codes with a COVERAGE INCOMPLETE banner, never zero; api_key redacted from all error output |

| 13 | 10/21 | ~~SUPERSEDED 11/05 by entry 14 — the diagnosis below was wrong: api.sam.gov was never blocked.~~ Daily runs reported SUCCEEDED Sept–Oct but finished in ~1 min and landed nothing; root cause: environment egress policy blocks api.sam.gov and sam.gov (HTTP 403 at CONNECT), so step 1 VERIFY stops every run. Watchdog never checked the network itself. | Watchdog now runs a live curl against api.sam.gov as check #1 and names the fix (claude.ai Settings > Capabilities > allowed domains). A run under 2 min is treated as a failed run. Cadence reduced to Mon/Thu per Andrew. |
| 14 | 11/05 | Entry 13 was wrong. api.sam.gov and sam.gov were reachable the whole time; the key was dead. Measured 10/15 and 10/21: both hosts answered in <1s while a keyed query returned HTTP 401 API_KEY_INVALID. The key was rotated 11/03 (f445385) but reports stayed blank on 11/04 and 11/05, because the rotation only changed the committed fallback — the runs that matter execute from a local Windows copy and/or a `SAM_API_KEY` env var, and **the env var overrides the file**. Same day, same 7-day window, the same code screened 819–822 notices here. The HTML report could not show any of this: `failed_codes` was tracked but the COVERAGE INCOMPLETE banner printed only to the console, so an all-401 run rendered identically to a quiet week. | Three changes: (a) the committed key is GONE — `SAM_API_KEY` or `--api-key` only, so there is one place a key can be stale instead of three; (b) a 401/403 from SAM aborts the run with exit 2 and writes no files, because a blank report is worse than no report; (c) the HTML report carries the coverage warning at the top, listing the failed codes, whenever any query failed or the run was rate-limited. Standing rule: never diagnose a blank report without a keyed probe — host reachability alone proves nothing. |
| 15 | 11/06 | **Entry 11's failure mode recurred and the watchdog it created did not catch it.** Nothing has landed in `capture/reports/` or `intl/reports/` since 8/18 — ~11 weeks — while all four Mon/Thu Routines reported SUCCEEDED on every run day. The 11/05 domestic run finished in 28 seconds, which cannot include a SAM sweep. Root cause: the scheduled sessions stop at step 1. Every capture prompt said "VERIFY: api.sam.gov reachable. If the egress proxy blocks it, STOP", and the watchdog prompt went further — it named the (now-retracted) network block as the "Known root cause of the Sept–Oct 2026 outage" and told the session to lead its report card with it. So a fresh session's cheapest reading of step 1 was: probe, see something non-200, declare the known block, stop. Entry 11 already required "any session auditing the system checks last artifact date first", but that rule lived only in this log, not in the prompt the watchdog actually executes. | Rewrote step 1 / check 1 in all three Routine prompts (DOMESTIC, INTERNATIONAL, weekly audit): verify the KEY, not the host — is `SAM_API_KEY` set, then ONE keyed probe, 200 to proceed; an unkeyed GET proves nothing (SAM answers 404 with no key); api.sam.gov is explicitly NOT blocked and the 10/21 finding must not be reinstated. The audit prompt now states that a SUCCEEDED `last_run` is only evidence the session started and ended, and makes the landed-artifact check the proof a run happened. Standing rule: **a rule that governs a scheduled run must live in that run's prompt — the Routine prompt is the only thing a fresh session is guaranteed to read, and a correction filed solely in the repo does not reach it.** Corollary: when a diagnosis is retracted, grep the Routine prompts for it the same day. |

## Standing experiment rules
1. Every PASS records its kill criterion (one line) — that's a data point,
   not paperwork.
2. Every loss gets a debrief request (09_loss_debrief.md) — price delta
   and weaknesses are the highest-grade data we can get.
3. Every win records actuals vs. estimate — pricing model calibration.
4. A recurring kill pattern (3+ occurrences) becomes a matcher filter so
   we stop spending screen time on it.
5. Nothing in this log is deleted — superseded rows get struck through
   with the date and reason.
6. A rule that must govern a scheduled run belongs in that run's Routine
   prompt, not only in this log — a fresh session reads the prompt, never
   the conversation that wrote the rule. When a diagnosis is retracted,
   grep every Routine prompt for it the same day (entry 15).
