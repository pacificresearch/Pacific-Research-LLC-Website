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

The workbook has nine tabs — **Top 10 – Do These First**, **Solo-Friendly
(1-Person)**, **Core Opportunities**, **Low-Barrier (Warm Body)**,
**International (Consulting)**, **Subcontracting**, **Recompete Radar**,
**WATCHLIST (prep, future)**, and **KILL LOG (screened out)** — each with
filterable, frozen headers.

### Deep-screen gates (auto-triage)

Every opportunity is run through PRG's deep-screen gates (a **keyword-level
first pass** — the definitive screen still requires reading each notice's
PWS/attachments) and gets a disposition:

- **PASS** → appears in the pursue lists above.
- **FAIL** → removed and logged in the **KILL LOG** with the failed gate and
  reason: Gate 0.5 structural (needs a clearance / GSA schedule / IDIQ / BPA /
  prior Phase-I award), Gate 4 scope (construction, janitorial, equipment
  maintenance, logistics, guards, trade labor), Gate 3 coverage (24/7, on-call,
  guaranteed response, embedded/daily on-site), Gate 1 self-performance (≥3
  FTE — needs a team).
- **FUTURE** → pre-solicitations and Sources Sought that fit PRG go to the
  **WATCHLIST** (prep and shape the requirement; not biddable yet).
- **Soft signals** (score down, never auto-fail): ~2 FTE, <10 days to respond,
  bonding/insurance, incumbent present, open competition (no SDVOSB
  preference), and NAICS catch-all codes flagged "verify scope".

The screen is deliberately strict — an empty PASS list is an acceptable outcome
(zero false positives beats a padded list).

### Go/No-Go verdict (first-contract lens)

PRG is a new SDVOSB with zero corporate past performance, so each surviving
opportunity also gets a **verdict**:

- **BID** — winnable as a first contract; the founder's individual credentials
  are the technical capability.
- **RESEARCH** — pre-sol/Sources Sought, or a corporate past-performance wall
  against a likely incumbent, or an open competition with a weak edge.
- **NO-BID** — failed a gate (logged in the KILL LOG).

Additional first-contract kill rules: **Gate 2** trade/professional credentials
the founder doesn't hold (ASSE/medical-gas, licensed electrician/plumber/HVAC,
PE stamp, medical licensure, CDL); **Gate 1 workforce** CBA / Service Contract
Act wage determinations / phase-in / right-of-first-refusal (incumbent-workforce
takeover); **Gate 5** bonding. Score-up signals (LPTA/price-dominant, remote,
neutral past-performance rating) lift winnable small buys. Each row also shows
an **estimated level of effort** to propose.

Run `python samgov_opportunity_matcher.py --selftest` to verify the NO-BID
rules fire against two known cases (VA 36C26026Q0674 medical-gas credential
wall; FDA 75F40126R00051 NCTR O&M CBA/workforce wall).

**Pro features:**

- **Top 10 – Do These First** — the single highest-scoring, still-open,
  bid-as-prime shortlist, so you act instead of scrolling 1,000+ rows.
- **Recompete Radar** — existing federal contracts in your NAICS that expire
  within N months (default 18), pulled from the keyless **USASpending.gov**
  API: the incumbent, the award amount, the agency, and the end date. These
  upcoming rebids are where most contracts are actually won. Tune with
  `--recompete-months N`; skip with `--no-recompetes`.
- **PSC search** — in addition to NAICS, the tool queries target **PSC
  (Product/Service) codes** (R408, R499, R707, B505/B506, Q301, AN11) for
  service-classified work NAICS can miss. Skip with `--no-psc`.
- **Certification toggles** — `IS_HUBZONE_CERTIFIED`, `IS_8A_CERTIFIED`,
  `IS_WOSB_CERTIFIED` near the top of the script. Flip one on as PRG earns it
  and the matching set-asides immediately count as eligible.
- **Interactive report** — clickable KPI cards and filter buttons (All / Best
  bets / On the fence / Skip / Solo / International / SDVOSB) plus a live search
  box filter the matrix in place. The
**International** tab is a dedicated category for opportunities with an overseas
place of performance (separate from domestic/CONUS work), and the executive
report has a matching 🌍 International section and KPI. The **Solo-Friendly** tab flags small-scale
knowledge work (research, analysis, writing, data, reviews) that one person
could realistically deliver, scored down for crew/physical/large-team signals
and large dollar values.

Each row is a **decision dashboard** ordered best-bet first, with:

- **Win Score (0–100)** and a three-band **rating** — 🟢 Green (68+, genuine
  best bet — pursue), 🟡 Yellow (45–67, on the fence — worth a look), 🔴 Red
  (<45, or ineligible, or the deadline has passed — do not pursue). The Win
  Score and Rating cells are color-coded in Excel. The score is tuned so a
  clean SDVOSB, solo-doable, eligible opportunity reaches Green even without a
  clinical/biomedical keyword match, and blends set-aside advantage, solo
  executability, capability fit, value sanity, and incumbent headwind. It is a
  planning heuristic, not a guarantee.
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

### Scheduled automation (Windows)

To run the scans hands-off, `automation/setup_prg_automation.ps1` registers two
Windows scheduled tasks and keeps a dated history:

- **Weekly** — Mondays 9:00 AM, `--days 10`, saved to
  `Desktop\PRG_SAMgov_Reports\Weekly\`
- **Monthly** — 1st of month 9:00 AM, `--days 90`, saved to
  `Desktop\PRG_SAMgov_Reports\Monthly\`

Each run writes date-stamped `PRG_Contracts_<date>.xlsx` and
`PRG_Executive_Report_<date>.html`. Set it up once by pasting this into
PowerShell:

```powershell
iex (irm "https://raw.githubusercontent.com/pacificresearch/Pacific-Research-LLC-Website/claude/samgov-opportunity-matcher-0a3c2f/automation/setup_prg_automation.ps1")
```

The `--outdir FOLDER` flag drives this (date-stamped files into a folder);
manage or remove the tasks any time in Windows **Task Scheduler**.

The executive report opens with a **Key Findings & Things to Keep in Mind**
review — opportunities closing within 14 days (🔴 within 7), strongest fits,
best solo play, largest value, and standing compliance reminders — so a
scheduled report is a ready-to-scan briefing, not just raw data.

## Notes

- SAM.gov requires `postedFrom`/`postedTo` date filters (`MM/DD/YYYY`) and caps
  the range at one year; the script derives these from `--days`.
- Network, HTTP, rate-limit (HTTP 429), and JSON-decode errors are handled
  gracefully — a failure on one NAICS query does not abort the whole run, and
  the report still renders with whatever was retrieved.
- Set-aside code mappings follow the SAM.gov set-aside code table; adjust
  `SDVOSB_SETASIDE_CODES` / `SMALL_BUSINESS_SETASIDE_CODES` if GSA revises them.
