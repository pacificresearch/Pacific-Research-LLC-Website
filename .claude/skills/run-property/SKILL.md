---
name: run-property
description: Run the PRG weekly property acquisition screen end to end — public-data market screen, RentCast 2-4 unit listing pull and underwriting, finalist research (catalysts, incentives, landlord law, tax rules) with sourced YAML, rankings, report, PIPELINE/HEALTH refresh, PR merged, notification. Use when Andrew says "run property system", "run the property screen", "/run-property", "find properties", or asks for the weekly property report.
---

# Run Property System

One command, the whole cycle: **SELF-TEST → STAGE 1 → STAGE 2 → RESEARCH → RE-RUN → BOARD → LAND → NOTIFY.**

Follow `property/WEEKLY_RUN.md` exactly. Do not ask permission between
steps (bias-to-action standing order). Gates that stay closed: never
contact a listing agent or lender on Andrew's behalf, never submit an
offer, never apply to an incentive program.

## 1. Self-test + tests
```
python3 -m pytest property/tests -q
python3 property/main.py --stage1-only
```
Read the self-test table. Missing `RENTCAST_API_KEY` ⇒ the notification's
first line says so; continue with Stage 1 + research anyway (that is still
useful work: verified market research compounds week over week).

## 2. Full run
```
python3 property/main.py --archive
```
Read `property/output/final_report.md`. Note the seven terminal summary
blocks — they are the skeleton of the notification.

## 3. Research finalist markets (web search — this is the analyst work)
For the markets that placed properties in Ranking E top 10 (no RentCast
key: top 8 Stage 1 markets + any seed with no research file), create or
refresh `property/research/markets/<cbsa>.yaml` from
`property/research/TEMPLATE.yaml`. Every item carries `source_url`;
`verified: true` only when you read the primary source. Source order:
government → official EDA → company release/SEC → BLS/Census/FHFA → local
business press. SEO real-estate blogs are never evidence. Absolute rules:
no invented programs, projects, rents, taxes, crime figures. UNKNOWN beats
a guess.

Then re-run `python3 property/main.py --archive` so catalyst, regulatory
and incentive fields reflect the verified layer.

## 4. Board + heartbeat
Refresh `property/PIPELINE.md` (top 5 Ranking E + carried-forward
finalists with status). Append the `property/HEALTH.md` line.

## 5. Land it (artifact rule)
Branch `property/weekly-YYYY-MM-DD` → commit reports/<date>, PIPELINE,
HEALTH, research YAML → push → PR to main → merge it. Failure ⇒
notification starts "RUN FAILED — artifacts not landed".

## 6. Notify
≤ 300 words to Andrew (Outlook connector + the session's final message):
top 3 properties with CF / CoC / DSCR / confidence / ceiling-vs-ask,
top 3 discovered markets, data-quality problems, most valuable missing
key, PR link. Every number that is an assumption says so.
