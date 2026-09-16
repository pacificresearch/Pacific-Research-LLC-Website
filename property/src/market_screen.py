"""STAGE 1 — screen every US metro with public data; pick ~20-30 for RentCast. Seeds always included.
Base universe: Census Population Estimates (all MSAs). Joined: Zillow ZHVI/ZORI, FHFA HPI, BLS LAUS, Census BPS, ACS (key), FRED (key)."""
from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional

from . import bls, census, fhfa, fred, permits, public_data
from .config import Config, api_keys
from .database import Cache
from .models import DataPoint, MarketProfile

log = logging.getLogger("prg.stage1")


def _state_of(name: str) -> str:
    m = re.search(r",\s*([A-Z]{2})", name)
    return m.group(1) if m else ""


def _cities_of(name: str) -> List[str]:
    return [c.strip() for c in name.split(",")[0].split("-") if c.strip()]


def _pct_rank(values: Dict[str, Optional[float]], higher_is_better: bool = True) -> Dict[str, float]:
    known = {k: v for k, v in values.items() if v is not None}
    if not known:
        return {}
    ordered = sorted(known, key=lambda k: known[k], reverse=higher_is_better)
    n = len(ordered)
    return {k: 1 - i / max(n - 1, 1) for i, k in enumerate(ordered)}


def _momentum_score(cagr: Optional[float]) -> Optional[float]:
    """Moderate positive HPI momentum scores best; negative and overheated (>10%/yr) score low."""
    if cagr is None:
        return None
    if cagr < 0:
        return max(0.0, 0.4 + cagr * 4)
    if cagr <= 0.06:
        return 0.6 + cagr / 0.06 * 0.4
    return max(0.2, 1.0 - (cagr - 0.06) * 8)


def run_stage1(cfg: Config, cache: Cache, budgets: dict) -> tuple[List[MarketProfile], List[MarketProfile], dict]:
    """Returns (selected_markets, full_universe_ranked, source_status)."""
    ttl = cfg["run"]["cache_ttl_hours"]
    status: Dict[str, str] = {}
    pop = public_data.popest_metros(cache, ttl["census"])
    status["census_popest"] = f"{len(pop)} MSAs" if pop else "FAILED"
    zil = public_data.zillow_metros(cache, ttl["census"])
    status["zillow_zhvi_zori"] = f"{len(zil)} metros" if zil else "FAILED"
    hpi = fhfa.load_hpi(cache, ttl["fhfa"])
    status["fhfa_hpi"] = f"{len(hpi) - 1} MSAs" if hpi else "FAILED"
    laus = public_data.laus_metros(cache, ttl["bls"])
    status["bls_laus"] = f"{len(laus)} metros" if laus else "FAILED"
    acs = census.metro_universe(cache, ttl["census"]) if api_keys().get("CENSUS_API_KEY") else {}
    status["census_acs"] = f"{len(acs)} metros" if acs else "SKIPPED (CENSUS_API_KEY missing) — income, renter share, 2-4 unit stock share, vacancy UNKNOWN"
    bps = permits.load_permits(cache, ttl["permits"])
    status["census_bps_permits"] = f"{len(bps)} CBSAs" if bps else "FAILED"

    seeds = {s["cbsa"] for s in cfg["seed_markets"]}
    seed_cities: Dict[str, List[str]] = {}
    for s in cfg["seed_markets"]:
        seed_cities.setdefault(s["cbsa"], []).append(s["city"])
    lo, hi = cfg["run"]["stage1_universe_min_pop"], cfg["run"]["stage1_universe_max_pop"]
    weights = cfg["market_screen_weights"]
    comp: Dict[str, Dict[str, Optional[float]]] = {k: {} for k in weights}
    profiles: Dict[str, MarketProfile] = {}

    for cbsa, pr in pop.items():
        p24 = pr["pop_2024"]
        if not (lo <= p24 <= hi) and cbsa not in seeds:
            continue
        p = MarketProfile(cbsa=cbsa, name=pr["name"], state=_state_of(pr["name"]), seed=cbsa in seeds)
        m = p.metrics
        psrc = "Census Population Estimates Program, Vintage 2024 (CBSA)"
        m["population"] = DataPoint.provider(p24, psrc, public_data.POPEST_URL, "2024-07-01", 0.9)
        m["population_growth_4y"] = DataPoint.provider(round(pr["growth_4y"], 4), psrc, public_data.POPEST_URL, "2020->2024", 0.9) if pr["growth_4y"] is not None else DataPoint.unknown()
        m["domestic_migration_per_1000"] = DataPoint.provider(round(pr["dom_mig_per_1000"], 2), psrc, public_data.POPEST_URL, "2022-2024 avg", 0.9, "net domestic migration per 1,000 residents") if pr["dom_mig_per_1000"] is not None else DataPoint.unknown()
        m["net_migration_per_1000"] = DataPoint.provider(round(pr["net_mig_per_1000"], 2), psrc, public_data.POPEST_URL, "2022-2024 avg", 0.9, "net migration incl. international per 1,000 residents") if pr["net_mig_per_1000"] is not None else DataPoint.unknown()
        z = zil.get(public_data.zillow_key_for(pr["name"]), {})
        zsrc = "Zillow Research ZHVI (mid-tier, SA) / ZORI (metro)"
        m["typical_home_value"] = DataPoint.provider(round(z["zhvi"]), zsrc, public_data.ZHVI_URL, z["zhvi_date"], 0.8) if z.get("zhvi") else DataPoint.unknown("metro not in Zillow file")
        m["typical_rent"] = DataPoint.provider(round(z["zori"]), zsrc, public_data.ZORI_URL, z.get("zori_date", ""), 0.8, "ZORI is all-rental-types asking rent; metro proxy only") if z.get("zori") else DataPoint.unknown("metro not in ZORI file")
        rtv = (z["zori"] * 12 / z["zhvi"]) if z.get("zori") and z.get("zhvi") else None
        m["rent_to_value_metro"] = DataPoint.estimated(round(rtv, 4), zsrc, "ZORI x12 / ZHVI — metro proxy, not a property metric", public_data.ZHVI_URL, 0.7) if rtv else DataPoint.unknown()
        m["rent_growth_1y"] = DataPoint.provider(round(z["zori_1y"], 4), zsrc, public_data.ZORI_URL, z.get("zori_date", ""), 0.8) if z.get("zori_1y") is not None else DataPoint.unknown()
        m["zhvi_1y"] = DataPoint.provider(round(z["zhvi_1y"], 4), zsrc, public_data.ZHVI_URL, z.get("zhvi_date", ""), 0.8) if z.get("zhvi_1y") is not None else DataPoint.unknown()
        m.update(fhfa.hpi_metrics(hpi, cbsa, pr["name"]))
        l = laus.get(cbsa, {})
        lsrc = "BLS LAUS metro (flat file)"
        m["unemployment_rate"] = DataPoint.provider(l["unemployment_rate"], lsrc, public_data.LAUS_URL, l.get("period", ""), 0.9) if l.get("unemployment_rate") is not None else DataPoint.unknown("LAUS series not in file (New England NECTA or micro)")
        m["unemployment_rate_yoy_change"] = DataPoint.provider(round(l["unemployment_rate_yoy_change"], 2), lsrc, public_data.LAUS_URL, l.get("period", ""), 0.9) if l.get("unemployment_rate_yoy_change") is not None else DataPoint.unknown()
        m["employment_growth_1y"] = DataPoint.provider(round(l["employment_growth_1y"], 4), lsrc, public_data.LAUS_URL, l.get("period", ""), 0.9) if l.get("employment_growth_1y") is not None else DataPoint.unknown()
        m["employment_level"] = DataPoint.provider(l["employment_level"], lsrc, public_data.LAUS_URL, l.get("period", ""), 0.9) if l.get("employment_level") else DataPoint.unknown()
        a = acs.get(cbsa, {})
        asrc = f"Census ACS {census.CURRENT_YEAR} 5-year (metro)"
        aurl = f"{census.BASE}/{census.CURRENT_YEAR}/acs/acs5"
        def adp(v, note=""):
            return DataPoint.provider(v, asrc, aurl, str(census.CURRENT_YEAR), 0.85, note) if v is not None else DataPoint.unknown(note or ("CENSUS_API_KEY missing" if not acs else "not reported"))
        m["median_hh_income"] = adp(a.get("median_hh_income"))
        smf = ((a["units_2"] + a["units_3_4"]) / a["units_in_structure_total"]) if a.get("units_in_structure_total") and a.get("units_2") is not None else None
        m["small_mf_share"] = adp(round(smf, 4) if smf else None, "share of housing units in 2-4 unit structures")
        rs = (a["renter_occupied"] / a["tenure_total"]) if a.get("tenure_total") else None
        m["renter_share"] = adp(round(rs, 4) if rs else None)
        vac = (a["vacant_units"] / a["housing_units"]) if a.get("housing_units") else None
        m["vacancy_rate"] = adp(round(vac, 4) if vac else None, "gross ACS vacancy")
        ig = (a["median_hh_income"] / a["median_hh_income_prior"] - 1) if a.get("median_hh_income") and a.get("median_hh_income_prior") else None
        m["median_hh_income_growth_5y"] = adp(round(ig, 4) if ig is not None else None)
        hhi = census.industry_hhi(a) if a else None
        m["industry_hhi"] = DataPoint.estimated(hhi, asrc, "Herfindahl of employment across 13 ACS industries; >0.15 = concentrated", aurl, 0.7) if hhi else DataPoint.unknown("needs CENSUS_API_KEY")
        m.update(permits.permits_metrics(bps, cbsa, p24))
        pg, pp = m["population_growth_4y"].v(), m["permits_per_1000_pop"].v()
        if pg is not None and pp is not None and pg / 4 * 1000 > 0.5:
            ratio = pp / (pg / 4 * 1000)
            m["permits_vs_pop_growth"] = DataPoint.estimated(round(ratio, 2), "Census BPS / PEP", "permitted units per net new resident (per-1000 basis); <0.4 supply-constrained, >1.0 ample supply", confidence=0.6)
        else:
            m["permits_vs_pop_growth"] = DataPoint.unknown("population flat/declining or permits unknown")
        p.research["cities"] = seed_cities.get(cbsa) or _cities_of(pr["name"])[:2]
        profiles[cbsa] = p

        comp["rent_to_value"][cbsa] = rtv
        comp["affordability"][cbsa] = (max(0.0, min(1.0, (500000 - z["zhvi"]) / 250000)) if z.get("zhvi") else None)
        comp["small_multifamily_stock"][cbsa] = smf
        comp["insurance_cost"][cbsa] = cfg["insurance"]["state_rate_per_1000"].get(p.state, cfg["insurance"]["default_rate_per_1000"])
        comp["population_growth"][cbsa] = pr["growth_4y"]
        comp["net_migration"][cbsa] = pr["dom_mig_per_1000"]
        comp["income_growth"][cbsa] = ig
        comp["unemployment"][cbsa] = l.get("unemployment_rate")
        comp["hpi_momentum"][cbsa] = _momentum_score(m["hpi_3y_cagr"].v())
        comp["vacancy"][cbsa] = vac

    active = {k: w for k, w in weights.items() if any(v is not None for v in comp[k].values())}
    wsum = sum(active.values())
    status["stage1_components_active"] = ", ".join(f"{k}={w / wsum:.2f}" for k, w in active.items())
    ranked: Dict[str, Dict[str, float]] = {}
    for key in active:
        vals = comp[key]
        if key in ("affordability", "hpi_momentum"):
            r_ = {k: v for k, v in vals.items() if v is not None}
        else:
            r_ = _pct_rank(vals, key not in ("unemployment", "vacancy", "insurance_cost"))
        for cbsa, s in r_.items():
            ranked.setdefault(cbsa, {})[key] = round(s, 3)
    for cbsa, p in profiles.items():
        c = ranked.get(cbsa, {})
        p.stage1_components = c
        p.stage1_score = round(sum(active[k] / wsum * c.get(k, 0.5) for k in active) * 100, 1)
        p.stage1_components["_missing"] = [k for k in active if k not in c]

    ordered = sorted(profiles.values(), key=lambda p: p.stage1_score or 0, reverse=True)
    for i, p in enumerate(ordered, 1):
        p.stage1_rank = i
    n_out = cfg["run"]["stage1_markets_out"]
    selected = [p for p in ordered if p.seed]
    for p in ordered:
        if len(selected) >= n_out:
            break
        if not p.seed:
            selected.append(p)
    selected.sort(key=lambda p: p.stage1_rank or 0)
    log.info("Stage 1: %d metros screened; %d selected (%d seeds)", len(ordered), len(selected), sum(p.seed for p in selected))

    # wages via BLS API (QCEW) for the selected set only; FRED optional
    wages = bls.metro_wages(cache, ttl["bls"], [p.cbsa for p in selected], budgets["bls"])
    for p in selected:
        p.metrics.update(wages.get(p.cbsa, {}))
        p.metrics.update(fred.metro_series(cache, ttl["fred"], p.cbsa))
    return selected, ordered, status
