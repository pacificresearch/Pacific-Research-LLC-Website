# 36C24E26Q0054 — Section 5 Pricing (built 2026-08-18, delegated authority)

**Deliverable:** `03_proposal/Section_5_Price_Attachment3_CLINS_PRG.xlsx` — a copy
of the Government's `Attachment+3+CLINSRev8-13-2026.xlsx` with ONLY column O
(Unit Price) filled, exactly as CO Q&A #6 instructs ("The only column that
should require input is O. Column DA should automatically populate.").
Column DA's table formulas are untouched; Excel populates them on open.
(LibreOffice recalc hangs in this container — extended totals verified in
Python instead; formulas confirmed intact.)

## CLIN structure (from the workbook + PWS)
One CLIN unit = one **block**: a pre/post work package, an on-site day, or a
portal-to-portal travel leg each count as QTY 1 (CLIN x001 description).
Estimated annual quantities: 475 blocks (x001) + 2,100 PQS hours (x002).
Travel (x003) is reimbursable — no unit price, left at 0.

## Prices entered (basis $105/hr — Andrew's confirmed target rate)
| CLIN | Item | Qty | Unit price | Extended |
|---|---|---|---|---|
| 0001 | CRQA visit blocks, base yr | 475 | **$840** (8 hr × $105) | $399,000 |
| 0002 | GCP PQS hourly, base yr | 2,100 | **$105** | $220,500 |
| 0003 | Travel | 0 | $0 (reimbursable) | $0 |
| 1001 | Option yr 1 blocks | 475 | **$864** ($108/hr) | $410,400 |
| 1002 | Option yr 1 PQS | 2,100 | **$108** | $226,800 |
| 2001 | Option yr 2 blocks | 475 | **$888** ($111/hr) | $421,800 |
| 2002 | Option yr 2 PQS | 2,100 | **$111** | $233,100 |
| | **Evaluated total (all periods)** | | | **$1,911,600** |

Escalation ≈2.9%/yr protects against monitor wage growth (ECI healthcare
labor trend). Total sits under the $2M IDIQ ceiling with ~$88K headroom.
These are ESTIMATED quantities on an IDIQ — only the minimum guarantee
($20K) is certain revenue; actual revenue follows task orders.

## Margin check (fulfillment: professional services, 30–50% band)
Senior contract CRQAs (10+ yrs, federal experience — required by PWS 7.3.5/
7.3.6) market at roughly $65–85/hr W2-equivalent ($600–700/day common for
1099 per-visit contract CRAs). At $105/hr billed:
- Pay $75/hr equiv → GM ≈ 22–28% after employer costs — below band but
  acceptable for entity PP building at low volume.
- Pay $65/hr equiv → GM ≈ 30–35% — in band.
- VAAR 852.219-75: ≥50% of personnel cost must go to PRG W2 employees or
  SDVOSB subs — 1099 monitors are NOT similarly situated; keep the primary
  monitor W2 (or predominantly W2 mix) once task orders flow.
- NACI (~$230/monitor) + credentialing time priced into overhead.

## ⛔ Open items for submission
- Named monitor(s) must satisfy PWS 7.3.5 (10 yr monitoring) + 7.3.6 (5 yr
  federal) + supply 3 references — placeholders in S2/S6 until the hire is
  selected. **No qualified monitor committed by ~8/22 = no-bid tripwire.**
- Signed SF30s (Amendments 0001, 0002) — Andrew.
- 852.219-75 certificate fill-in — at package assembly.
