# SAM.gov Opportunity Matcher — Pacific Research Group LLC

A self-contained Python script that queries the [SAM.gov Opportunities
API](https://open.gsa.gov/api/opportunities-api/), filters active federal
contract opportunities by the company's target NAICS codes, evaluates each one
against Pacific Research Group LLC's SDVOSB profile and core capabilities, and
prints a clean Markdown screening report to the console.

## What it does

1. **Query construction** — pulls active opportunities from the SAM.gov
   Opportunities API for each target NAICS code (`541715`, `541611`, `541990`,
   `811210`) within a posted-date window.
2. **Socioeconomic filtering** — inspects each notice's `typeOfSetAside` code
   and flags it as **SDVOSB**, **Total SB**, **VOSB**, another restricted
   set-aside, or **None (Unrestricted)**, and decides whether PRG may bid.
3. **Capability matching** — scans the title, description, and NAICS/PSC codes
   for clinical-research, data-management, and biomedical-equipment keywords.
4. **Output generation** — prints a Markdown report with a full reviewed-list
   table (with Yes/No eligibility and a short reason/gap analysis) plus the top
   three best-matching opportunities.

## Requirements

- Python 3.8+
- [`requests`](https://pypi.org/project/requests/): `pip install requests`

## Usage

```bash
python3 samgov_opportunity_matcher.py                 # default: last 30 days
python3 samgov_opportunity_matcher.py --days 60        # widen the window
python3 samgov_opportunity_matcher.py --limit 200      # more records per NAICS
python3 samgov_opportunity_matcher.py --api-key SAM-…  # override the API key
```

The API key defaults to the value baked into the script but can be overridden
with the `--api-key` flag or the `SAM_API_KEY` environment variable (preferred,
so the key stays out of shell history and source control):

```bash
export SAM_API_KEY="SAM-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
python3 samgov_opportunity_matcher.py
```

## Notes

- SAM.gov requires `postedFrom`/`postedTo` date filters (`MM/DD/YYYY`) and caps
  the range at one year; the script derives these from `--days`.
- Network, HTTP, rate-limit (HTTP 429), and JSON-decode errors are handled
  gracefully — a failure on one NAICS query does not abort the whole run, and
  the report still renders with whatever was retrieved.
- Set-aside code mappings follow the SAM.gov set-aside code table; adjust
  `SDVOSB_SETASIDE_CODES` / `SMALL_BUSINESS_SETASIDE_CODES` if GSA revises them.
