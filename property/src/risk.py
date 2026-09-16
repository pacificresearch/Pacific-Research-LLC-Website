"""Physical hazard flags (never equated to insurance cost), landlord insurance ESTIMATE, capex/diligence flags, regulatory notes."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .config import Config
from .models import DataPoint, Listing, PropertyRecord, Status

CAPEX_KEYWORDS = {
    "knob-and-tube": ["knob and tube", "knob-and-tube"], "federal_pacific_or_zinsco_panel": ["federal pacific", "zinsco", "fpe panel"],
    "galvanized_plumbing": ["galvanized"], "cast_iron_sewer": ["cast iron"], "foundation_issues": ["foundation issue", "foundation repair", "settling"],
    "unpermitted_units": ["unpermitted", "non-conforming", "nonconforming"], "shared_utilities": ["shared utilities", "shared meter", "one meter"],
    "master_metered": ["master meter", "master-meter", "owner pays all utilities", "landlord pays utilities"], "asbestos_risk": ["asbestos"],
    "flood_zone": ["flood zone", "floodplain", "flood plain"], "deferred_maintenance": ["as-is", "as is", "handyman", "needs work", "tlc", "fixer"],
    "tenant_delinquency": ["delinquent", "non-paying", "nonpaying"], "below_market_leases": ["below market"], "month_to_month": ["month to month", "month-to-month", "mtm"],
    "seller_projected_rents": ["pro forma", "proforma", "projected rent", "potential rent", "could rent", "market rent of"], "vacant_units": ["vacant unit", "one vacant", "units vacant", "vacant at closing"],
}


def hazards(state: str, cfg: Config, zip_profile: Optional[dict] = None) -> Dict[str, Any]:
    flags = list(cfg["hazards_by_state"].get(state, []))
    score = min(100, len(flags) * 18 + (20 if any(h in flags for h in ("hurricane", "flood", "wildfire", "earthquake")) else 0))
    return {"physical_hazard_flags": flags, "hazard_score": score,
            "note": "State-level reference flags only (FEMA/NOAA hazard classes). Parcel flood zone must be checked on FEMA NFHL; hazard != premium.",
            "flood_zone": DataPoint.unknown("check FEMA Flood Map Service Center for the parcel")}


def insurance_estimate(listing: Listing, units: int, cfg: Config, quote: Optional[dict] = None) -> DataPoint:
    if quote and quote.get("annual_premium"):
        return DataPoint(value=float(quote["annual_premium"]), status=Status.VERIFIED, source=quote.get("source", "insurance quote"), url=quote.get("url", ""), confidence=0.95, note="actual quote")
    ins = cfg["insurance"]
    rate = ins["state_rate_per_1000"].get(listing.state, ins["default_rate_per_1000"])
    rebuild = max(listing.price or 0, (listing.square_footage or 0) * ins["rebuild_cost_per_sqft"])
    prem = max(ins["default_per_unit_minimum"] * units, rebuild / 1000 * rate)
    return DataPoint.estimated(round(prem), "config insurance table (landlord DP-3/commercial residential, hazard-tiered by state)",
                               f"ESTIMATED: ${rate}/$1,000 on ${rebuild:,.0f} replacement proxy, floor ${ins['default_per_unit_minimum']}/unit. Not a quote. Sensitivity at +25%/+50% shown.", confidence=0.4)


def capex_flags(listing: Listing, record: Optional[PropertyRecord], research: Optional[dict] = None) -> List[Dict[str, str]]:
    flags: List[Dict[str, str]] = []
    text = " ".join(str(listing.raw.get(k, "")) for k in ("description", "remarks", "publicRemarks")).lower()
    for flag, kws in CAPEX_KEYWORDS.items():
        if any(k in text for k in kws):
            flags.append({"flag": flag, "status": "PROVIDER DATA", "note": "keyword in listing remarks — verify"})
    feats = (record.features if record else {}) or {}
    yb = listing.year_built or (record.year_built if record else None)
    for f, label in [("roofType", "roof_age_unknown"), ("heatingType", "hvac_age_unknown"), ("waterHeater", "water_heater_age_unknown")]:
        flags.append({"flag": label, "status": "UNKNOWN", "note": f"{f}: {feats.get(f, 'not in record')} — age not in any source; inspect"})
    if yb and yb < 1978:
        flags.append({"flag": "lead_paint_exposure", "status": "ESTIMATED", "note": f"built {yb} (pre-1978): federal lead disclosure applies; local lead-safe rules may apply"})
    if yb and yb < 1960:
        flags.append({"flag": "old_electrical_panel_possible", "status": "UNKNOWN", "note": f"built {yb}: panel/wiring age unknown; inspect for FPE/Zinsco/fuses"})
        flags.append({"flag": "asbestos_risk", "status": "UNKNOWN", "note": "pre-1980 construction: asbestos-containing materials possible"})
    if yb and yb < 1950:
        flags.append({"flag": "galvanized_or_cast_iron_plumbing_possible", "status": "UNKNOWN", "note": "age-typical; sewer scope recommended"})
    if record is None or record.unit_count is None:
        flags.append({"flag": "unit_count_unverified", "status": "UNKNOWN", "note": "unit count not confirmed by property record; verify legal unit status with zoning/CO"})
    flags.append({"flag": "legal_unit_status_unverified", "status": "UNKNOWN", "note": "confirm certificate of occupancy / zoning for the stated unit count"})
    flags.append({"flag": "utility_responsibility_unverified", "status": "UNKNOWN", "note": "who pays water/sewer/trash/electric/gas is not in any structured source"})
    return flags


def rehab_range(listing: Listing, cfg: Config, flags: List[Dict[str, str]]) -> DataPoint:
    lo, hi = cfg["acquisition_costs"]["rehab_range_if_unknown"]
    evid = [f["flag"] for f in flags if f["status"] == "PROVIDER DATA"]
    if evid:
        hi = hi * 2
    return DataPoint(value={"low": lo, "high": hi}, status=Status.ASSUMED, source="config", confidence=0.2,
                     note=("range widened: listing remarks flag " + ", ".join(evid)) if evid else "no condition evidence; range shown for inspection budgeting only — NOT added to NOI")


def regulatory(research: Optional[dict]) -> Dict[str, Any]:
    keys = ["rent_control", "just_cause_eviction", "eviction_timeline_days", "rental_licensing", "inspection_frequency", "lead_rules",
            "certificate_of_occupancy_rules", "security_deposit_limits", "local_landlord_taxes_fees", "utility_obligations"]
    ll = (research or {}).get("landlord_law") or {}
    out = {k: (ll.get(k) if ll.get(k) not in (None, "") else "UNKNOWN — not yet researched") for k in keys}
    out["sources"] = ll.get("sources", [])
    out["status"] = "VERIFIED" if ll.get("verified") else ("ESTIMATED" if ll else "UNKNOWN")
    known = sum(1 for k in keys if ll.get(k))
    # regulatory friction score: higher = more landlord-adverse; only computed on researched items
    friction = 0
    if str(ll.get("rent_control", "")).lower().startswith(("yes", "true")):
        friction += 40
    if str(ll.get("just_cause_eviction", "")).lower().startswith(("yes", "true")):
        friction += 20
    try:
        if float(ll.get("eviction_timeline_days", 0)) > 90:
            friction += 15
    except (TypeError, ValueError):
        pass
    if str(ll.get("rental_licensing", "")).lower().startswith(("yes", "true")):
        friction += 10
    out["friction_score"] = friction if known else None
    out["coverage"] = f"{known}/{len(keys)} items researched"
    return out
