# Weekly Property Run — procedure for the scheduled session

Cadence: **Monday 06:30 PT (13:30 UTC)**, one session, one notification.
Bias to action applies (`CLAUDE.md`): run it, land it, report it. The
only gates: never contact a listing agent, never submit an offer, never
apply to an incentive program — prepare and notify.

## 🩺 STEP 0 — SELF-TEST
1. **Heartbeat**: read `property/HEALTH.md` on main. Newest successful
   run older than 9 days ⇒ the notification MUST lead with
   "⚠️ PROPERTY SYSTEM DEGRADED since <date>".
2. **Keys**: `python3 property/main.py --stage1-only` prints the
   self-test. `RENTCAST_API_KEY` MISSING ⇒ Stage 2 cannot run on real
   data; the notification MUST lead with "⚠️ RENTCAST KEY MISSING — no
   property analysis this week. Fix: add RENTCAST_API_KEY to the
   environment at claude.ai/code → environment settings."
3. **Sources**: the self-test table shows popest / zillow / fhfa / laus /
   permits counts. Any FAILED ⇒ say so in the notification; never
   fabricate a market table.

## 🧾 ARTIFACT RULE — a run that leaves no trace FAILED
```
python3 property/main.py --archive            # writes property/output/* and property/reports/<date>/
```
Commit `property/reports/<date>/`, the `property/PIPELINE.md` refresh,
`property/HEALTH.md` line, and any `property/research/markets/*.yaml`
you filled; push to `property/weekly-YYYY-MM-DD`; open a PR to main and
MERGE it before finishing. Push/merge failure ⇒ notification begins
"RUN FAILED — artifacts not landed".

## 1. Run
`python3 -m pytest property/tests -q` first (18 tests, <1s). Then the run
above. Read `property/output/final_report.md`.

## 2. Research the finalists (this is the session's real work)
For each market that placed a property in Ranking E top 10 (or, with no
RentCast key, the top 8 Stage 1 markets), fill or refresh
`property/research/markets/<cbsa>.yaml` from `research/TEMPLATE.yaml`
using web search, **source URL on every item**, in this source order:
government → official EDA → company press release/SEC → BLS/Census/FHFA →
local business press. Never an SEO real-estate blog.
- catalysts (company, $, jobs, dates, status announced/under_construction/completed)
- relocation incentives (all 12 fields; cash vs non-cash)
- landlord law (10 items) + rental license fee
- tax_rules: county assessor + treasurer URLs, post-sale treatment, risk
- major employers, state income tax, single-employer dependence
Then re-run `main.py --archive` so the scores use the verified layer.

## 3. Finalists → PIPELINE.md
Top 5 by Ranking E with: address, price, units, conservative CF, CoC,
econ DSCR, confidence, POST-SALE TAX RISK, underwriting ceiling, and the
open diligence list. Carry prior weeks' finalists forward with status
(active / price change / withdrawn / passed — reason).

## 4. Notify (the run's final message — reaches Andrew by push + email)
Executive summary, ≤ 300 words: top 3 properties (CF, CoC, DSCR,
confidence, ceiling vs ask), top 3 discovered markets not on the seed
list, biggest data-quality problems, keys that would help most, and
the merged PR link. Fixture mode or missing RentCast key ⇒ say so in
the first line. Use the Outlook connector to Andrew@pacificresearchllc.com
as the daily run does; if Outlook is disconnected, the push notification
carries it and the message says "OUTLOOK DISCONNECTED".
