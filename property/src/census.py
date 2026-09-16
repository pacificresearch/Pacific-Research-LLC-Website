"""Census ACS 5-year: metro (CBSA) universe and ZIP (ZCTA) neighborhood profiles. Works without a key (rate-limited)."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from .config import api_keys
from .database import Cache
from .http_client import HttpError, get_json
from .models import DataPoint, Status

log = logging.getLogger("prg.census")
BASE = "https://api.census.gov/data"
CURRENT_YEAR = 2023      # latest ACS 5-year with metro geography as of this build
PRIOR_YEAR = 2018        # non-overlapping 5-year window for growth

DETAIL_VARS = {
    "population": "B01003_001E",
    "median_hh_income": "B19013_001E",
    "households": "B11001_001E",
    "tenure_total": "B25003_001E",
    "renter_occupied": "B25003_003E",
    "housing_units": "B25002_001E",
    "vacant_units": "B25002_003E",
    "median_home_value": "B25077_001E",
    "median_gross_rent": "B25064_001E",
    "units_in_structure_total": "B25024_001E",
    "units_2": "B25024_004E",
    "units_3_4": "B25024_005E",
    "median_year_built": "B25035_001E",
}
# ACS profile: industry of civilian employed population (for economic-diversity HHI) + unemployment rate
PROFILE_VARS = {
    "ind_agri_mining": "DP03_0033E", "ind_construction": "DP03_0034E", "ind_manufacturing": "DP03_0035E",
    "ind_wholesale": "DP03_0036E", "ind_retail": "DP03_0037E", "ind_transport_util": "DP03_0038E",
    "ind_information": "DP03_0039E", "ind_finance_re": "DP03_0040E", "ind_prof_sci_mgmt": "DP03_0041E",
    "ind_edu_health": "DP03_0042E", "ind_arts_food": "DP03_0043E", "ind_other_svc": "DP03_0044E",
    "ind_public_admin": "DP03_0045E", "acs_unemployment_rate": "DP03_0009PE",
    "per_capita_income": "DP03_0088E", "moved_from_other_state_pct": "DP02_0084PE" ,
}
METRO_GEO = "metropolitan statistical area/micropolitan statistical area"


def _key_param() -> dict:
    k = api_keys().get("CENSUS_API_KEY")
    return {"key": k} if k else {}


def _num(x) -> Optional[float]:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if v <= -111111111 or v < -1e8:   # Census sentinel for N/A (-666666666 etc.)
        return None
    return v


def _fetch_table(cache: Cache, ttl: float, year: int, dataset: str, variables: Dict[str, str],
                 geo_for: str, geo_in: str = "") -> List[dict]:
    url = f"{BASE}/{year}/{dataset}"
    params = {"get": "NAME," + ",".join(variables.values()), "for": geo_for}
    if geo_in:
        params["in"] = geo_in
    inv = {v: k for k, v in variables.items()}

    def fetch():
        try:
            data = get_json(url, {**params, **_key_param()})
        except HttpError as e:
            log.warning("census %s %s failed: %s", year, dataset, e)
            return None
        cache.log_call("census", f"{year}/{dataset}", cached=False, status=200)
        return data

    data, _ = cache.cached("census", url, params, ttl, fetch, endpoint=f"{year}/{dataset}")
    if not data:
        return []
    header, rows = data[0], data[1:]
    out = []
    for row in rows:
        rec = {"NAME": row[header.index("NAME")]}
        for h, val in zip(header, row):
            if h in inv:
                rec[inv[h]] = _num(val)
            elif h not in ("NAME",):
                rec[h] = val
        out.append(rec)
    return out


def metro_universe(cache: Cache, ttl: float) -> Dict[str, dict]:
    """All metros with current + prior ACS detail vars and current profile vars, keyed by CBSA."""
    cur = _fetch_table(cache, ttl, CURRENT_YEAR, "acs/acs5", DETAIL_VARS, f"{METRO_GEO}:*")
    prior = _fetch_table(cache, ttl, PRIOR_YEAR, "acs/acs5",
                         {k: DETAIL_VARS[k] for k in ["population", "median_hh_income", "households", "median_home_value", "median_gross_rent"]},
                         f"{METRO_GEO}:*")
    prof = _fetch_table(cache, ttl, CURRENT_YEAR, "acs/acs5/profile", PROFILE_VARS, f"{METRO_GEO}:*")
    prior_by = {r[METRO_GEO]: r for r in prior}
    prof_by = {r[METRO_GEO]: r for r in prof}
    out: Dict[str, dict] = {}
    for r in cur:
        cbsa = r[METRO_GEO]
        rec = dict(r)
        p = prior_by.get(cbsa, {})
        for k in ["population", "median_hh_income", "households", "median_home_value", "median_gross_rent"]:
            rec[f"{k}_prior"] = p.get(k)
        rec.update({k: v for k, v in prof_by.get(cbsa, {}).items() if k != "NAME"})
        rec["cbsa"] = cbsa
        rec["is_metro"] = "Metro Area" in r["NAME"]
        out[cbsa] = rec
    return out


def zcta_profile(cache: Cache, ttl: float, zip_code: str) -> Dict[str, DataPoint]:
    """ZIP-level neighborhood profile (ACS 5-year ZCTA). Returns DataPoints; UNKNOWN when unavailable."""
    src = f"Census ACS {CURRENT_YEAR-4}-{CURRENT_YEAR} 5-year, ZCTA {zip_code}"
    url = f"{BASE}/{CURRENT_YEAR}/acs/acs5"
    cur = _fetch_table(cache, ttl, CURRENT_YEAR, "acs/acs5", DETAIL_VARS, f"zip code tabulation area:{zip_code}")
    prior = _fetch_table(cache, ttl, PRIOR_YEAR, "acs/acs5",
                         {k: DETAIL_VARS[k] for k in ["population", "median_hh_income", "median_home_value"]},
                         f"zip code tabulation area:{zip_code}", geo_in="state:*")
    out: Dict[str, DataPoint] = {}
    if not cur:
        for k in ["median_hh_income", "renter_share", "population", "vacancy_rate", "median_home_value", "income_growth_5y", "population_growth_5y"]:
            out[k] = DataPoint.unknown("ACS ZCTA data not returned for this ZIP")
        return out
    r = cur[0]
    p = prior[0] if prior else {}

    def dp(v, note=""):
        return DataPoint.provider(v, src, url, data_date=str(CURRENT_YEAR), confidence=0.75, note=note) if v is not None else DataPoint.unknown(note or "not reported")

    out["population"] = dp(r.get("population"))
    out["median_hh_income"] = dp(r.get("median_hh_income"))
    out["median_home_value"] = dp(r.get("median_home_value"))
    out["median_gross_rent"] = dp(r.get("median_gross_rent"))
    if r.get("tenure_total") and r.get("renter_occupied") is not None:
        out["renter_share"] = dp(round(r["renter_occupied"] / r["tenure_total"], 3))
    else:
        out["renter_share"] = DataPoint.unknown()
    if r.get("housing_units") and r.get("vacant_units") is not None:
        out["vacancy_rate"] = dp(round(r["vacant_units"] / r["housing_units"], 3), "gross ACS vacancy incl. seasonal/for-sale")
    else:
        out["vacancy_rate"] = DataPoint.unknown()
    if r.get("units_in_structure_total") and r.get("units_2") is not None and r.get("units_3_4") is not None:
        out["small_mf_share"] = dp(round((r["units_2"] + r["units_3_4"]) / r["units_in_structure_total"], 3))
    out["median_year_built"] = dp(r.get("median_year_built"))
    for k in ["population", "median_hh_income", "median_home_value"]:
        a, b = p.get(k), r.get(k)
        if a and b:
            out[f"{k}_growth_5y"] = DataPoint.provider(round(b / a - 1, 4), f"{src} vs {PRIOR_YEAR-4}-{PRIOR_YEAR}", url, data_date=f"{PRIOR_YEAR}->{CURRENT_YEAR}", confidence=0.7)
        else:
            out[f"{k}_growth_5y"] = DataPoint.unknown("prior-period ZCTA not available")
    out["crime"] = DataPoint.unknown("No reliable granular crime source wired; do not invent a score. Check local PD open-data portal for the finalist.")
    return out


def industry_hhi(rec: dict) -> Optional[float]:
    """Herfindahl index of employment by 13 ACS industries (0..1). Higher = more concentrated."""
    vals = [rec.get(k) for k in PROFILE_VARS if k.startswith("ind_")]
    vals = [v for v in vals if v]
    tot = sum(vals)
    if not tot:
        return None
    return round(sum((v / tot) ** 2 for v in vals), 4)
