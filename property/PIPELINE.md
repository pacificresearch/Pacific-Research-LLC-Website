# Property Pipeline — finalists board
> Refreshed every weekly run. Status: active / price change / withdrawn / passed (reason) / under contract.
> Last refresh: 2026-11-23 (persistent weekly session). RENTCAST_API_KEY still missing — Stage 2 has never run on real listings.

## Current finalists (Ranking E)
| First seen | Address | Market | Units | Ask | Cons. CF/mo | CoC | Econ DSCR | Conf. | Post-sale tax risk | UW ceiling | Status | Open diligence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| — | (no RentCast key yet — no real listings underwritten) | | | | | | | | | | | |

## Markets under watch (discovered, not seed) — top 8 Stage 1, research file on disk
Catalyst = fundamentals + verified projects (research/markets/<cbsa>.yaml). Tax risk = what the county does to assessed value after an arm's-length sale. "2-4 OK?" = whether the homebuyer incentive on file admits an owner-occupied 2-4 unit.
| Rank | Market | Stage 1 | Catalyst | Top verified project | Incentive on file (2-4 OK?) | Tax risk | Landlord-law note | File |
|---|---|---|---|---|---|---|---|---|
| 1 | Abilene, TX | 78.3 | 64.4 | Dyess AFB B-21 beddown ~$1.6B, under construction (AF sites 403 — unverified $); Crusoe/Stargate 1.2 GW campus ($ unverified) | none found | HIGH — Taylor CAD reappraises all property annually; homestead cap dies on sale | No rent control (LGC 214.902); 3-day notice; no registration found | `research/markets/10180.yaml` |
| 2 | Greenville, NC | 77.5 | 52.5 | Nipro Medical $398M / 232 jobs, announced; Boviet Solar $294M / 908 jobs, completed 2025 | City HOME DPA up to $40K (unverified — city site blocked; 2-4 UNKNOWN) | MEDIUM — no sale reset (G.S. 105-287); 4-yr cycle, next 2028 | G.S. 160D-1207 bars rental registration; deposit 1.5–2 mo | `research/markets/24780.yaml` |
| 3 | Columbia, SC | 77.0 | 80.6 | Scout Motors $2.0B / 4,000 jobs, under construction, production 2027 | Richland Co. HAP $24,500 (single-family detached only — NO) | HIGH — ATI reset to sale price (12-37-3140) + 6% non-owner ratio | Rental permit $25/unit/yr; rent control preempted (27-39-60) | `research/markets/17900.yaml` |
| 4 | Warner Robins, GA | 76.8 | 60.2 | Audi US plant, Peach Co. megasite ~$4B / 4,500 jobs, announced 2026-10, production 2031 | Georgia Dream $10K statewide (2-4 UNKNOWN) | MEDIUM — sale price caps next-year FMV (48-5-2(3)) | HB 404: 2-mo deposit cap, 3-business-day notice; single-employer (Robins AFB >21K) | `research/markets/47580.yaml` |
| 5 | Hickory-Lenoir-Morganton, NC | 76.2 | 54.9 | Prysmian Claremont $1B+ / 385 jobs, under construction; Microsoft 4 data centers $1B+ | Unifour Consortium DPA 15% to $20K (first-time; 2-4 UNKNOWN) | HIGH — Catawba revaluation effective 2027-01-01 (5 weeks out) | Same NC statutory frame; no Hickory registration | `research/markets/25860.yaml` |
| 6 | Bangor, ME | 75.6 | 46.4 | UMaine Morse Arena $170M under construction (trade press — unverified); 0 of 5 catalysts primary-verified | City CDBG DPA ~$20K (city page 404 — unverified); MaineHousing $5K | MEDIUM — first full citywide reval since 1980s effective 4/1/2026 | No rent control; Bangor Ch. 282: 60-day notice of any rent increase, no application fees | `research/markets/12620.yaml` |
| 7 | Jackson, TN | 74.6 | 48.3 | Prysmian Jackson doubling $100M / 100 jobs, announced 2026-08; Ford Stanton plant adjacent — EV cancelled 12/2025, gas trucks 2029 | THDA Great Choice Plus statewide (amount unverified) | MEDIUM — 5-yr cycle, 2027 reappraisal; ratio 0.7574 (values ~24% under market) | URLTA 14-day notice; no state registry below 500K metros | `research/markets/27180.yaml` |
| 8 | Iowa City, IA | 74.5 | 26.9 | P&G expansion $150M / 100 jobs, announced (IEDA verified); UIHC tower Ph.1 $72.5M | City DPA up to $24,999 (city page 403 — unverified) | MEDIUM — odd-year statewide reassessment, no sale reset; rollback 44.5% | Rent control preempted (Iowa Code 364.3(9)); rental permit program — fee UNKNOWN; single-employer (UI/UIHC ~47% of county jobs) | `research/markets/26980.yaml` |

Next unresearched by Stage 1 rank: Gulfport-Biloxi MS (#9), Winston-Salem NC (#10), Augusta GA-SC (#11, catalyst 68.3), Johnson City TN (#12), Spartanburg SC (#15, catalyst 90.7 on fundamentals alone — research next week).

## Seed markets — research coverage (14 of 14 filed 2026-11-23)
| Market | Stage 1 rank | Catalyst | Top verified project | Tax risk | Compliance stack | File |
|---|---|---|---|---|---|---|
| Cleveland, OH | 16 | 57.2 | Browns stadium district Brook Park $2.6B; Bedrock riverfront $3.5B; Clinic Neuro Institute $1.3B | LOW (next reappraisal 2031) | $70/unit/yr registration + Lead Safe Certificate every 2 yrs; Lakewood point-of-sale inspection | `17410` |
| Toledo, OH | 44 | 32.5 | Stellantis Toledo Assembly ~$400M / 900+ jobs (SEC 6-K); First Solar R&D $488M | LOW | Lead-Safe certificate on every pre-1978 1-4 unit before new tenancy (due 2026-12-31); auditor registry, no fee | `45780` |
| Fort Wayne, IN | 45 | 56.3 | Google data center $2B / 200 jobs, under construction | MEDIUM (1%→2% cap, sale field inspection) | Housing Registration Form for non-owner-occupied (fee UNKNOWN); IC 32-31-1-20 preempts rent control | `23060` |
| Odessa, TX | 48 | 35.8 | TCDC Ector Co. AI campus 200 MW Ph.1 (SEC 8-K; $ undisclosed); Liberty Energy HQ $35M | HIGH (annual) | none; energy_boom_watch | `36220` |
| Little Rock, AR | 60 | 63.9 | AVAIO Leo AI data center $6B Ph.1 / 500 jobs, announced; Eaton NLR $242M / 1,200 jobs | HIGH (26-26-1123 reset to 20% of full value at next assessment) | Registration $35/yr ≤3 units; inspection on title transfer | `30780` |
| Montgomery, AL | 70 | 21.1 | HMMA engine expansion $413M / 53 jobs; HD Hyundai transformers $200M / 200 jobs | HIGH (Class II 20% ratio; annual) | City developing rental registry (announced 2026-04, no fee yet) | `33860` |
| Chattanooga, TN-GA | 75 | 52.2 | West Star Aviation $32M / 200 jobs; NOVONIX ~$1B / 500 jobs ($ unverified, conditional DOE loan) | LOW (reappraised 2025, next 2029) | No registration; complaint-driven + district sweeps | `16860` |
| Midland, TX | 92 | 64.6 | AST SpaceMobile plant $100M+ / 1,800 jobs, announced (MDC repost); Behavioral Health Center $220M completed | HIGH (annual) | none; energy_boom_watch | `33260` |
| Huntsville, AL | 93 | 57.7 | US Space Command HQ ~1,400 jobs, under construction; Eli Lilly API campus $6B / 450 jobs (Limestone Co.) | HIGH (Class II; Act 2024-344 cap removed on ownership change) | No registration; single-employer (Redstone ~45,500) | `26620` |
| Fayetteville-Springdale-Rogers, AR | 129 | 67.1 | Mercy/Walton $700M health affiliation; Walmart HQ completed 2025; Conagra $220M | HIGH (same AR reset) | Life Works Here relocation incentive CLOSED; business license unless individual <3 units | `22220` |
| Memphis, TN-MS-AR | 164 | 42.4 | St. Jude $12.9B plan / 2,300 jobs (verified); xAI Colossus $12B ($ unverified) | LOW (reappraised 2025, next 2029) | No registry; Environmental Court enforcement | `32820` |
| Louisville, KY-IN | 175 | 52.2 | Ford Louisville Assembly EV retool $1.9B (2,200 jobs retained); GE Appliances $490M / 800 jobs | HIGH (PVA uses sale price ~2 yrs + inspection on every sale) | Heaviest stack: $50/yr registry, proactive inspections in 11 areas, Lead-Safe Registry risk assessment on every pre-1978 rental | `31140` |
| Philadelphia, PA-NJ-DE-MD | 189 | 65.6 | Navy Yard $6B plan / 12,000 jobs ($30M PA SITES grant verified); 76ers arena cancelled | MEDIUM (OPA sales-driven revaluations, no reset) | Good-cause eviction now covers ALL leases at expiry (eff. 2026-11-01, owner-occupant 2-4 NOT exempt); 30-day diversion; $69/unit license; Philly First Home $10K admits duplexes | `37980` |
| Milwaukee, WI | 223 | 52.2 | Microsoft Mount Pleasant $7B+ (Racine Co., regional); Northwestern Mutual $500M / 2,000 jobs | MEDIUM (annual full-value) | No licensing (66.0104); Uptown inspection-district pilot adopted 2026-09 | `33340` |

## Passed / withdrawn
| Address | Date | Reason |
|---|---|---|
