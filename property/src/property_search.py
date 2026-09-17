"""STAGE 2 — RentCast listing pull per selected market, early filters, budgeted enrichment, full underwriting per property."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from . import appreciation, census, relocation, rent_analysis, risk, scoring, tax_analysis, underwriting as uw
from .config import Config, api_keys
from .database import Cache
from .models import DataPoint, Listing, MarketProfile, PropertyRecord, Status
from .rentcast import Budget, RentCast, normalize_listing, normalize_property

log = logging.getLogger("prg.stage2")


def dpd(dp: DataPoint) -> Dict[str, Any]:
    d = dp.model_dump()
    d["status"] = dp.status.value
    d["known"] = dp.known
    return d


def load_research(cfg: Config, cbsa: str) -> dict:
    f = cfg.research_dir / f"{cbsa}.yaml"
    if f.exists():
        with open(f) as fh:
            return yaml.safe_load(fh) or {}
    return {}


def load_fixtures(path: Path) -> List[Listing]:
    with open(path) as f:
        data = json.load(f)
    out = []
    for r in data["listings"]:
        r["_fixture"] = True
        out.append(normalize_listing(r))
    return out


def estimate_calls(markets: List[MarketProfile], cfg: Config) -> Dict[str, int]:
    b = cfg["api_budget"]
    per_market = b["rentcast_listing_pages_per_market"]
    n_cities = sum(len(m.research.get("cities") or [1]) for m in markets)
    return {"listing_pulls": min(n_cities, len(markets) * per_market), "enrichment_max": b["rentcast_max_enrich_properties"] * 3,
            "total_estimate": min(n_cities, len(markets) * per_market) + b["rentcast_max_enrich_properties"] * 3, "budget_cap": b["rentcast_max_calls_per_run"]}


def pull_listings(markets: List[MarketProfile], rc: RentCast, cfg: Config, fixtures: Optional[List[Listing]]) -> List[Listing]:
    ceiling = cfg.capital.price_ceiling
    if fixtures is not None:
        by_cbsa = {m.cbsa: m for m in markets}
        out = []
        for l in fixtures:
            if l.price and l.price <= ceiling and l.cbsa in by_cbsa:
                l.market_name = by_cbsa[l.cbsa].name
                out.append(l)
        return out
    out: List[Listing] = []
    seen = set()
    for m in markets:
        cities = m.research.get("cities") or [m.name.split(",")[0].split("-")[0]]
        for city in cities[: cfg["api_budget"]["rentcast_listing_pages_per_market"]]:
            if not rc.budget.ok():
                log.warning("RentCast budget exhausted before listing pull for %s", m.name)
                break
            for l in rc.sale_listings(city, m.state, ceiling):
                if l.id in seen:
                    continue
                seen.add(l.id)
                l.cbsa, l.market_name = m.cbsa, m.name
                out.append(l)
    return out


def early_filter(listings: List[Listing], markets: Dict[str, MarketProfile], cfg: Config) -> List[Dict[str, Any]]:
    """Cheap pre-enrichment triage on metro rent proxies; returns candidates ordered for enrichment."""
    ra = cfg["rent_analysis"]
    rows = []
    for l in listings:
        if not l.price or l.price > cfg.capital.price_ceiling or l.property_type not in ("Multi-Family", "Apartment", ""):
            continue
        m = markets.get(l.cbsa)
        units_proxy = l.unit_count_hint or (max(2, min(4, round((l.bedrooms or 4) / 2))))
        zori = m.metrics["typical_rent"].v() if m and "typical_rent" in m.metrics else None
        proxy_rtp = (zori * 0.85 * units_proxy / l.price) if zori else None   # 2-4 unit rents typically below metro ZORI; 0.85 haircut
        exception = bool(m and ((m.catalyst_score or 0) >= 70 or (m.stage1_rank or 99) <= 5))
        keep = proxy_rtp is None or proxy_rtp >= ra["early_filter_min_rent_to_price"] or exception
        rows.append({"listing": l, "units_proxy": units_proxy, "proxy_rent_to_price": round(proxy_rtp, 4) if proxy_rtp else None,
                     "keep": keep, "exception": exception and not (proxy_rtp and proxy_rtp >= ra["early_filter_min_rent_to_price"])})
    kept = [r for r in rows if r["keep"]]
    kept.sort(key=lambda r: ((r["proxy_rent_to_price"] or 0) + 0.001 * r["units_proxy"]), reverse=True)
    log.info("early filter: %d listings -> %d candidates (%d via exception)", len(rows), len(kept), sum(r["exception"] for r in kept))
    return kept


def underwrite_listing(l: Listing, m: MarketProfile, rc: RentCast, cache: Cache, cfg: Config, research: dict) -> Dict[str, Any]:
    ttl = cfg["run"]["cache_ttl_hours"]
    record: Optional[PropertyRecord] = None
    if l.fixture and l.raw.get("_fixture_record"):
        record = normalize_property(l.raw["_fixture_record"])
    elif rc.available:
        record = rc.property_record(l.formatted_address)
    units, units_status = None, Status.UNKNOWN
    if record and record.unit_count:
        units, units_status = int(record.unit_count), Status.PROVIDER
    elif l.unit_count_hint:
        units, units_status = int(l.unit_count_hint), Status.ESTIMATED
    listing_research = (research.get("listings") or {}).get(l.id) or {}
    if listing_research.get("units_verified"):
        units, units_status = int(listing_research["units_verified"]), Status.VERIFIED
    n = units or (max(2, min(4, round((l.bedrooms or 4) / 2))))

    avm = None
    rent = rent_analysis.analyze(l, record, units, rc, cfg, contractual=listing_research.get("contractual_rent"))
    if rent["per_building"]["conservative"]["base"] is None and rc.available:
        avm = rc.rent_avm(l.formatted_address, bedrooms=(l.bedrooms / n if l.bedrooms and units else None))
        rent = rent_analysis.analyze(l, record, units, rc, cfg, contractual=listing_research.get("contractual_rent"), avm=avm)
    taxes = tax_analysis.analyze(record, l.price, l.state, cfg, research)
    ins = risk.insurance_estimate(l, n, cfg, listing_research.get("insurance_quote"))
    flags = risk.capex_flags(l, record, research)
    rehab = risk.rehab_range(l, cfg, flags)
    haz = risk.hazards(l.state, cfg)
    reg = risk.regulatory(research)
    owner_pays = listing_research.get("owner_pays_utilities")
    master = any(f["flag"] == "master_metered" for f in flags) or None
    d = uw.DealInputs(price=l.price, units=units, units_status=units_status, sqft=l.square_footage or (record.square_footage if record else None),
                      year_built=l.year_built or (record.year_built if record else None), state=l.state, cbsa=l.cbsa,
                      rent_cases=rent["per_building"], tax_current_annual=taxes["current_tax_bill"], tax_post_sale_annual=taxes["post_sale_tax_estimate"],
                      post_sale_tax_risk=taxes["post_sale_tax_risk"], insurance_annual=ins, hoa_monthly=l.hoa_fee or (record.hoa_fee if record else None),
                      owner_pays_utilities=owner_pays, master_metered=master, vacant_units=int(listing_research.get("vacant_units") or 0),
                      immediate_rehab=DataPoint(value=float(listing_research["immediate_rehab"]), status=Status.ESTIMATED, source="research file") if listing_research.get("immediate_rehab") else DataPoint.unknown(),
                      rental_license_annual=DataPoint(value=float(research["landlord_law"]["rental_license_fee_annual"]), status=Status.VERIFIED if research.get("landlord_law", {}).get("verified") else Status.ESTIMATED, source="research file") if (research.get("landlord_law") or {}).get("rental_license_fee_annual") else DataPoint.unknown())
    dp_base, rate = cfg.capital.baseline_down_payment_pct, cfg.financing.interest_rate
    base_ex = uw.expense_lines(d, cfg, "conservative")
    base = uw.metrics(d, cfg, dp_base, rate, base_ex) if base_ex.get("gsr") else None
    structures = uw.equity_structures(d, cfg)
    scen = uw.scenarios(d, cfg, dp_base, rate)
    neigh = census.zcta_profile(cache, ttl["census"], l.zip_code) if (api_keys().get("CENSUS_API_KEY") and l.zip_code) else {k: DataPoint.unknown("CENSUS_API_KEY missing — ZIP-level ACS not pulled") for k in ["median_hh_income", "renter_share", "population", "vacancy_rate", "median_hh_income_growth_5y", "population_growth_5y", "crime"]}
    stale = None
    if l.last_seen_date:
        try:
            stale = (datetime.now(timezone.utc) - datetime.fromisoformat(l.last_seen_date.replace("Z", "+00:00"))).days
        except ValueError:
            stale = None
    inc = relocation.incentives(m)
    result: Dict[str, Any] = {
        "listing": {k: v for k, v in l.model_dump().items() if k != "raw"},
        "record": ({k: v for k, v in record.model_dump().items() if k != "raw"} if record else None),
        "units": n, "units_status": units_status.value, "legal_units_verified": bool(listing_research.get("legal_units_verified")),
        "owner_pays_utilities": owner_pays, "listing_stale_days": stale or 0, "fixture": l.fixture,
        "market": {"cbsa": m.cbsa, "name": m.name, "state": m.state, "stage1_rank": m.stage1_rank, "stage1_score": m.stage1_score,
                   "catalyst_score": m.catalyst_score, "catalyst": m.catalyst_components,
                   "rent_to_value_metro": m.metrics["rent_to_value_metro"].v() if "rent_to_value_metro" in m.metrics else None,
                   "employment_growth_1y": m.metrics["employment_growth_1y"].v() if "employment_growth_1y" in m.metrics else None,
                   "unemployment_rate": m.metrics["unemployment_rate"].v() if "unemployment_rate" in m.metrics else None,
                   "hpi_5y_cagr": m.metrics["hpi_5y_cagr"].v() if "hpi_5y_cagr" in m.metrics else None,
                   "hpi_1y": m.metrics["hpi_1y"].v() if "hpi_1y" in m.metrics else None,
                   "living_score": relocation.living_score(m), "living": relocation.living_overlay(m), "incentives": inc},
        "neighborhood": {k: dpd(v) for k, v in neigh.items()},
        "rent": {"per_building": rent["per_building"], "units_used": rent["units_used"], "layout_note": rent["layout_note"], "comps_used": rent["comps_used"],
                 "cases": {k: {kk: vv for kk, vv in v.model_dump().items() if kk != "comps"} for k, v in rent["cases"].items()}},
        "avm": avm, "taxes": {k: (dpd(v) if isinstance(v, DataPoint) else v) for k, v in taxes.items()},
        "insurance": dpd(ins), "insurance_sensitivity": uw.insurance_sensitivity(d, cfg, dp_base, rate) if base else [],
        "hazards": haz, "capex_flags": flags, "rehab_range": dpd(rehab), "regulatory": reg,
        "expenses": base_ex, "base": base, "structures": structures, "rate_sensitivity": uw.rate_sensitivity(d, cfg, dp_base) if base else [],
        "scenarios": scen, "negotiation": uw.negotiation(d, cfg, dp_base, rate) if base else {},
    }
    result["confidence"] = scoring.confidence_score(result)
    result["diligence_items"] = diligence(result)
    return result


def diligence(r: Dict[str, Any]) -> List[str]:
    items = []
    if r["rent"]["per_building"]["contractual"]["base"] is None:
        items.append("Obtain the actual rent roll and leases (contractual rent unknown; seller pro-forma is not contractual).")
    if not r["taxes"]["current_tax_bill"]["known"]:
        items.append("Pull the parcel's latest tax bill and assessed value from the county treasurer/assessor.")
    if r["taxes"]["post_sale_tax_risk"] in ("UNKNOWN", "HIGH"):
        items.append(f"Confirm post-sale reassessment treatment with the county assessor (risk={r['taxes']['post_sale_tax_risk']}).")
    if r["insurance"]["status"] != "VERIFIED":
        items.append("Get a landlord (DP-3 / commercial residential) insurance quote — the estimate here is a table value.")
    if r["units_status"] not in ("PROVIDER DATA", "VERIFIED"):
        items.append("Verify the unit count and legal status (certificate of occupancy / zoning).")
    if r["owner_pays_utilities"] is None:
        items.append("Confirm who pays water/sewer/trash/electric/gas and whether units are separately metered.")
    if r["rent"]["per_building"]["conservative"].get("grade", "D") in ("C", "D"):
        items.append("Rental comps are thin (grade C/D): pull additional comps or a broker opinion of rent.")
    items.append("Inspection: roof/HVAC/water-heater ages, panel type, plumbing material, sewer scope, foundation, lead/asbestos.")
    items.append("Check the parcel on the FEMA flood map; confirm flood insurance requirement.")
    if r["regulatory"]["status"] == "UNKNOWN":
        items.append("Research rental licensing/inspection, deposit limits, eviction timeline and lead rules for the city.")
    return items


def attach_research_and_catalysts(markets: List[MarketProfile], cfg: Config) -> None:
    """Load research/markets/<cbsa>.yaml and compute the catalyst score for every selected market (Stage 1 output)."""
    for m in markets:
        m.research.update(load_research(cfg, m.cbsa))
        cat = appreciation.catalyst_score(m)
        m.catalyst_score, m.catalyst_components = cat["score"], cat


def run_stage2(markets: List[MarketProfile], cfg: Config, cache: Cache, rc: RentCast, fixtures: Optional[List[Listing]] = None,
               max_enrich: Optional[int] = None) -> Dict[str, Any]:
    by_cbsa = {m.cbsa: m for m in markets}
    listings = pull_listings(markets, rc, cfg, fixtures)
    for l in listings:
        cache.store("listings", l.id, l.raw, {"cbsa": l.cbsa})
    candidates = early_filter(listings, by_cbsa, cfg)
    limit = max_enrich or cfg["api_budget"]["rentcast_max_enrich_properties"]
    results, skipped = [], []
    for c in candidates:
        l = c["listing"]
        if len(results) >= limit:
            skipped.append(l.id)
            continue
        try:
            results.append(underwrite_listing(l, by_cbsa[l.cbsa], rc, cache, cfg, by_cbsa[l.cbsa].research))
        except Exception as e:  # never lose the run to one bad listing
            log.exception("underwriting failed for %s: %s", l.formatted_address, e)
    ranks = scoring.rankings(results, cfg)
    return {"listings_pulled": len(listings), "candidates": len(candidates), "underwritten": len(results), "skipped_for_budget": len(skipped),
            "results": results, "rankings": ranks, "triage": [{"id": c["listing"].id, "address": c["listing"].formatted_address, "price": c["listing"].price,
                                                               "proxy_rent_to_price": c["proxy_rent_to_price"], "exception": c["exception"]} for c in candidates]}
