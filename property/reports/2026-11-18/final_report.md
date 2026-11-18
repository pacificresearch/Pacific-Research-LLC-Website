# PRG Property Acquisition Screener — 2026-11-18-a28583

_Generated 2026-11-18T10:38:11.416904+00:00_. Cadence: weekly. Strategy: 2–4 unit pure cash flow, ≤ $400,000, conventional investor financing, VA entitlement preserved (never modelled).

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
| 1 | Abilene, TX | 78.3 | $222,349 | $1,956 | 10.5% | 4.2% | 5.33 | 3.5 | 6.2% | 6.29 | 61.4 |  |
| 2 | Greenville, NC | 77.5 | $240,934 | $1,515 | 7.5% | 4.1% | 4.55 | 3.5 | 4.3% | 7.11 | 50.6 |  |
| 3 | Columbia, SC | 77.0 | $252,399 | $1,560 | 7.4% | 4.8% | 8.41 | 3.6 | 4.9% | 6.98 | 71.4 |  |
| 4 | Warner Robins, GA | 76.9 | $253,069 | $1,506 | 7.1% | 6.1% | 10.11 | 3.5 | 4.5% | 6.65 | 60.4 |  |
| 5 | Hickory-Lenoir-Morganton, NC | 76.2 | $264,389 | $1,590 | 7.2% | 2.2% | 9.04 | 3.0 | 4.9% | 8.41 | 44.1 |  |
| 6 | Bangor, ME | 75.6 | $274,203 | $1,530 | 6.7% | 3.1% | 8.71 | 3.4 | 4.7% | 3.1 | 52.5 |  |
| 7 | Jackson, TN | 74.6 | $200,556 | $1,388 | 8.3% | 1.7% | 5.83 | 3.7 | 5.7% | 2.57 | 47.1 |  |
| 8 | Iowa City, IA | 74.5 | $298,537 | $1,873 | 7.5% | 4.0% | -2.75 | 2.8 | 3.9% | 6.93 | 42.5 |  |
| 9 | Gulfport-Biloxi, MS | 73.1 | $221,697 | $1,420 | 7.7% | 2.4% | 4.32 | 3.1 | 3.1% | 7.76 | 39.5 |  |
| 10 | Winston-Salem, NC | 73.1 | $275,635 | $1,495 | 6.5% | 4.2% | 8.69 | 3.2 | 4.4% | 6.66 | 58.9 |  |
| 11 | Augusta-Richmond County, GA-SC | 72.5 | $247,989 | $1,469 | 7.1% | 4.0% | 7.44 | 4.0 | 4.4% | 6.5 | 69.7 |  |
| 12 | Johnson City, TN | 72.3 | $277,718 | $1,471 | 6.3% | 3.6% | 15.21 | 3.2 | 5.3% | 4.26 | 59.1 |  |
| 13 | Dothan, AL | 72.2 | $191,224 | $1,192 | 7.5% | 2.4% | 7.88 | 3.6 | 4.9% | 3.81 | 48.0 |  |
| 14 | Pittsburgh, PA | 72.0 | $225,658 | $1,478 | 7.9% | -1.0% | -2.27 | 3.0 | 4.6% | 2.39 | 47.3 |  |
| 15 | Spartanburg, SC | 71.6 | $274,268 | $1,448 | 6.3% | 11.0% | 23.72 | 3.8 | 5.1% | 11.01 | 87.7 |  |
| 16 | Cleveland, OH | 71.4 | $249,000 | $1,417 | 6.8% | -0.6% | -2.23 | 1.9 | 6.3% | 1.92 | 45.7 | ✓ |
| 17 | Hagerstown-Martinsburg, MD-WV | 71.4 | $321,112 | $1,581 | 5.9% | 5.7% | 12.59 | 3.3 | 4.7% | 5.22 | 62.8 |  |
| 44 | Toledo, OH | 67.1 | $201,281 | $1,248 | 7.4% | -0.7% | -2.54 | 3.9 | 5.5% | 0.82 | 31.7 | ✓ |
| 45 | Fort Wayne, IN | 66.9 | $256,388 | $1,252 | 5.9% | 3.2% | 1.48 | 3.4 | 5.2% | 3.54 | 53.8 | ✓ |
| 48 | Odessa, TX | 66.3 | $250,549 | $1,572 | 7.5% | 2.7% | -0.04 | 3.7 | 4.9% | 5.42 | 46.6 | ✓ |
| 61 | Little Rock-North Little Rock-Conway, AR | 64.2 | $227,541 | $1,205 | 6.4% | 2.7% | 4.83 | 3.6 | 3.2% | 4.08 | 61.9 | ✓ |
| 70 | Montgomery, AL | 62.7 | $211,412 | $1,372 | 7.8% | 0.6% | -1.75 | 3.8 | 4.5% | 2.77 | 24.5 | ✓ |
| 75 | Chattanooga, TN-GA | 61.7 | $317,452 | $1,486 | 5.6% | 4.2% | 9.92 | 3.2 | 4.2% | 5.03 | 59.1 | ✓ |
| 92 | Midland, TX | 60.2 | $328,391 | $1,555 | 5.7% | 7.3% | 10.05 | 3.2 | 4.7% | 7.0 | 67.1 | ✓ |
| 93 | Huntsville, AL | 60.1 | $312,822 | $1,387 | 5.3% | 9.6% | 18.4 | 3.1 | 3.0% | 8.33 | 68.8 | ✓ |
| 126 | Fayetteville-Springdale-Rogers, AR | 57.7 | $362,029 | $1,549 | 5.1% | 10.1% | 13.22 | 3.1 | 4.3% | 14.8 | 83.8 | ✓ |
| 164 | Memphis, TN-MS-AR | 54.2 | $241,757 | $1,400 | 7.0% | -0.5% | -5.95 | 4.1 | 2.0% | 2.46 | 25.1 | ✓ |
| 176 | Louisville/Jefferson County, KY-IN | 52.6 | $276,651 | $1,359 | 5.9% | 2.3% | -0.19 | 4.4 | 4.7% | 4.38 | 39.3 | ✓ |
| 189 | Philadelphia-Camden-Wilmington, PA-NJ-DE-MD | 50.8 | $384,753 | $1,884 | 5.9% | 1.4% | -3.42 | 3.6 | 5.0% | 2.04 | 55.5 | ✓ |
| 223 | Milwaukee-Waukesha, WI | 43.5 | $382,089 | $1,501 | 4.7% | -0.0% | -3.36 | 3.2 | 6.5% | 1.97 | 40.4 | ✓ |

Discovered (non-seed) markets in the top of the universe that are NOT on the seed list: Abilene, TX, Greenville, NC, Columbia, SC, Warner Robins, GA, Hickory-Lenoir-Morganton, NC, Bangor, ME, Jackson, TN, Iowa City, IA, Gulfport-Biloxi, MS, Winston-Salem, NC, Augusta-Richmond County, GA-SC, Johnson City, TN, Dothan, AL, Pittsburgh, PA, Spartanburg, SC.

## 2. Stage 2 — properties

Listings pulled: 0 · candidates after early filter: 0 · underwritten: 0 · skipped for API budget: 0.

**No properties were underwritten.** RENTCAST_API_KEY missing: no live listings, no property records, no rent comps. Stage 2 skipped. Set the key (property/.env) and re-run.

## 4. Market report (selected markets)

| Market | Underwritten | Median price | Median gross rent | Median tax | Median econ cap | Median CF | Median CoC | Pop trend | Emp. trend | Wage | HPI 5y | Permits/1000 | Catalysts | Risks | Incentive | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Abilene, TX | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 4.2% | 0.1% | 1151.0 | 7.9% | 6.29 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Greenville, NC | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 4.1% | -1.3% | 1205.0 | 7.7% | 7.11 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Columbia, SC | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 4.8% | 3.2% | 1236.0 | 8.7% | 6.98 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Warner Robins, GA | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 6.1% | -0.0% | 1227.0 | 9.4% | 6.65 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Hickory-Lenoir-Morganton, NC | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 2.2% | -1.9% | 1123.0 | 9.0% | 8.41 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Bangor, ME | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 3.1% | -1.9% | 1097.0 | 9.2% | 3.1 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Jackson, TN | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 1.7% | -1.1% | 1120.0 | 9.4% | 2.57 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Iowa City, IA | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 4.0% | -2.3% | 1283.0 | 6.0% | 6.93 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Gulfport-Biloxi, MS | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 2.4% | -2.2% | 1126.0 | 7.3% | 7.76 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Winston-Salem, NC | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 4.2% | -0.6% | 1363.0 | 9.2% | 6.66 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Augusta-Richmond County, GA-SC | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 4.0% | 2.6% | 1214.0 | 8.3% | 6.5 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Johnson City, TN | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 3.6% | -0.8% | 1123.0 | 10.3% | 4.26 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Dothan, AL | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 2.4% | -1.9% | 1096.0 | 7.3% | 3.81 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Pittsburgh, PA | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | -1.0% | 2.1% | 1549.0 | 6.5% | 2.39 | NOT RESEARCHED | not researched | NOT RESEARCHED | 72.0 |
| Spartanburg, SC | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 11.0% | 4.1% | 1224.0 | 8.9% | 11.01 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Cleveland, OH | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | -0.6% | 0.9% | 1482.0 | 8.2% | 1.92 | NOT RESEARCHED | not researched | NOT RESEARCHED | 72.0 |
| Hagerstown-Martinsburg, MD-WV | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 5.7% | -0.4% | 1151.0 | 7.1% | 5.22 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Toledo, OH | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | -0.7% | -1.4% | 1260.0 | 7.4% | 0.82 | NOT RESEARCHED | not researched | NOT RESEARCHED | 72.0 |
| Fort Wayne, IN | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 3.2% | 0.3% | 1283.0 | 9.0% | 3.54 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Odessa, TX | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 2.7% | 0.8% | 1521.0 | 4.5% | 5.42 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Little Rock-North Little Rock-Conway, AR | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 2.7% | 2.1% | 1241.0 | 6.6% | 4.08 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Montgomery, AL | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 0.6% | -2.1% | 1170.0 | 7.1% | 2.77 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Chattanooga, TN-GA | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 4.2% | -0.2% | 1292.0 | 8.7% | 5.03 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Midland, TX | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 7.3% | 1.6% | 2013.0 | 5.0% | 7.0 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Huntsville, AL | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 9.6% | -0.4% | 1545.0 | 7.4% | 8.33 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Fayetteville-Springdale-Rogers, AR | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 10.1% | 3.5% | 1887.0 | 9.6% | 14.8 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Memphis, TN-MS-AR | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | -0.5% | -1.5% | 1361.0 | 5.9% | 2.46 | NOT RESEARCHED | not researched | NOT RESEARCHED | 72.0 |
| Louisville/Jefferson County, KY-IN | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 2.3% | -0.1% | 1409.0 | 7.0% | 4.38 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Philadelphia-Camden-Wilmington, PA-NJ-DE-MD | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 1.4% | 2.5% | 1708.0 | 5.9% | 2.04 | NOT RESEARCHED | not researched | NOT RESEARCHED | 76.0 |
| Milwaukee-Waukesha, WI | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | -0.0% | 1.7% | 1461.0 | 8.7% | 1.97 | NOT RESEARCHED | not researched | NOT RESEARCHED | 72.0 |

## 5. Data-quality problems (biggest first)

- RENTCAST_API_KEY missing — no live listings, property records, tax bills, or rent comps; Stage 2 could not run on real data.
- CENSUS_API_KEY missing — ACS income, renter share, 2-4 unit stock share, vacancy and ZIP-level neighborhood profiles are UNKNOWN (Census API now requires a key).
- No verified project catalysts on file for any market (research/markets/<cbsa>.yaml empty) — catalyst scores rest on fundamentals only.
- BRAVE_SEARCH_API_KEY missing — relocation incentives, landlord law, assessor sources and project catalysts were not researched automatically; the weekly Claude run must fill research/markets/*.yaml via web search.

## 6. API calls used

- bls: {'live': 2, 'cached': 0}
- bls_laus_file: {'live': 1, 'cached': 0}
- census_bps: {'live': 1, 'cached': 0}
- census_popest: {'live': 1, 'cached': 0}
- fhfa: {'live': 1, 'cached': 0}
- zillow: {'live': 2, 'cached': 0}

## 7. Keys / data that would most improve accuracy

- RENTCAST_API_KEY (highest impact): live 2-4 unit listings, property records with actual tax bills/assessments, unit counts, rental comps and AVMs — without it there is no property-level analysis.
- CENSUS_API_KEY (second): metro and ZIP-level income, renter share, 2-4 unit stock share, vacancy, in-migration, industry mix (economic diversity).
- BLS_API_KEY: lifts the shared-IP daily quota so QCEW wages and LAUS series come from the API reliably.
- BRAVE_SEARCH_API_KEY: automated research leads for catalysts, incentives, landlord law and assessor sources (still human-verified).
- FRED_API_KEY: metro active-listing counts and median days on market (Realtor.com series on FRED) for liquidity/inventory.
- Non-API: a lender quote (replaces the 7.50% assumption), one landlord insurance quote per finalist, county tax bills and rent rolls for finalists.

---
_No number in this report is a lender quote, an insurance quote, or a verified tax bill unless its status says VERIFIED. UNKNOWN is deliberate._
