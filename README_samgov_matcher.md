# SAM.gov Opportunity Matcher — Pacific Research Group LLC

A self-contained Python script that queries the [SAM.gov Opportunities
API](https://open.gsa.gov/api/opportunities-api/), filters active federal
contract opportunities by the company's target NAICS codes, evaluates each one
against Pacific Research Group LLC's SDVOSB profile and core capabilities, and
prints a clean Markdown screening report to the console.

## What it does

1. **Query construction** — pulls active opportunities from the SAM.gov
   Opportunities API for each **core-target NAICS** code (`541715`, `541611`,
   `541990`, `811210`) *and* each **low-barrier NAICS** code (staffing,
   administrative, facilities, and health-support categories) within a
   posted-date window.
2. **Socioeconomic filtering** — inspects each notice's `typeOfSetAside` code
   and flags it as **SDVOSB**, **Total SB**, **VOSB**, another restricted
   set-aside, or **None (Unrestricted)**, and decides whether PRG may bid.
3. **Capability matching** — scans the title, description, and NAICS/PSC codes
   for clinical-research, data-management, and biomedical-equipment keywords,
   and separately for staffing / "warm body" support signals.
4. **Output generation** — prints a Markdown report with four sections:
   1. **Complete list of reviewed opportunities** (core-target NAICS) with
      Yes/No eligibility and a short reason/gap analysis.
   2. **Actionable recommendations** — the top three best-matching prime
      opportunities.
   3. **Low-barrier / "warm body" opportunities** — adjacent staffing,
      administrative, and support work under secondary NAICS codes that PRG can
      reasonably win by fielding qualified personnel, without deep domain
      specialization.
   4. **Subcontracting & teaming opportunities** — awarded primes and large
      unrestricted solicitations where the realistic path is teaming as a
      subcontractor (unrestricted primes must meet FAR 52.219-9 small-business
      subcontracting goals, making an SDVOSB an attractive teammate).

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

### Excel / CSV output

By **default** the script saves an Excel workbook named **`PRG_Contracts.xlsx`
to your Desktop** every time it runs — no extra flags needed:

```bash
python3 samgov_opportunity_matcher.py --days 90      # -> Desktop/PRG_Contracts.xlsx
```

Overrides:

```bash
# Choose your own path/filename:
python3 samgov_opportunity_matcher.py --days 90 --excel my_report.xlsx

# Skip the spreadsheet entirely (console output only):
python3 samgov_opportunity_matcher.py --days 90 --no-excel

# Skip the console report (spreadsheet only):
python3 samgov_opportunity_matcher.py --days 90 --no-print
```

Each tab includes an **Est. Value (Revenue)** column — the dollar amount the
contract would generate. For award notices this is the actual awarded amount;
for open solicitations it is any dollar figure found in the notice text, or
"Not stated" (SAM rarely publishes a value up front, so no figure is invented).
The console report also prints an estimated total pipeline value across the
opportunities PRG can pursue.

The workbook has four tabs — **Solo-Friendly (1-Person)**, **Core
Opportunities**, **Low-Barrier (Warm Body)**, and **Subcontracting** — each
with filterable, frozen headers. The **Solo-Friendly** tab flags small-scale
knowledge work (research, analysis, writing, data, reviews) that one person
could realistically deliver, scored down for crew/physical/large-team signals
and large dollar values.

Each row is a **decision dashboard** ordered best-bet first, with:

- **Win Score (0–100)** and a **RAG rating** — 🟢 Green (80+, pursue),
  🟡 Yellow (60–79, good), 🟠 Orange (40–59, stretch), 🔴 Red (<40, likely
  skip / ineligible). The Win Score and Rating cells are color-coded in Excel.
  The score blends set-aside advantage, capability fit, executability for a
  small/solo shop, value sanity, and incumbent headwind. It is a planning
  heuristic, not a guarantee.
- **Fit for PRG**, **Set-Aside**, **Eligible as LLC?**, **Est. Value**,
  **Personnel (FTE)**, **Hire New or Take Over?** (incumbent detection),
  **Solo-Doable?**, **Timeframe**, **Location**, and **Intl / CONUS** (filter
  this column to separate overseas consulting from domestic work).

If
`openpyxl` is not installed, the script automatically falls back to writing one
CSV file per section (which Excel opens directly). When run interactively
(e.g. double-clicked on Windows) the window stays open until you press Enter,
so the output and the saved-file location don't disappear.

The API key defaults to the value baked into the script but can be overridden
with the `--api-key` flag or the `SAM_API_KEY` environment variable (preferred,
so the key stays out of shell history and source control):

```bash
export SAM_API_KEY="SAM-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
python3 samgov_opportunity_matcher.py
```

### Executive HTML report

By default the script also writes **`PRG_Executive_Report.html`** to your
Desktop — a self-contained, browser-openable executive dashboard (no internet
or libraries needed). It contains:

- **KPI cards** — total pipeline value, eligible opportunities, solo-friendly
  count, SDVOSB set-asides, and top agency.
- **Two inline SVG charts** — pipeline value by agency, and opportunity count
  by win rating (RAG).
- **Contract / opportunity matrix** — every eligible opportunity, best-bet
  first, with value, set-aside, NAICS/PSC, personnel, solo flag, location, and
  response deadline.
- **Deep-dive cards** for the top opportunities — scope, government contacts
  (CO/COR name, email, phone pulled from the notice), and risk/action items.
- **Growth & pipeline insights** — strongest agency footprints, recommended
  target agencies, and strongest NAICS demand.

```bash
python3 samgov_opportunity_matcher.py --days 180           # report to Desktop
python3 samgov_opportunity_matcher.py --report my.html      # custom path
python3 samgov_opportunity_matcher.py --no-report           # skip it
```

The report analyzes the live opportunity pipeline; for awarded contracts it
also surfaces the awardee and award amount, so the same layout doubles as a
portfolio dashboard once contracts are won.

## Notes

- SAM.gov requires `postedFrom`/`postedTo` date filters (`MM/DD/YYYY`) and caps
  the range at one year; the script derives these from `--days`.
- Network, HTTP, rate-limit (HTTP 429), and JSON-decode errors are handled
  gracefully — a failure on one NAICS query does not abort the whole run, and
  the report still renders with whatever was retrieved.
- Set-aside code mappings follow the SAM.gov set-aside code table; adjust
  `SDVOSB_SETASIDE_CODES` / `SMALL_BUSINESS_SETASIDE_CODES` if GSA revises them.
