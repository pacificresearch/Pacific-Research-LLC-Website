"""Three rent cases per property. Per-unit comps -> per-building RANGE. Never an invented exact gross rent."""
from __future__ import annotations

import logging
import statistics
from typing import Any, Dict, List, Optional

from .config import Config
from .models import Listing, PropertyRecord, RentComp, RentEstimate, Status
from .rentcast import RentCast

log = logging.getLogger("prg.rent")


def _grade(n: int, radius: float, age: int, cfg: Config) -> str:
    g = cfg["rent_analysis"]["min_comps_for_grade"]
    if n >= g["A"] and radius <= 1.0 and age <= 90:
        return "A"
    if n >= g["B"] and radius <= 2.0 and age <= 180:
        return "B"
    if n >= g["C"]:
        return "C"
    return "D"


def _layout(listing: Listing, units: Optional[int]) -> tuple[Optional[float], str]:
    """Bedrooms per unit if the building's total bedrooms divide evenly; else None."""
    if not units or not listing.bedrooms:
        return None, "unit-by-unit layout UNKNOWN (no per-unit bedroom data)"
    per = listing.bedrooms / units
    if abs(per - round(per)) < 1e-6 and 1 <= per <= 4:
        return float(round(per)), f"ASSUMED similar layouts: {units} units x {int(per)}BR each (total listing bedrooms {int(listing.bedrooms)} divide evenly) — DISCLOSED ASSUMPTION"
    return None, f"layouts differ or unknown ({listing.bedrooms} bedrooms across {units} units)"


def _select_comps(comps: List[RentComp], bed: Optional[float], sqft_per_unit: Optional[float]) -> List[RentComp]:
    out = []
    for c in comps:
        if c.price <= 200 or c.price > 6000:
            continue
        if bed is not None and c.bedrooms is not None and abs(c.bedrooms - bed) > 0.5:
            continue
        if c.property_type and c.property_type.lower() in ("land", "manufactured"):
            continue
        out.append(c)
    if sqft_per_unit and len(out) > 6:
        sized = [c for c in out if c.square_footage and 0.6 * sqft_per_unit <= c.square_footage <= 1.6 * sqft_per_unit]
        if len(sized) >= 4:
            out = sized
    return out


def analyze(listing: Listing, record: Optional[PropertyRecord], units: Optional[int], rc: RentCast, cfg: Config,
            contractual: Optional[Dict[str, Any]] = None, avm: Optional[dict] = None) -> Dict[str, Any]:
    """Returns {'cases': {case: RentEstimate}, 'per_building': {case: {low, base, high, status, grade}}, 'comps_used': [...]}"""
    ra = cfg["rent_analysis"]
    n = units or listing.unit_count_hint or 2
    bed, layout_note = _layout(listing, units)
    sqft_unit = (listing.square_footage / n) if listing.square_footage and n else None
    comps: List[RentComp] = []
    radius_used, age_used = ra["comp_radius_miles"][0], ra["comp_max_age_days"][0]
    if rc.available and listing.latitude and listing.longitude:
        for radius in ra["comp_radius_miles"]:
            for age in ra["comp_max_age_days"]:
                raw = rc.rental_listings_near(listing.latitude, listing.longitude, radius, age)
                comps = _select_comps(raw, bed, sqft_unit)
                radius_used, age_used = radius, age
                if len(comps) >= ra["min_comps_for_grade"]["B"]:
                    break
            if len(comps) >= ra["min_comps_for_grade"]["B"]:
                break
    elif listing.fixture and listing.raw.get("_fixture_comps"):
        comps = _select_comps([RentComp(**c) for c in listing.raw["_fixture_comps"]], bed, sqft_unit)

    cases: Dict[str, RentEstimate] = {}
    # 1) contractual — only from a reliable supplied source (research file / verified rent roll). Never seller pro-forma.
    if contractual and contractual.get("monthly_gross") and contractual.get("source"):
        cases["contractual"] = RentEstimate(case="contractual", low=contractual["monthly_gross"], base=contractual["monthly_gross"],
                                            high=contractual["monthly_gross"], status=Status.VERIFIED if contractual.get("verified") else Status.PROVIDER,
                                            method=f"contractual rent roll: {contractual['source']}", grade="A" if contractual.get("verified") else "B")
    else:
        cases["contractual"] = RentEstimate(case="contractual", status=Status.UNKNOWN, method="no reliable contractual rent source (seller-projected rents are NOT contractual)")

    prices = sorted(c.price for c in comps)
    if prices:
        q = statistics.quantiles(prices, n=4) if len(prices) >= 4 else [prices[0], statistics.median(prices), prices[-1]]
        low_u, base_u, high_u = q[0], statistics.median(prices), q[2]
        dists = [c.distance_miles for c in comps if c.distance_miles is not None]
        ages = [c.days_old for c in comps if c.days_old is not None]
        grade = _grade(len(comps), radius_used, age_used, cfg)
        med_d = statistics.median(dists) if dists else None
        med_a = statistics.median(ages) if ages else None
        method = f"{len(comps)} active rental comps within {radius_used} mi / {age_used} d; per-unit 25th pct / median / 75th pct" + (f"; matched {int(bed)}BR" if bed else "; bedroom match unavailable — all unit types")
        cases["conservative"] = RentEstimate(case="conservative", low=round(low_u), base=round(min(base_u, low_u * 1.10 if grade in "CD" else base_u)), high=round(base_u),
                                             n_comps=len(comps), median_comp_distance=med_d, median_comp_age_days=med_a, grade=grade,
                                             status=Status.ESTIMATED, method=method + " (conservative: base capped near low quartile when comps are weak)", comps=comps[:15], layout_assumption=layout_note)
        cases["market_upside"] = RentEstimate(case="market_upside", low=round(base_u), base=round(high_u), high=round(high_u * 1.05),
                                              n_comps=len(comps), median_comp_distance=med_d, median_comp_age_days=med_a, grade=grade,
                                              status=Status.ESTIMATED, method=method + " (upside: 75th pct; +5% only as a ceiling, no unverified rent growth)", comps=comps[:15], layout_assumption=layout_note)
    elif avm and avm.get("rent"):
        # AVM is PER UNIT. Only usable for the building when layouts are similar (disclosed); otherwise a wide range with grade D.
        rent, lo, hi = avm["rent"], avm.get("rentRangeLow") or avm["rent"] * 0.85, avm.get("rentRangeHigh") or avm["rent"] * 1.15
        if bed is not None:
            method, grade = f"RentCast rent AVM per unit x {n} similar units — {layout_note}", "C"
        else:
            method, grade = "RentCast per-unit rent AVM; layouts unknown so range widened and confidence D", "D"
            lo, hi = lo * 0.85, hi
        cases["conservative"] = RentEstimate(case="conservative", low=round(lo), base=round(lo if grade == "D" else (lo + rent) / 2), high=round(rent), status=Status.ESTIMATED, method=method, grade=grade, layout_assumption=layout_note)
        cases["market_upside"] = RentEstimate(case="market_upside", low=round(rent), base=round(hi), high=round(hi), status=Status.ESTIMATED, method=method, grade=grade, layout_assumption=layout_note)
    else:
        for case in ("conservative", "market_upside"):
            cases[case] = RentEstimate(case=case, status=Status.UNKNOWN, method="no rental comps and no AVM available", layout_assumption=layout_note)

    per_building: Dict[str, Dict[str, Any]] = {}
    for case, est in cases.items():
        if est.base is None:
            per_building[case] = {"low": None, "base": None, "high": None, "status": est.status.value, "grade": est.grade, "note": est.method}
            continue
        mult = 1 if case == "contractual" else n
        per_building[case] = {"low": round(est.low * mult), "base": round(est.base * mult), "high": round(est.high * mult), "status": est.status.value,
                              "grade": est.grade, "note": (f"per-unit x {n} units; " if mult > 1 else "") + est.method,
                              "n_comps": est.n_comps, "median_comp_distance": est.median_comp_distance, "median_comp_age_days": est.median_comp_age_days}
    return {"cases": cases, "per_building": per_building, "units_used": n, "layout_note": layout_note,
            "comps_used": [c.model_dump() for c in comps[:15]]}
