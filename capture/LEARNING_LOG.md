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
| 16 | 11/07 | Entries 13-15 all trace to one design flaw, not three bugs: **the SAM key had to be copied into every place a run could happen** — the committed source, a `.env`, a shell variable, a cloud environment, a GitHub secret, Andrew's Windows user environment. Six copies, no way to tell which one a given run used, and a rotation silently fixed some and not others. That is why the 11/03 rotation did not restore Andrew's reports, and why removing the committed fallback (entry 14) fixed the local copy but broke the scheduled cloud runs, which had been living on it. | SAM (api.data.gov) accepts the key as an `X-Api-Key` header, verified live. So the key moves OUT of the code and OUT of environment variables into the network proxy's credential store, which attaches it to every request to api.sam.gov from any session in the environment. `_auth_params()` sends no `api_key` parameter when no local key is held; `SAM_API_KEY` and `--api-key` still work and take precedence, for off-proxy machines. Keyless + no stored credential yields 404 from api.data.gov, which is now treated as an auth failure (it is not 'this code has no notices') and aborts the run. Standing rule: **a credential that must be copied to N places will be stale in at least one of them; prefer the store that every runner reads from.** |

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
7. A credential belongs in the one store every runner already reads,
   never copied per-machine. Count the copies: more than one means a
   rotation will miss some of them (entry 16).

## Entry 17 — 2026-11-13 · "the executive report is always blank"

**Reported by Andrew, repeatedly.** Empty executive reports kept reaching
him. Entries 14–16 each fixed a *cause* of an empty sweep (dead key, stale
env var, retracted network diagnosis). None of them fixed the thing that
turned an empty sweep into a blank report in his hands.

**The actual defect:** `samgov_opportunity_matcher.py` `main()` wrote the
`.html` and `.xlsx` and returned **0 even when it had screened 0 notices**.
`_die_auth()` already refused to write on a rejected key, with a comment
naming this exact hazard — "a report reading '0 notices screened' that is
indistinguishable from a week with no postings" — but that protection was
wired only to HTTP 401/403. Every other way a sweep comes back empty —
HTTP 429 quota exhaustion, a network failure, all NAICS codes failing, a
genuinely empty window — fell straight through to the save block. The run
then exited 0, the scheduled task read that as success, and published a
blank page as a real sweep.

**Fix:** the no-write rule now keys off the *result*, not the cause. Zero
results ⇒ write nothing, name the cause (rate-limited / failed codes /
undetermined), exit 2. A scheduled run has no blank page left to publish.
Verified both ways offline: 0 results ⇒ exit 2, no files; normal run ⇒
exit 0, 185 notices, 221 rows.

**Second defect, same root:** `capture/check_sam_key.py` reported
**"SAM CREDENTIAL IS DEAD"** on HTTP 429, because every non-401/403 code
fell through to the dead-key branch — then printed renewal steps telling
Andrew to regenerate a key that was working fine. 429 is quota exhaustion,
usually because a sweep already ran that day. Now its own branch: "VALID
but THROTTLED", with the reset time SAM supplies, exit 1, and an explicit
"do NOT regenerate the key".

**Rule 8 for the standing list:** a guard against a misleading artifact
must key off the artifact, not off one cause of it. "Don't write a blank
report when the key is dead" is a special case of "don't ever write a blank
report"; only the general form survives a new cause. Three entries fixed
causes; the blank reports continued until the general form was written.

**Rule 9:** every lane's report is emitted with the same `<title>`
("PRG Pipeline Executive Report — <date>"), so domestic, international and
any other run are indistinguishable in a browser tab, a file listing and
the artifact gallery. That ambiguity cost real diagnostic time on 11-12:
two same-titled reports from the same day were conflated. The INTL run
already writes `PRG_INTL_*` filenames; the `<title>` should carry the lane
too. Not yet fixed — logged so it is not rediscovered.

**Follow-up, same day — an exit-code collision I introduced.** The first
version of this fix returned **exit 2** on a zero-result run. Exit 2 already
meant "SAM rejected the key", and both capture Routine prompts turn a 2 into
"FAILED — regenerate the credential at sam.gov". So a quota-exhausted sweep
would have told Andrew to replace a key that was working — the identical
wrong-advice failure this entry fixes in `check_sam_key.py`, reintroduced one
level up. Zero-result now returns **exit 3**, and the run prints
"EXIT 3 = swept but empty ... NOT a rejected credential (that is exit 2)".

Addendum to rule 8: when you add a new failure exit, check who already reads
that code. A guard is only as good as the consumer's interpretation of it.


## Entry 18 — 2026-11-17 · the blank report was on a machine no fix had touched

Andrew kept opening a blank `PRG_Executive_Report_<date>.html` on his Windows
Desktop for weeks after the cloud run was repaired. That file is written by a
**second, separate job**: Windows Task Scheduler running `run_daily.bat` in
`OneDrive\Desktop\PRG_SAMgov_Reports` with its own copy of the matcher. Every
fix in entries 14 to 17 landed in the repository and the cloud routines. None
reached that folder, because a cloud session has no access to his PC. The PC
copy was the old script (hardcoded, since-dead key; writes a report on zero
results), so it produced a blank page daily while the cloud run was healthy.

What went wrong on our side, in order:
1. "Fixed" was said about the cloud run while the artifact Andrew actually
   looks at was produced somewhere else. The claim was true and useless.
2. The updated script was handed over as a file to copy by hand, with no check
   that it landed and no mention that the PC also needed the new key.
3. When the real cause was finally named, the fix arrived with a request to
   run a test and send a screenshot. That was for our reassurance, not his need.

**Rule 10:** before saying a report is fixed, identify **which machine writes
the file the owner opens**. If it is not one this session can reach, say so in
the first sentence and do not call anything fixed.

**Rule 11:** when a fix must happen on Andrew's PC, give it **once, complete,
as a paste-ready command**, the first time the problem is seen. No hand-copy
instructions, no follow-up verification tasks, no screenshots requested unless
he asks what to check. His time is the scarcest input in the system.

State after 2026-11-17: the PC script was replaced with the current matcher
via a one-line `Invoke-WebRequest` from `main`, so the PC can no longer write
a blank report. Whether it writes a real one depends on `SAM_API_KEY` being
set on the PC, which is not verified. The PC key and the cloud credential may
be the same key and would then share one daily quota.

### Entry 18, correction (2026-11-19)

Entry 18 said the PC "runs an old copy" of the matcher and that replacing
the file would fix it. Wrong. The PC's `run_daily.bat`, written by
`automation/setup_prg_automation.ps1` on the frozen branch
`claude/samgov-opportunity-matcher-0a3c2f`, **re-downloads the matcher from
that branch before every run**. So every replacement Andrew pasted in was
overwritten by the next run, and the blank reports continued. The answer
was in the repository the whole time: `git log --all -S run_daily.bat`
finds it in one command. It was found only on 11-19, after Andrew pointed
out that "it was a couple of lines in PowerShell."

Fix: `automation/setup_prg_automation.ps1` now exists on main and points
the runners at main (PR #58).

**Rule 12:** before diagnosing any report, read how it is produced, from the
repository, across every branch, and including the automation that calls it.
A fix aimed at a file that a scheduler overwrites is not a fix.

## Entry 19 — 2026-11-19 · a fix that depends on Andrew running it is not a fix

The 11-19 Desktop report was blank again ("0 notices screened"). Main's
matcher refuses to write a report from an empty sweep, so that page could
only have come from the frozen-branch copy. The PC was still on the August
runner, because the PR #58 fix needed Andrew to paste a setup line, and
nothing made sure he had. The old runner opens the newest report whatever
happened, so any failure (spent quota, a missing or expired key, a crash)
put a blank page on his screen.

Fix (Andrew, 11-19: "make sure the executive report works always when it
pops up"):
- `samgov_opportunity_matcher.py` on a Windows `--outdir` run never leaves a
  blank page. Before the run it deletes blank and stale fallback pages and
  repoints any `run_*.bat` still on the frozen branch at main. After a
  failed run it writes today's page as the last good report, with a box on
  top. The box says what failed and gives the one paste line only when
  Andrew must act (a key problem). Cloud and CI runs still write nothing
  on failure, so no fallback page is ever published as a real sweep.
- The frozen branch now serves that same matcher. The PC's next scheduled
  run migrates itself to main with no action from Andrew.
- The setup script tests the saved key and asks again only if SAM
  rejects it. Its runner opens today's page even after a failure, and never
  pauses.

**Rule 13:** if a fix only works once Andrew takes a step, it is not done.
Change what the machine already runs, so the fix reaches him without his
help.

## Entry 20 — 2026-11-19 · a same-day call invite went badly

A partner call was proposed with about 20 minutes' notice. The partner
pushed back on the notice, and the Teams link in the invite was never
created, so the call fell back to phone. **Rule 14:** propose meetings at
least one week out, and confirm the meeting link exists before sending the
invite (`capture/SENDING_AUTHORITY.md`, "Meeting lead time").
