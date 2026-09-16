# PRG Property Acquisition Screener — 2026-09-16-fb8c4f

_Generated 2026-09-16T22:49:40.891081+00:00_. Cadence: weekly. Strategy: 2–4 unit pure cash flow, ≤ $400,000, conventional investor financing, VA entitlement preserved (never modelled).

## 0. Self-test and data sources

| Check | Status |
|---|---|
| RENTCAST_API_KEY | MISSING |
| BRAVE_SEARCH_API_KEY | MISSING |
| CENSUS_API_KEY | MISSING |
| FRED_API_KEY | MISSING |
| BLS_API_KEY | MISSING |
| ATTOM_API_KEY | MISSING |
| rentcast_reachable | ok |
| zillow_reachable | ok |
| census_popest_reachable | ok |
| fhfa_reachable | ok |
| cache_db | /home/user/Pacific-Research-LLC-Website/property/cache/prg_property.sqlite |
| census_popest | 387 MSAs |
| zillow_zhvi_zori | 894 metros |
| fhfa_hpi | 410 MSAs |
| bls_laus | 393 metros |
| census_acs | SKIPPED (CENSUS_API_KEY missing) — income, renter share, 2-4 unit stock share, vacancy UNKNOWN |
| census_bps_permits | 931 CBSAs |
| stage1_components_active | rent_to_value=0.31, affordability=0.13, insurance_cost=0.13, population_growth=0.13, net_migration=0.13, unemployment=0.13, hpi_momentum=0.06 |

**Assumptions in force (config.yaml, not quotes):** 7.50% / 30-yr, baseline 25% down; vacancy 5%, credit loss 1%, management 8% of collected, R&M 5% GSR, capex 5% GSR (raised for pre-1960/1940 stock). Insurance is a hazard-tiered table ESTIMATE.

## 1. Stage 1 — market screen

275 metros screened on public data; 30 selected for Stage 2 (14 seeds forced in). Component weights active this run: rent_to_value=0.31, affordability=0.13, insurance_cost=0.13, population_growth=0.13, net_migration=0.13, unemployment=0.13, hpi_momentum=0.06.

| Rank | Market | Score | ZHVI | ZORI | Rent/Value | Pop 20→24 | Dom. mig/1000 | Unemp. | HPI 3y | Permits/1000 | Catalyst | Seed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Warner Robins, GA | 81.4 | $254,475 | $1,517 | 7.1% | 6.1% | 10.11 | 3.0 | 4.5% | 6.65 | 63.4 |  |
| 2 | Abilene, TX | 77.2 | $222,914 | $2,007 | 10.8% | 4.2% | 5.33 | 3.9 | 6.2% | 6.29 | 64.9 |  |
| 3 | Columbia, SC | 75.9 | $256,132 | $1,559 | 7.3% | 4.8% | 8.41 | 4.0 | 4.9% | 6.98 | 70.3 |  |
| 4 | Dothan, AL | 75.6 | $196,154 | $1,275 | 7.8% | 2.4% | 7.88 | 3.6 | 4.9% | 3.81 | 45.7 |  |
| 5 | Bangor, ME | 75.3 | $281,810 | $1,515 | 6.5% | 3.1% | 8.71 | 3.3 | 4.7% | 3.1 | 54.6 |  |
| 6 | Jackson, TN | 75.3 | $205,926 | $1,412 | 8.2% | 1.7% | 5.83 | 3.9 | 5.7% | 2.57 | 49.3 |  |
| 7 | Hickory-Lenoir-Morganton, NC | 74.7 | $269,037 | $1,618 | 7.2% | 2.2% | 9.04 | 3.7 | 4.9% | 8.41 | 44.0 |  |
| 8 | Augusta-Richmond County, GA-SC | 74.5 | $252,841 | $1,488 | 7.1% | 4.0% | 7.44 | 4.0 | 4.4% | 6.5 | 69.2 |  |
| 9 | Macon-Bibb County, GA | 74.0 | $200,076 | $1,250 | 7.5% | 1.7% | 6.68 | 3.8 | 6.0% | 2.15 | 55.3 |  |
| 10 | Gulfport-Biloxi, MS | 73.0 | $224,579 | $1,443 | 7.7% | 2.4% | 4.32 | 3.4 | 3.1% | 7.76 | 41.7 |  |
| 11 | Spartanburg, SC | 73.0 | $276,318 | $1,510 | 6.6% | 11.0% | 23.72 | 4.4 | 5.1% | 11.01 | 86.0 |  |
| 12 | Valdosta, GA | 72.8 | $225,960 | $1,372 | 7.3% | 2.9% | 3.82 | 3.6 | 9.5% | 5.93 | 61.7 |  |
| 13 | Greenville, NC | 72.3 | $244,755 | $1,448 | 7.1% | 4.1% | 4.55 | 4.3 | 4.3% | 7.11 | 50.5 |  |
| 14 | Hagerstown-Martinsburg, MD-WV | 72.2 | $323,970 | $1,646 | 6.1% | 5.7% | 12.59 | 3.8 | 4.7% | 5.22 | 59.7 |  |
| 15 | Savannah, GA | 72.1 | $342,336 | $1,789 | 6.3% | 6.5% | 10.24 | 2.7 | 4.5% | 12.44 | 60.6 |  |
| 16 | Winston-Salem, NC | 71.9 | $280,379 | $1,541 | 6.6% | 4.2% | 8.69 | 3.8 | 4.4% | 6.66 | 55.2 |  |
| 18 | Cleveland, OH | 71.3 | $253,678 | $1,454 | 6.9% | -0.6% | -2.23 | 3.1 | 6.3% | 1.92 | 37.9 | ✓ |
| 31 | Fort Wayne, IN | 68.7 | $260,238 | $1,281 | 5.9% | 3.2% | 1.48 | 3.3 | 5.2% | 3.54 | 58.3 | ✓ |
| 34 | Toledo, OH | 68.1 | $205,237 | $1,264 | 7.4% | -0.7% | -2.54 | 4.0 | 5.5% | 0.82 | 38.8 | ✓ |
| 49 | Montgomery, AL | 65.6 | $214,806 | $1,405 | 7.8% | 0.6% | -1.75 | 3.7 | 4.5% | 2.77 | 24.9 | ✓ |
| 51 | Little Rock-North Little Rock-Conway, AR | 65.2 | $231,747 | $1,265 | 6.6% | 2.7% | 4.83 | 4.2 | 3.2% | 4.08 | 59.9 | ✓ |
| 59 | Odessa, TX | 64.2 | $253,302 | $1,561 | 7.4% | 2.7% | -0.04 | 4.3 | 4.9% | 5.42 | 38.8 | ✓ |
| 66 | Chattanooga, TN-GA | 63.0 | $322,958 | $1,519 | 5.6% | 4.2% | 9.92 | 3.3 | 4.2% | 5.03 | 59.3 | ✓ |
| 73 | Midland, TX | 62.1 | $330,518 | $1,599 | 5.8% | 7.3% | 10.05 | 3.4 | 4.7% | 7.0 | 65.5 | ✓ |
| 86 | Huntsville, AL | 60.7 | $315,402 | $1,386 | 5.3% | 9.6% | 18.4 | 3.1 | 3.0% | 8.33 | 66.9 | ✓ |
| 131 | Fayetteville-Springdale-Rogers, AR | 57.3 | $367,718 | $1,582 | 5.2% | 10.1% | 13.22 | 3.5 | 4.3% | 14.8 | 83.7 | ✓ |
| 159 | Memphis, TN-MS-AR | 53.6 | $244,737 | $1,400 | 6.9% | -0.5% | -5.95 | 4.7 | 2.0% | 2.46 | 24.1 | ✓ |
| 178 | Louisville/Jefferson County, KY-IN | 51.1 | $280,129 | $1,348 | 5.8% | 2.3% | -0.19 | 4.8 | 4.7% | 4.38 | 43.5 | ✓ |
| 200 | Philadelphia-Camden-Wilmington, PA-NJ-DE-MD | 48.9 | $389,524 | $1,911 | 5.9% | 1.4% | -3.42 | 4.2 | 5.0% | 2.04 | 54.1 | ✓ |
| 228 | Milwaukee-Waukesha, WI | 42.4 | $388,845 | $1,563 | 4.8% | -0.0% | -3.36 | 3.8 | 6.5% | 1.97 | 36.9 | ✓ |

Discovered (non-seed) markets in the top of the universe that are NOT on the seed list: Warner Robins, GA, Abilene, TX, Columbia, SC, Dothan, AL, Bangor, ME, Jackson, TN, Hickory-Lenoir-Morganton, NC, Augusta-Richmond County, GA-SC, Macon-Bibb County, GA, Gulfport-Biloxi, MS, Spartanburg, SC, Valdosta, GA, Greenville, NC, Hagerstown-Martinsburg, MD-WV, Savannah, GA.

## 2. Stage 2 — properties

Listings pulled: 0 · candidates after early filter: 0 · underwritten: 0 · skipped for API budget: 0.

**No properties were underwritten.** RENTCAST_API_KEY missing: no live listings, no property records, no rent comps. Stage 2 skipped. Set the key (property/.env) and re-run.

## 4. Market report (selected markets)

| Market | Underwritten | Median price | Median gross rent | Median tax | Median econ cap | Median CF | Median CoC | Pop trend | Emp. trend | Wage | HPI 5y | Permits/1000 | Catalysts | Risks | Incentive | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Warner Robins, GA | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 6.1% | -0.5% | 1227.0 | 9.4% | 6.65 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Abilene, TX | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 4.2% | 1.3% | 1151.0 | 7.9% | 6.29 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Columbia, SC | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 4.8% | 2.8% | 1236.0 | 8.7% | 6.98 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Dothan, AL | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 2.4% | -1.8% | 1096.0 | 7.3% | 3.81 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Bangor, ME | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 3.1% | -0.9% | 1097.0 | 9.2% | 3.1 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Jackson, TN | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 1.7% | -1.2% | 1120.0 | 9.4% | 2.57 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Hickory-Lenoir-Morganton, NC | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 2.2% | -4.2% | 1123.0 | 9.0% | 8.41 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Augusta-Richmond County, GA-SC | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 4.0% | 2.3% | 1214.0 | 8.3% | 6.5 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Macon-Bibb County, GA | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 1.7% | 0.8% | 1131.0 | 8.9% | 2.15 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Gulfport-Biloxi, MS | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 2.4% | -1.2% | 1126.0 | 7.3% | 7.76 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Spartanburg, SC | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 11.0% | 4.2% | 1224.0 | 8.9% | 11.01 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Valdosta, GA | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 2.9% | 1.1% | 991.0 | 9.4% | 5.93 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Greenville, NC | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 4.1% | -1.8% | 1205.0 | 7.7% | 7.11 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Hagerstown-Martinsburg, MD-WV | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 5.7% | -1.2% | 1151.0 | 7.1% | 5.22 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Savannah, GA | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 6.5% | 1.2% | 1232.0 | 10.3% | 12.44 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Winston-Salem, NC | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 4.2% | -2.0% | 1363.0 | 9.2% | 6.66 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Cleveland, OH | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | -0.6% | -1.2% | 1482.0 | 8.2% | 1.92 | NOT RESEARCHED | not researched | NOT RESEARCHED | 72.0 |
| Fort Wayne, IN | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 3.2% | 0.5% | 1283.0 | 9.0% | 3.54 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Toledo, OH | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | -0.7% | 0.1% | 1260.0 | 7.4% | 0.82 | NOT RESEARCHED | not researched | NOT RESEARCHED | 72.0 |
| Montgomery, AL | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 0.6% | -2.3% | 1170.0 | 7.1% | 2.77 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Little Rock-North Little Rock-Conway, AR | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 2.7% | 2.1% | 1241.0 | 6.6% | 4.08 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Odessa, TX | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 2.7% | 0.5% | 1521.0 | 4.5% | 5.42 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Chattanooga, TN-GA | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 4.2% | -0.3% | 1292.0 | 8.7% | 5.03 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Midland, TX | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 7.3% | 2.2% | 2013.0 | 5.0% | 7.0 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Huntsville, AL | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 9.6% | -0.9% | 1545.0 | 7.4% | 8.33 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Fayetteville-Springdale-Rogers, AR | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 10.1% | 3.4% | 1887.0 | 9.6% | 14.8 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Memphis, TN-MS-AR | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | -0.5% | -1.9% | 1361.0 | 5.9% | 2.46 | NOT RESEARCHED | not researched | NOT RESEARCHED | 72.0 |
| Louisville/Jefferson County, KY-IN | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 2.3% | 0.4% | 1409.0 | 7.0% | 4.38 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Philadelphia-Camden-Wilmington, PA-NJ-DE-MD | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 1.4% | 2.1% | 1708.0 | 5.9% | 2.04 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Milwaukee-Waukesha, WI | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | -0.0% | 0.8% | 1461.0 | 8.7% | 1.97 | NOT RESEARCHED | not researched | NOT RESEARCHED | 72.0 |

## 5. Data-quality problems (biggest first)

- RENTCAST_API_KEY missing — no live listings, property records, tax bills, or rent comps; Stage 2 could not run on real data.
- CENSUS_API_KEY missing — ACS income, renter share, 2-4 unit stock share, vacancy and ZIP-level neighborhood profiles are UNKNOWN (Census API now requires a key).
- No verified project catalysts on file for any market (research/markets/<cbsa>.yaml empty) — catalyst scores rest on fundamentals only.
- BRAVE_SEARCH_API_KEY missing — relocation incentives, landlord law, assessor sources and project catalysts were not researched automatically; the weekly Claude run must fill research/markets/*.yaml via web search.

## 6. API calls used

- bls: {'live': 0, 'cached': 2}
- bls_laus_file: {'live': 0, 'cached': 1}
- census_bps: {'live': 0, 'cached': 1}
- census_popest: {'live': 0, 'cached': 1}
- fhfa: {'live': 0, 'cached': 1}
- zillow: {'live': 0, 'cached': 2}

## 7. Keys / data that would most improve accuracy

- RENTCAST_API_KEY (highest impact): live 2-4 unit listings, property records with actual tax bills/assessments, unit counts, rental comps and AVMs — without it there is no property-level analysis.
- CENSUS_API_KEY (second): metro and ZIP-level income, renter share, 2-4 unit stock share, vacancy, in-migration, industry mix (economic diversity).
- BLS_API_KEY: lifts the shared-IP daily quota so QCEW wages and LAUS series come from the API reliably.
- BRAVE_SEARCH_API_KEY: automated research leads for catalysts, incentives, landlord law and assessor sources (still human-verified).
- FRED_API_KEY: metro active-listing counts and median days on market (Realtor.com series on FRED) for liquidity/inventory.
- Non-API: a lender quote (replaces the 7.50% assumption), one landlord insurance quote per finalist, county tax bills and rent rolls for finalists.

---
_No number in this report is a lender quote, an insurance quote, or a verified tax bill unless its status says VERIFIED. UNKNOWN is deliberate._
