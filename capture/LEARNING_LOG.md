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
