# PRG Property Acquisition Screener

Weekly system that finds 2–4 unit properties (≤ $400K) for **pure cash
flow**, in markets with credible appreciation catalysts, underwritten
line by line with full data provenance. Third PRG lane, beside
`capture/` (domestic) and `intl/` (international).

```
python3 property/main.py                 # full run
python3 property/main.py --stage1-only   # market screen only (no paid calls)
python3 property/main.py --fixture       # synthetic listings: proves math + reports
python3 property/main.py --archive       # + copy outputs to property/reports/<date>/
python3 -m pytest property/tests -q      # 18 hand-checked tests
```

## Two stages, one budget

1. **Stage 1 — market screen (free, public data).** Every US metro
   (Census PEP) joined with Zillow ZHVI/ZORI, FHFA HPI, BLS LAUS, Census
   building permits, ACS (if key). Percentile-scored on rent/value,
   affordability, insurance tier, population growth, domestic migration,
   unemployment, HPI momentum. ~30 markets go forward; the 14 seed CBSAs
   are always in.
2. **Stage 2 — properties (RentCast, budgeted).** Active Multi-Family
   listings per market → early triage on metro rent proxy → enrichment
   (property record with actual tax bills/assessments, unit count,
   rental comps, rent AVM only as fallback) → underwriting → five
   separate rankings.

## What the math does
- Three rent cases per building (contractual / conservative / upside),
  from per-unit comps × units with the layout assumption disclosed.
  Per-unit AVM is never silently multiplied.
- Taxes: current **owner's** bill vs **post-purchase** estimate, with
  `POST-SALE TAX RISK` per state rule notes (verify with county).
- Insurance: hazard-tiered table ESTIMATE with +25%/+50% sensitivity.
- Standard NOI vs economic NOI (capex below the line), every required
  metric, 25/30/35/40/50% equity structures within the $200K cap, rate
  sensitivity 6.5–8.5%, BASE/DOWNSIDE/SEVERE/UPSIDE stress, negotiation
  solver (price for 9%/10% cap, 12%/15% CoC, 1.25/1.40 DSCR) and an
  underwriting ceiling. Confidence 0–100 with listed deductions.

## Provenance
Every number is a `DataPoint` with status VERIFIED / PROVIDER DATA /
ESTIMATED / ASSUMED / UNKNOWN, source, URL, retrieved_at, data date.
UNKNOWN is deliberate — nothing is back-filled.

## Keys (`.env`, never committed)
`RENTCAST_API_KEY` (required for Stage 2) · `CENSUS_API_KEY` (ACS —
now required by Census for any API call) · `BLS_API_KEY` ·
`BRAVE_SEARCH_API_KEY` · `FRED_API_KEY` · `ATTOM_API_KEY` (reserved).
Missing keys degrade to UNKNOWN; the report says which key would help most.

## Layout
`main.py` · `config.yaml` (all assumptions) · `src/` (config, models,
database, http_client, census, public_data, bls, fhfa, permits, fred,
brave_search, rentcast, market_screen, property_search, rent_analysis,
tax_analysis, financing, underwriting, risk, appreciation, relocation,
scoring, reporting) · `tests/` · `research/` (verified qualitative layer)
· `output/` (this run) · `reports/<date>/` (archived) · `cache/` (SQLite).
