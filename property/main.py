#!/usr/bin/env python3
"""PRG Property Acquisition Screener — weekly run.

  python3 main.py                 # full run (Stage 1 public data; Stage 2 needs RENTCAST_API_KEY)
  python3 main.py --stage1-only   # market screen only
  python3 main.py --fixture       # Stage 2 on labeled synthetic listings (pipeline/math proof, no API)
  python3 main.py --max-enrich 8  # cap paid enrichment
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src import brave_search, fred  # noqa: E402
from src.config import KEY_NAMES, ROOT, api_keys, load_config  # noqa: E402
from src.database import Cache  # noqa: E402
from src.http_client import HttpError, get_json, get_text  # noqa: E402
from src.market_screen import run_stage1  # noqa: E402
from src.property_search import attach_research_and_catalysts, estimate_calls, load_fixtures, run_stage2  # noqa: E402
from src.rentcast import Budget, RentCast  # noqa: E402
from src.reporting import write_all  # noqa: E402

log = logging.getLogger("prg")


def selftest(cfg) -> dict:
    keys = api_keys()
    st = {k: ("set" if v else "MISSING") for k, v in keys.items()}
    probes = {"rentcast_reachable": ("https://api.rentcast.io/v1/markets", 401), "zillow_reachable": ("https://files.zillowstatic.com/research/public_csvs/zori/Metro_zori_uc_sfrcondomfr_sm_month.csv", 200),
              "census_popest_reachable": ("https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/metro/totals/", 200), "fhfa_reachable": ("https://www.fhfa.gov/hpi/download/monthly/hpi_master.csv", 200)}
    import requests
    for name, (url, ok_code) in probes.items():
        try:
            r = requests.head(url, timeout=15, allow_redirects=True, headers={"User-Agent": "PRG-PropertyScreener/0.1 (andrew@pacificresearchllc.com)"})
            st[name] = "ok" if r.status_code in (ok_code, 200, 401, 403, 405) else f"HTTP {r.status_code}"
        except requests.RequestException as e:
            st[name] = f"FAILED ({type(e).__name__})"
    st["cache_db"] = str(cfg.cache_db)
    return st


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage1-only", action="store_true")
    ap.add_argument("--fixture", action="store_true", help="run Stage 2 on tests/fixtures/sample_listings.json (SYNTHETIC)")
    ap.add_argument("--max-enrich", type=int, default=None)
    ap.add_argument("--markets-out", type=int, default=None)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--archive", action="store_true", help="also copy outputs to reports/<date>/ (artifact rule)")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    cfg = load_config()
    if args.markets_out:
        cfg.raw["run"]["stage1_markets_out"] = args.markets_out
    cache = Cache(cfg.cache_db)
    started = datetime.now(timezone.utc)
    run_id = started.strftime("%Y-%m-%d") + "-" + uuid.uuid4().hex[:6]
    out_dir = args.out or cfg.output_dir
    st = selftest(cfg)
    log.info("self-test: %s", json.dumps(st))
    budgets = {"bls": {"used": 0, "max": cfg["api_budget"]["bls_max_queries_per_run"]}, "brave": {"used": 0, "max": cfg["api_budget"]["brave_max_calls_per_run"]}}

    markets, universe, src_status = run_stage1(cfg, cache, budgets)
    st.update(src_status)
    attach_research_and_catalysts(markets, cfg)
    rc = RentCast(cache, cfg["run"]["cache_ttl_hours"], Budget(cfg["api_budget"]["rentcast_max_calls_per_run"]))
    fixtures = None
    stage2 = {"results": [], "rankings": {}, "listings_pulled": 0, "candidates": 0, "underwritten": 0, "skipped_for_budget": 0}
    stage2_note = ""
    if args.stage1_only:
        stage2_note = "Stage 2 skipped by flag."
    elif args.fixture:
        fixtures = load_fixtures(ROOT / "tests" / "fixtures" / "sample_listings.json")
        stage2_note = "FIXTURE MODE — synthetic listings."
    elif not rc.available:
        stage2_note = "RENTCAST_API_KEY missing: no live listings, no property records, no rent comps. Stage 2 skipped. Set the key (property/.env) and re-run."
    if fixtures is not None or rc.available:
        est = estimate_calls(markets, cfg)
        log.info("RentCast call estimate before bulk pulls: %s", est)
        st["rentcast_call_estimate"] = json.dumps(est)
        # Brave research leads (optional) are drafted to research/drafts for verification; never fed straight into scores
        if brave_search.available():
            drafts = ROOT / "research" / "drafts"
            drafts.mkdir(parents=True, exist_ok=True)
            for m in markets:
                leads = brave_search.research_leads(cache, cfg["run"]["cache_ttl_hours"]["brave"], {"city": (m.research.get("cities") or [m.name.split(',')[0]])[0], "state": m.state, "county": ""}, budgets["brave"])
                if leads:
                    (drafts / f"{m.cbsa}.json").write_text(json.dumps(leads, indent=1))
        stage2 = run_stage2(markets, cfg, cache, rc, fixtures=fixtures, max_enrich=args.max_enrich)
    finished = datetime.now(timezone.utc)

    results = stage2["results"]
    calls = cache.call_counts(since=started.isoformat())
    problems = []
    if not api_keys()["RENTCAST_API_KEY"]:
        problems.append("RENTCAST_API_KEY missing — no live listings, property records, tax bills, or rent comps; Stage 2 could not run on real data.")
    if not api_keys()["CENSUS_API_KEY"]:
        problems.append("CENSUS_API_KEY missing — ACS income, renter share, 2-4 unit stock share, vacancy and ZIP-level neighborhood profiles are UNKNOWN (Census API now requires a key).")
    if "FAILED" in st.get("bls_laus", ""):
        problems.append("BLS LAUS metro file failed — unemployment/employment trend UNKNOWN for all markets.")
    if all("avg_weekly_wage" not in m.metrics or not m.metrics["avg_weekly_wage"].known for m in markets):
        problems.append("BLS QCEW wages UNKNOWN — keyless BLS API daily quota exhausted on this egress IP (BLS_API_KEY fixes).")
    if not any(m.research.get("catalysts") for m in markets):
        problems.append("No verified project catalysts on file for any market (research/markets/<cbsa>.yaml empty) — catalyst scores rest on fundamentals only.")
    if not brave_search.available():
        problems.append("BRAVE_SEARCH_API_KEY missing — relocation incentives, landlord law, assessor sources and project catalysts were not researched automatically; the weekly Claude run must fill research/markets/*.yaml via web search.")
    if results:
        unk_tax = sum(1 for r in results if r["taxes"]["post_sale_tax_risk"] == "UNKNOWN")
        low_grade = sum(1 for r in results if r["rent"]["per_building"]["conservative"].get("grade", "D") in ("C", "D"))
        problems.append(f"{sum(1 for r in results if r['rent']['per_building']['contractual']['base'] is None)}/{len(results)} properties have no contractual rent; {low_grade}/{len(results)} have grade C/D rent comps; {unk_tax}/{len(results)} have POST-SALE TAX RISK = UNKNOWN; insurance is ESTIMATED on {sum(1 for r in results if r['insurance']['status'] != 'VERIFIED')}/{len(results)}.")
        if any(r["fixture"] for r in results):
            problems.insert(0, "FIXTURE MODE: all underwritten properties are synthetic — nothing here is investable.")
    improvements = ["RENTCAST_API_KEY (highest impact): live 2-4 unit listings, property records with actual tax bills/assessments, unit counts, rental comps and AVMs — without it there is no property-level analysis.",
                    "CENSUS_API_KEY (second): metro and ZIP-level income, renter share, 2-4 unit stock share, vacancy, in-migration, industry mix (economic diversity).",
                    "BLS_API_KEY: lifts the shared-IP daily quota so QCEW wages and LAUS series come from the API reliably.",
                    "BRAVE_SEARCH_API_KEY: automated research leads for catalysts, incentives, landlord law and assessor sources (still human-verified).",
                    "FRED_API_KEY: metro active-listing counts and median days on market (Realtor.com series on FRED) for liquidity/inventory.",
                    "Non-API: a lender quote (replaces the 7.50% assumption), one landlord insurance quote per finalist, county tax bills and rent rolls for finalists."]
    summary = {"run_id": run_id, "markets_screened": len(universe), "markets_selected": len(markets), "listings_pulled": stage2["listings_pulled"], "candidates": stage2["candidates"],
               "underwritten": stage2["underwritten"], "skipped_for_budget": stage2["skipped_for_budget"], "stage2_note": stage2_note, "rentcast_live_calls": rc.budget.used,
               "rentcast_cached_hits": rc.budget.cached_hits, "api_calls": calls, "data_quality_problems": problems, "improvements": improvements}
    run = {"run_id": run_id, "started_at": started.isoformat(), "finished_at": finished.isoformat(), "selftest": st, "summary": summary, "fixture_mode": fixtures is not None}
    paths = write_all(cfg, run, markets, universe, stage2, out_dir)
    cache.record_run(run_id, run["started_at"], run["finished_at"], summary)

    # ---- terminal summary ----------------------------------------------------
    ranks = stage2.get("rankings", {})
    P = print
    P("\n" + "=" * 100)
    P(f"PRG PROPERTY SCREENER — {run_id}" + ("   *** FIXTURE MODE: SYNTHETIC PROPERTIES ***" if fixtures is not None else ""))
    P("=" * 100)
    def block(title, rows, fmt):
        P(f"\n{title}")
        if not rows:
            P("   (none — " + stage2_note + ")")
        for i, r in enumerate(rows[:10], 1):
            P(f"  {i:>2}. {fmt(r)}")
    block("1) BEST 10 BY CONSERVATIVE MONTHLY CASH FLOW", ranks.get("A_conservative_cash_flow", []), lambda r: f"{r['address'][:48]:48} {r['units']}u ${r['price']:>9,.0f}  CF ${r['monthly_cash_flow']:>7,.0f}/mo  DSCR {r['economic_dscr']}  conf {r['confidence']}")
    block("2) BEST 10 BY CASH-ON-CASH", ranks.get("B_cash_on_cash", []), lambda r: f"{r['address'][:48]:48} {r['units']}u ${r['price']:>9,.0f}  CoC {r['cash_on_cash']:.1%} on ${r['coc_denominator']:,.0f}  conf {r['confidence']}")
    block("3) BEST 10 CASH FLOW + APPRECIATION", ranks.get("C_cash_flow_plus_appreciation", []), lambda r: f"{r['address'][:48]:48} {r['units']}u  asym {r['asymmetry_score']}  CF ${r['monthly_cash_flow']:,.0f}  catalyst {r['catalyst_score']}  conf {r['confidence']}")
    P("\n4) TOP 10 MARKETS (Stage 1 public-data screen; seeds marked S)")
    for m in markets[:10]:
        v = lambda k: (m.metrics[k].v() if k in m.metrics else None)
        P(f"  {m.stage1_rank:>3}. {'S' if m.seed else ' '} {m.name[:40]:40} score {m.stage1_score:5.1f}  ZHVI ${v('typical_home_value') or 0:>8,.0f}  ZORI ${v('typical_rent') or 0:>5,.0f}  R/V {(v('rent_to_value_metro') or 0):.1%}  pop20-24 {(v('population_growth_4y') or 0):+.1%}  dom.mig/1k {v('domestic_migration_per_1000')}  unemp {v('unemployment_rate')}  catalyst {m.catalyst_score}")
    P("\n5) BIGGEST DATA-QUALITY PROBLEMS")
    for p in problems:
        P(f"  - {p}")
    P("\n6) API CALLS USED THIS RUN (live / cached)")
    for k, v in calls.items():
        P(f"  - {k}: {v['live']} live, {v['cached']} cached")
    P(f"  - rentcast budget: {rc.budget.used}/{rc.budget.max} live, {rc.budget.cached_hits} cache hits, {rc.budget.skipped} skipped")
    P("\n7) WHAT WOULD MOST IMPROVE ACCURACY")
    for p in improvements:
        P(f"  - {p}")
    if args.archive:
        import shutil
        arch = ROOT / "reports" / started.strftime("%Y-%m-%d")
        arch.mkdir(parents=True, exist_ok=True)
        for k, p in paths.items():
            if k != "raw_data.json":          # raw JSON stays in output/ (size); the cache DB holds the provenance
                shutil.copy(p, arch / k)
        paths["archive_dir"] = arch
    P("\nOUTPUT FILES")
    for k, p in paths.items():
        P(f"  - {p}")
    P("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
