# NMRC N323988871 — Firm Pricing Model (researched 2026-08-14)

## The binding constraint
PWS §2.0: purchase order **may not exceed the Simplified Acquisition
Threshold — $250,000 TOTAL** for the full 30 months. This is the
government's hard budget signal. Any estimate above it disqualifies the
bidder's credibility.

## Demand (from PWS — not assumptions)
| Period | Dates | Hours |
|---|---|---|
| Base | 9/8/2026 – 9/7/2027 | 1,920 |
| Option I | 9/8/2027 – 9/7/2028 | 1,920 |
| 52.217-8 extension | 9/8/2028 – 3/31/2029 (~6.75 mo) | ~1,080 |
| **Total** | 30 months | **~4,920** |

**Revenue ceiling per billable hour: $250,000 / 4,920 = $50.81/hr.**
1 FTE, on-site Fort Detrick, Mon–Fri 8 hrs/day, federal holidays off.
GFP: workspace, computer, phone, CAC (≈ zero ODCs; occ-health exams
~$800/yr are contractor cost, NOT chargeable).

## Market wage data (BLS OES 2025 via O*NET, occupation 49-9062)
| Percentile | US hourly | Maryland hourly | MD annual |
|---|---|---|---|
| 25th | $22.82 | $27.84 | $57,910 |
| **Median** | $29.64 | **$34.77** | **$72,310** |
| 75th | $37.74 | $43.36 | $90,180 |

## Cost build (W2, 2,080 paid hrs → 1,920 billable)
| Element | @$33.00/hr wage | @$34.77/hr (MD median) | @$38.46/hr ($80K) |
|---|---|---|---|
| Annual wages | $68,640 | $72,322 | $79,997 |
| SCA H&W fringe (~$5.36/hr × 2080)* | $11,149 | $11,149 | $11,149 |
| Employer taxes+WC (~10.65%) | $7,310 | $7,702 | $8,520 |
| Occ-health exams | $800 | $800 | $800 |
| **Direct cost / year** | **$87,899** | **$91,973** | **$100,466** |
| **Direct cost / billable hr** | **$45.78** | **$47.90** | **$52.33** ❌ over ceiling |

*H&W rate: verify current DOL rate + the actual Wage Determination in
the RFQ. **RISK FLAG:** Frederick MD falls in the DC-metro SCA area;
if the WD floor for BMET II/III lands ≥ $38/hr, the math breaks and we
re-decide at RFQ time. Verify WD FIRST THING when the solicitation drops.

## Price (firm — fills the ceiling, stays under it)
| CLIN | Price | Effective rate |
|---|---|---|
| Base year | **$97,000** | $50.52/hr |
| Option I | **$99,000** | $51.56/hr |
| 52.217-8 extension | **$53,500** | $49.54/hr |
| **TOTAL** | **$249,500** | $50.71/hr blended — under SAT ✓ |

## Margin reality (Andrew's decision)
| Hire wage | Annual salary | GM% | 30-mo profit |
|---|---|---|---|
| $33.00/hr | $68,640 | ~9.7% | ~$24,000 |
| $34.77/hr | $72,310 | ~5.5% | ~$14,000 |
| $36.50/hr | $75,920 | ~2.5% | ~$6,000 |
| $38.46/hr | $80,000 | negative | ❌ |

**ANDREW'S DECISION (8/15): posting stays at $80–90K.** Accepted
consequence: at $80K hire the contract is ≈ break-even to slightly
negative (≈ −$3.5K/yr vs. billings, before ~$2–4K/yr overhead); at $90K
it loses ~$15K/yr. Operating rule: POST 80–90, OFFER AT $80K; treat
asks above ~$83K as walk-away unless the candidate is exceptional.
30-month P&L swing between hiring at $80K vs $90K ≈ $28K. Contract is
explicitly a strategic loss-leader/PP builder at this salary band —
value = first prime DoD contract + CPARS + incumbency on a recompete
likely to exceed SAT next cycle.

## Strategic read (why thin margin is still a BID)
CLAUDE.md: sub-$250K simplified acquisitions are strategic
past-performance builders worth more than face value. This is PRG's
lowest-friction path to: first prime DoD contract, CPARS record,
NMRC/BUMED customer relationship, and incumbency on the recompete —
which, given the documented backlog, likely grows beyond SAT next cycle
(where margins normalize). Price to win at $249,500; hire at $33–35/hr;
treat the ~$14–24K profit as paid business development.
